import os
import mimetypes
from django.core.files.base import ContentFile
from django.shortcuts import redirect, get_object_or_404
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.db.models import Sum, Q, Count
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Job, Application, RecruiterNote, ApplicationStatusHistory, Company
from .forms import JobForm, CompanyForm


class JobListView(ListView):
    model = Job
    template_name = 'job_list.html'
    context_object_name = 'all_jobs'
    paginate_by = 12

    def get_queryset(self):
        queryset = Job.objects.filter(is_closed=False).select_related('posted_by', 'company').annotate(
            applications_count=Count('application')
        )

        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(company_name__icontains=q) |
                Q(skills__icontains=q) |
                Q(location__icontains=q) |
                Q(description__icontains=q)
            )

        job_type = self.request.GET.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)

        work_mode = self.request.GET.get('work_mode')
        if work_mode:
            queryset = queryset.filter(work_mode=work_mode)

        experience_level = self.request.GET.get('experience_level')
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)

        min_salary = self.request.GET.get('min_salary')
        if min_salary and min_salary.isdigit():
            queryset = queryset.filter(salary__gte=min_salary)

        max_salary = self.request.GET.get('max_salary')
        if max_salary and max_salary.isdigit():
            queryset = queryset.filter(salary__lte=max_salary)

        location = self.request.GET.get('location', '').strip()
        if location:
            queryset = queryset.filter(location__icontains=location)

        industry = self.request.GET.get('industry', '').strip()
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
            
        skills = self.request.GET.get('skills', '').strip()
        if skills:
            queryset = queryset.filter(skills__icontains=skills)

        date_posted = self.request.GET.get('date_posted')
        if date_posted:
            now = timezone.now()
            if date_posted == 'today':
                queryset = queryset.filter(date_posted__gte=now - timedelta(days=1))
            elif date_posted == '7days':
                queryset = queryset.filter(date_posted__gte=now - timedelta(days=7))
            elif date_posted == '30days':
                queryset = queryset.filter(date_posted__gte=now - timedelta(days=30))

        sort_by = self.request.GET.get('sort_by', 'newest')
        if sort_by == 'oldest':
            queryset = queryset.order_by('date_posted')
        elif sort_by == 'highest_salary':
            queryset = queryset.order_by('-salary')
        elif sort_by == 'lowest_salary':
            queryset = queryset.order_by('salary')
        elif sort_by == 'most_applications':
            queryset = queryset.order_by('-applications_count', '-date_posted')
        elif sort_by == 'company_name':
            queryset = queryset.order_by('company_name', '-date_posted')
        else:
            queryset = queryset.order_by('-date_posted')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Build query string to preserve filters in pagination links
        query_dict = self.request.GET.copy()
        if 'page' in query_dict:
            del query_dict['page']
        context['query_string'] = query_dict.urlencode()
        
        # Pass choices to template
        context['job_type_choices'] = Job.JOB_TYPE_CHOICES
        context['work_mode_choices'] = Job.WORK_MODE_CHOICES
        context['experience_level_choices'] = Job.EXPERIENCE_LEVEL_CHOICES
        
        # Pass applied filters back to template
        context['filters'] = {
            'q': self.request.GET.get('q', ''),
            'job_type': self.request.GET.get('job_type', ''),
            'work_mode': self.request.GET.get('work_mode', ''),
            'experience_level': self.request.GET.get('experience_level', ''),
            'min_salary': self.request.GET.get('min_salary', ''),
            'max_salary': self.request.GET.get('max_salary', ''),
            'location': self.request.GET.get('location', ''),
            'industry': self.request.GET.get('industry', ''),
            'skills': self.request.GET.get('skills', ''),
            'date_posted': self.request.GET.get('date_posted', ''),
            'sort_by': self.request.GET.get('sort_by', 'newest'),
        }
        
        return context


class JobDetailView(DetailView):
    model = Job
    template_name = 'job_details.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            app = Application.objects.filter(job=self.object, applicant=user).first()
            if app:
                context['already_applied'] = True
                context['application_status'] = app.status
        return context


class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('job-list')

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        try:
            form.instance.company = self.request.user.company
        except Company.DoesNotExist:
            pass
        return super().form_valid(form)


class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'job_form.html'
    success_url = reverse_lazy('job-list')

    def test_func(self):
        return self.get_object().posted_by == self.request.user

    def form_valid(self, form):
        try:
            if not form.instance.company:
                form.instance.company = self.request.user.company
        except Company.DoesNotExist:
            pass
        return super().form_valid(form)


class JobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Job
    template_name = 'job_confirm_delete.html'
    success_url = reverse_lazy('job-list')

    def test_func(self):
        return self.get_object().posted_by == self.request.user


class EmployerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'employer_dashboard.html'

    def test_func(self):
        return self.request.user.role == 'employer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if employer has a company profile
        try:
            context['company'] = self.request.user.company
        except Company.DoesNotExist:
            context['company'] = None

        my_jobs = Job.objects.filter(posted_by=self.request.user).select_related('company').annotate(applications_count=Count('application'))
        context['total_jobs'] = my_jobs.count()
        context['active_jobs'] = my_jobs.filter(is_closed=False).count()
        context['closed_jobs'] = my_jobs.filter(is_closed=True).count()
        
        now = timezone.now()
        context['total_applications'] = Application.objects.filter(job__in=my_jobs).count()
        context['applications_today'] = Application.objects.filter(job__in=my_jobs, date_applied__gte=now - timedelta(days=1)).count()
        context['applications_this_week'] = Application.objects.filter(job__in=my_jobs, date_applied__gte=now - timedelta(days=7)).count()
        
        context['total_views'] = my_jobs.aggregate(Sum('views_count'))['views_count__sum'] or 0
        context['recent_applicants'] = Application.objects.filter(job__in=my_jobs).select_related('job', 'applicant', 'applicant__profile').order_by('-date_applied')[:5]
        context['my_jobs'] = my_jobs
        
        # ATS Additions
        status_counts = Application.objects.filter(job__in=my_jobs).values('status').annotate(count=Count('status'))
        context['applications_by_status'] = {item['status']: item['count'] for item in status_counts}
        
        context['recent_status_changes'] = ApplicationStatusHistory.objects.filter(
            application__job__in=my_jobs
        ).select_related('application__applicant', 'application__job', 'updated_by').order_by('-timestamp')[:5]
        
        return context

class CompanyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'company_form.html'
    success_url = reverse_lazy('employer-dashboard')

    def test_func(self):
        # Only employers who don't already have a company can create one
        if self.request.user.role != 'employer':
            return False
        try:
            self.request.user.company
            return False  # Company exists, deny creation
        except Company.DoesNotExist:
            return True  # No company yet, allow creation

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'company_form.html'
    
    def get_success_url(self):
        return reverse('company-detail', kwargs={'slug': self.object.slug})

    def test_func(self):
        return self.get_object().owner == self.request.user


