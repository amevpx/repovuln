from django.apps import AppConfig
import crypto_issues.signals

class CryptoIssuesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crypto_issues'

    def ready(self):
        # Import signal handlers or Celery tasks if needed
        import crypto_issues.signals