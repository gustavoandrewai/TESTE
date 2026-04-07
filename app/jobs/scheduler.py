from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.daily_pipeline import DailyPipelineService


scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")


def start_scheduler() -> None:
    if not settings.scheduler_enabled:
        return

    def _job():
        with SessionLocal() as db:
            DailyPipelineService(db).run()

    scheduler.add_job(_job, "cron", hour=19, minute=0, id="daily_fii_pipeline", replace_existing=True)
    scheduler.start()
