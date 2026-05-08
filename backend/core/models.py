from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_USER = "USER"
    ROLE_BUNK = "BUNK"
    ROLE_CHOICES = [
        (ROLE_USER, "Traveler"),
        (ROLE_BUNK, "Petrol Bunk"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    bunk_name = models.CharField(max_length=120, blank=True)
    is_available = models.BooleanField(default=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class FuelRequest(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_ACCEPTED = "ACCEPTED"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    FUEL_PETROL = "PETROL"
    FUEL_DIESEL = "DIESEL"
    FUEL_CHOICES = [
        (FUEL_PETROL, "Petrol"),
        (FUEL_DIESEL, "Diesel"),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fuel_requests")
    assigned_bunk = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_requests",
        null=True,
        blank=True,
    )
    fuel_type = models.CharField(max_length=10, choices=FUEL_CHOICES)
    quantity_liters = models.DecimalField(max_digits=6, decimal_places=2)
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_note = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    service_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=12, default="UNPAID")
    payment_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.id} {self.fuel_type} {self.quantity_liters}L - {self.status}"
