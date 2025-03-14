from django import forms
from .models import Project, ProjectRole, Invitation, Report
from accounts.models import Skill

class ProjectForm(forms.ModelForm):
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    new_skills = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add new skills (comma separated)'}),
        required=False
    )
    
    class Meta:
        model = Project
        fields = ('name', 'description', 'required_skills')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def save(self, commit=True):
        project = super().save(commit=False)
        
        if commit:
            project.save()
            
            # Add existing skills
            if self.cleaned_data.get('required_skills'):
                project.required_skills.set(self.cleaned_data['required_skills'])
            
            # Process and add new skills
            if self.cleaned_data.get('new_skills'):
                skill_names = [s.strip() for s in self.cleaned_data['new_skills'].split(',') if s.strip()]
                for skill_name in skill_names:
                    skill, created = Skill.objects.get_or_create(name=skill_name)
                    project.required_skills.add(skill)
        
        return project

class ProjectRoleForm(forms.ModelForm):
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    new_skills = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add new skills (comma separated)'}),
        required=False
    )
    
    class Meta:
        model = ProjectRole
        fields = ('title', 'description', 'required_skills')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def save(self, commit=True):
        role = super().save(commit=False)
        
        if commit:
            role.save()
            
            # Add existing skills
            if self.cleaned_data.get('required_skills'):
                role.required_skills.set(self.cleaned_data['required_skills'])
            
            # Process and add new skills
            if self.cleaned_data.get('new_skills'):
                skill_names = [s.strip() for s in self.cleaned_data['new_skills'].split(',') if s.strip()]
                for skill_name in skill_names:
                    skill, created = Skill.objects.get_or_create(name=skill_name)
                    role.required_skills.add(skill)
        
        return role

class InvitationForm(forms.ModelForm):
    role = forms.ModelChoiceField(
        queryset=ProjectRole.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = Invitation
        fields = ('role',)
    
    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].queryset = ProjectRole.objects.filter(project=project, is_filled=False)

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('reason', 'description')
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }