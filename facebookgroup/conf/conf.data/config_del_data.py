import mysql.connector
from mysql.connector import Error

# ฟังก์ชันเชื่อมต่อกับ MySQL
def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host='localhost',    
            user='root',             
            password='',            
            database='mydb'          
        )
        if connection.is_connected():
            print("Connected to MySQL successfully")
            return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
    return None

# ฟังก์ชันรันคำสั่ง SQL แบบทั่วไป
def execute_query(connection, query, params=None, fetch=False, commit=False):
    cursor = connection.cursor(dictionary=True)
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

# ฟังก์ชันเรียงลำดับและลบข้อมูลในตาราง sentiment_post และ posts สำหรับวันที่ระบุ
def sort_and_delete_data_for_dates(connection, dates):
    for date in dates:
        print(f"Processing data for date: {date}")
        
        select_query = """
            SELECT id
            FROM sentiment_post 
            WHERE DATE(Date) = %s
            ORDER BY Reactions DESC
            LIMIT 5
        """
        
        top_5_ids = execute_query(connection, select_query, params=(date,), fetch=True)
        
        if not top_5_ids:
            print(f"No records found in sentiment_post for date: {date}.")
            continue

        top_5_ids = [row['id'] for row in top_5_ids]
        
        if top_5_ids:
            delete_query = f"""
                DELETE FROM sentiment_post 
                WHERE DATE(Date) = %s
                AND id NOT IN ({', '.join(['%s'] * len(top_5_ids))})
            """
            execute_query(connection, delete_query, params=(date, *top_5_ids), commit=False)
            print(f"Deleted rows except top 5 in sentiment_post for date: {date}.")

        # ลบข้อมูลทั้งหมดในตาราง posts สำหรับวันที่ระบุ
        delete_posts_query = """
            DELETE FROM posts 
            WHERE DATE(Date) = %s
        """
        execute_query(connection, delete_posts_query, params=(date,), commit=False)
        print(f"Deleted all rows in posts for date: {date}.")

    connection.commit()  # ยืนยัน Transaction หลังจากทุกวันที่

# ฟังก์ชันหลักในการเชื่อมต่อและรันคำสั่งสำหรับวันที่หลายวัน
def data_config_sort_del():
    connection = connect_to_mysql()
    if connection:
        try:
            # กำหนดวันที่ที่ต้องการใช้
            dates = [
                '2024-09-24', '2024-09-25', '2024-09-26', '2024-09-27',
                '2024-10-01', '2024-10-02', '2024-10-03', '2024-10-05',
                '2024-10-07', '2024-10-08', '2024-10-09', '2024-10-10',
                '2024-10-11'
            ]
            sort_and_delete_data_for_dates(connection, dates)
        finally:
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    data_config_sort_del()
