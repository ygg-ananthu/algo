# celery_config.py
from celery import Celery
from celery.schedules import crontab

app = Celery('trade_tasks', broker='redis://localhost:6379/0')


app.conf.update(
    timezone='Asia/Calcutta',  # Set your local timezone here
    enable_utc=True,  # Ensure UTC is enabled
)
app.autodiscover_tasks(['cronjobs'])

app.conf.beat_schedule = {
    'run-trade-task-every-friday': {
        'task': 'trades.tasks.execute_trading_bot',
        'schedule': crontab(minute=0, hour=10, day_of_week='fri'),
    },
}
