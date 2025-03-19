import mysql.connector
from mysql.connector import Error

# Function to connect to MySQL database
def connect_to_mysql(host='localhost', user='root', password='', database='mydb'):
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        if connection.is_connected():
            print("Connected to MySQL successfully!")
            return connection
    except Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None
if __name__ == "__main__":
    connect_to_mysql()
