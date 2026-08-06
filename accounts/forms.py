from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile
from django import forms
import re
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'role') 

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'profile_picture', 'cover_image', 'headline', 'about',
            'location', 'phone_number', 'github_url', 'linkedin_url', 'portfolio_url',
            'resume', 'skills', 'education', 'experience', 'projects', 'certifications', 'languages'
        ]
        widgets = {
            'about': forms.Textarea(attrs={'rows': 4}),
            'skills': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., Python, Django, React'}),
            'education': forms.Textarea(attrs={'rows': 3}),
            'experience': forms.Textarea(attrs={'rows': 4}),
            'projects': forms.Textarea(attrs={'rows': 3}),
            'certifications': forms.Textarea(attrs={'rows': 2}),
            'languages': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            if not re.match(r'^\+?1?\d{9,15}$', phone_number):
                raise ValidationError("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
        return phone_number

    def clean_github_url(self):
        url = self.cleaned_data.get('github_url')
        if url and not url.startswith(('http://', 'https://')):
            raise ValidationError("Invalid URL. Must start with http:// or https://")
        return url
        
    def clean_linkedin_url(self):
        url = self.cleaned_data.get('linkedin_url')
        if url and not url.startswith(('http://', 'https://')):
            raise ValidationError("Invalid URL. Must start with http:// or https://")
        return url
        
    def clean_portfolio_url(self):
        url = self.cleaned_data.get('portfolio_url')
        if url and not url.startswith(('http://', 'https://')):
            raise ValidationError("Invalid URL. Must start with http:// or https://")
        return url

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['resume']