from django.db import models
from django.utils.text import slugify

class Repository(models.Model):
    name = models.CharField(max_length=200)
    owner = models.CharField(max_length=100)
    url = models.URLField()
    stars = models.IntegerField(default=0)
    last_analyzed = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('analyzing', 'Analyzing'),
        ('completed', 'Completed'),
        ('error', 'Error')
    ], default='pending')
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.owner}/{self.name}"

    @property
    def full_name(self):
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