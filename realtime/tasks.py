from celery import shared_task
from .celery import app


@app.task()
def parse(x, y):
    return x + y