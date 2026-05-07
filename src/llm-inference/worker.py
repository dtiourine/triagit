from celery import Celery
from src.config import settings

celery_app = Celery(
    "myapp",
    broker=str(settings.REDIS_URL),
    backend=str(settings.REDIS_URL),
    include=[
        "src.llm_inference.tasks",  # explicitly list task modules
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=5 * 60,
    task_soft_time_limit=4 * 60,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)
