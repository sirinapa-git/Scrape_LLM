import time
import pymysql
# from mysql.connector import Error
from datetime import datetime
import pytz
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as bs
import os
import re
from dotenv import load_dotenv

# โหลดข้อมูลจากไฟล์ .env
load_dotenv()

# Function to connect to MySQL database
def connect_to_mysql():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='mydb'
        )
        print("Connected to MySQL successfully")
        return connection
    except Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

# Setup logging to record events and errors
log_filename = os.path.join('scrape','config','app.log')
logging.basicConfig(
    level=logging.INFO,                  # Set log level to INFO
    filename=log_filename,               # Log file location
    filemode='w',                        # Overwrite log file each time
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    encoding='utf-8-sig'                 # Encoding format
)

# Function to get current time in Asia/Bangkok timezone
def current_time():
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    return datetime.now(bangkok_tz)

# Read credentials (email, password, group_url) from a file
def read_credentials():
    credentials = {}
    with open('scrape\config_path_scrape.txt', 'r') as f:
        lines = f.readlines()
    for line in lines:
        if '=' in line:
            key, value = line.strip().split(' = ', 1)
            credentials[key] = value
    return credentials

# Function to create 'posts' table in MySQL if it doesn't exist
def create_table(connection):
    create_posts_table = """
    CREATE TABLE IF NOT EXISTS posts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        Date VARCHAR(255),
        Post TEXT,
        Reactions INT
    )
    """
    try:
        cursor = connection.cursor()
        cursor.execute(create_posts_table)
        connection.commit()
        print("Table 'posts' ensured to exist.")
    except Error as err:
        print(f"Error creating table: {err}")

# Insert a new post into the 'posts' table
def insert_post(connection, post_data):
    insert_query = """
    INSERT INTO posts (Date, Post, Reactions)
    VALUES (%s, %s, %s)
    """
    try:
        cursor = connection.cursor()
        cursor.execute(insert_query, (
            post_data['Date'],
            post_data['Post'],
            post_data['Reactions']
        ))
        connection.commit()
    except Error as err:
        print(f"Error inserting data: {err}")

# Insert or update a post in the 'posts' table based on existence
def insert_or_update_post(connection, post_data):
    try:
        select_query = "SELECT Date FROM posts WHERE Post = %s"
        cursor = connection.cursor()
        cursor.execute(select_query, (post_data['Post'],))
        existing_post = cursor.fetchone()

        # Update post if newer date is found
        if existing_post and existing_post[0] < post_data['Date']:
            update_query = """
            UPDATE posts SET Date = %s, Reactions = %s WHERE Post = %s
            """
            cursor.execute(update_query, (
                post_data['Date'],
                post_data['Reactions'],
                post_data['Post']
            ))
        elif not existing_post:
            insert_post(connection, post_data)  # Insert if post doesn't exist

        connection.commit()
    except Error as err:
        print(f"Error inserting or updating data: {err}")

# Convert Thai numeral text or abbreviations like K, M to numeric values
def convert_numbers(text):
    try:
        number = re.findall(r'\d+\.?\d*', text)[0]  # Find the numeric part
        number = float(number)
        # Convert based on Thai numerals or abbreviations
        if 'พัน' in text or 'K' in text:
            return number * 1000
        elif 'หมื่น' in text:
            return number * 10000
        elif 'แสน' in text:
            return number * 100000
        elif 'ล้าน' in text or 'M' in text:
            return number * 1000000
        return number
    except IndexError:
        logging.error(f"Error converting number: {text}")
        return 0

# Extract numeric value from text using Thai numerals or abbreviations
def extract_number(text):
    thai_numerals = ['พัน', 'หมื่น', 'แสน', 'ล้าน', 'K', 'M']
    for numeral in thai_numerals:
        if numeral in text:
            return str(convert_numbers(text))
    try:
        return str(float(re.findall(r'\d+\.?\d*', text)[0]))
    except IndexError:
        return '0'

# Save post data (without Comments and Shares)
def save_post_data(post_html, connection):
    try:
        # Extract post text from HTML
        post_text_div = post_html.find('div', {'data-ad-preview': 'message'})
        post_text = post_text_div.get_text(strip=True).replace('\n', ' ').replace('\r', ' ') if post_text_div else ""

        # Extract image post text if no text post found
        image_post_div = post_html.find('div', {'class': 'x6s0dn4 x78zum5 xdt5ytf x5yr21d xl56j7k x10l6tqk x17qophe x13vifvy xh8yej3'})
        image_post_text = image_post_div.get_text(strip=True).replace('\n', ' ').replace('\r', ' ') if image_post_div else ""
        if not post_text and image_post_text:
            post_text = image_post_text

        if not post_text.strip():
            # logging.info("No post text found, skipping saving to database.")
            logging.info("saving to database.")
            return

        # Extract reactions count from HTML
        reaction_span = post_html.find_all('span', {'class': 'xrbpyxo x6ikm8r x10wlt62 xlyipyv x1exxlbk'})
        reactions = int(float(extract_number(reaction_span[0].get_text(strip=True)))) if reaction_span else 0

        # Prepare data for insertion
        new_data = {
            'Date': current_time().strftime('%Y-%m-%d %H:%M:%S'),
            'Post': post_text,
            'Reactions': reactions
        }

        # Insert or update post in database
        insert_or_update_post(connection, new_data)
    except Exception as e:
        logging.error(f"Failed to save post data: {e}")

