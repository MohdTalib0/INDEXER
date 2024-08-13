from celery import Celery
from data_updater import update_data
from logging_config import logger

app = Celery('tasks', broker='sqla+mysql://Errorsearching:7408185999@Talib@Errorsearching.mysql.pythonanywhere-services.com/Errorsearching$INDEXER')

@app.task
def scheduled_update():
    logger.info("Running scheduled update task...")
    try:
        update_data()
        logger.info("Scheduled update task completed successfully.")
    except Exception as e:
        logger.error(f"Error in scheduled update task: {e}")
