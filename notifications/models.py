from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = (
        ('invitation', 'Project Invitation'),
        ('invitation_response', 'Invitation Response'),
        ('project_update', 'Project Update'),
        ('project_completion', 'Project Completion'),
        ('message', 'New Message'),
        ('warning', 'Warning'),
    )
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_notifications', on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    content = models.TextField()
    related_project = models.ForeignKey('projects.Project', related_name='notifications', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.get_notification_type_display()}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()