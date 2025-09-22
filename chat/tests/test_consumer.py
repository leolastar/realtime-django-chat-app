import pytest
from channels.testing import WebsocketCommunicator
from chat.consumers import ChatConsumer
from django.test import override_settings
from channels.layers import get_channel_layer
from django.urls import re_path
from channels.routing import URLRouter

application = URLRouter([
    re_path(r"ws/chat/(?P<conversation_id>\w+)/$", ChatConsumer.as_asgi()),   
])

@pytest.mark.asyncio
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
async def test_websocket_connection():
    communicator = WebsocketCommunicator(application, "/ws/chat/test_conversation_id")
    connected, _ = await communicator.connect()
    assert connected
    await communicator.disconnect()

@pytest.mark.asyncio
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
async def test_receive_message():
    communicator = WebsocketCommunicator(application, "/ws/chat/test_conversation_id")
    await communicator.connect()

    # Send a message to the WebSocket
    await communicator.send_json_to({"type": "message", "message": "hello"})

    # Receive a message from the WebSocket
    response = await communicator.receive_json_from()
    assert response == {"type": "chat.message", "user": "testuser", "message": "hello"}

    await communicator.disconnect()

@pytest.mark.asyncio
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
async def test_broadcast_message():
    channel_layer = get_channel_layer()
    communicator1 = WebsocketCommunicator(application, "/ws/chat/test_conversation_id")
    communicator2 = WebsocketCommunicator(application, "/ws/chat/test_conversation_id")
    await communicator1.connect()
    await communicator2.connect()

    # Send a message to the channel layer
    await channel_layer.group_send(
        "chat",
        {
            "type": "chat.message",
            "message": {"user": "testuser", "message": "hello everyone"},
        }
    )

    # Receive the message from both communicators
    response1 = await communicator1.receive_json_from()
    response2 = await communicator2.receive_json_from()
    assert response1 == {"type": "chat.message", "user": "testuser", "message": "hello everyone"}
    assert response2 == {"message": "hello everyone"}

    await communicator1.disconnect()
    await communicator2.disconnect()

@pytest.mark.asyncio
@override_settings(CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}})
async def test_disconnect():
    communicator = WebsocketCommunicator(application, "/ws/chat/test_conversation_id")
    await communicator.connect()
    await communicator.disconnect()

    # Try to send a message after disconnect
    with pytest.raises(Exception):
        await communicator.send_json_to({"type": "message", "message": "should fail"})
