from rest_framework import serializers
from .models import User, Conversation, Message, ConversationParticipant
import logging

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False)
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name")

class ConversationCreateSerializer(serializers.ModelSerializer):
    owner = UserSerializer()

    class Meta:
        model = Conversation
        fields = ("id", "title", "created_at", "owner")

    def create(self, validated_data):
        owner = validated_data.pop("owner")
        owner = User.objects.get(id=owner["id"])
        conversation = Conversation.objects.create(owner=owner, **validated_data)
        logger.info("ConversationCreateSerializer create conversation", conversation)
        return conversation

class ConversationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=False)
    owner = UserSerializer()

    class Meta:
        model = Conversation
        fields = ("id", "title", "created_at", "owner")

class ConversationParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    conversation = ConversationSerializer()
    class Meta:
        model = ConversationParticipant
        fields = ("id", "user", "joined_at", "conversation")

    def create(self, validated_data):   
        user = validated_data.pop("user")   
        conversation = validated_data.pop("conversation")  
        user = User.objects.get(id=user["id"])
        conversation = Conversation.objects.get(id=conversation["id"])
        conversation_participant = ConversationParticipant.objects.create(user=user, conversation=conversation, **validated_data)
        logger.info("ConversationParticipantSerializer create conversation_participant", conversation_participant)
        return conversation_participant

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source="sender.id")
    conversation = ConversationSerializer()

    class Meta:
        model = Message
        fields = ("id", "conversation", "sender", "content", "timestamp")
        read_only_fields = ("timestamp",)
