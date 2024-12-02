from django.db import models
from django.utils.text import slugify
from django.db import models
from django.utils import timezone

# crypto_issues/models.py

from django.db import models
from django.utils import timezone
# crypto_issues/models.py

from django.db import models
from django.utils import timezone

class Repository(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    owner = models.CharField(max_length=255)  # GitHub owner
    name = models.CharField(max_length=255)   # Repository name
    repo_url = models.URLField(unique=True)   # Full repository URL
    uploaded_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    analysis_result = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.owner}/{self.name}"

class CryptoIssue(models.Model):
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=500)
    line_number = models.IntegerField()
    issue_type = models.CharField(max_length=100)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    code_snippet = models.TextField()
    recommendation = models.TextField()

    def __str__(self):
        return f"{self.repository.full_name} - {self.issue_type} at {self.file_path}:{self.line_number}"