from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz
import subprocess
import os

# Function to get current time in Bangkok timezone
def current_time():
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    return datetime.now(bangkok_tz)

# Task: Scrape data, run sentiment analysis, and aggregate results
def scrape_and_analyze():
    print("Running scrape task at", current_time())
    subprocess.run(["python", "scrapedata.py"], check=True)

    print("Running sentiment analysis task at", current_time())
    subprocess.run(["python", "sentiment_Wangchan.py"], check=True)

    print("Completed all tasks at", current_time())

# Task: Delete old posts (if required)
def delete_old_posts():
    print("Running delete old posts task at", current_time())
    subprocess.run(["python", "delete_old_posts.py"], check=True)  # Ensure you have this script

# Read config times from a file
def read_config_time(file_path):
    config = {"scrape_times": [], "delete_times": []}
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(":")
                if len(parts) == 3:
                    category, hour, minute = parts
                    if category == "scrape":
                        config["scrape_times"].append((int(hour), int(minute)))
                    elif category == "delete":
                        config["delete_times"].append((int(hour), int(minute)))
    return config

# Load configuration times from config_time.txt
config_time_path = "config_time.txt"
config_time = read_config_time(config_time_path)

print(f"Loaded configuration: {config_time}")

# Create Scheduler
scheduler = BlockingScheduler(timezone="Asia/Bangkok")

# Schedule scrape and analyze task
if "scrape_times" in config_time:
    for hour, minute in config_time["scrape_times"]:
        scheduler.add_job(scrape_and_analyze, "cron", hour=hour, minute=minute)
else:
    print("No 'scrape_times' found in config_time.txt.")

# Schedule delete_old_posts task
if "delete_times" in config_time:
    for hour, minute in config_time["delete_times"]:
        scheduler.add_job(delete_old_posts, "cron", hour=hour, minute=minute)
else:
    print("No 'delete_times' found in config_time.txt.")

# Start the scheduler
print("Starting scheduler...")
scheduler.start()
