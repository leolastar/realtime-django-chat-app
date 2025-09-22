import json
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
import logging
from django.core.cache import cache
from collections import defaultdict

logger = logging.getLogger(__name__)

class RateLimiter:
    _limits = defaultdict(list)  

    def __init__(self, max_per_second=1):
        self.max_per_second = max_per_second

    async def allow(self, user_id):
        now = time.time()
        window_start = now - 1
        timestamps = self._limits[user_id]
        timestamps = [ts for ts in timestamps if ts > window_start]
        self._limits[user_id] = timestamps
        if len(timestamps) >= self.max_per_second:
            return False
        timestamps.append(now)
        return True

rate_limiter = RateLimiter(max_per_second=1)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.group_name = f"chat_{self.conversation_id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        

        logger.info(f'User {self.scope["user"]} connected to {self.group_name}')

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f'User {self.scope["user"]} disconnected from {self.group_name}')       

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        action = data.get('type')
        if action == 'join': 
            messages = await self.get_messages()   
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.join',
                    'message': {
                        'user': self.scope["user"].first_name,
                        'user_id': self.scope["user"].id,
                        'message': self.scope["user"].first_name + " joined the chat",
                        'timestamp': timezone.now().isoformat()
                    },
                    'messages': json.dumps(messages)
                }
            )
            logger.info(f'User {self.scope["user"]} joined the chat {self.group_name}')
        elif action == 'message':
            rate_limit_allowed = await rate_limiter.allow(self.scope['user'].id)
            if not rate_limit_allowed:
                message = {
                    'user': self.scope["user"].first_name,
                    'user_id': self.scope["user"].id,
                    'message': self.scope["user"].first_name + " has reached the rate limit" 
                }
                await self.send(text_data=json.dumps({
                    'type': 'chat.message',
                    'user': self.scope["user"].first_name,
                    'message': message
                }))
                logger.info(f'User {self.scope["user"]} is rate limited in {self.group_name}')
                
                return
            message = data.get('content')
            if not message:
                return
            timestamp = timezone.now().isoformat()
            msg_obj = {
                'user': self.scope["user"].first_name,
                'message': message,
                'timestamp': timestamp,
            }
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.message',
                    'message': msg_obj
                }
            )
            key = f'chat:{self.group_name}:messages'

            await self.save_message(msg_obj)
            logger.info(f'User {self.scope["user"]} sent message to {self.group_name}')
        elif action == 'typing':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.typing',
                    'user': self.scope["user"].first_name,
                    'user_id': self.scope["user"].id
                }
            )
            logger.info(f'User {self.scope["user"]} is typing in {self.group_name}')
        elif action == 'stop_typing':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.stop_typing',
                    'user': self.scope["user"].first_name,
                    'user_id': self.scope["user"].id
                }
            )
            logger.info(f'User {self.scope["user"]} stopped typing in {self.group_name}')
        elif action == 'leave':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.leave',
                    'user': self.scope["user"].first_name,
                    'user_id': self.scope["user"].id
                }
            )
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
            logger.info(f'User {self.scope["user"]} left the chat {self.group_name}')
        elif action == 'history':

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.history',
                    'messages': json.dumps(await self.get_messages())
                }
            )
            logger.info(f'User {self.scope["user"]} requested history for {self.group_name}')
        else:
            return
            

    async def chat_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat.join',
            'message': event['message'],
            'messages': event['messages']
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': event['message'],
        }))

    async def chat_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat.typing',
            'user': event['user'],
            'user_id': event['user_id']
        }))       

    async def chat_stop_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat.stop_typing',
            'user': event['user'],
            'user_id': event['user_id']
        }))

    async def chat_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat.leave',
            'user': event['user'],
            'user_id': event['user_id']
        }))

    async def chat_history(self, event):

        await self.send(text_data=json.dumps({
            'type': 'chat.history',
            'messages': event['messages']
        }))

    # @database_sync_to_async
    async def get_messages(self):

        messages = cache.get(f"chat:{self.group_name}:messages")

        if messages is None :
            return []
        messages = json.loads(messages)

        if not isinstance(messages, list):
            return [messages]
        return messages

    # @database_sync_to_async
    async def save_message(self, content):

        existing_messages = await self.get_messages()

        if existing_messages:
            existing_messages.append(content)
        else:
            existing_messages = [content]
        
        cache.set(f"chat:{self.group_name}:messages", json.dumps(existing_messages))
        return existing_messages


        