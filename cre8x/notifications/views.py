from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def notification_list(request):
    """View all notifications for the current user"""
    notifications = request.user.notifications.all()
    
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications
    })

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    else:
        # Redirect to appropriate page based on notification type
        if notification.related_project:
            return redirect('project_detail', project_id=notification.related_project.id)
        else:
            return redirect('notification_list')

@login_required
def mark_all_read(request):
    """Mark all notifications as read"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    else:
        return redirect('notification_list')