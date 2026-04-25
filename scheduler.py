# -*- coding: utf-8 -*-
import time
import schedule
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduler")

def run_browser_post():
    logger.info("Starting scheduled browser-post task...")
    try:
        # We run the cli command as a subprocess
        # Using --limit 1 to post one by one every hour until daily limit reached
        # This makes it more organic
        result = subprocess.run(
            ["python", "main.py", "browser-post", "--limit", "5"],
            capture_output=True,
            text=True
        )
        logger.info(f"Task output:\n{result.stdout}")
        if result.stderr:
            logger.error(f"Task error:\n{result.stderr}")
    except Exception as e:
        logger.error(f"Failed to run task: {e}")

# Schedule the task every 2 hours (or whatever interval makes sense)
# Since we have a daily limit of 5, running every 2 hours is fine.
schedule.every(2).hours.do(run_browser_post)

# Also run once immediately on start
run_browser_post()

logger.info("Scheduler started. Running every 2 hours.")

while True:
    schedule.run_pending()
    time.sleep(60)
