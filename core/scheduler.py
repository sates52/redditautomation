from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class PostScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
    
    def start(self):
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def stop(self):
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def add_job(self, func: Callable, hour: int, minute: int, day_of_week: str = None,
                job_id: str = None):
        if day_of_week:
            trigger = CronTrigger(hour=hour, minute=minute, day_of_week=day_of_week)
        else:
            trigger = CronTrigger(hour=hour, minute=minute)
        
        job = self.scheduler.add_job(
            func,
            trigger,
            id=job_id,
            replace_existing=True
        )
        
        self.jobs[job_id or func.__name__] = job
        logger.info(f"Scheduled job {job_id or func.__name__} at {hour:02d}:{minute:02d}")
        return job
    
    def remove_job(self, job_id: str):
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"Removed job {job_id}")
        except Exception as e:
            logger.error(f"Error removing job: {e}")
    
    def get_next_run_time(self, job_id: str) -> datetime:
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None
