from django.db import models
from django.conf import settings
from django.utils.text import slugify
from accounts.models import validate_resume, validate_image

class Company(models.Model):
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    website = models.URLField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, validators=[validate_image])
    banner = models.ImageField(upload_to='company_banners/', blank=True, null=True, validators=[validate_image])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('Full Time', 'Full Time'),
        ('Part Time', 'Part Time'),
        ('Internship', 'Internship'),
        ('Contract', 'Contract'),
        ('Freelance', 'Freelance'),
    ]
    
    WORK_MODE_CHOICES = [
        ('Remote', 'Remote'),
        ('Hybrid', 'Hybrid'),
        ('On-site', 'On-site'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('Fresher', 'Fresher'),
        ('Junior', 'Junior'),
        ('Mid-Level', 'Mid-Level'),
        ('Senior', 'Senior'),
    ]

    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200) # Legacy
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Advanced Filtering Fields
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='Full Time')
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='On-site')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='Mid-Level')
    industry = models.CharField(max_length=100, blank=True)
    skills = models.CharField(max_length=300, blank=True, help_text="Comma-separated skills (e.g. Python, Django, React)")
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)

    date_posted = models.DateTimeField(auto_now_add=True)
    is_closed = models.BooleanField(default=False)
    views_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date_posted']

    def __str__(self):
        return self.title
    
class Application(models.Model):
        STATUS_CHOICES = [
            ('Applied', 'Applied'),
            ('Under Review', 'Under Review'),
            ('Shortlisted', 'Shortlisted'),
            ('Interview Scheduled', 'Interview Scheduled'),
            ('Technical Round', 'Technical Round'),
            ('HR Round', 'HR Round'),
            ('Offer Extended', 'Offer Extended'),
            ('Hired', 'Hired'),
            ('Rejected', 'Rejected'),
            ('Withdrawn', 'Withdrawn')
        ]
        job = models.ForeignKey(Job, on_delete=models.CASCADE)
        applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
        resume = models.FileField(upload_to='resumes/applications/', blank=True, null=True, validators=[validate_resume])
        status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Applied')
        date_applied = models.DateTimeField(auto_now_add=True)

        class Meta:
            unique_together = ('job', 'applicant')

        def __str__(self):
            return f"{self.applicant} applied to {self.job}"

class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=30, choices=Application.STATUS_CHOICES)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.application} - {self.status} on {self.timestamp}"

class RecruiterNote(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='recruiter_notes')
    title = models.CharField(max_length=200)
    note = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(0, 6)], default=0)
    recommendation = models.CharField(max_length=50, blank=True)
    strong_candidate = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Note by {self.created_by} for {self.application.applicant}"