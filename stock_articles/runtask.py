import schedule
import time
import subprocess


def run_scraper():
    print("Run scrapedata.py")
    subprocess.run(["python", "scrapedata.py"])

def run_sentiment_analysis():
    print("Run sentiment_Wangchan.py")
    subprocess.run(["python", "sentiment_Wangchan.py"])

def run_tasks():
    run_scraper()
    time.sleep(5)  
    run_sentiment_analysis()

print("START🔥")
run_tasks()

# ตั้งให้รันซ้ำทุก 2 นาที
schedule.every(2).minutes.do(run_tasks)

print("Scheduler Start... Ctrl+C to STOP")

while True:
    schedule.run_pending()
    time.sleep(1)
