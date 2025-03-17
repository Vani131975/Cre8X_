from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomLoginForm, ProfileUpdateForm
from .models import CustomUser, Skill
from projects.models import Project
from projects.recommender import ProjectRecommender
from django.contrib.auth import logout

from db_connection import accounts_collection, MongoDBConnector

from .forms import ProfileUpdateForm

def home(request):
    """Home page view"""
    return render(request, 'accounts/home.html')

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            mongo_user = {
                'username': user.username,
                'email': user.email,
                'date_joined': user.date_joined.isoformat(),
                'skills': [],
                'projects': []
            }
            mongo_result = accounts_collection.insert_one(mongo_user)

            user.mongo_id = mongo_result.inserted_id
            user.save()

            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login') 

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
                
                if user.mongo_id:
                    accounts_collection.update_one(
                        {'_id': user.mongo_id},
                        {'$set': {'last_login': user.last_login.isoformat()}}
                    )
                
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    """Logs out the user and redirects to the login page"""
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    """User dashboard view"""
    created_projects = Project.objects.filter(created_by=request.user)
    
    joined_projects = Project.objects.filter(team_members__user=request.user)
    
    pending_invitations = request.user.received_invitations.filter(status='pending')
    
    recommended_projects = ProjectRecommender.recommend_projects_for_user(request.user)
    
    unread_notifications = request.user.notifications.filter(is_read=False)

    mongo_user_data = None
    if request.user.mongo_id:
        mongo_user_data = accounts_collection.find_one({'_id': request.user.mongo_id})
    
    context = {
        'created_projects': created_projects,
        'joined_projects': joined_projects,
        'pending_invitations': pending_invitations,
        'recommended_projects': recommended_projects,
        'unread_notifications': unread_notifications,
        'mongo_user_data': mongo_user_data,
    }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db() 

            print(f"User Mongo ID: {user.mongo_id}")
            print(f"Skills in Django: {list(user.skills.values_list('name', flat=True))}")

            user.save_to_mongodb()  

            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {'form': form}
    return render(request, 'accounts/profile.html', context)





@login_required
def user_detail(request, user_id):
    """View another user's profile"""
    user = get_object_or_404(CustomUser, id=user_id)
    is_warned = user.is_warned
    
    mongo_user_data = None
    if user.mongo_id:
        mongo_user_data = accounts_collection.find_one({'_id': user.mongo_id})
    
    context = {
        'profile_user': user,
        'is_warned': is_warned,
        'mongo_user_data': mongo_user_data
    }
    
    return render(request, 'accounts/user_detail.html', context)