import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async

from chat.serializers import MessageWritableSerializer, MessageSerializer
from event.models import Event


class ChatConsumer(AsyncWebsocketConsumer):
    SOCKET_EVENT_TYPE = "chat_message"
    event_id: int

    @property
    def room_group_name(self):
        return f"event_{self.event_id}_chat"

    @property
    def user(self):
        return self.scope.get("user", None)

    @sync_to_async
    def save_message_to_db(self, message_serializer: MessageWritableSerializer):
        print(self.user, self.event_id)
        return message_serializer.save(user=self.user, event_id=self.event_id)

    @staticmethod
    @sync_to_async
    def event_exists(event_id: int) -> bool:
        try: Event.objects.get(id=event_id)
        except Event.DoesNotExist: return False
        return True

    async def connect(self):
        self.event_id = self.scope["url_route"]["kwargs"]["event_id"]
        if not await ChatConsumer.event_exists(self.event_id):
            await self.close()
            return

        # Check if the user is authenticated
        if self.user == AnonymousUser():
            await self.close()
            return

        # Join the chat group for this specific event
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    # Leave the chat group when disconnecting
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return

        try: data = json.loads(text_data)
        except json.decoder.JSONDecodeError: return

        # add parents info to message
        serializer = MessageWritableSerializer(data=data)
        if not serializer.is_valid():
            return

        instance = await self.save_message_to_db(serializer)
        resp_serializer = MessageSerializer(instance=instance)

        # Broadcast the message to the group for the specific event
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": self.SOCKET_EVENT_TYPE,
                **resp_serializer.data,
            }
        )

    # Send the message to WebSocket clients connected to the group
    async def chat_message(self, event):
        try: del event["type"]
        except KeyError: pass
        await self.send(text_data=json.dumps(event))
