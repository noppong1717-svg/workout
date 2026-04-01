from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date
from database import get_db_connection

app = FastAPI()

# ---------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class MetricCreate(BaseModel):
    user_id: int
    weight_kg: float
    waist_cm: Optional[float] = None
    recorded_date: date

class MetricUpdate(BaseModel):
    weight_kg: float
    waist_cm: Optional[float] = None

class ExerciseCreate(BaseModel):
    title: str
    video_filename: Optional[str] = None
    rest_time_seconds: Optional[int] = 60

class ExerciseUpdate(BaseModel):
    title: str
    video_filename: Optional[str] = None
    rest_time_seconds: Optional[int] = 60

# ---------------------------------------------------------
# Root
# ---------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Hello Home Workout App! FastAPI is running."}

# ---------------------------------------------------------
# Users CRUD
# ---------------------------------------------------------

@app.post("/users/")
def create_user(user: UserCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM users WHERE username = %s", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username นี้มีคนใช้แล้ว")
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (user.username, user.password)
        )
        conn.commit()
        return {"message": "สร้างบัญชีผู้ใช้สำเร็จ!", "username": user.username}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/login/")
def login(user: UserLogin):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT user_id, username FROM users WHERE username = %s AND password_hash = %s",
            (user.username, user.password)
        )
        found = cursor.fetchone()
        if not found:
            raise HTTPException(status_code=401, detail="Username หรือ Password ไม่ถูกต้อง")
        return {"message": "เข้าสู่ระบบสำเร็จ!", "user_id": found["user_id"], "username": found["username"]}
    finally:
        cursor.close()
        conn.close()

@app.get("/users/")
def get_all_users():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, username FROM users")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, username FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งาน")
        return user
    finally:
        cursor.close()
        conn.close()

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET username = %s, password_hash = %s WHERE user_id = %s",
            (user.username, user.password, user_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งาน")
        return {"message": "แก้ไขข้อมูลผู้ใช้สำเร็จ!"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งาน")
        return {"message": "ลบผู้ใช้สำเร็จ!"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# Exercises CRUD (ตารางที่ 2 — มี Relationship กับ users ผ่าน body_metrics)
# ---------------------------------------------------------

@app.get("/exercises/")
def get_exercises():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM exercises ORDER BY exercise_id ASC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@app.get("/exercises/{exercise_id}")
def get_exercise(exercise_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM exercises WHERE exercise_id = %s", (exercise_id,))
        ex = cursor.fetchone()
        if not ex:
            raise HTTPException(status_code=404, detail="ไม่พบท่าออกกำลังกาย")
        return ex
    finally:
        cursor.close()
        conn.close()

@app.post("/exercises/")
def create_exercise(ex: ExerciseCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO exercises (title, video_filename, rest_time_seconds) VALUES (%s, %s, %s)",
            (ex.title, ex.video_filename, ex.rest_time_seconds)
        )
        conn.commit()
        return {"message": "เพิ่มท่าออกกำลังกายสำเร็จ!", "exercise_id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/exercises/{exercise_id}")
def update_exercise(exercise_id: int, ex: ExerciseUpdate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE exercises SET title = %s, video_filename = %s, rest_time_seconds = %s WHERE exercise_id = %s",
            (ex.title, ex.video_filename, ex.rest_time_seconds, exercise_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบท่าออกกำลังกาย")
        return {"message": "แก้ไขท่าออกกำลังกายสำเร็จ!"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.delete("/exercises/{exercise_id}")
def delete_exercise(exercise_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM exercises WHERE exercise_id = %s", (exercise_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบท่าออกกำลังกาย")
        return {"message": "ลบท่าออกกำลังกายสำเร็จ!"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ---------------------------------------------------------
# Body Metrics CRUD
# ---------------------------------------------------------

@app.get("/metrics/{user_id}")
def get_metrics(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM body_metrics WHERE user_id = %s ORDER BY recorded_date DESC",
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

@app.post("/metrics/")
def create_metric(metric: MetricCreate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO body_metrics (user_id, weight_kg, waist_cm, recorded_date) VALUES (%s, %s, %s, %s)",
            (metric.user_id, metric.weight_kg, metric.waist_cm, metric.recorded_date)
        )
        conn.commit()
        return {"message": "บันทึกสัดส่วนสำเร็จ!"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.put("/metrics/{metric_id}")
def update_metric(metric_id: int, metric: MetricUpdate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE body_metrics SET weight_kg = %s, waist_cm = %s WHERE metric_id = %s",
            (metric.weight_kg, metric.waist_cm, metric_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูล")
        return {"message": "แก้ไขข้อมูลสำเร็จ!"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.delete("/metrics/{metric_id}")
def delete_metric(metric_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM body_metrics WHERE metric_id = %s", (metric_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="ไม่พบข้อมูล")
        return {"message": "ลบข้อมูลสำเร็จ!"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()