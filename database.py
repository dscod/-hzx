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
    
    # Таблица постов (добавили поле image_url)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(username, password_hash):
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
        return False
    finally:
        conn.close()

def get_user(username):
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

def add_post(user_id, text, image_url=None):
    """Добавляет пост с опциональной картинкой"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (user_id, text, image_url) VALUES (?, ?, ?)",
        (user_id, text, image_url)
    )
    conn.commit()
    conn.close()

def get_all_posts():
    """Получает все посты с именами авторов"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT posts.id, posts.text, users.username, posts.created_at, posts.image_url
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    ''')
    posts_data = cursor.fetchall()
    conn.close()
    
    posts = []
    for post in posts_data:
        posts.append({
            'id': post[0],
            'text': post[1],
            'author': post[2],
            'date': post[3],
            'image_url': post[4]
        })
    return posts

def delete_post(post_id, user_id):
    """Удаляет пост только если он принадлежит пользователю"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM posts WHERE id = ? AND user_id = ?",
        (post_id, user_id)
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_post_author(post_id):
    """Получает ID автора поста"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM posts WHERE id = ?",
        (post_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Создаем таблицы при первом запуске
if not os.path.exists(DB_FILE):
    init_database()
    # Добавляем начальные посты
    admin_hash = "fake_hash_for_admin"
    add_user("Администратор", admin_hash)
    admin = get_user("Администратор")
    if admin:
        add_post(admin['id'], "Добро пожаловать в нашу социальную сеть!")
        add_post(admin['id'], "Теперь можно добавлять картинки и удалять посты!")