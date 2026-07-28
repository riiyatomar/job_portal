from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobListView.as_view(), name='job-list'),

    path('jobs/create/', views.JobCreateView.as_view(), name='job-create'),

    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),

    path('jobs/<int:pk>/update/', views.JobUpdateView.as_view(), name='job-update'),

    path('jobs/<int:pk>/delete/', views.JobDeleteView.as_view(), name='job-delete'),

    path('jobs/<int:pk>/apply/', views.apply_to_job, name='apply-to-job'),

    path('my-jobs/', views.MyJobsListView.as_view(), name='my-jobs'),

    path('my-applications/', views.MyApplicationsListView.as_view(), name='my-applications'),
]