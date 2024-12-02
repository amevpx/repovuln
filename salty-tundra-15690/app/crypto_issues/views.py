
# views.py
from django.views.generic import ListView, FormView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count
from django.conf import settings
from .models import Repository, CryptoIssue
from .forms import RepositoryForm
from .services import CryptoAnalyzer

class IssueListView(ListView):
    template_name = 'crypto_issues/issue_list.html'
    context_object_name = 'issues'
    paginate_by = settings.PAGINATE_BY

    def get_queryset(self):
        queryset = CryptoIssue.objects.select_related('repository').all()
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['severities'] = [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical')
        ]
        context['current_severity'] = self.request.GET.get('severity', '')
        
        # Add statistics
        context['stats'] = {
            'total_issues': CryptoIssue.objects.count(),
            'total_repos': Repository.objects.count(),
            'low_issues': CryptoIssue.objects.filter(severity='low').count(),
            'medium_issues': CryptoIssue.objects.filter(severity='medium').count(),
            'high_issues': CryptoIssue.objects.filter(severity='high').count(),
            'critical_issues': CryptoIssue.objects.filter(severity='critical').count(),
        }
        
        return context

class RepositoryAnalysisView(FormView):
    template_name = 'crypto_issues/analyze.html'
    form_class = RepositoryForm
    success_url = reverse_lazy('crypto_issues:analyze')

    def form_valid(self, form):
        try:
            analyzer = CryptoAnalyzer(settings.GITHUB_TOKEN)
            repo = analyzer.analyze_repository(form.cleaned_data['repository_url'])
            messages.success(self.request, 'Repository analysis completed successfully')
            return redirect('crypto_issues:repository-detail', pk=repo.pk)
        except Exception as e:
            messages.error(self.request, f'Error analyzing repository: {str(e)}')
            return self.form_invalid(form)

class RepositoryDetailView(ListView):
    template_name = 'crypto_issues/repository_detail.html'
    context_object_name = 'issues'
    paginate_by = settings.PAGINATE_BY

    def get_queryset(self):
        return CryptoIssue.objects.filter(repository_id=self.kwargs['pk']).order_by(
            'severity', 'file_path', 'line_number'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        repo = Repository.objects.get(pk=self.kwargs['pk'])
        context['repository'] = repo
        context['stats'] = {
            'total_issues': self.get_queryset().count(),
            'critical_issues': self.get_queryset().filter(severity='critical').count(),
            'high_issues': self.get_queryset().filter(severity='high').count(),
            'medium_issues': self.get_queryset().filter(severity='medium').count(),
            'low_issues': self.get_queryset().filter(severity='low').count(),
            'files_affected': self.get_queryset().values('file_path').distinct().count()
        }
        return context