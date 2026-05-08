from django.urls import re_path

from .consumers import FuelUpdatesConsumer

websocket_urlpatterns = [
    re_path(r"ws/updates/$", FuelUpdatesConsumer.as_asgi()),
]
