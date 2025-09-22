import json
import logging
from datetime import datetime, timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import logout, login, authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework import status, permissions
from .models import User, Conversation, Message, ConversationParticipant
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer, ConversationParticipantSerializer, ConversationCreateSerializer
from .forms import SignUpForm
from .signals import typing_signal, stop_typing_signal


logger = logging.getLogger(__name__)

# ---------- Front‑end Views ----------
def home(request):  
    return render(request, "home.html")

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("login")

    form = SignUpForm()
    return render(request, "signup.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        raw_body = request.body
        decoded_body = raw_body.decode('utf-8')
        data = json.loads(decoded_body)
        username = data.get("username")
        password = data.get("password")
        user = authenticate(request=request, username=username, password=password)
        if user is None:
            return JsonResponse({"detail": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        request.session.modified = True
        refresh = RefreshToken.for_user(user)

        serializer = UserSerializer(user)
        response = {
            "user": serializer.data,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }
        return JsonResponse(response, status=status.HTTP_200_OK)

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    response = redirect("home")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

def chat(request):
    return render(request, "chat_list.html")

# ---------- API Views ----------
def user_detail(request):
    permission_classes = [IsAuthenticated]
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

def get_all_users(request):
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)   
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

 
def conversation_list(request):
    """Return list of conversations for the logged‑in user."""
    if request.method == "POST":
        conversations = []
        raw_body = request.body
        decoded_body = raw_body.decode('utf-8')
        data = json.loads(decoded_body)
        user_id = data.get("user_id")
        user = User.objects.get(id=user_id)
        print("conversation_list", user)
        conversations_participants = ConversationParticipant.objects.filter(user=user) 
        print("conversations_participants", conversations_participants)

        for conversation in conversations_participants:
            print("conversation", conversation)
            conversation_instance = Conversation.objects.get(id=conversation.conversation.id)
            print("conversation_instance", conversation_instance)
            conversation_serializer = ConversationSerializer(conversation_instance)
            print("conversation_serializer", conversation_serializer.data)
            conversations.append(conversation_serializer.data)
        print("conversations", conversations)
        serializer = ConversationSerializer(conversations, many=True)
        print("serializer.data", serializer.data)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


def create_conversation(request):
    """Create a conversation with the supplied participants."""
    if request.method == "POST":
        raw_body = request.body
        decoded_body = raw_body.decode('utf-8')
        data = json.loads(decoded_body)
        user_id = data.get("user_id")
        user = User.objects.get(id=user_id)
        title = data.get("title")
        conversation_data = {
            "title": title,
            "owner": UserSerializer(user).data,  
        }
        conversation_serializer = ConversationCreateSerializer(data=conversation_data)
        if conversation_serializer.is_valid():
            conv = conversation_serializer.save()
            conv.save()
            conversation_id = conv.id
            conversation_participants = data.get("conversation_participants")
            conversation_participants = conversation_participants.split(",")
            conversation_participants = [User.objects.get(email=participant) for participant in conversation_participants]
            conversation_participants.append(user)
            print("create_conversation conversation_participants", conversation_participants)
            for participant in conversation_participants:
                conversation_instance = Conversation.objects.get(id=conversation_id)
                print("create_conversation conversation_instance", conversation_instance)
                user_instance = User.objects.get(id=participant.id)
                print("create_conversation user_instance", user_instance)
                conversation_participant_data = {
                    "conversation": ConversationSerializer(conversation_instance).data,
                    "user": UserSerializer(user_instance).data,
                }
                print("create_conversation conversation_participant_data", conversation_participant_data)
                conversation_participant_serializer = ConversationParticipantSerializer(data=conversation_participant_data)
                print("create_conversation conversation_participant_serializer", conversation_participant_serializer.is_valid())
                if conversation_participant_serializer.is_valid():
                    conversation_participant_serializer.save()
                    print("create_conversation conversation_participant_serializer saved")
                else:
                    print("create_conversation conversation_participant_serializer errors", conversation_participant_serializer.errors)
            
            return JsonResponse(conversation_serializer.data, safe=False, status=status.HTTP_201_CREATED)
        return JsonResponse(conversation_serializer.errors, safe=False, status=status.HTTP_400_BAD_REQUEST)


def conversation_detail(request, conversation_id):
    print("conversation_detail conversation_id", conversation_id)
    print("conversation_detail conversation_id", conversation_id)
    conv = Conversation.objects.get(id=conversation_id)
    print("conversation_detail conv", conv)
    serializer = ConversationSerializer(conv)
    print("conversation_detail serializer", serializer.data)
    return render(request, "chat_room.html", {"conversation": serializer.data})    


def send_message(request, conv_id):
    """
    POST body: {"content": "Hello"}
    Throttle: 1 request per second per user (custom throttle class)
    """
    conv = Conversation.objects.get(id=conv_id)
    if request.user not in conv.conversation_participants.all():
        return HttpResponseForbidden("Not a participant.")
    content = request.data.get("content", "").strip()
    if not content:
        return Response({"detail": "Empty content."}, status=status.HTTP_400_BAD_REQUEST)

    message = Message.objects.create(conversation=conv, sender=request.user, content=content)
    serializer = MessageSerializer(message)
    # Publish to Redis channel for real‑time
    channel_name = f"conversation_{conv.id}"
    message_data = serializer.data
    # Use Django Redis cache as pub/sub
    from django.core.cache import cache
    cache.publish(channel_name, json.dumps(message_data))
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# ---------- Typing Indicator ----------
def typing(request, conv_id):
    conv = Conversation.objects.get(id=conv_id)
    if request.user not in conv.participants.all():
        return HttpResponseForbidden()
    typing_signal(conv.id, request.user.id)
    return Response(status=status.HTTP_204_NO_CONTENT)


def stop_typing(request, conv_id):
    conv = Conversation.objects.get(id=conv_id)
    if request.user not in conv.participants.all():
        return HttpResponseForbidden()
    stop_typing_signal(conv.id, request.user.id)
    return Response(status=status.HTTP_204_NO_CONTENT)
