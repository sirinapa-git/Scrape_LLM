import pymysql
# from mysql.connector import Error
import os

# ฟังก์ชันเชื่อมต่อกับ MySQL
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
    
# ฟังก์ชันสร้างตาราง daily_summary และ tag_summary ถ้ายังไม่มี
def create_tables_if_not_exists():
    connection = connect_to_mysql()
    if connection:
        cursor = connection.cursor()
        try:
            # สร้างตาราง daily_summary สำหรับเก็บข้อมูล tag + sentiment
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summary (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    tag VARCHAR(255) NOT NULL,
                    sentiment VARCHAR(255) NOT NULL,
                    count INT NOT NULL,
                    UNIQUE KEY unique_date_tag_sentiment (date, tag, sentiment)
                );
            """)

            # สร้างตาราง tag_summary สำหรับเก็บข้อมูล tag อย่างเดียว
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tag_summary (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    tag VARCHAR(255) NOT NULL,
                    count INT NOT NULL,
                    UNIQUE KEY unique_date_tag (date, tag)
                );
            """)

            connection.commit()
            print("Checked for daily_summary and tag_summary tables and created if not exists.")

        except Error as err:
            print(f"Error creating tables: {err}")
        finally:
            cursor.close()
            connection.close()

# ฟังก์ชันบันทึกจำนวนของ tag และ sentiment ลงในตาราง daily_summary
def save_tag_and_sentiment_count():
    connection = connect_to_mysql()
    if connection:
        cursor = connection.cursor()
        try:
            # Query นับจำนวน tag และ sentiment
            count_query = """
                SELECT DATE(Date) AS post_date, tag, sentiment, COUNT(*) AS count
                FROM sentiment_post
                WHERE DATE(Date) = CURDATE()
                GROUP BY post_date, tag, sentiment
            """
            cursor.execute(count_query)
            results = cursor.fetchall()

            # แทรกข้อมูลลงใน daily_summary
            insert_query = """
                INSERT INTO daily_summary (date, tag, sentiment, count)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE count = VALUES(count)
            """
            for row in results:
                post_date, tag, sentiment, count = row
                cursor.execute(insert_query, (post_date, tag, sentiment, count))
            
            connection.commit()
            print("Saved tag and sentiment count to daily_summary.")

        except Error as err:
            print(f"Error saving tag and sentiment count: {err}")
        finally:
            cursor.close()
            connection.close()

# ฟังก์ชันบันทึกจำนวนของ tag ลงในตาราง tag_summary
def save_tag_count():
    connection = connect_to_mysql()
    if connection:
        cursor = connection.cursor()
        try:
            # Query นับจำนวน tag โดยไม่สนใจ sentiment
            count_query = """
                SELECT DATE(Date) AS post_date, tag, COUNT(*) AS count
                FROM sentiment_post
                WHERE DATE(Date) = CURDATE()
                GROUP BY post_date, tag
            """
            cursor.execute(count_query)
            results = cursor.fetchall()

            # แทรกข้อมูลลงใน tag_summary
            insert_query = """
                INSERT INTO tag_summary (date, tag, count)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE count = VALUES(count)
            """
            for row in results:
                post_date, tag, count = row
                cursor.execute(insert_query, (post_date, tag, count))
            
            connection.commit()
            print("Saved tag count to tag_summary.")

        except Error as err:
            print(f"Error saving tag count: {err}")
        finally:
            cursor.close()
            connection.close()

# Define the sum_daily function that calls all necessary functions
def sum_daily():
    create_tables_if_not_exists()
    save_tag_and_sentiment_count()
    save_tag_count()

# Start the process when the script is executed
if __name__ == "__main__":
    sum_daily()
