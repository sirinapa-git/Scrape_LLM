import pymysql
import pandas as pd
import re
from bs4 import BeautifulSoup
from transformers import pipeline, CamembertTokenizer
import onnxruntime
import numpy as np
import os
import pymysql.cursors

# ฟังก์ชันสำหรับเชื่อมต่อกับ MySQL
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

# ฟังก์ชันสำหรับทำนายข้อมูลในวันนี้ โดยกรองโพสต์ที่ยังไม่มีใน sentiment_post
def sentiment_data_today():
    # เชื่อมต่อกับ MySQL
    connection = connect_to_mysql()
    if not connection:
        return

    cursor = connection.cursor(pymysql.cursors.DictCursor)

    # ตรวจสอบว่าตาราง 'sentiment_post' มีอยู่หรือไม่ ถ้าไม่มีก็สร้างขึ้น
    create_sentiment_table = """
    CREATE TABLE IF NOT EXISTS sentiment_post (
        id INT AUTO_INCREMENT PRIMARY KEY,
        Date VARCHAR(255),
        Post TEXT,
        Cleaned_Post TEXT,
        sentiment VARCHAR(50),
        tag VARCHAR(255),
        Reactions INT
    )
    """
    cursor.execute(create_sentiment_table)
    connection.commit()
    print("Ensured 'sentiment_post' table exists.")

    # ตรวจสอบโพสต์ที่มีใน sentiment_post แต่ reaction เปลี่ยนไป
    cursor.execute("""
        SELECT sp.Post, sp.Reactions AS Old_Reactions, p.Reactions AS New_Reactions
        FROM sentiment_post sp
        JOIN posts p ON sp.Post = p.Post
        WHERE DATE(sp.Date) = CURDATE() AND sp.Reactions != p.Reactions
    """)
    mismatched_reactions = cursor.fetchall()

    # อัพเดท reaction เฉพาะโพสต์ที่เหมือนกัน แต่มี reaction ต่างกัน
    update_query = """
        UPDATE sentiment_post
        SET Reactions = %s
        WHERE Date = CURDATE() AND Post = %s
    """
    for row in mismatched_reactions:
        try:
            cursor.execute(update_query, (row['New_Reactions'], row['Post']))
        except Error as err:
            print(f"Error updating reactions for Post '{row['Post']}': {err}")

    connection.commit()
    print(f"Updated {len(mismatched_reactions)} records with the latest reaction counts.")

    # ดึงข้อมูลของวันนี้จาก posts ที่ยังไม่มีใน sentiment_post ตามคอลัมน์ Post
    try:
        cursor.execute("""
            SELECT * FROM posts
            WHERE DATE(Date) = CURDATE()
            AND Post NOT IN (SELECT Post FROM sentiment_post WHERE DATE(Date) = CURDATE())
        """)
        data = cursor.fetchall()
        print(f"Retrieved {len(data)} unique records from MySQL for today based on Post.")
    except Error as err:
        print(f"Error retrieving data from MySQL: {err}")
        return

    # แปลงข้อมูลเป็น DataFrame
    df = pd.DataFrame(data)

    if df.empty:
        print("No new data found in 'posts' table for today.")
        return
    else:
        # โหลดโมเดลและ tokenizer
        drive_model_path = './model'
        pruned_model_path = os.path.join(drive_model_path, "sentiment0.71.onnx")
        classifier = pipeline("zero-shot-classification", model="joeddav/xlm-roberta-large-xnli")
        tokenizer = CamembertTokenizer.from_pretrained(drive_model_path)
        ort_session = onnxruntime.InferenceSession(pruned_model_path)

        # กำหนด label mapping และ candidate labels 
        id2label = {0: 'Positive', 1: 'Neutral', 2: 'Negative', 3: 'Question'}
        candidate_labels = ["รีวิว/สอบถาม", "การเรียน", "กิจกรรม", "ที่พัก", "การเงิน", "เรื่องทั่วไป", "สิ่งอำนวยความสะดวก", "อื่นๆ"]

        # ฟังก์ชันทำความสะอาดข้อความ
        def clean_text(text):
            if not text or text.isdigit():
                return None
            soup = BeautifulSoup(text, 'html.parser')
            clean_text = soup.get_text()
            clean_text = re.sub(r'http[s]?://\S+', '', clean_text)
            clean_text = re.sub(r'[^\w\sก-๙]', '', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            return clean_text.strip()

        # ฟังก์ชันทำนาย
        def predict(text):
            inputs = tokenizer(text, return_tensors='np', max_length=512, truncation=True, padding="max_length")
            input_ids = inputs['input_ids'].astype(np.int64)
            attention_mask = inputs['attention_mask'].astype(np.int64)
            ort_inputs = {'input_ids': input_ids, 'attention_mask': attention_mask}
            logits = ort_session.run(None, ort_inputs)[0]
            predicted_label_id = np.argmax(logits, axis=1)[0]

            predicted_sentiment = id2label.get(predicted_label_id)
            classification_result = classifier(text, candidate_labels)
            predicted_tag = classification_result['labels'][0]
            return predicted_sentiment, predicted_tag

        # ทำความสะอาดและกรองข้อมูล
        df['Cleaned_Post'] = df['Post'].apply(clean_text)
        df.dropna(subset=['Cleaned_Post'], inplace=True)
        df = df[df['Cleaned_Post'].str.strip() != '']

        # เตรียมคำสั่ง SQL สำหรับการเพิ่มข้อมูล
        insert_query = """
            INSERT INTO sentiment_post 
            (Date, Post, Cleaned_Post, sentiment, tag, Reactions)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        # ทำนายและเพิ่มข้อมูลใหม่ลงในฐานข้อมูล
        for index, row in df.iterrows():
            sentiment, tag = predict(row['Cleaned_Post'])
            try:
                cursor.execute(insert_query, (
                    row['Date'],
                    row['Post'],
                    row['Cleaned_Post'],
                    sentiment,
                    tag,
                    row['Reactions']
                ))
            except Error as err:
                print(f"Error inserting data for Post '{row['Post']}': {err}")

        connection.commit()
        print("New data has been inserted into the 'sentiment_post' table!")

    # ปิด cursor และ connection
    cursor.close()
    connection.close()

if __name__ == "__main__":
    sentiment_data_today()