# Initialize Chrome options for Selenium WebDriver
chrome_options = Options()
chrome_options.binary_location = r"scrape\chrome\chrome-win64\chrome.exe"  # Chrome binary path
chrome_options.add_argument('--headless')  # Run in headless mode (no UI)
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920x1080')
chrome_options.add_argument('--disable-software-rasterizer')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--disable-logging')
chrome_options.add_argument('--remote-debugging-port=9222') #set port
chrome_options.add_argument('--lang=th')  # Set language to Thai
chrome_options.add_argument('--disable-notifications')


# Setup Selenium WebDriver
chromedriver_path = r"scrape\chrome\chromedriver-win64\chromedriver.exe"
driver_service = Service(chromedriver_path)
driver = webdriver.Chrome(service=driver_service, options=chrome_options)

# Function to log into Facebook
def login(email, password):
    logging.info("Attempting to log in...")
    driver.get('https://www.facebook.com/login/')
    try:
        email_input = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'email')))
        password_input = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'pass')))
        login_button = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'login')))
        
        # Input email and password, then click login
        email_input.send_keys(email)
        password_input.send_keys(password)
        login_button.click()
        
        # Wait for successful login
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Facebook"]')))
        logging.info("Logged in successfully.")
    except TimeoutException:
        logging.error("Login failed due to timeout.")
        driver.save_screenshot('login_timeout.png')
        driver.quit()
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        # driver.save_screenshot('login_error.png')
        driver.quit()

# Extract post data from the Facebook group page
def extract_data(driver, connection):
    try:
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//div[@role='article']")))

        # Click 'See more' to expand posts
        see_more_list = driver.find_elements(By.XPATH, "//*[contains(text(), 'See more') or contains(text(), 'ดูเพิ่มเติม')]")
        for s in see_more_list:
            driver.execute_script("arguments[0].click();", s)
            time.sleep(2)

        # Find all post elements and save their data
        article_list = driver.find_elements(By.XPATH, "//div[@role='article']")
        for a in article_list:
            post_html = bs(a.get_attribute('outerHTML'), 'html.parser')
            save_post_data(post_html, connection)

        # Return the new scroll height to check if scrolling needs to continue
        new_height = driver.execute_script("return document.body.scrollHeight")
        return new_height
    except Exception as e:
        logging.error(f"Error in extract_data: {str(e)}")
        return 'err'

# Function to scroll the page and extract posts
def scroll(connection, PAUSE_TIME):
    new_height = extract_data(driver, connection)
    driver.execute_script("window.scrollTo({ left: 0, top: document.body.clientHeight, behavior: 'smooth' })")
    new_height = driver.execute_script("return document.body.scrollHeight")
    time.sleep(PAUSE_TIME)
    return new_height

# Main function to start data extraction from a Facebook group
def get_data(email, password, group_url, PAUSE_TIME, MINUTES):
    logging.info("Navigating to the group URL...")
    driver.get(group_url)
    time.sleep(15)

    last_height = 1
    connection = connect_to_mysql()
    if not connection:
        return

    # Ensure the 'posts' table exists
    create_table(connection)

    start_time = time.time()

    # Scroll through the group page and extract posts
    while True:
        new_height = scroll(connection, PAUSE_TIME)
        if new_height == last_height or new_height == 'err' or (time.time() - start_time) > (MINUTES * 60):
            break
        last_height = new_height
        time.sleep(2)

    logging.info("Data extraction complete.")
    driver.quit()
    connection.close()

# Main function to read credentials and start the scraping process
def scrape_data():
    try:
        credentials = read_credentials()
        email = os.getenv('EMAIL')
        password = os.getenv('PASSWORD')
        group_url = credentials.get('group_url')
        pause_time = int(credentials.get('PAUSE_TIME', 10))  # แปลงเป็น integer
        scrape_time = int(credentials.get('MINUTES', 2))  # แปลงเป็น integer
        
        # ตรวจสอบว่า email, password และ group_url ถูกดึงมาอย่างถูกต้อง
        if not email or not password or not group_url:
            logging.error(f"Credentials are missing: email={email}, password={password}, group_url={group_url}")
            return

        # ล็อกอินเข้าสู่ระบบ
        login(email, password)

        # ดึงข้อมูลจาก Facebook group
        get_data(email, password, group_url, pause_time, scrape_time)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        driver.quit()


# Start the scraping process when the script is executed
if __name__ == "__main__":
    scrape_data()

# SELECT Post, COUNT(*) AS count
# FROM posts
# GROUP BY Post
# HAVING count > 1;

# DELETE p1
# FROM posts p1
# INNER JOIN posts p2 
# WHERE 
#     p1.id > p2.id AND 
#     p1.Post = p2.Post;

# wordcloud->noun only
# wordcloud->tokenize each label noun only dropdown
# scrape_data->twice,each 6 hr.->30 min

#docker -> airflow 
