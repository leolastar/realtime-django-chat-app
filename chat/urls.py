from django.urls import path   
from chat import views as chat_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", chat_views.home, name="home"),
    path("signup/", chat_views.signup, name="signup"),
    path("login/", chat_views.login_view, name="login"),
    path("logout/", chat_views.logout_view, name="logout-user"),
    path("chat_list/", chat_views.chat, name="chat_list"),
    path("conversation/<int:conversation_id>/", chat_views.conversation_detail, name="conversation"),
    # # API
    path("api/me/", chat_views.user_detail, name="api_user"),
    path("api/users/", chat_views.get_all_users, name="api_get_all_users"),
    path("api/conversations/", chat_views.conversation_list, name="api_conversations"),
    path("api/conversations/create/", chat_views.create_conversation, name="api_create_conv"),
    path("api/conversations/<int:conversation_id>/", chat_views.conversation_detail, name="api_conv_detail"),
    path("api/conversations/<int:conversation_id>/send/", chat_views.send_message, name="api_send_message"),
    path("api/conversations/<int:conversation_id>/typing/", chat_views.typing, name="api_typing"),
    path("api/conversations/<int:conversation_id>/stop_typing/", chat_views.stop_typing, name="api_stop_typing"),
] 
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)