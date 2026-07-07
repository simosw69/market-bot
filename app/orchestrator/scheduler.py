from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import os
from typing import Callable, Dict

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self._scheduler = BackgroundScheduler()
        self.jobs: Dict[str, any] = {}  # map job_id to job object

    def add_job(self, func, trigger, id: str, **kwargs):
        """Add a job to the scheduler."""
        job = self._scheduler.add_job(func, trigger, id=id, **kwargs)
        self.jobs[id] = job
        logger.info(f"Added job {id}")
        return job

    def remove_job(self, id: str):
        """Remove a job by its id."""
        if id in self.jobs:
            self._scheduler.remove_job(id)
            del self.jobs[id]
            logger.info(f"Removed job {id}")

    def start(self):
        """Start the scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        self._scheduler.shutdown()
        logger.info("Scheduler shutdown")

# Global scheduler instance
scheduler = TaskScheduler()