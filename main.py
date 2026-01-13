from fastapi import FastAPI, Request, HTTPException
import mysql.connector
app = FastAPI()

# DB 연결 설정
def get_db():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="1234",
        database="test_db"
    )

# ---------------------------
# CREATE
# ---------------------------
@app.post("/todos")
async def create_todo(request: Request):
    body = await request.json()
    content = body.get("content")

    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    conn = get_db()
    cursor = conn.cursor()

    # INSERT 문 작성
    sql_insert = "INSERT INTO todo (content) VALUES (%s)"
    cursor.execute(
        sql_insert,
        (content,)
    )

    conn.commit()

    todo_id = cursor.lastrowid

    # SELECT 문 작성하여 방금 만든 todo 조회
    sql_select = "SELECT id, content, created_at FROM todo WHERE id = %s"
    cursor.execute(
        sql_select
        ,
        (todo_id,)
    )
    row = cursor.fetchone()

    cursor.close()
    conn.close()

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
    conn = get_db()
    cursor = conn.cursor()

    # [정답 3] 전체 todo 조회 SELECT 문 작성
    sql_select_all = "SELECT id, content, created_at FROM todo"
    cursor.execute(
        sql_select_all
    )
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

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
    conn = get_db()
    cursor = conn.cursor()

    # 삭제 DELETE 문 작성
    sql_delete = "DELETE FROM todo WHERE id = %s"
    cursor.execute(
        sql_delete,
        (todo_id,)
    )
    conn.commit()

    affected = cursor.rowcount

    cursor.close()
    conn.close()

    if affected == 0:
        raise HTTPException(status_code=404, detail="Todo not found")

    return {"message": "Todo deleted"}