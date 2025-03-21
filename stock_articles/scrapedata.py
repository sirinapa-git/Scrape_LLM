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

# Function to clean up text
def clean_text(text):
    if not text or text.isdigit():
        return None
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()
    text = re.sub(r'http[s]?://\S+', '', text) 
    text = re.sub(r'\s+', ' ', text) 
    return text.strip()

# Set up Chrome WebDriver
def setup_chrome():
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.set_page_load_timeout(60)
        print("✅ Chrome WebDriver is ready!")
        return driver
    except Exception as e:
        print(f"Couldn't start Chrome WebDriver: {e}")
        return None

# Load existing news titles to avoid duplicates
def load_existing_titles():
    if os.path.exists("kaohoon_news.csv"):
        df = pd.read_csv("kaohoon_news.csv")
        return set(df["title"].dropna().str.strip()) if "title" in df.columns else set()
    return set()

# Get article links from Kaohoon
def get_news_links(driver):
    url = "https://www.kaohoon.com/latest-news"
    driver.get(url)
    time.sleep(5)

    try:
        links = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "tie-col-md-11")]/a'))
        )
        return list(set(link.get_attribute("href") for link in links if link.get_attribute("href")))
    except Exception as e:
        print(f"Couldn't get article links: {e}")
        return []

# Get article content
def get_news_content(driver, links, existing_titles, max_articles=20):
    news_data = []
    
    for link in links[:max_articles]:
        try:
            driver.get(link)
            title_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            title = clean_text(title_element.text)

            if title in existing_titles:
                continue

            # Try multiple class names to find content
            content = None
            for class_name in ["entry-content", "post-content", "article-content"]:
                try:
                    content_div = driver.find_element(By.CLASS_NAME, class_name)
                    content = clean_text(content_div.text)
                    break
                except:
                    continue
            
            if content and content.lower() != "no content found":
                news_data.append({"title": title, "link": link, "content": content})
                print(f"✅ Added: {title}")
            else:
                print(f"Skipped (No content): {title}")

            time.sleep(2)

        except Exception as e:
            print(f"Failed to fetch {link}: {e}")

    return news_data

# Main function
def main():
    driver = setup_chrome()
    if not driver:
        return

    print("📥 Getting news links...")
    links = get_news_links(driver)
    print(f"✅ Found {len(links)} articles.")

    if not links:
        driver.quit()
        return

    existing_titles = load_existing_titles()

    print("📄 Getting news content...")
    news_data = get_news_content(driver, links, existing_titles)

    if not news_data:
        print("✅ No new articles to save.")
        driver.quit()
        return

    df = pd.DataFrame(news_data)

    if os.path.exists("kaohoon_news.csv"):
        df_existing = pd.read_csv("kaohoon_news.csv")
        df = pd.concat([df_existing, df], ignore_index=True)

    df.to_csv("kaohoon_news.csv", index=False, encoding='utf-8-sig')
    print(f"✅ Saved {len(df)} articles to kaohoon_news.csv.")

    driver.quit()

if __name__ == "__main__":
    main()
    print("✅ Done!")
