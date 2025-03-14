import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from notifications.models import Notification

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user_id = self.scope['user'].id
        
        # Save message to database
        await self.save_message(user_id, message)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': user_id,
                'username': self.scope['user'].username,
            }
        )
    
    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user_id = event['user_id']
        username = event['username']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user_id': user_id,
            'username': username,
            'timestamp': self.get_timestamp(),
        }))
    
    def get_timestamp(self):
        from django.utils import timezone
        return timezone.now().isoformat()
    
    @database_sync_to_async
    def save_message(self, user_id, message_content):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get the chat room
        chat_room = ChatRoom.objects.get(id=self.room_id)
        sender = User.objects.get(id=user_id)
        
        # Create message
        message = Message.objects.create(
            chat_room=chat_room,
            sender=sender,
            content=message_content
        )
        
        # Create notifications for all team members except sender
        project = chat_room.project
        team_members = project.team_members.exclude(user=sender)
        
        for member in team_members:
            Notification.objects.create(
                recipient=member.user,
                sender=sender,
                notification_type='message',
                content=f"New message in {project.name}",
                related_project=project
            )
        
        return message