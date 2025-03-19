from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz
from scrape.scrape import scrape_data
from facebookgroup.model import sentiment_data_today
from conf.config_daily import sum_daily
from conf.config_del import data_config_sort_top5_del
from conf.read_config_time import read_config_time

# ฟังก์ชันสำหรับแสดงเวลาปัจจุบันใน time zone "Asia/Bangkok"
def current_time():
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    return datetime.now(bangkok_tz)

# Task: scrape_data, model, and sum_daily (config_daily)
def scrape_model_and_sum_task():
    print("Running scrape task at", current_time())
    scrape_data()

    print("Running model task immediately after scrape task at", current_time())
    sentiment_data_today()  # Run model immediately after scraping

    print("Running sum_daily task immediately after model task at", current_time())
    sum_daily()  # Aggregate data after the model

# Task: Delete old posts (config_del)
def delete_old_posts():
    print("Running delete old posts task at", current_time())
    data_config_sort_top5_del()

# อ่านค่าเวลาจากไฟล์ config_time.txt พร้อม path handling
config_time_path = 'config_time.txt' 
config_time = read_config_time(config_time_path)  # เรียกใช้ฟังก์ชันอ่านเวลาและเก็บผลลัพธ์ไว้ในตัวแปร

# Debug print เพื่อดูค่าที่อ่านได้จากไฟล์ config_time.txt
print(f"Loaded configuration: {config_time}")

# สร้าง Scheduler
scheduler = BlockingScheduler(timezone="Asia/Bangkok")

# ตั้งเวลารันงาน scrape_model_and_sum_task ตามช่วงเวลาที่กำหนดใน config_time.txt
if 'scrape_times' in config_time:
    for hour, minute in config_time['scrape_times']:
        scheduler.add_job(scrape_model_and_sum_task, 'cron', hour=hour, minute=minute)
else:
    print("No 'scrape_times' found in config_time.txt.")

# ตั้งเวลารันงาน delete_old_posts เฉพาะถ้ามีการกำหนด delete_times ใน config_time.txt
if 'delete_times' in config_time:
    for hour, minute in config_time['delete_times']:
        scheduler.add_job(delete_old_posts, 'cron', hour=hour, minute=minute)
else:
    print("No 'delete_times' found in config_time.txt, skipping delete_old_posts scheduling.")

# เริ่มการทำงาน Scheduler
print("Starting scheduler...")
scheduler.start()
