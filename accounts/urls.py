from django.urls import path
from .views import (
    signup, profile_edit_view, profile_detail_view, 
    my_profile, resume_manage,
    ResumeAnalysisListView, ResumeAnalysisDetailView, analyze_resume_view
)

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('profile/', my_profile, name='my-profile'),
    path('profile/edit/', profile_edit_view, name='profile-edit'),
    path('profile/resume/', resume_manage, name='resume-manage'),
    path('profile/<str:username>/', profile_detail_view, name='profile-detail'),
    
    # AI Resume Analyzer
    path('analysis/', ResumeAnalysisListView.as_view(), name='resume-analysis-list'),
    path('analysis/<int:pk>/', ResumeAnalysisDetailView.as_view(), name='resume-analysis-detail'),
    path('analyze-resume/', analyze_resume_view, name='analyze-resume'),
]
