from django.urls import path
from . import views

app_name = 'crypto_issues'

urlpatterns = [
    path('', views.IssueListView.as_view(), name='issue-list'),
    path('analyze/', views.RepositoryAnalysisView.as_view(), name='analyze'),
    path('repository/<int:pk>/', views.RepositoryDetailView.as_view(), name='repository-detail'),
    path('upload/', views.upload_repo, name='upload_repo'),
    path('status/<int:repo_id>/', views.get_status, name='get_status'),
    path('api/upload_repo/', views.upload_repo, name='upload_repo'),
    path('api/upload_repo/', views.upload_repo, name='upload_repo'),
    path('upload/', views.upload_repo, name='upload_repo'),

]

