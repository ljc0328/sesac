import os
import logging
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI, Request, HTTPException
import mysql.connector

#.env 파일을 읽기 위한 라이브러리
from dotenv import load_dotenv

#.env 파일 로드 (이제 os.getenv로 값을 꺼낼 수 있음)
load_dotenv()

# ==========================================
# [로그 설정]
# ==========================================
if not os.path.exists("logs"):
    os.makedirs("logs")

logger = logging.getLogger("todo_app")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

file_handler = TimedRotatingFileHandler(
    filename="logs/todo_app.log",
    when="M",
    interval=1,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ==========================================

app = FastAPI()

#.env에서 환경변수 가져오기
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),      # .env의 DB_HOST 값 사용
        port=int(os.getenv("DB_PORT", 3306)),        # .env의 DB_PORT 값 사용 (숫자로 변환)
        user=os.getenv("DB_USER", "root"),           # .env의 DB_USER 값 사용
        password=os.getenv("DB_PASSWORD", "1234"),   # .env의 DB_PASSWORD 값 사용
        database=os.getenv("DB_NAME", "test_db")     # .env의 DB_NAME 값 사용
    )

# ---------------------------
# CREATE
# ---------------------------
@app.post("/todos")
async def create_todo(request: Request):
    logger.info("CREATE API 요청됨")

    body = await request.json()
    content = body.get("content")

    if not content:
        logger.error("CREATE API 실패 - content 누락")
        raise HTTPException(status_code=400, detail="content is required")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO todo (content) VALUES (%s)", (content,))
    conn.commit()

    todo_id = cursor.lastrowid

    cursor.execute("SELECT id, content, created_at FROM todo WHERE id = %s", (todo_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    logger.info(f"CREATE API 성공 - ID: {row[0]}, Content: {row[1]}")

    return {
        "id": row[0],
        "content": row[1],
        "created_at": str(row[2])
    }

# ---------------------------
# READ
# ---------------------------
@app.get("/todos")
def get_todos():
    logger.info("READ API 요청됨")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, content, created_at FROM todo ORDER BY id DESC")
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    logger.info(f"READ API 성공 - 조회된 개수: {len(rows)}")
    return [
        {
            "id": r[0],
            "content": r[1],
            "created_at": str(r[2])
        }
        for r in rows
    ]

# ---------------------------
# DELETE
# ---------------------------
@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    logger.info(f"DELETE API 요청됨 - ID: {todo_id}")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM todo WHERE id = %s", (todo_id,))
    conn.commit()

    affected = cursor.rowcount

    cursor.close()
    conn.close()

    if affected == 0:
        logger.warning(f"DELETE API 실패 - 존재하지 않는 ID: {todo_id}")
        raise HTTPException(status_code=404, detail="Todo not found")

    logger.info(f"DELETE API 성공 - ID: {todo_id} 삭제 완료")
    return {"message": "Todo deleted"}