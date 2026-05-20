import sqlite3
from datetime import datetime, timedelta


# Cоздаем таблицу для TO-DO листа
def init_db():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS todos
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       text text, 
                       done boolean)
                   ''')
    conn.commit()
    conn.close()

def add_todo(text, done=False):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO todos (text, done) VALUES (?, ?)", (text, done))
    todo_id = cursor.lastrowid  # ← id новой задачи
    conn.commit()
    conn.close()
    return todo_id  # ← возвращаем

def load_todos():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM todos")
    todos = cursor.fetchall()
    conn.close()
    return todos


def toggle_todo(todo_id, done):
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE todos SET done = ? WHERE id = ?", (done, todo_id))
    conn.commit()
    conn.close()


def init_streak():
    conn = sqlite3.connect('data/streak.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS streak
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        last_used TEXT,
                        streak_count integer
                      )
                   ''')
    conn.commit()
    conn.close()

def update_streak():
    conn = sqlite3.connect('data/streak.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT last_used, streak_count
                      FROM streak
                      WHERE id = 1''')
    streak = cursor.fetchone()
    if streak is None:
        streak = 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO streak (id, last_used, streak_count) VALUES (?, ?, ?)", (1, now_str, 1))
    else:
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        last_used_str = streak[0]
        last_used = datetime.strptime(last_used_str, "%Y-%m-%d %H:%M:%S")
        diff = now - last_used
        if diff >= timedelta(hours=24):
            cursor.execute("UPDATE streak SET streak_count = streak_count + 1, last_used = ?", (now_str,))
        result = streak[1]
    conn.commit()
    conn.close()
    return result



