from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Project, ProjectRole, Invitation, TeamMember, Report

class ProjectRoleInline(admin.TabularInline):
    model = ProjectRole
    extra = 1

class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 1

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ProjectRoleInline, TeamMemberInline]
    filter_horizontal = ('required_skills',)

class InvitationAdmin(admin.ModelAdmin):
    list_display = ('project', 'sender', 'recipient', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('project__name', 'sender__username', 'recipient__username')

class ReportAdmin(admin.ModelAdmin):
    list_display = ('reporter', 'reported_user', 'project', 'reason', 'created_at')
    list_filter = ('reason', 'created_at')
    search_fields = ('reporter__username', 'reported_user__username', 'project__name')

admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectRole)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(TeamMember)
admin.site.register(Report, ReportAdmin)