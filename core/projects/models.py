from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from accounts.models import Skill

class Project(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_projects', on_delete=models.CASCADE)
    required_skills = models.ManyToManyField(Skill, related_name='required_for_projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def mark_completed(self):
        self.status = 'completed'
        self.save()

class ProjectRole(models.Model):
    project = models.ForeignKey(Project, related_name='roles', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill, related_name='required_for_roles')
    is_filled = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} for {self.project.name}"

class Invitation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    project = models.ForeignKey(Project, related_name='invitations', on_delete=models.CASCADE)
    role = models.ForeignKey(ProjectRole, related_name='invitations', on_delete=models.CASCADE, null=True, blank=True)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_invitations', on_delete=models.CASCADE)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_invitations', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invitation for {self.recipient.username} to join {self.project.name}"

    def accept(self):
        self.status = 'accepted'
        self.save()
        
        # Create a team member record
        TeamMember.objects.create(
            project=self.project,
            user=self.recipient,
            role=self.role
        )
        
        if self.role:
            self.role.is_filled = True
            self.role.save()
            
    def reject(self):
        self.status = 'rejected'
        self.save()

class TeamMember(models.Model):
    project = models.ForeignKey(Project, related_name='team_members', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='joined_projects', on_delete=models.CASCADE)
    role = models.ForeignKey(ProjectRole, related_name='assigned_members', on_delete=models.CASCADE, null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('project', 'user')
    
    def __str__(self):
        return f"{self.user.username} in {self.project.name}"

class Report(models.Model):
    REASON_CHOICES = (
        ('abandonment', 'Project Abandonment'),
        ('inactivity', 'Inactivity'),
        ('misconduct', 'Misconduct'),
        ('other', 'Other'),
    )
    
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reports_filed', on_delete=models.CASCADE)
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reports_received', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name='reports', on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Report against {self.reported_user.username} in {self.project.name}"
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        
        if is_new:
            # Increment the reported count for the user
            self.reported_user.add_report()