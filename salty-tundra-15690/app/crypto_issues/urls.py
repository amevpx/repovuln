from django.urls import path
from . import views

app_name = 'crypto_issues'

urlpatterns = [
    path('', views.IssueListView.as_view(), name='issue-list'),
    path('analyze/', views.RepositoryAnalysisView.as_view(), name='analyze'),
    path('repository/<int:pk>/', views.RepositoryDetailView.as_view(), name='repository-detail'),
]