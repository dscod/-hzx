import os
import httpx
from dotenv import load_dotenv
from datetime import datetime, timedelta

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

# ========== СУПЕР-АДМИН (ЗАЩИТА) ==========
SUPER_ADMIN = "твой_логин"  # 🔥 ЗАМЕНИ НА СВОЙ ЛОГИН!

def format_date(date_str):
    """Форматирует дату в нужный формат"""
    try:
        # Парсим дату из строки
        if isinstance(date_str, str):
            # Пробуем разные форматы
            try:
                post_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                try:
                    post_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
                except:
                    post_date = datetime.strptime(date_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
        else:
            post_date = date_str
        
        # Текущая дата
        now = datetime.now(post_date.tzinfo) if post_date.tzinfo else datetime.now()
        today = now.date()
        post_date_only = post_date.date()
        
        # Разница в днях
        delta = today - post_date_only
        
        # Форматируем время
        time_str = post_date.strftime("%H:%M")
        
        # Определяем формат даты
        if delta.days == 0:
            return f"сегодня в {time_str}"
        elif delta.days == 1:
            return f"вчера в {time_str}"
        else:
            return post_date.strftime("%d.%m.%Y в %H:%M")
            
    except Exception as e:
        print(f"Ошибка форматирования даты: {e}")
        return date_str

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

def add_user(username, password_hash):
    try:
        print(f"🔍 add_user: {username}")
        with httpx.Client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                json={"username": username, "password": password_hash}
            )
            print(f"🔍 Response status: {response.status_code}")
            print(f"🔍 Response body: {response.text}")
            return response.status_code == 201
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")
        import traceback
        traceback.print_exc()
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
    """Получает все посты с информацией об авторе, лайках, комментариях и аватаре"""
    try:
        with httpx.Client() as client:
            # Получаем посты
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={
                    "select": "id,text,image_url,created_at,user_id",
                    "order": "created_at.desc"
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Ошибка получения постов: статус {response.status_code}")
                return []
            
            posts_data = response.json()
            posts = []
            
            for post in posts_data:
                # Получаем данные автора (включая аватар)
                user_response = client.get(
                    f"{SUPABASE_URL}/rest/v1/users",
                    headers=HEADERS,
                    params={"id": f"eq.{post['user_id']}", "select": "username,avatar_url"}
                )
                
                username = "Неизвестный"
                avatar_url = None
                if user_response.status_code == 200 and user_response.json():
                    user_data = user_response.json()[0]
                    username = user_data['username']
                    avatar_url = user_data.get('avatar_url')
                
                # Получаем количество лайков
                likes_response = client.get(
                    f"{SUPABASE_URL}/rest/v1/likes",
                    headers=HEADERS,
                    params={"post_id": f"eq.{post['id']}", "select": "id"}
                )
                likes_count = len(likes_response.json()) if likes_response.status_code == 200 else 0
                
                # Получаем комментарии
                comments_response = client.get(
                    f"{SUPABASE_URL}/rest/v1/comments",
                    headers=HEADERS,
                    params={
                        "post_id": f"eq.{post['id']}",
                        "select": "id,content,created_at,user_id",
                        "order": "created_at.desc",
                        "limit": 3
                    }
                )
                
                comments_preview = []
                if comments_response.status_code == 200:
                    for comment in comments_response.json():
                        # Получаем автора комментария
                        comment_user = client.get(
                            f"{SUPABASE_URL}/rest/v1/users",
                            headers=HEADERS,
                            params={"id": f"eq.{comment['user_id']}", "select": "username,avatar_url"}
                        )
                        comment_username = "Неизвестный"
                        comment_avatar = None
                        if comment_user.status_code == 200 and comment_user.json():
                            comment_user_data = comment_user.json()[0]
                            comment_username = comment_user_data['username']
                            comment_avatar = comment_user_data.get('avatar_url')
                        
                        # Форматируем дату комментария
                        comment_date = format_date(comment['created_at'])
                        
                        comments_preview.append({
                            'id': comment['id'],
                            'content': comment['content'],
                            'author': comment_username,
                            'author_avatar': comment_avatar,
                            'date': comment_date
                        })
                
                # Форматируем дату поста
                post_date = format_date(post['created_at'])
                
                posts.append({
                    'id': post['id'],
                    'text': post['text'],
                    'author': username,
                    'author_avatar': avatar_url,
                    'author_id': post['user_id'],
                    'date': post_date,
                    'image_url': post.get('image_url'),
                    'likes': likes_count,
                    'comments_preview': comments_preview
                })
            return posts
    except Exception as e:
        print(f"❌ Ошибка получения постов: {e}")
        import traceback
        traceback.print_exc()
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

# ========== ЛАЙКИ ==========

def like_post(user_id, post_id):
    """Добавляет лайк к посту"""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/likes",
                headers=HEADERS,
                json={"user_id": user_id, "post_id": post_id}
            )
            return response.status_code == 201
    except Exception as e:
        print(f"❌ Ошибка добавления лайка: {e}")
        return False

