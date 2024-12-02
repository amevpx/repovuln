
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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.views.decorators.http import require_http_methods
from .tasks import analyze_repository
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Repository
from .tasks import analyze_repository
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'crypto_issues/issue_list.html')

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
            messages.success(self.request, f"Analysis completed for {repo.owner}/{repo.name}")
            return redirect('crypto_issues:repository-detail', pk=repo.pk)
        except Exception as e:
            messages.error(self.request, f"Error analyzing repository: {str(e)}")
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

@csrf_exempt
@require_http_methods(["POST"])
def upload_repo(request):
    try:
        data = json.loads(request.body)
        repo_url = data.get('repo_url')

        if not repo_url:
            logger.warning("repo_url not provided in the request.")
            return JsonResponse({'error': 'repo_url is required'}, status=400)

        # Validate the repo_url format (basic validation)
        if not repo_url.startswith('https://github.com/'):
            logger.warning(f"Invalid GitHub repository URL: {repo_url}")
            return JsonResponse({'error': 'Invalid GitHub repository URL'}, status=400)

        # Check if the repository already exists
        repository, created = Repository.objects.get_or_create(repo_url=repo_url)

        if not created:
            logger.info(f"Repository already exists: {repo_url} (ID: {repository.id})")
            # Re-enqueue task for re-analysis
            repository.status = 'pending'  # Reset status for reprocessing
            repository.analysis_result = None  # Clear previous results
            repository.save()
            analyze_repository.delay(repository.id)
            logger.info(f"Re-enqueued analyze_repository task for repo_id={repository.id}")
            return JsonResponse({'message': 'Repository re-enqueued for analysis', 'repo_id': repository.id}, status=202)

        # New repository, enqueue for the first time
        analyze_repository.delay(repository.id)
        logger.info(f"Enqueued analyze_repository task for repo_id={repository.id}")
        return JsonResponse({'message': 'Repository submitted for analysis', 'repo_id': repository.id}, status=202)

    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received.")
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        logger.exception(f"Unexpected error in upload_repo view: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_status(request, repo_id):
    try:
        repository = Repository.objects.get(id=repo_id)
        return JsonResponse({
            'repo_id': repository.id,
            'repo_url': repository.repo_url,
            'status': repository.status,
            'analysis_result': repository.analysis_result
        }, status=200)
    except Repository.DoesNotExist:
        return JsonResponse({'error': 'Repository not found'}, status=404)