class CompanyDetailView(DetailView):
    model = Company
    template_name = 'company_detail.html'
    context_object_name = 'company'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        open_jobs_list = self.object.jobs.filter(is_closed=False).select_related('posted_by').order_by('-date_posted')
        paginator = Paginator(open_jobs_list, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['open_jobs'] = page_obj
        return context


class CompanyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Company
    template_name = 'company_confirm_delete.html'
    success_url = reverse_lazy('employer-dashboard')

    def test_func(self):
        return self.get_object().owner == self.request.user

@login_required
@require_POST
def job_toggle_status(request, pk, action):
    job = get_object_or_404(Job, pk=pk)
    if job.posted_by != request.user:
        raise PermissionDenied("You cannot modify this job.")
    
    if action == 'close':
        job.is_closed = True
        messages.success(request, "Job closed successfully.")
    elif action == 'reopen':
        job.is_closed = False
        messages.success(request, "Job reopened successfully.")
    job.save(update_fields=['is_closed'])
    return redirect('employer-dashboard')

class JobApplicantsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Job
    template_name = 'job_applicants.html'
    context_object_name = 'job'

    def test_func(self):
        return self.get_object().posted_by == self.request.user
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.object.application_set.select_related('applicant', 'applicant__profile').order_by('-date_applied')
        
        # Filtering
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Searching
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(applicant__username__icontains=search_query)
            
        paginator = Paginator(queryset, 20)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
            
        context['applications'] = page_obj
        context['current_status'] = status_filter
        context['search_query'] = search_query or ''
        context['status_choices'] = Application.STATUS_CHOICES
        return context

    def post(self, request, *args, **kwargs):
        job = self.get_object()
        
        # Check for bulk action
        bulk_status = request.POST.get('bulk_status')
        application_ids = request.POST.getlist('application_ids')
        
        if bulk_status and application_ids:
            apps = Application.objects.filter(id__in=application_ids, job=job)

            count = 0
            for app in apps:
                if app.status != bulk_status:
                    app.status = bulk_status
                    app.save(update_fields=['status'])
                    ApplicationStatusHistory.objects.create(
                        application=app,
                        status=bulk_status,
                        updated_by=request.user,
                        note="Bulk status update."
                    )
                    count += 1
            messages.success(request, f"Status updated to {bulk_status} for {count} candidate(s).")
            return redirect('job-applicants', pk=job.pk)

        # Single action
        app_id = request.POST.get('application_id')
        new_status = request.POST.get('status')
        note = request.POST.get('note', '')
        
        if app_id and new_status:
            app = get_object_or_404(Application, pk=app_id, job=job)
            if app.status != new_status:
                app.status = new_status
                app.save(update_fields=['status'])
                
                # Create history entry

                ApplicationStatusHistory.objects.create(
                    application=app,
                    status=new_status,
                    updated_by=request.user,
                    note=note
                )
                
                messages.success(request, f"Status updated to {new_status} for {app.applicant.username}.")
        return redirect('job-applicants', pk=job.pk)

@login_required
@require_POST
def withdraw_application(request, pk):
    app = get_object_or_404(Application, pk=pk)
    if app.applicant != request.user:
        raise PermissionDenied("You can only withdraw your own applications.")
        
    if app.status in ['Hired', 'Rejected', 'Withdrawn']:
        messages.error(request, f"You cannot withdraw this application (current status: {app.status}).")
        return redirect('my-applications')
        
    if request.method == 'POST':
        app.status = 'Withdrawn'
        app.save(update_fields=['status'])
        

        ApplicationStatusHistory.objects.create(
            application=app,
            status='Withdrawn',
            updated_by=request.user,
            note="Application withdrawn by candidate."
        )
        messages.success(request, "Your application has been withdrawn.")
        
    return redirect('my-applications')


class ApplicantProfileView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Application
    template_name = 'applicant_profile.html'
    context_object_name = 'application'

    def get_queryset(self):
        return Application.objects.select_related('applicant', 'applicant__profile', 'job')

    def test_func(self):
        application = self.get_object()
        return application.job.posted_by == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recruiter_notes'] = self.object.recruiter_notes.select_related('created_by').all()
        context['status_choices'] = Application.STATUS_CHOICES
        
        # Safe resume file size calculation
        def get_file_size(file_field):
            try:
                return round(file_field.size / (1024 * 1024), 2)
            except (ValueError, OSError, AttributeError):
                return 0

        if self.object.resume:
            context['resume_size_mb'] = get_file_size(self.object.resume)
        elif self.object.applicant.profile.resume:
            context['resume_size_mb'] = get_file_size(self.object.applicant.profile.resume)
        else:
            context['resume_size_mb'] = 0

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        action = request.POST.get('action')

        if action == 'add_note':
            title = request.POST.get('title')
            note = request.POST.get('note')
            rating = request.POST.get('rating')
            recommendation = request.POST.get('recommendation')
            strong_candidate = request.POST.get('strong_candidate') == 'on'

            RecruiterNote.objects.create(
                application=self.object,
                title=title,
                note=note,
                rating=rating if rating else 0,
                recommendation=recommendation,
                strong_candidate=strong_candidate,
                created_by=request.user
            )
            messages.success(request, "Recruiter note added.")
            
        elif action == 'change_status':
            new_status = request.POST.get('status')
            if new_status and new_status != self.object.status:
                self.object.status = new_status
                self.object.save(update_fields=['status'])
                
                ApplicationStatusHistory.objects.create(
                    application=self.object,
                    status=new_status,
                    updated_by=request.user,
                    note="Status updated via Quick Actions."
                )
                messages.success(request, f"Status updated to {new_status}.")

        return redirect('applicant-profile', pk=self.object.pk)


@login_required
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if job.posted_by == request.user:
        raise PermissionDenied("You cannot apply to your own job.")
    
    if request.method == 'POST':
        resume = request.FILES.get('resume')
        if not resume:
            try:
                profile_resume = request.user.profile.resume
                if profile_resume:
                    resume = ContentFile(profile_resume.read(), name=os.path.basename(profile_resume.name))
            except Exception:
                resume = None
        
        if not resume:
            messages.error(request, "You must provide a resume to apply.")
            return redirect('job-detail', pk=job.pk)

        app, created = Application.objects.get_or_create(job=job, applicant=request.user)
        if created:
            app.resume = resume
            try:
                app.full_clean()
                app.save()
                messages.success(request, "Successfully applied for the job!")
            except ValidationError as e:
                app.delete()
                messages.error(request, getattr(e, 'messages', [str(e)])[0])
    
    return redirect('job-detail', pk=job.pk)


class MyApplicationsListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'my_applications.html'
    context_object_name = 'applications'
    paginate_by = 10

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user).select_related('job', 'job__posted_by', 'job__company').prefetch_related('status_history')

@login_required
def download_resume(request, pk):
    app = get_object_or_404(Application.objects.select_related('applicant', 'job__posted_by', 'applicant__profile'), pk=pk)
    
    if app.applicant != request.user and app.job.posted_by != request.user:
        raise PermissionDenied("You do not have permission to view this resume.")
        
    resume_file = app.resume or (app.applicant.profile.resume if hasattr(app.applicant, 'profile') else None)
    if not resume_file:
        raise Http404("Resume not found.")
        
    try:
        if not resume_file.storage.exists(resume_file.name):
            raise Http404("Resume file is missing from storage.")

        # Detect MIME type dynamically
        filename = os.path.basename(resume_file.name)
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = 'application/octet-stream'

        response = FileResponse(resume_file.open('rb'), content_type=content_type)

        # PDFs open inline in browser; everything else downloads
        if content_type == 'application/pdf':
            response['Content-Disposition'] = f'inline; filename="{filename}"'
        else:
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response
    except (ValueError, OSError, FileNotFoundError):
        raise Http404("Resume file is missing or corrupted.")