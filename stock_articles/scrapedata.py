from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
import re
from bs4 import BeautifulSoup

# def clean_text(text):
#     if not text or text.isdigit():
#         return None
#     soup = BeautifulSoup(text, 'html.parser')
#     clean_text = soup.get_text()
#     clean_text = re.sub(r'http[s]?://\S+', '', clean_text)
#     clean_text = re.sub(r'[^\w\sก-๙]', '', clean_text)
#     clean_text = re.sub(r'\s+', ' ', clean_text)
#     return clean_text.strip()

def clean_text(text):
    if not text or text.isdigit():
        return None
    soup = BeautifulSoup(text, 'html.parser')
    clean_text = soup.get_text()
    clean_text = re.sub(r'http[s]?://\S+', '', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()

def setup_chrome():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')  
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36")
    chrome_options.page_load_strategy = 'eager' 
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)  # timeout 60
        print("✅ Chrome WebDriver Setup Completed!")
        return driver
    except Exception as e:
        print(f"❌ Error initializing Chrome WebDriver: {e}")
        return None

def check_dataduplicate():
    existing_titles = set()
    
    if os.path.exists("kaohoon_news.csv"):
        df_existing = pd.read_csv("kaohoon_news.csv")
        if "title" in df_existing.columns:
            existing_titles = set(df_existing["title"].str.strip())  

    return existing_titles

def fetch_kaohoon_news_links(driver):
    url = "https://www.kaohoon.com/latest-news"
    driver.get(url)
    time.sleep(5)

    news_links = []
    
    try:
        links_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//div[contains(@class, "tie-col-md-11")]/a')
            )
        )

        for link in links_elements:
            href = link.get_attribute("href")
            if href and "kaohoon.com" in href:
                news_links.append(href)

    except Exception as e:
        print(f"❌ Error fetching links: {e}")

    return list(set(news_links))

def fetch_news_content(driver, news_links, max_articles=20):
    existing_titles = check_dataduplicate()
    news_data = []

    for i, link in enumerate(news_links[:max_articles]):
        try:
            driver.get(link)

            try:
                title = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                ).text.strip()
                title = clean_text(title)
                
                if title in existing_titles:
                    print(f"⚠️ Skipping duplicate article: {title}")
                    continue  

                content = "No content found"
                for class_name in ["entry-content", "post-content", "article-content"]:
                    try:
                        content_div = driver.find_element(By.CLASS_NAME, class_name)
                        content = content_div.text.strip()
                        break
                    except:
                        continue

                content = clean_text(content)

            except Exception as e:
                print(f"❌ Failed to fetch content from {link}: {e}")
                title = "Failed to retrieve data"
                content = "Unable to fetch content"

            news_data.append({"title": title, "link": link, "content": content})
            time.sleep(2)

        except Exception as e:
            print(f"❌ Error with link {link}: {e}")

    return news_data

def main():
    try:
        print("🔧 Setting up Chrome...")
        driver = setup_chrome()
        
        print("📥 Fetching news links from Kaohoon...")
        news_links = fetch_kaohoon_news_links(driver)
        print(f"✅ Found {len(news_links)} articles")

        if not news_links:
            print("⚠️ No links found, exiting.")
            driver.quit()
            return

        print("📄 Scraping news content...")
        news_data = fetch_news_content(driver, news_links, max_articles=20)

        if not news_data:
            print("✅ No new articles found. Exiting...")
            return

        df = pd.DataFrame(news_data)

        if os.path.exists("kaohoon_news.csv"):
            df_existing = pd.read_csv("kaohoon_news.csv")
            df = pd.concat([df_existing, df], ignore_index=True)

        df.to_csv("kaohoon_news.csv", index=False, encoding='utf-8-sig')
        print(f"✅ Saved {len(df)} articles to kaohoon_news.csv")

        return df

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        try:
            driver.quit()
            print("🔒 Closed WebDriver")
        except:
            pass

if __name__ == "__main__":
    df = main()
    
    if isinstance(df, pd.DataFrame) and not df.empty:
        print(df.head())

    print("✅ Finished Scraping!")
