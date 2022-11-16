from celery import Celery
from dash import CeleryManager
import worker_settings

celery_app = Celery(
    __name__,
    broker=worker_settings.REDIS_URL,
    backend=worker_settings.REDIS_URL,
)
celery_manager = CeleryManager(celery_app=celery_app)
