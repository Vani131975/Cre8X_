from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q
from .models import Project, ProjectRole, Invitation, TeamMember, Report
from .forms import ProjectForm, ProjectRoleForm, InvitationForm, ReportForm
from accounts.models import CustomUser
from notifications.models import Notification
from chat.models import ChatRoom
from .recommender import ProjectRecommender

@login_required
def project_list(request):
    """View all projects"""
    # Filter projects based on search
    search_query = request.GET.get('search', '')
    
    if search_query:
        projects = Project.objects.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    else:
        projects = Project.objects.all()
    
    # Get recommended projects for current user
    recommended_projects = ProjectRecommender.recommend_projects_for_user(request.user)
    
    context = {
        'projects': projects,
        'recommended_projects': recommended_projects,
        'search_query': search_query
    }
    
    return render(request, 'projects/project_list.html', context)

@login_required
def create_project(request):
    """Create a new project"""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m()  # Save many-to-many relationships
            
            # Create a chat room for the project
            ChatRoom.objects.create(
                project=project,
                name=f"Chat for {project.name}"
            )
            
            messages.success(request, 'Project created successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/create_project.html', {'form': form})

@login_required
def project_detail(request, project_id):
    """View project details"""
    project = get_object_or_404(Project, id=project_id)
    
    # Check if user is part of the project
    is_creator = project.created_by == request.user
    is_member = TeamMember.objects.filter(project=project, user=request.user).exists()
    
    # Get team members
    team_members = TeamMember.objects.filter(project=project)
    
    # Get roles
    roles = ProjectRole.objects.filter(project=project)
    
    # Get recommended users for the project
    recommended_users = None
    if is_creator:
        recommended_users = ProjectRecommender.recommend_users_for_project(project)
    
    context = {
        'project': project,
        'is_creator': is_creator,
        'is_member': is_member,
        'team_members': team_members,
        'roles': roles,
        'recommended_users': recommended_users,
    }
    
    return render(request, 'projects/project_detail.html', context)

@login_required
def add_project_role(request, project_id):
    """Add a role to a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Only project creator can add roles
    if project.created_by != request.user:
        messages.error(request, 'You do not have permission to add roles to this project.')
        return redirect('project_detail', project_id=project.id)
    
    if request.method == 'POST':
        form = ProjectRoleForm(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.project = project
            role.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Role added successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectRoleForm()
    
    return render(request, 'projects/add_role.html', {'form': form, 'project': project})

@login_required
def invite_user(request, project_id):
    """Invite a user to join a project"""
    project = get_object_or_404(Project, id=project_id)
    
    # Only project creator can send invitations
    if project.created_by != request.user:
        messages.error(request, 'You do not have permission to invite users to this project.')
        return redirect('project_detail', project_id=project.id)
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        recipient = get_object_or_404(CustomUser, id=user_id)
        form = InvitationForm(project, request.POST)
        
        if form.is_valid():
            # Check if invitation already exists
            if Invitation.objects.filter(
                project=project, 
                recipient=recipient, 
                status='pending'
            ).exists():
                messages.warning(request, f'An invitation to {recipient.username} is already pending.')
                return redirect('project_detail', project_id=project.id)
            
            # Create invitation
            invitation = form.save(commit=False)
            invitation.project = project
            invitation.sender = request.user
            invitation.recipient = recipient
            invitation.save()
            
            # Create notification
            Notification.objects.create(
                recipient=recipient,
                sender=request.user,
                notification_type='invitation',
                content=f'You have been invited to join "{project.name}"',
                related_project=project
            )
            
            messages.success(request, f'Invitation sent to {recipient.username}!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = InvitationForm(project)
    
    recommended_users = ProjectRecommender.recommend_users_for_project(project)
    
    context = {
        'form': form, 
        'project': project,
        'recommended_users': recommended_users
    }
    
    return render(request, 'projects/invite_user.html', context)

@login_required
def respond_to_invitation(request, invitation_id, action):
    """Respond to a project invitation"""
    invitation = get_object_or_404(
        Invitation, 
        id=invitation_id, 
        recipient=request.user, 
        status='pending'
    )
    
    if action == 'accept':
        invitation.accept()
        
        Notification.objects.create(
            recipient=invitation.sender,
            sender=request.user,
            notification_type='invitation_response',
            content=f'{request.user.username} accepted your invitation to join "{invitation.project.name}"',
            related_project=invitation.project
        )
        
        messages.success(request, f'You have joined the project "{invitation.project.name}"')
    
    elif action == 'decline':
        invitation.reject()
        
        Notification.objects.create(
            recipient=invitation.sender,
            sender=request.user,
            notification_type='invitation_response',
            content=f'{request.user.username} declined your invitation to join "{invitation.project.name}"',
            related_project=invitation.project
        )
        
        messages.info(request, f'You have declined the invitation to join "{invitation.project.name}"')
    
    return redirect('dashboard')

@login_required
def mark_project_completed(request, project_id):
    """Mark a project as completed"""
    project = get_object_or_404(Project, id=project_id)
    
    if project.created_by != request.user:
        messages.error(request, 'You do not have permission to mark this project as completed.')
        return redirect('project_detail', project_id=project.id)
    
    if request.method == 'POST':
        project.mark_completed()
        
        team_members = TeamMember.objects.filter(project=project)
        for member in team_members:
            if member.user != request.user:
                Notification.objects.create(
                    recipient=member.user,
                    sender=request.user,
                    notification_type='project_completion',
                    content=f'Yay! The project "{project.name}" has been marked as completed.',
                    related_project=project
                )
        
        messages.success(request, f'Project "{project.name}" has been marked as completed!')
        return redirect('project_detail', project_id=project.id)
    
    return render(request, 'projects/confirm_completion.html', {'project': project})

@login_required
def report_user(request, project_id, user_id):
    """Report a user in a project"""
    project = get_object_or_404(Project, id=project_id)
    reported_user = get_object_or_404(CustomUser, id=user_id)
    
    if not (project.created_by == request.user or 
            TeamMember.objects.filter(project=project, user=request.user).exists()):
        messages.error(request, 'You must be part of the project to report a user.')
        return redirect('project_detail', project_id=project.id)
    
    if not (project.created_by == reported_user or 
            TeamMember.objects.filter(project=project, user=reported_user).exists()):
        messages.error(request, 'The reported user must be part of the project.')
        return redirect('project_detail', project_id=project.id)
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.reported_user = reported_user
            report.project = project
            report.save()
            
            messages.success(request, 'Your report has been submitted.')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ReportForm()
    
    context = {
        'form': form,
        'project': project,
        'reported_user': reported_user
    }
    
    return render(request, 'projects/report_user.html', context)