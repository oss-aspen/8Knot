from celery import Celery
from dash import CeleryManager
import worker_settings

celery_app = Celery(
    __name__,
    broker=worker_settings.REDIS_URL,
    backend=worker_settings.REDIS_URL,
)

celery_app.conf.update(
    task_time_limit=84600, task_acks_late=True, task_track_started=True
)

celery_manager = CeleryManager(celery_app=celery_app)