def unlike_post(user_id, post_id):
    """Убирает лайк с поста"""
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
    """Получает количество лайков у поста"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/likes",
                headers=HEADERS,
                params={"post_id": f"eq.{post_id}", "select": "id"}
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

# ========== КОММЕНТАРИИ ==========

def add_comment(user_id, post_id, content):
    """Добавляет комментарий к посту"""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/comments",
                headers=HEADERS,
                json={"user_id": user_id, "post_id": post_id, "content": content}
            )
            return response.status_code == 201
    except Exception as e:
        print(f"❌ Ошибка добавления комментария: {e}")
        return False

def get_comments(post_id):
    """Получает все комментарии к посту"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/comments",
                headers=HEADERS,
                params={
                    "post_id": f"eq.{post_id}",
                    "select": "id,content,created_at,user_id",
                    "order": "created_at.desc"
                }
            )
            
            if response.status_code != 200:
                return []
            
            comments_data = response.json()
            comments = []
            
            for comment in comments_data:
                # Получаем имя автора комментария
                user_response = client.get(
                    f"{SUPABASE_URL}/rest/v1/users",
                    headers=HEADERS,
                    params={"id": f"eq.{comment['user_id']}", "select": "username,avatar_url"}
                )
                
                username = "Неизвестный"
                avatar_url = None
                if user_response.status_code == 200 and user_response.json():
                    user_data = user_response.json()[0]
                    username = user_data['username']
                    avatar_url = user_data.get('avatar_url')
                
                # Форматируем дату комментария
                comment_date = format_date(comment['created_at'])
                
                comments.append({
                    'id': comment['id'],
                    'content': comment['content'],
                    'author': username,
                    'author_avatar': avatar_url,
                    'date': comment_date,
                    'user_id': comment['user_id']
                })
            return comments
    except Exception as e:
        print(f"❌ Ошибка получения комментариев: {e}")
        return []

def delete_comment(comment_id, user_id):
    """Удаляет комментарий"""
    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{SUPABASE_URL}/rest/v1/comments",
                headers=HEADERS,
                params={"id": f"eq.{comment_id}", "user_id": f"eq.{user_id}"}
            )
            return response.status_code == 204
    except Exception as e:
        print(f"❌ Ошибка удаления комментария: {e}")
        return False

# ========== АВАТАРКИ ==========

def update_avatar(user_id, avatar_url):
    """Обновляет аватар пользователя"""
    try:
        with httpx.Client() as client:
            response = client.patch(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"id": f"eq.{user_id}"},
                json={"avatar_url": avatar_url}
            )
            return response.status_code == 204
    except Exception as e:
        print(f"❌ Ошибка обновления аватара: {e}")
        return False

def get_user_with_avatar(user_id):
    """Получает данные пользователя включая аватар"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"id": f"eq.{user_id}", "select": "id,username,avatar_url"}
            )
            if response.status_code == 200 and response.json():
                return response.json()[0]
        return None
    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return None

def get_user_avatar(username):
    """Получает URL аватара по имени пользователя"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"username": f"eq.{username}", "select": "avatar_url"}
            )
            if response.status_code == 200 and response.json():
                return response.json()[0].get('avatar_url')
        return None
    except Exception as e:
        print(f"❌ Ошибка получения аватара: {e}")
        return None

# ========== АДМИНИСТРИРОВАНИЕ ==========

def get_user_role(username):
    """Получает роль пользователя"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"username": f"eq.{username}", "select": "role"}
            )
            if response.status_code == 200 and response.json():
                return response.json()[0].get('role', 'user')
        return 'user'
    except Exception as e:
        print(f"❌ Ошибка получения роли: {e}")
        return 'user'

def is_admin(username):
    """Проверяет, является ли пользователь админом"""
    if not username:
        return False
    
    # Супер-админ всегда админ независимо от роли в базе
    if username == "dscod":
        return True
    
    # Для остальных проверяем роль в базе
    return get_user_role(username) == 'admin'

def get_all_users():
    """Получает список всех пользователей (только для админов)"""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"select": "id,username,role,created_at,avatar_url"}
            )
            if response.status_code == 200:
                return response.json()
        return []
    except Exception as e:
        print(f"❌ Ошибка получения пользователей: {e}")
        return []

def admin_delete_post(post_id):
    """Удаляет любой пост (только для админов)"""
    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={"id": f"eq.{post_id}"}
            )
            return response.status_code == 204
    except Exception as e:
        print(f"❌ Ошибка удаления поста админом: {e}")
        return False

def set_user_role(username, new_role):
    """Изменяет роль пользователя (только для админов)"""
    try:
        # Запрещаем менять роль супер-админа
        if username == SUPER_ADMIN:
            print("❌ Нельзя изменить роль супер-админа")
            return False
        
        with httpx.Client() as client:
            # Сначала получаем id пользователя
            user_response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"username": f"eq.{username}", "select": "id"}
            )
            if user_response.status_code != 200 or not user_response.json():
                return False
            
            user_id = user_response.json()[0]['id']
            
            # Обновляем роль
            response = client.patch(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"id": f"eq.{user_id}"},
                json={"role": new_role}
            )
            return response.status_code == 204
    except Exception as e:
        print(f"❌ Ошибка изменения роли: {e}")
        return False

def get_site_stats():
    """Получает статистику сайта (только для админов)"""
    try:
        with httpx.Client() as client:
            stats = {}
            
            # Количество пользователей
            users_response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"select": "id"}
            )
            stats['total_users'] = len(users_response.json()) if users_response.status_code == 200 else 0
            
            # Количество постов
            posts_response = client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={"select": "id"}
            )
            stats['total_posts'] = len(posts_response.json()) if posts_response.status_code == 200 else 0
            
            # Количество комментариев
            comments_response = client.get(
                f"{SUPABASE_URL}/rest/v1/comments",
                headers=HEADERS,
                params={"select": "id"}
            )
            stats['total_comments'] = len(comments_response.json()) if comments_response.status_code == 200 else 0
            
            # Количество лайков
            likes_response = client.get(
                f"{SUPABASE_URL}/rest/v1/likes",
                headers=HEADERS,
                params={"select": "id"}
            )
            stats['total_likes'] = len(likes_response.json()) if likes_response.status_code == 200 else 0
            
            return stats
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return {}