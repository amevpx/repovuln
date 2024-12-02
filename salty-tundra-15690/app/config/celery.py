# app/config/celery.py
import os
from celery import Celery
from kombu import Queue

app = Celery('crypto_issues')

app.config_from_object('django.conf:settings', namespace='CELERY')



# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('crypto_issues')

# Default queue
app.conf.task_default_queue = 'celery'
app.conf.task_default_exchange = 'celery'
app.conf.task_default_routing_key = 'celery'

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


app.conf.task_queues = (
    Queue('celery', durable=True),  # Make the 'celery' queue durable
)
