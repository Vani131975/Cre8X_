from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, Skill

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.isdigit():
            raise ValidationError('Phone number should contain only digits.')
        return phone_number
    
    
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class ProfileUpdateForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False)
    profile_image = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}), required=False)
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    new_skills = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add new skills (comma separated)'}),
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ('bio', 'profile_image', 'skills')

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()

            if self.cleaned_data.get('skills'):
                user.skills.set(self.cleaned_data['skills'])

            if self.cleaned_data.get('new_skills'):
                skill_names = [s.strip() for s in self.cleaned_data['new_skills'].split(',') if s.strip()]
                for skill_name in skill_names:
                    skill, created = Skill.objects.get_or_create(name=skill_name)
                    user.skills.add(skill)

        return user
    

