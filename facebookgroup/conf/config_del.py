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

# ฟังก์ชันเรียงลำดับและลบข้อมูลในตาราง sentiment_post และ posts สำหรับวันก่อนหน้า
def sort_top5_and_delete_yesterday_data(connection):
    # เลือกข้อมูล 5 อันดับแรกตาม Reactions จากตาราง sentiment_post ของวันก่อนหน้า
    select_query = """
        SELECT id
        FROM sentiment_post 
        WHERE DATE(Date) = CURDATE()
        ORDER BY Reactions DESC
        LIMIT 5
    """
    connection.start_transaction()  # เริ่ม Transaction
    top_5_ids = execute_query(connection, select_query, fetch=True)
    
    if not top_5_ids:
        print("No records found in sentiment_post for yesterday's date.")
        return

    top_5_ids = [row['id'] for row in top_5_ids]
    
    if top_5_ids:
        # ลบข้อมูลใน sentiment_post ยกเว้น 5 อันดับแรก
        delete_query = f"""
            DELETE FROM sentiment_post 
            WHERE DATE(Date) = CURDATE()
            AND id NOT IN ({', '.join(['%s'] * len(top_5_ids))})
        """
        execute_query(connection, delete_query, top_5_ids, commit=False)
        print("Deleted all rows except top 5 in sentiment_post .")

    # ลบข้อมูลทั้งหมดในตาราง posts สำหรับวันก่อนหน้า
    delete_posts_query = """
        DELETE FROM posts 
        WHERE DATE(Date) = CURDATE() - INTERVAL 1 DAY
    """
    execute_query(connection, delete_posts_query, commit=False)
    print("Deleted all rows in posts for yesterday's date.")

    connection.commit()  # ยืนยัน Transaction

# ฟังก์ชันหลักในการเชื่อมต่อและรันคำสั่ง
def data_config_sort_top5_del():
    connection = connect_to_mysql()
    if connection:
        try:
            sort_top5_and_delete_yesterday_data(connection)
        finally:
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    data_config_sort_top5_del()
