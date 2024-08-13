import time
from data_updater import update_data
from celery_tasks import scheduled_update
from logging_config import logger
from database import create_tables

if __name__ == "__main__":
    logger.info("Starting scheduler...")
    create_tables()
    while True:
        try:
            scheduled_update.apply_async()
            logger.info("Scheduled update task dispatched.")
            time.sleep(3600)  # Runs every hour
        except Exception as e:
            logger.error(f"Error in scheduler: {e}")
