import pymysql
# from mysql.connector import Error

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
def create_tables_if_not_exists(connection):
    cursor = connection.cursor()
    try:
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

# ฟังก์ชันรันคำสั่ง SQL แบบทั่วไป
def execute_query(connection, query, params=None, fetch=False, commit=False):
    cursor = connection.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            connection.commit()
        if fetch:
            return cursor.fetchall()
    except Error as err:
        print(f"Error executing query: {err}")
    finally:
        cursor.close()

# ฟังก์ชันเรียงลำดับ เก็บข้อมูล 5 อันดับแรกใน sentiment_post และลบข้อมูลทั้งหมดใน posts
def sort_and_delete_data(connection):
    select_query = """
        SELECT id
        FROM sentiment_post 
        WHERE DATE(Date) = CURDATE()
        ORDER BY Reactions DESC
        LIMIT 5
    """
    top_5_ids = execute_query(connection, select_query, fetch=True)
    if not top_5_ids:
        print("No records found in sentiment_post for today's date.")
        return  # ออกจากฟังก์ชันถ้าไม่มีข้อมูล

    top_5_ids = [row[0] for row in top_5_ids]
    
    delete_query = f"""
        DELETE FROM sentiment_post 
        WHERE DATE(Date) = CURDATE()
        AND id NOT IN ({', '.join(['%s'] * len(top_5_ids))})
    """
    execute_query(connection, delete_query, top_5_ids, commit=True)
    
    delete_posts_query = "DELETE FROM posts"
    execute_query(connection, delete_posts_query, commit=True)
    print("Deleted rows except top 5 in sentiment_post and cleared posts table.")

# ฟังก์ชันบันทึกจำนวนของ tag และ sentiment ลงในตาราง daily_summary
def save_tag_and_sentiment_count(connection):
    dates_to_select = ['2024-09-22', '2024-09-24', '2024-09-25', '2024-09-26', '2024-09-27',
                       '2024-10-01', '2024-10-02', '2024-10-03', '2024-10-05', '2024-10-07',
                       '2024-10-09', '2024-10-10', '2024-10-11']
    count_query = f"""
        SELECT DATE(Date) AS post_date, tag, sentiment, COUNT(*) AS count
        FROM sentiment_post
        WHERE DATE(Date) IN ({', '.join(f"'{date}'" for date in dates_to_select)})
        GROUP BY post_date, tag, sentiment
    """
    results = execute_query(connection, count_query, fetch=True)
    if not results:
        print("No matching records found for selected dates in sentiment_post.")
        return  # ออกจากฟังก์ชันถ้าไม่มีข้อมูล

    insert_query = """
        INSERT INTO daily_summary (date, tag, sentiment, count)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE count = VALUES(count)
    """
    cursor = connection.cursor()
    try:
        for row in results:
            cursor.execute(insert_query, row)
        connection.commit()
        print("Saved tag and sentiment count to daily_summary for selected dates.")
    except Error as err:
        print(f"Error saving tag and sentiment count: {err}")
    finally:
        cursor.close()

# ฟังก์ชันบันทึกจำนวนของ tag ลงในตาราง tag_summary
def save_tag_count(connection):
    dates_to_select = ['2024-09-22', '2024-09-24', '2024-09-25', '2024-09-26', '2024-09-27',
                       '2024-10-01', '2024-10-02', '2024-10-03', '2024-10-05', '2024-10-07',
                       '2024-10-09', '2024-10-10', '2024-10-11']
    count_query = f"""
        SELECT DATE(Date) AS post_date, tag, COUNT(*) AS count
        FROM sentiment_post
        WHERE DATE(Date) IN ({', '.join(f"'{date}'" for date in dates_to_select)})
        GROUP BY post_date, tag
    """
    results = execute_query(connection, count_query, fetch=True)
    if not results:
        print("No matching records found for selected dates in sentiment_post.")
        return  # ออกจากฟังก์ชันถ้าไม่มีข้อมูล

    insert_query = """
        INSERT INTO tag_summary (date, tag, count)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE count = VALUES(count)
    """
    cursor = connection.cursor()
    try:
        for row in results:
            cursor.execute(insert_query, row)
        connection.commit()
        print("Saved tag count to tag_summary for selected dates.")
    except Error as err:
        print(f"Error saving tag count: {err}")
    finally:
        cursor.close()

# เรียกใช้ฟังก์ชันโดยเชื่อมต่อกับ MySQL ครั้งเดียว
connection = connect_to_mysql()
if connection:
    create_tables_if_not_exists(connection)
    sort_and_delete_data(connection)
    save_tag_and_sentiment_count(connection)
    save_tag_count(connection)
    connection.close()
