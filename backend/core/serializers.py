from django.contrib.auth.models import User
from rest_framework import serializers

from .models import FuelRequest, UserProfile


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bunk_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_role(self, value):
        if value not in [UserProfile.ROLE_USER, UserProfile.ROLE_BUNK]:
            raise serializers.ValidationError("Invalid role")
        return value

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["role", "phone", "bunk_name", "is_available", "latitude", "longitude"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]


class FuelRequestSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.username", read_only=True)
    bunk_name = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(read_only=True)

    class Meta:
        model = FuelRequest
        fields = [
            "id",
            "customer",
            "customer_name",
            "assigned_bunk",
            "bunk_name",
            "fuel_type",
            "quantity_liters",
            "latitude",
            "longitude",
            "location_note",
            "status",
            "service_fee",
            "payment_status",
            "payment_reference",
            "distance_km",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "customer",
            "assigned_bunk",
            "status",
            "created_at",
            "updated_at",
        ]

    def get_bunk_name(self, obj):
        if obj.assigned_bunk and hasattr(obj.assigned_bunk, "profile"):
            return obj.assigned_bunk.profile.bunk_name or obj.assigned_bunk.username
        return None
