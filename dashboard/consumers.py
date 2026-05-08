import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PostureConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("posture_dashboard", self.channel_name)
        await self.accept()
        print("[WS] Client connecté")

    async def disconnect(self, code):
        await self.channel_layer.group_discard("posture_dashboard", self.channel_name)

    async def posture_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))