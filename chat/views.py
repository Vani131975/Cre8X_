from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import ChatRoom, Message
from projects.models import Project, TeamMember

@login_required
def chat_room(request, project_id):
    """View and participate in a project chat room"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is part of the project
    is_member = (project.created_by == request.user or 
                 TeamMember.objects.filter(project=project, user=request.user).exists())
    
    if not is_member:
        messages.error(request, 'You must be a member of the project to access the chat room.')
        return redirect('project_detail', project_id=project.id)
    
    # Get or create chat room
    chat_room, created = ChatRoom.objects.get_or_create(
        project=project,
        defaults={'name': f"Chat for {project.name}"}
    )
    
    # Get messages
    messages_list = Message.objects.filter(chat_room=chat_room)
    
    context = {
        'chat_room': chat_room,
        'messages': messages_list,
        'project': project
    }
    
    return render(request, 'chat/chat_room.html', context)

@login_required
def load_messages(request, room_id):
    """AJAX endpoint to load messages"""
    chat_room = get_object_or_404(ChatRoom, id=room_id)
    project = chat_room.project
    
    # Check if user is part of the project
    is_member = (project.created_by == request.user or 
                 TeamMember.objects.filter(project=project, user=request.user).exists())
    
    if not is_member:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get messages
    messages = Message.objects.filter(chat_room=chat_room)
    
    # Format messages for JSON response
    message_list = []
    for msg in messages:
        message_list.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat(),
            'is_own': msg.sender == request.user
        })
    
    return JsonResponse({'messages': message_list})