from django.contrib import admin

from .models import FuelRequest, UserProfile

admin.site.register(UserProfile)
admin.site.register(FuelRequest)

# Register your models here.
