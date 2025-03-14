from django.urls import path
from . import views

urlpatterns = [
    path('project/<int:project_id>/', views.chat_room, name='chat_room'),
    path('load-messages/<int:room_id>/', views.load_messages, name='load_messages'),
]