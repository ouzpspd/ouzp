import json
from channels.generic.websocket import AsyncWebsocketConsumer

from asyncio import sleep

# class AChatConsumer(WebsocketConsumer):
#     def connect(self):
#         self.accept()
#
#     def disconnect(self, close_code):
#         pass
#
#     def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         message = text_data_json['message']
#         time.sleep(10)
#         self.send(text_data=json.dumps({
#             'message': message
#         }))


class ChatConsumer(AsyncWebsocketConsumer):
    # async def connect(self):
    #     await self.accept()
    #
    # async def disconnect(self, close_code):
    #     pass

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        await sleep(120)
        await self.send(text_data=json.dumps({
            'message': message
        }))