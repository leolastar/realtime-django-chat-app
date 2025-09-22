import json
from django.core.cache import cache

def typing_signal(conv_id, user_id):
    payload = {"type": "typing", "user_id": user_id}
    channel = f"conversation_{conv_id}_typing"
    cache.publish(channel, json.dumps(payload))

def stop_typing_signal(conv_id, user_id):
    payload = {"type": "stop_typing", "user_id": user_id}
    channel = f"conversation_{conv_id}_typing"
    cache.publish(channel, json.dumps(payload))