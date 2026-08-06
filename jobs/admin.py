from django.contrib import admin
from .models import Job, Application, Company, ApplicationStatusHistory, RecruiterNote

class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'location', 'website']
    search_fields = ['name', 'owner__username', 'owner__email']
    list_filter = ['location']
    readonly_fields = ['slug']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')

class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'salary', 'posted_by', 'date_posted', 'is_closed']
    search_fields = ['title', 'company__name', 'company_name', 'posted_by__username']
    list_filter = ['is_closed', 'job_type', 'work_mode', 'experience_level', 'location']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'posted_by')

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'applicant', 'status', 'date_applied']
    list_filter = ['status', 'date_applied']
    search_fields = ['job__title', 'applicant__username', 'applicant__email']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('job', 'applicant')

class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['application', 'status', 'updated_by', 'timestamp']
    list_filter = ['status', 'timestamp']
    search_fields = ['application__job__title', 'application__applicant__username', 'updated_by__username']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('application__job', 'application__applicant', 'updated_by')

class RecruiterNoteAdmin(admin.ModelAdmin):
    list_display = ['application', 'title', 'rating', 'strong_candidate', 'created_by', 'timestamp']
    list_filter = ['rating', 'strong_candidate', 'timestamp']
    search_fields = ['application__applicant__username', 'title', 'created_by__username']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('application__applicant', 'created_by')

admin.site.register(Company, CompanyAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(ApplicationStatusHistory, ApplicationStatusHistoryAdmin)
admin.site.register(RecruiterNote, RecruiterNoteAdmin)
