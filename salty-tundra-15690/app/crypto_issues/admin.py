from django.contrib import admin
from .models import Repository, CryptoIssue

admin.site.register(Repository)
admin.site.register(CryptoIssue)