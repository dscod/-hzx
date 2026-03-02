import os
import httpx
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные из .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"URL: {SUPABASE_URL}")
print(f"KEY: {SUPABASE_KEY[:20]}..." if SUPABASE_KEY else "KEY: None")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ОШИБКА: Не найдены SUPABASE_URL или SUPABASE_KEY в .env файле!")
    exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def init_database():
    print("✅ База данных Supabase подключена")
    return True

def add_user(username, password_hash):
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                json={"username": username, "password": password_hash}
            )
            return response.status_code == 201
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")
        return False

def get_user(username):
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"username": f"eq.{username}"}
            )
            if response.status_code == 200 and response.json():
                user = response.json()[0]
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'password': user['password']
                }
        return None
    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return None

def add_post(user_id, text, image_url=None):
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                json={"user_id": user_id, "text": text, "image_url": image_url}
            )
            return response.status_code == 201
    except Exception as e:
        print(f"❌ Ошибка добавления поста: {e}")
        return False

def get_all_posts():
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={
                    "select": "id,text,image_url,created_at,user_id",
                    "order": "created_at.desc"
                }
            )
            
            if response.status_code != 200:
                return []
            
            posts_data = response.json()
            posts = []
            
            for post in posts_data:
                user_response = client.get(
                    f"{SUPABASE_URL}/rest/v1/users",
                    headers=HEADERS,
                    params={"id": f"eq.{post['user_id']}"}
                )
                
                username = "Неизвестный"
                if user_response.status_code == 200 and user_response.json():
                    username = user_response.json()[0]['username']
                
                posts.append({
                    'id': post['id'],
                    'text': post['text'],
                    'author': username,
                    'date': post['created_at'],
                    'image_url': post.get('image_url')
                })
            return posts
    except Exception as e:
        print(f"❌ Ошибка получения постов: {e}")
        return []

def delete_post(post_id, user_id):
    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={"id": f"eq.{post_id}", "user_id": f"eq.{user_id}"}
            )
            return response.status_code == 204
    except Exception as e:
        print(f"❌ Ошибка удаления поста: {e}")
        return False

def get_post_author(post_id):
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={"id": f"eq.{post_id}", "select": "user_id"}
            )
            if response.status_code == 200 and response.json():
                return response.json()[0]['user_id']
        return None
    except Exception as e:
        print(f"❌ Ошибка получения автора поста: {e}")
        return None
    
def add_like(user_id, post_id):
    """Добавляет лайк к посту"""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/likes",
                headers=HEADERS,
                json={"user_id": str(user_id), "post_id": post_id}
            )
            return response.status_code == 201
    except Exception as e:
        print(f"❌ Ошибка добавления лайка: {e}")
        return False

def remove_like(user_id, post_id):
    """Удаляет лайк с поста"""
    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{SUPABASE_URL}/rest/v1/likes",
                headers=HEADERS,
                params={"user_id": f"eq.{user_id}", "post_id": f"eq.{post_id}"}
            )
            return response.status_code == 204
    except Exception as e:
        print(f"❌ Ошибка удаления лайка: {e}")
        return False

def get_likes_count(post_id):
    """Получает количество лайков поста"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/likes",
                headers=HEADERS,
                params={"post_id": f"eq.{post_id}", "select": "count"}
            )
            if response.status_code == 200:
                return len(response.json())
        return 0
    except Exception as e:
        print(f"❌ Ошибка получения лайков: {e}")
        return 0

def check_user_like(user_id, post_id):
    """Проверяет, лайкнул ли пользователь пост"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/likes",
                headers=HEADERS,
                params={"user_id": f"eq.{user_id}", "post_id": f"eq.{post_id}"}
            )
            return len(response.json()) > 0
    except Exception as e:
        print(f"❌ Ошибка проверки лайка: {e}")
        return False

def get_user_posts(username):
    """Получает посты конкретного пользователя"""
    try:
        # Сначала получаем пользователя
        user = get_user(username)
        if not user:
            return []
        
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={
                    "user_id": f"eq.{user['id']}",
                    "order": "created_at.desc"
                }
            )
            
            if response.status_code != 200:
                return []
            
            posts_data = response.json()
            posts = []
            
            for post in posts_data:
                # Получаем количество лайков
                likes_count = get_likes_count(post['id'])
                
                posts.append({
                    'id': post['id'],
                    'text': post['text'],
                    'author': username,
                    'date': post['created_at'],
                    'image_url': post.get('image_url'),
                    'likes': likes_count
                })
            return posts
    except Exception as e:
        print(f"❌ Ошибка получения постов пользователя: {e}")
        return []

def get_all_posts_with_likes(username=None):
    """Получает все посты с лайками и отметкой, лайкнул ли текущий пользователь"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={
                    "select": "id,text,image_url,created_at,user_id",
                    "order": "created_at.desc"
                }
            )
            
            if response.status_code != 200:
                return []
            
            posts_data = response.json()
            posts = []
            
            for post in posts_data:
                # Получаем пользователя
                user_response = client.get(
                    f"{SUPABASE_URL}/rest/v1/users",
                    headers=HEADERS,
                    params={"id": f"eq.{post['user_id']}"}
                )
                
                username_author = "Неизвестный"
                if user_response.status_code == 200 and user_response.json():
                    username_author = user_response.json()[0]['username']
                
                # Получаем количество лайков
                likes_count = get_likes_count(post['id'])
                
                # Проверяем, лайкнул ли текущий пользователь
                user_liked = False
                if username:
                    user = get_user(username)
                    if user:
                        user_liked = check_user_like(user['id'], post['id'])
                
                posts.append({
                    'id': post['id'],
                    'text': post['text'],
                    'author': username_author,
                    'date': post['created_at'],
                    'image_url': post.get('image_url'),
                    'likes': likes_count,
                    'user_liked': user_liked
                })
            return posts
    except Exception as e:
        print(f"❌ Ошибка получения постов: {e}")
        return []