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