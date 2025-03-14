from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.create_project, name='create_project'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/add-role/', views.add_project_role, name='add_project_role'),
    path('<int:project_id>/invite/', views.invite_user, name='invite_user'),
    path('invitation/<int:invitation_id>/<str:action>/', views.respond_to_invitation, name='respond_to_invitation'),
    path('<int:project_id>/complete/', views.mark_project_completed, name='mark_project_completed'),
    path('<int:project_id>/report/<int:user_id>/', views.report_user, name='report_user'),
]