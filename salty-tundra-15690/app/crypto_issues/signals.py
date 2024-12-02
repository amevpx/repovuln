from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender='crypto_issues.Repository')
def repository_post_save(sender, instance, created, **kwargs):
    if created:
        from .tasks import analyze_repository
        analyze_repository.delay(instance.id)
