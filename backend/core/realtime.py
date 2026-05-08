from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_requests_updated():
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        "fuel_updates",
        {"type": "requests.updated", "message": {"event": "requests_updated"}},
    )
