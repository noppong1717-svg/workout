import mysql.connector
from mysql.connector import Error

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='192.168.100.23',  # IP ของเครื่อง MariaDB 
            database='home_workout_db', # ชื่อฐานข้อมูลที่เราเพิ่งสร้าง
            user='root', # เปลี่ยนเป็น username ของ MariaDB (ปกติมักจะเป็น root)
            password='P@ssw0rd' # ใส่รหัสผ่าน MariaDB ลงไปตรงนี้
        )
        return connection
    except Error as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {e}")
        return None