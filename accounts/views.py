import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.utils import timezone
from datetime import timedelta
from .forms import CustomUserCreationForm, ProfileForm, ResumeForm
from .models import Profile, CustomUser, ResumeAnalysis
from .ai_utils import analyze_resume
from jobs.models import Job

logger = logging.getLogger(__name__)

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login') 
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def profile_edit_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile-detail', username=request.user.username)
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'profile_edit.html', {'form': form})

@login_required
def my_profile(request):
    return redirect('profile-detail', username=request.user.username)

def profile_detail_view(request, username):
    user_obj = get_object_or_404(CustomUser, username=username)
    profile, created = Profile.objects.get_or_create(user=user_obj)
    context = {
        'profile': profile,
        'completion_percentage': profile.get_completion_percentage()
    }
    return render(request, 'profile_detail.html', context)

@login_required
def resume_manage(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        if 'delete_resume' in request.POST:
            if profile.resume:
                profile.resume.delete(save=True)
                messages.success(request, 'Your resume has been deleted.')
            return redirect('resume-manage')
            
        form = ResumeForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your resume has been updated.')
            return redirect('resume-manage')
    else:
        form = ResumeForm(instance=profile)
        
    return render(request, 'resume_manage.html', {'form': form, 'profile': profile})

class ResumeAnalysisListView(LoginRequiredMixin, ListView):
    model = ResumeAnalysis
    template_name = 'resume_analysis_list.html'
    context_object_name = 'analyses'

    def get_queryset(self):
        return ResumeAnalysis.objects.filter(user=self.request.user).order_by('-timestamp')

class ResumeAnalysisDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ResumeAnalysis
    template_name = 'resume_analysis_detail.html'
    context_object_name = 'analysis'

    def test_func(self):
        return self.get_object().user == self.request.user

@login_required
def analyze_resume_view(request):
    if request.method == 'POST':
        profile = getattr(request.user, 'profile', None)
        if not profile or not profile.resume:
            messages.error(request, "You must upload a resume to your profile before analyzing it.")
            return redirect('resume-manage')
            
        try:
            resume_path = profile.resume.path
            resume_filename = profile.resume.name
        except ValueError:
            messages.error(request, "Resume file is missing from the server.")
            return redirect('resume-manage')
        
        job_id = request.POST.get('job_id')
        job = None
        job_description = None
        if job_id:
            job = get_object_or_404(Job, pk=job_id)
            job_description = f"{job.title} at {job.company_name}. {job.description}. Skills: {job.skills}. Experience Level: {job.experience_level}"

        # Prevent duplicate requests / Cache repeated analyses
        recent_analysis = ResumeAnalysis.objects.filter(
            user=request.user,
            job=job,
            resume_filename=resume_filename,
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).first()

        if recent_analysis:
            messages.info(request, "Displaying recent analysis results from cache.")
            return redirect('resume-analysis-detail', pk=recent_analysis.pk)

        try:
            result = analyze_resume(resume_path, job_description)
            
            analysis = ResumeAnalysis.objects.create(
                user=request.user,
                job=job,
                resume_filename=resume_filename,
                resume_score=result.get('resume_score', 0),
                ats_score=result.get('ats_score', 0),
                summary_review=result.get('summary_review', ''),
                skills_detected=result.get('skills_detected', []),
                missing_skills=result.get('missing_skills', []),
                strengths=result.get('strengths', []),
                weaknesses=result.get('weaknesses', []),
                grammar_suggestions=result.get('grammar_suggestions', []),
                formatting_suggestions=result.get('formatting_suggestions', []),
                actionable_improvements=result.get('actionable_improvements', []),
                match_percentage=result.get('match_percentage'),
                matching_skills=result.get('matching_skills', []),
                job_missing_skills=result.get('job_missing_skills', []),
                job_recommendations=result.get('job_recommendations', [])
            )
            messages.success(request, "Resume analysis complete!")
            return redirect('resume-analysis-detail', pk=analysis.pk)
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.exception(f"AI Analysis Error for user '{request.user.username}': {e}")
            messages.error(request, f"AI analysis error: {str(e)}")
            
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
    return redirect('resume-manage')