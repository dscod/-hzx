import sqlite3
import os

DB_FILE = 'social_network.db'

def init_database():
    """Создает таблицы, если их нет"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица постов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(username, password_hash):
    """Добавляет пользователя в базу"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Пользователь уже есть
    finally:
        conn.close()

def get_user(username):
    """Получает пользователя по имени"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, password FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'password': user[2]
        }
    return None

def add_post(user_id, text):
    """Добавляет пост"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (user_id, text) VALUES (?, ?)",
        (user_id, text)
    )
    conn.commit()
    conn.close()

def get_all_posts():
    """Получает все посты с именами авторов"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT posts.text, users.username, posts.created_at
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    ''')
    posts_data = cursor.fetchall()
    conn.close()
    
    posts = []
    for post in posts_data:
        posts.append({
            'text': post[0],
            'author': post[1],
            'date': post[2]
        })
    return posts

# Создаем таблицы при первом запуске
if not os.path.exists(DB_FILE):
    init_database()
    # Добавляем начальные посты
    add_user("Администратор", "fake_hash")
    admin = get_user("Администратор")
    if admin:
        add_post(admin['id'], "Добро пожаловать в нашу социальную сеть!")
        add_post(admin['id'], "Теперь мы на базе данных SQLite!")  