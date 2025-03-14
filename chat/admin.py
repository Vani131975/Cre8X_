from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ChatRoom, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0

class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_at')
    search_fields = ('name', 'project__name')
    inlines = [MessageInline]

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'chat_room', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('content', 'sender__username', 'chat_room__name')

admin.site.register(ChatRoom, ChatRoomAdmin)
admin.site.register(Message, MessageAdmin)