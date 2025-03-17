from django.db import models
from django.conf import settings
from accounts.models import Skill
from bson import ObjectId
from db_connection import projects_collection

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
    mongo_id = models.CharField(max_length=100, blank=True, null=True) 

    def save(self, *args, **kwargs):
        """Override save method to sync with MongoDB"""
        super().save(*args, **kwargs)
        self.save_to_mongodb()

    def save_to_mongodb(self):
        """Save project to MongoDB"""
        project_data = {
            'django_id': self.id,  # Store Django ID for reference
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by.username,
            'status': self.status,
            'required_skills': list(self.required_skills.values_list('name', flat=True)),  # Fix skill saving
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

        if self.mongo_id:
            try:
                mongo_obj_id = ObjectId(self.mongo_id)
                update_result = projects_collection.update_one({'_id': mongo_obj_id}, {'$set': project_data})
                print(f"✅ Updated MongoDB Project: {update_result.modified_count}")
            except Exception as e:
                print(f"❌ MongoDB Update Error: {e}")
        else:
            result = projects_collection.insert_one(project_data)
            self.mongo_id = str(result.inserted_id)
            super().save(update_fields=["mongo_id"])  # Save `mongo_id` in SQLite

    def mark_completed(self):
        """Mark the project as completed in MongoDB and Django"""
        self.status = 'completed'
        self.save()
        if self.mongo_id:
            projects_collection.update_one(
                {'_id': ObjectId(self.mongo_id)},
                {'$set': {'status': 'completed'}}
            )

    def __str__(self):
        return self.name


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

    def accept(self):
        """Accept invitation and update MongoDB"""
        self.status = 'accepted'
        self.save()

        # Create a team member record
        TeamMember.objects.create(
            project=self.project,
            user=self.recipient,
            role=self.role
        )

        # Update MongoDB team members
        if self.project.mongo_id:
            projects_collection.update_one(
                {'_id': ObjectId(self.project.mongo_id)},
                {'$push': {'team_members': self.recipient.username}}
            )

        if self.role:
            self.role.is_filled = True
            self.role.save()

    def reject(self):
        """Reject invitation"""
        self.status = 'rejected'
        self.save()

    def __str__(self):
        return f"Invitation for {self.recipient.username} to join {self.project.name}"


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

    def save(self, *args, **kwargs):
        """Save report and update reported user warning count"""
        is_new = not self.pk
        super().save(*args, **kwargs)

        if is_new:
            self.reported_user.add_report()

    def __str__(self):
        return f"Report against {self.reported_user.username} in {self.project.name}"
