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


logger = logging.getLogger(__name__)

# ---------- Front‑end Views ----------
def home(request):  
    logger.info("home request", request)
    return render(request, "home.html")

def signup(request):
    logger.info("signup request", request)
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("login")

    form = SignUpForm()
    return render(request, "signup.html", {"form": form})

def login_view(request):
    logger.info("login_view request", request)
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
    logger.info("logout_view request", request)
    logout(request)
    response = redirect("home")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

def chat(request):
    logger.info("chat request", request)
    return render(request, "chat_list.html")

# ---------- API Views ----------
def user_detail(request):
    logger.info("user_detail request", request)
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

def get_all_users(request):
    logger.info("get_all_users request", request)
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)   
    return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

 
def conversation_list(request):
    """Return list of conversations for the logged‑in user."""
    if request.method == "POST":
        logger.info("conversation_list request", request)
        conversations = []
        raw_body = request.body
        decoded_body = raw_body.decode('utf-8')
        data = json.loads(decoded_body)
        user_id = data.get("user_id")
        user = User.objects.get(id=user_id)
 
        conversations_participants = ConversationParticipant.objects.filter(user=user) 

        for conversation in conversations_participants:
            conversation_instance = Conversation.objects.get(id=conversation.conversation.id)   
            conversation_serializer = ConversationSerializer(conversation_instance)
            conversations.append(conversation_serializer.data)

        serializer = ConversationSerializer(conversations, many=True)

        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)


def create_conversation(request):
    """Create a conversation with the supplied participants."""
    if request.method == "POST":
        logger.info("create_conversation request", request)
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

            for participant in conversation_participants:
                conversation_instance = Conversation.objects.get(id=conversation_id)
                user_instance = User.objects.get(id=participant.id)

                conversation_participant_data = {
                    "conversation": ConversationSerializer(conversation_instance).data,
                    "user": UserSerializer(user_instance).data,
                }
                conversation_participant_serializer = ConversationParticipantSerializer(data=conversation_participant_data)

                if conversation_participant_serializer.is_valid():
                    conversation_participant_serializer.save() 
                else:
                    logger.error("create_conversation conversation_participant_serializer errors", conversation_participant_serializer.errors)
            
            return JsonResponse(conversation_serializer.data, safe=False, status=status.HTTP_201_CREATED)
        return JsonResponse(conversation_serializer.errors, safe=False, status=status.HTTP_400_BAD_REQUEST)


def conversation_detail(request, conversation_id):
    logger.info("conversation_detail request", request)
    conv = Conversation.objects.get(id=conversation_id)
    serializer = ConversationSerializer(conv)
    return render(request, "chat_room.html", {"conversation": serializer.data})    




