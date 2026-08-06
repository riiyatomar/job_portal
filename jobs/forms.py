from django import forms
from .models import Job, Company

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'company_name', 'company_logo', 'description', 
            'location', 'salary', 'job_type', 'work_mode', 
            'experience_level', 'industry', 'skills'
        ]
        
    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary is not None and salary < 0:
            raise forms.ValidationError("Salary cannot be negative.")
        return salary

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'website', 'location', 'logo', 'banner']