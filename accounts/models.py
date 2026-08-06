from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

def validate_resume(value):
    max_size = 5 * 1024 * 1024  # 5 MB
    if value.size > max_size:
        raise ValidationError('Max file size is 5 MB.')

    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.doc', '.docx']
    if ext not in valid_extensions:
        raise ValidationError('Unsupported file extension. Allowed extensions are: .pdf, .doc, .docx.')
        
    if hasattr(value, 'file') and hasattr(value.file, 'read'):
        try:
            header = value.file.read(4)
            value.file.seek(0)
            if ext == '.pdf' and not header.startswith(b'%PDF'):
                raise ValidationError('Invalid PDF file content.')
            if ext == '.doc' and not header.startswith(b'\xd0\xcf\x11\xe0'):
                raise ValidationError('Invalid DOC file content.')
            if ext == '.docx' and not header.startswith(b'PK'):
                raise ValidationError('Invalid DOCX file content.')
        except Exception:
            raise ValidationError('Could not validate file contents.')

def validate_image(value):
    max_size = 2 * 1024 * 1024  # 2 MB
    if value.size > max_size:
        raise ValidationError('Max image size is 2 MB.')
    
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError('Unsupported image extension. Allowed extensions are: .jpg, .jpeg, .png.')

    if hasattr(value, 'file') and hasattr(value.file, 'read'):
        try:
            header = value.file.read(8)
            value.file.seek(0)
            if ext in ['.jpg', '.jpeg'] and not header.startswith(b'\xff\xd8'):
                raise ValidationError('Invalid JPEG file content.')
            if ext == '.png' and not header.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValidationError('Invalid PNG file content.')
        except Exception:
            raise ValidationError('Could not validate image contents.')

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('employer', 'Employer'),
        ('seeker', 'Job Seeker'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='seeker')

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    
    # Images
    profile_picture = models.ImageField(upload_to='profiles/pictures/', blank=True, null=True, validators=[validate_image])
    cover_image = models.ImageField(upload_to='profiles/covers/', blank=True, null=True, validators=[validate_image])
    
    # Basic Info
    headline = models.CharField(max_length=150, blank=True)
    about = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Links
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    
    # Resume (Existing)
    resume = models.FileField(upload_to='resumes/profiles/', blank=True, null=True, validators=[validate_resume])
    
    # Complex Sections
    skills = models.TextField(blank=True, help_text="Comma separated skills")
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    languages = models.TextField(blank=True)

    def get_completion_percentage(self):
        fields_to_check = [
            self.profile_picture, self.headline, self.about, 
            self.location, self.phone_number, self.resume,
            self.skills, self.education, self.experience
        ]
        filled_count = sum(1 for field in fields_to_check if field)
        return int((filled_count / len(fields_to_check)) * 100)

    def __str__(self):
        return f"{self.user.username} Profile"

@receiver(post_save, sender=CustomUser)
def manage_user_profile(sender, instance, created, **kwargs):
    Profile.objects.get_or_create(user=instance)
    if not created:
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            pass

class ResumeAnalysis(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='resume_analyses')
    job = models.ForeignKey('jobs.Job', on_delete=models.SET_NULL, null=True, blank=True, related_name='resume_analyses')
    resume_filename = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    resume_score = models.IntegerField(default=0)
    ats_score = models.IntegerField(default=0)
    summary_review = models.TextField()
    
    skills_detected = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    grammar_suggestions = models.JSONField(default=list)
    formatting_suggestions = models.JSONField(default=list)
    actionable_improvements = models.JSONField(default=list)
    
    match_percentage = models.IntegerField(null=True, blank=True)
    matching_skills = models.JSONField(default=list, blank=True)
    job_missing_skills = models.JSONField(default=list, blank=True)
    job_recommendations = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Analysis for {self.user.username} on {self.timestamp.strftime('%Y-%m-%d')}"