import json

from channels.generic.websocket import AsyncWebsocketConsumer


class FuelUpdatesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("fuel_updates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("fuel_updates", self.channel_name)

    async def requests_updated(self, event):
        await self.send(text_data=json.dumps(event["message"]))
