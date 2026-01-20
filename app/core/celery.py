from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from datetime import timedelta


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Set the timezone
# app.conf.timezone = 'Asia/Singapore'

# Add the new setting to handle broker connection retries on startup
app.conf.broker_connection_retry_on_startup = True

# Configure Celery beat schedule
app.conf.beat_schedule = {
    'check-expired-dates-every-second': {
        'task': 'api.tasks.check_expired_quest',
        'schedule': timedelta(seconds=10),
    },
}

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
