from django.contrib import admin
from .models import CustomUser, Profile

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email']

class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'headline', 'location', 'phone_number']
    search_fields = ['user__username', 'user__email', 'headline', 'location']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)