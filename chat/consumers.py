import json
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
# from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("ChatConsumer connect scope", self.scope['user'].id)
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        print("ChatConsumer connect conversation_id", self.conversation_id)
        self.group_name = f"chat_{self.conversation_id}"
        print("ChatConsumer connect group_name", self.group_name)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send historical messages
        messages = await self.get_messages(self.conversation_id, 50)    
        print("ChatConsumer connect messages", messages)
        await self.send(json.dumps({
            'type': 'chat.history',
            'messages': messages
        }))
        logger.info(f'User {self.scope["user"]} connected to {self.group_name}')

    async def disconnect(self, close_code):
        print("ChatConsumer disconnect scope", self.scope)
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f'User {self.scope["user"]} disconnected from {self.group_name}')       


    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        print("ChatConsumer receive data", data)
        action = data.get('type')
        if action == 'join':   
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.join',
                    'message': {
                        'user': self.scope["user"].first_name,
                        'user_id': self.scope["user"].id,
                        'message': self.scope["user"].first_name + " joined the chat",
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
           
        elif action == 'message':
            message = data.get('content')
            if not message:
                return
            timestamp = timezone.now().isoformat()
            msg_obj = {
                'user': self.scope["user"].first_name,
                'message': message,
                'timestamp': timestamp,
            }
            print("ChatConsumer receive msg_obj", msg_obj)
            # msg_obj = await self.save_message(msg_obj)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.message',
                    'message': msg_obj
                }
            )
        elif action == 'typing':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.typing',
                    'user': self.scope["user"].first_name,
                    'user_id': self.scope["user"].id
                }
            )
        elif action == 'stop_typing':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.stop_typing',
                    'user': self.scope["user"].first_name,
                    'user_id': self.scope["user"].id
                }
            )
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
        else:
            return

        
        # Cache list for quick retrieval
        # key = f'room:{self.group_name}:msgs'
        # print("ChatConsumer receive key", key)
        # await cache.redis.rpush(key, json.dumps(msg_obj))
        # await cache.redis.expire(key, 60*60*24*7)  
        print(f'ChatConsumer receive Message from {self.scope["user"]} in {self.group_name}')

    async def chat_join(self, event):
        print("ChatConsumer chat_join event", event)
        await self.send(text_data=json.dumps({
            'type': 'chat.join',
            'message': event['message']
        }))

    async def chat_message(self, event):
        print("ChatConsumer chat_message event", event)
        await self.send(text_data=json.dumps({
            'type': 'chat.message',
            'message': event['message'],
        }))

    async def chat_typing(self, event):
        print("ChatConsumer chat_typing event", event)
        await self.send(text_data=json.dumps({
            'type': 'chat.typing',
            'user': event['user'],
            'user_id': event['user_id']
        }))       

    async def chat_stop_typing(self, event):
        print("ChatConsumer chat_stop_typing event", event)
        await self.send(text_data=json.dumps({
            'type': 'chat.stop_typing',
            'user': event['user'],
            'user_id': event['user_id']
        }))

    async def chat_leave(self, event):
        print("ChatConsumer chat_leave event", event)
        await self.send(text_data=json.dumps({
            'type': 'chat.leave',
            'user': event['user'],
            'user_id': event['user_id']
        }))


    @database_sync_to_async
    def get_messages(self, conversation_id, limit=50):
        print("ChatConsumer get_messages conversation_id", self.conversation_id)
        # messages = cache.redis.lrange(f"chat:{self.conversation_id}:messages", 0, -1)
        messages = []
        print("ChatConsumer get_messages messages", messages)
        return [json.loads(m) for m in messages]

    @database_sync_to_async
    def save_message(self, content):
        print("ChatConsumer save_message conversation_id", self.conversation_id)
        message = {
            'sender_id': self.scope['user'].id,
            'content': content,
            'conversation_id': self.conversation_id,
            'timestamp': timezone.now().isoformat()
        }
        # cache.redis.rpush(f"chat:{self.conversation_id}:messages", json.dumps(message))
        print("ChatConsumer save_message message", message)
        return message

    async def check_throttle(self):
        print("ChatConsumer check_throttle conversation_id", self.conversation_id)
        user_id = self.scope['user'].id
        print("ChatConsumer check_throttle user_id", user_id)
        key = f"throttle:{user_id}"
        current_time = time.time()
        print("ChatConsumer check_throttle key", key)
        # Fixed window (1 msg/sec)
        # if not cache.redis.get(key):
        #     cache.set(key, 1, 1)
        #     return True
        
        # Check if within limit
        # count = cache.redis.get(key)
        # print("ChatConsumer check_throttle count", count)
        # if count >= 1:
        #     return False
        # cache.incr(key)
        return True
        