from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobListView.as_view(), name='job-list'),

    path('jobs/create/', views.JobCreateView.as_view(), name='job-create'),

    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),

    path('jobs/<int:pk>/update/', views.JobUpdateView.as_view(), name='job-update'),

    path('jobs/<int:pk>/delete/', views.JobDeleteView.as_view(), name='job-delete'),

    path('jobs/<int:pk>/apply/', views.apply_to_job, name='apply-to-job'),

    path('dashboard/', views.EmployerDashboardView.as_view(), name='employer-dashboard'),

    path('jobs/<int:pk>/applicants/', views.JobApplicantsView.as_view(), name='job-applicants'),

    path('jobs/application/<int:pk>/', views.ApplicantProfileView.as_view(), name='applicant-profile'),

    path('jobs/<int:pk>/status/<str:action>/', views.job_toggle_status, name='job-toggle-status'),

    path('my-applications/', views.MyApplicationsListView.as_view(), name='my-applications'),

    path('my-applications/<int:pk>/withdraw/', views.withdraw_application, name='withdraw-application'),
    
    path('jobs/application/<int:pk>/resume/', views.download_resume, name='download-resume'),
    
    # Company URLs
    path('company/create/', views.CompanyCreateView.as_view(), name='company-create'),
    path('company/<slug:slug>/', views.CompanyDetailView.as_view(), name='company-detail'),
    path('company/<slug:slug>/edit/', views.CompanyUpdateView.as_view(), name='company-update'),
    path('company/<slug:slug>/delete/', views.CompanyDeleteView.as_view(), name='company-delete'),
]