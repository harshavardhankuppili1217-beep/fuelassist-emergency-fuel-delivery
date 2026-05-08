import math
import random

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import FuelRequest, UserProfile
from .realtime import broadcast_requests_updated
from .serializers import FuelRequestSerializer, RegisterSerializer, UserSerializer


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data
    user = User.objects.create_user(
        username=payload["username"],
        password=payload["password"],
        email=payload.get("email", ""),
    )
    UserProfile.objects.create(
        user=user,
        role=payload["role"],
        phone=payload.get("phone", ""),
        bunk_name=payload.get("bunk_name", ""),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
    )
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user": UserSerializer(user).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username", "")
    password = request.data.get("password", "")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["GET"])
def me_view(request):
    return Response(UserSerializer(request.user).data)


@api_view(["GET", "POST"])
def fuel_requests_view(request):
    user = request.user
    profile = getattr(user, "profile", None)
    if not profile:
        return Response({"detail": "User profile not found."}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == "POST":
        if profile.role != UserProfile.ROLE_USER:
            return Response({"detail": "Only users can create requests."}, status=status.HTTP_403_FORBIDDEN)
        serializer = FuelRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fuel_request = serializer.save(customer=user, status=FuelRequest.STATUS_PENDING)

        nearby_bunks = User.objects.filter(
            profile__role=UserProfile.ROLE_BUNK,
            profile__is_available=True,
            profile__latitude__isnull=False,
            profile__longitude__isnull=False,
        ).select_related("profile")
        closest_bunk = None
        min_distance = None
        for bunk in nearby_bunks:
            distance = haversine_km(
                fuel_request.latitude,
                fuel_request.longitude,
                bunk.profile.latitude,
                bunk.profile.longitude,
            )
            if min_distance is None or distance < min_distance:
                min_distance = distance
                closest_bunk = bunk
        if closest_bunk:
            fuel_request.assigned_bunk = closest_bunk
            fuel_request.save(update_fields=["assigned_bunk", "updated_at"])

        broadcast_requests_updated()
        return Response(FuelRequestSerializer(fuel_request).data, status=status.HTTP_201_CREATED)

    if profile.role == UserProfile.ROLE_USER:
        queryset = FuelRequest.objects.filter(customer=user)
    else:
        queryset = FuelRequest.objects.filter(status=FuelRequest.STATUS_PENDING, assigned_bunk__isnull=True) | FuelRequest.objects.filter(
            assigned_bunk=user
        )
    items = []
    for item in queryset.distinct().select_related("assigned_bunk", "assigned_bunk__profile"):
        data = FuelRequestSerializer(item).data
        if profile.role == UserProfile.ROLE_BUNK and profile.latitude is not None and profile.longitude is not None:
            data["distance_km"] = round(
                haversine_km(profile.latitude, profile.longitude, item.latitude, item.longitude), 2
            )
        items.append(data)
    return Response(items)


@api_view(["POST"])
def accept_request_view(request, request_id):
    user = request.user
    profile = getattr(user, "profile", None)
    if not profile or profile.role != UserProfile.ROLE_BUNK:
        return Response({"detail": "Only petrol bunks can accept requests."}, status=status.HTTP_403_FORBIDDEN)
    fuel_request = FuelRequest.objects.filter(id=request_id).first()
    if not fuel_request:
        return Response({"detail": "Request not found."}, status=status.HTTP_404_NOT_FOUND)
    if fuel_request.status != FuelRequest.STATUS_PENDING:
        return Response({"detail": "Request is no longer pending."}, status=status.HTTP_400_BAD_REQUEST)

    fuel_request.assigned_bunk = user
    fuel_request.status = FuelRequest.STATUS_ACCEPTED
    fuel_request.save(update_fields=["assigned_bunk", "status", "updated_at"])
    broadcast_requests_updated()
    return Response(FuelRequestSerializer(fuel_request).data)


@api_view(["POST"])
def complete_request_view(request, request_id):
    user = request.user
    fuel_request = FuelRequest.objects.filter(id=request_id, assigned_bunk=user).first()
    if not fuel_request:
        return Response({"detail": "Assigned request not found."}, status=status.HTTP_404_NOT_FOUND)
    if fuel_request.status != FuelRequest.STATUS_ACCEPTED:
        return Response({"detail": "Only accepted requests can be completed."}, status=status.HTTP_400_BAD_REQUEST)

    fuel_request.status = FuelRequest.STATUS_COMPLETED
    fee = request.data.get("service_fee")
    if fee is not None:
        fuel_request.service_fee = fee
    fuel_request.save(update_fields=["status", "service_fee", "updated_at"])
    broadcast_requests_updated()
    return Response(FuelRequestSerializer(fuel_request).data)


@api_view(["POST"])
def pay_request_view(request, request_id):
    user = request.user
    fuel_request = FuelRequest.objects.filter(id=request_id, customer=user).first()
    if not fuel_request:
        return Response({"detail": "Request not found."}, status=status.HTTP_404_NOT_FOUND)
    if fuel_request.status != FuelRequest.STATUS_COMPLETED:
        return Response({"detail": "Payment is available after completion."}, status=status.HTTP_400_BAD_REQUEST)

    fuel_request.payment_status = "PAID"
    fuel_request.payment_reference = f"PAY-{fuel_request.id}-{random.randint(1000, 9999)}"
    fuel_request.save(update_fields=["payment_status", "payment_reference", "updated_at"])
    broadcast_requests_updated()
    return Response(FuelRequestSerializer(fuel_request).data)
