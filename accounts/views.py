from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomLoginForm, ProfileUpdateForm
from .models import CustomUser
from projects.models import Project
from projects.recommender import ProjectRecommender

def home(request):
    """Home page view"""
    return render(request, 'accounts/home.html')

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Cre8X.')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    """User login view"""
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def dashboard(request):
    """User dashboard view"""
    # Projects created by the user
    created_projects = Project.objects.filter(created_by=request.user)
    
    # Projects the user has joined
    joined_projects = Project.objects.filter(team_members__user=request.user)
    
    # Pending invitations
    pending_invitations = request.user.received_invitations.filter(status='pending')
    
    # Recommended projects
    recommended_projects = ProjectRecommender.recommend_projects_for_user(request.user)
    
    # Unread notifications
    unread_notifications = request.user.notifications.filter(is_read=False)
    
    context = {
        'created_projects': created_projects,
        'joined_projects': joined_projects,
        'pending_invitations': pending_invitations,
        'recommended_projects': recommended_projects,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def user_detail(request, user_id):
    """View another user's profile"""
    user = get_object_or_404(CustomUser, id=user_id)
    is_warned = user.is_warned
    
    context = {
        'profile_user': user,
        'is_warned': is_warned,
    }
    
    return render(request, 'accounts/user_detail.html', context)