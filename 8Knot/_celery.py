from celery import Celery
from dash import CeleryManager
import os

redis_host = "{}".format(os.getenv("REDIS_SERVICE_HOST", "redis-cache"))
redis_port = "{}".format(os.getenv("REDIS_SERVICE_PORT", "6379"))
redis_password = "{}@".format(os.getenv("REDIS_PASSWORD", ""))
REDIS_URL = f"redis://:{redis_password}{redis_host}:{redis_port}"


"""CREATE CELERY TASK QUEUE AND MANAGER"""
celery_app = Celery(
    __name__,
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_time_limit=2700,  # 45 minutes
    task_acks_late=True,
    task_track_started=True,
    result_extended=True,
    worker_prefetch_multiplier=1,
)

celery_manager = CeleryManager(celery_app=celery_app)
