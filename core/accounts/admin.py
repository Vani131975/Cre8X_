from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Skill

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'reported_count', 'is_warned', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {'fields': ('phone_number', 'bio', 'profile_image', 'reported_count', 'is_warned')}),
    )
    filter_horizontal = ('skills', 'groups', 'user_permissions')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Skill)