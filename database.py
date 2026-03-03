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

# Единые заголовки для всех запросов (Prefer не мешает DELETE)
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ========== СУПЕР-АДМИН (ЗАЩИТА) ==========
SUPER_ADMIN = "dscod"

def format_date(date_str):
    """Форматирует дату в нужный формат"""
    try:
        if isinstance(date_str, str):
            try:
                post_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except:
                try:
                    post_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
                except:
                    post_date = datetime.strptime(date_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
        else:
            post_date = date_str
        
        now = datetime.now(post_date.tzinfo) if post_date.tzinfo else datetime.now()
        today = now.date()
        post_date_only = post_date.date()
        
        delta = today - post_date_only
        time_str = post_date.strftime("%H:%M")
        
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
        print(f"🔍 add_user: {username}")
        with httpx.Client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                json={"username": username, "password": password_hash}
            )
            print(f"🔍 Response status: {response.status_code}")
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
                
                likes_response = client.get(
                    f"{SUPABASE_URL}/rest/v1/likes",
                    headers=HEADERS,
                    params={"post_id": f"eq.{post['id']}", "select": "id"}
                )
                likes_count = len(likes_response.json()) if likes_response.status_code == 200 else 0
                
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
                        
                        comment_date = format_date(comment['created_at'])
                        
                        comments_preview.append({
                            'id': comment['id'],
                            'content': comment['content'],
                            'author': comment_username,
                            'author_avatar': comment_avatar,
                            'date': comment_date
                        })
                
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

def delete_post(post_id, user_id, is_admin=False):
    """Удаляет пост. Если is_admin=True - может удалять любые посты"""
    try:
        print(f"🔍 Попытка удалить пост {post_id} пользователем {user_id} (админ: {is_admin})")
        
        with httpx.Client() as client:
            # Проверяем существование поста
            check_response = client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={"id": f"eq.{post_id}"}
            )
            
            post_data = check_response.json()
            if not post_data:
                print(f"❌ Пост {post_id} не найден")
                return False
            
            # Если не админ - проверяем права
            if not is_admin:
                post_author_id = post_data[0]['user_id']
                if post_author_id != user_id:
                    print(f"❌ Нет прав на удаление чужого поста")
                    return False
            
            # Удаляем пост
            response = client.delete(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={"id": f"eq.{post_id}"}
            )
            
            print(f"🔍 Статус удаления: {response.status_code}")
            
            # Проверяем результат
            check_after = client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={"id": f"eq.{post_id}"}
            )
            
            return len(check_after.json()) == 0
            
    except Exception as e:
        print(f"❌ Ошибка удаления поста: {e}")
        import traceback
        traceback.print_exc()
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

def check_user_like(user_id, post_id):
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

def get_user_avatar(username):
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

def get_user_by_id(user_id):
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"id": f"eq.{user_id}", "select": "username,avatar_url"}
            )
            if response.status_code == 200 and response.json():
                return response.json()[0]
        return None
    except Exception as e:
        print(f"❌ Ошибка получения пользователя по ID: {e}")
        return None

# ========== ЧАТЫ И СООБЩЕНИЯ ==========

def get_or_create_private_chat(user1_id, user2_id):
    try:
        print(f"🔍 get_or_create_private_chat: {user1_id} - {user2_id}")
        
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/chat_members",
                headers=HEADERS,
                params={"user_id": f"eq.{user1_id}", "select": "chat_id"}
            )
            
            if response.status_code != 200:
                print(f"❌ Ошибка получения чатов: {response.status_code}")
                return None
            
            chat_ids = [item['chat_id'] for item in response.json()]
            
            for chat_id in chat_ids:
                members_response = client.get(
                    f"{SUPABASE_URL}/rest/v1/chat_members",
                    headers=HEADERS,
                    params={"chat_id": f"eq.{chat_id}", "user_id": f"eq.{user2_id}"}
                )
                
                if members_response.status_code == 200 and members_response.json():
                    print(f"🔍 Найден существующий чат: {chat_id}")
                    return chat_id
            
            return create_private_chat(user1_id, user2_id)
            
    except Exception as e:
        print(f"❌ Ошибка получения/создания чата: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_private_chat(user1_id, user2_id):
    try:
        print(f"🔍 create_private_chat: {user1_id} - {user2_id}")
        
        with httpx.Client() as client:
            chat_response = client.post(
                f"{SUPABASE_URL}/rest/v1/chats",
                headers=HEADERS,
                json={"name": None}
            )
            
            if chat_response.status_code != 201:
                print(f"❌ Ошибка создания чата: {chat_response.text}")
                return None
            
            chat_id = chat_response.json()[0]['id']
            
            client.post(
                f"{SUPABASE_URL}/rest/v1/chat_members",
                headers=HEADERS,
                json={"chat_id": chat_id, "user_id": user1_id}
            )
            
            client.post(
                f"{SUPABASE_URL}/rest/v1/chat_members",
                headers=HEADERS,
                json={"chat_id": chat_id, "user_id": user2_id}
            )
            
            return chat_id
            
    except Exception as e:
        print(f"❌ Ошибка создания личного чата: {e}")
        import traceback
        traceback.print_exc()
        return None

def send_message(chat_id, user_id, content):
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/messages",
                headers=HEADERS,
                json={"chat_id": chat_id, "user_id": user_id, "content": content}
            )
            return response.status_code == 201
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        return False

def get_chat_messages(chat_id, limit=50):
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/messages",
                headers=HEADERS,
                params={
                    "chat_id": f"eq.{chat_id}",
                    "order": "created_at.desc",
                    "limit": limit,
                    "select": "id,content,created_at,user_id"
                }
            )
            
            if response.status_code != 200:
                return []
            
            messages_data = response.json()
            messages = []
            
            for msg in messages_data:
                user_response = client.get(
                    f"{SUPABASE_URL}/rest/v1/users",
                    headers=HEADERS,
                    params={"id": f"eq.{msg['user_id']}", "select": "username,avatar_url"}
                )
                
                username = "Неизвестный"
                avatar_url = None
                if user_response.status_code == 200 and user_response.json():
                    user_data = user_response.json()[0]
                    username = user_data['username']
                    avatar_url = user_data.get('avatar_url')
                
                messages.append({
                    'id': msg['id'],
                    'content': msg['content'],
                    'author': username,
                    'author_avatar': avatar_url,
                    'date': format_date(msg['created_at']),
                    'user_id': msg['user_id']
                })
            
            return list(reversed(messages))
            
    except Exception as e:
        print(f"❌ Ошибка получения сообщений: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_user_chats(user_id):
    try:
        print(f"🔍 get_user_chats для user_id: {user_id}")
        
        with httpx.Client() as client:
            members_response = client.get(
                f"{SUPABASE_URL}/rest/v1/chat_members",
                headers=HEADERS,
                params={"user_id": f"eq.{user_id}", "select": "chat_id"}
            )
            
            if members_response.status_code != 200:
                return []
            
            chat_ids = [item['chat_id'] for item in members_response.json()]
            
            if not chat_ids:
                return []
            
            chats = []
            for chat_id in chat_ids:
                try:
                    other_members = client.get(
                        f"{SUPABASE_URL}/rest/v1/chat_members",
                        headers=HEADERS,
                        params={
                            "chat_id": f"eq.{chat_id}",
                            "user_id": f"neq.{user_id}",
                            "select": "user_id"
                        }
                    )
                    
                    if other_members.status_code != 200 or not other_members.json():
                        continue
                    
                    other_user_id = other_members.json()[0]['user_id']
                    
                    user_response = client.get(
                        f"{SUPABASE_URL}/rest/v1/users",
                        headers=HEADERS,
                        params={"id": f"eq.{other_user_id}", "select": "username,avatar_url"}
                    )
                    
                    if user_response.status_code != 200 or not user_response.json():
                        continue
                    
                    other_user = user_response.json()[0]
                    
                    messages_response = client.get(
                        f"{SUPABASE_URL}/rest/v1/messages",
                        headers=HEADERS,
                        params={
                            "chat_id": f"eq.{chat_id}",
                            "order": "created_at.desc",
                            "limit": 1
                        }
                    )
                    
                    last_message = None
                    if messages_response.status_code == 200 and messages_response.json():
                        last_msg = messages_response.json()[0]
                        last_message = {
                            'content': last_msg['content'],
                            'date': format_date(last_msg['created_at'])
                        }
                    
                    chats.append({
                        'id': chat_id,
                        'other_user': other_user['username'],
                        'other_avatar': other_user.get('avatar_url'),
                        'last_message': last_message
                    })
                except Exception as e:
                    print(f"⚠️ Ошибка обработки чата {chat_id}: {e}")
                    continue
            
            return chats
            
    except Exception as e:
        print(f"⚠️ Ошибка получения чатов: {e}")
        return []

# ========== ПОДПИСКИ ==========

def follow_user(follower_id, following_id):
    if follower_id == following_id:
        print("❌ Нельзя подписаться на самого себя")
        return False
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{SUPABASE_URL}/rest/v1/follows",
                headers=HEADERS,
                json={"follower_id": follower_id, "following_id": following_id}
            )
            return response.status_code == 201
    except Exception as e:
        print(f"❌ Ошибка подписки: {e}")
        return False

def unfollow_user(follower_id, following_id):
    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{SUPABASE_URL}/rest/v1/follows",
                headers=HEADERS,
                params={
                    "follower_id": f"eq.{follower_id}",
                    "following_id": f"eq.{following_id}"
                }
            )
            return response.status_code == 204
    except Exception as e:
        print(f"❌ Ошибка отписки: {e}")
        return False

def is_following(follower_id, following_id):
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/follows",
                headers=HEADERS,
                params={
                    "follower_id": f"eq.{follower_id}",
                    "following_id": f"eq.{following_id}"
                }
            )
            return len(response.json()) > 0
    except Exception as e:
        print(f"❌ Ошибка проверки подписки: {e}")
        return False

def get_followers_count(user_id):
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/follows",
                headers=HEADERS,
                params={"following_id": f"eq.{user_id}", "select": "id"}
            )
            return len(response.json()) if response.status_code == 200 else 0
    except Exception as e:
        print(f"❌ Ошибка получения подписчиков: {e}")
        return 0

def get_following_count(user_id):
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/follows",
                headers=HEADERS,
                params={"follower_id": f"eq.{user_id}", "select": "id"}
            )
            return len(response.json()) if response.status_code == 200 else 0
    except Exception as e:
        print(f"❌ Ошибка получения подписок: {e}")
        return 0

# ========== АДМИНИСТРИРОВАНИЕ ==========

def get_user_role(username):
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
    if not username:
        return False
    if username == SUPER_ADMIN:
        return True
    return get_user_role(username) == 'admin'

def get_all_users():
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
    try:
        if username == SUPER_ADMIN:
            print("❌ Нельзя изменить роль супер-админа")
            return False
        
        with httpx.Client() as client:
            user_response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"username": f"eq.{username}", "select": "id"}
            )
            if user_response.status_code != 200 or not user_response.json():
                return False
            
            user_id = user_response.json()[0]['id']
            
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
    try:
        with httpx.Client() as client:
            stats = {}
            
            users_response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=HEADERS,
                params={"select": "id"}
            )
            stats['total_users'] = len(users_response.json()) if users_response.status_code == 200 else 0
            
            posts_response = client.get(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=HEADERS,
                params={"select": "id"}
            )
            stats['total_posts'] = len(posts_response.json()) if posts_response.status_code == 200 else 0
            
            comments_response = client.get(
                f"{SUPABASE_URL}/rest/v1/comments",
                headers=HEADERS,
                params={"select": "id"}
            )
            stats['total_comments'] = len(comments_response.json()) if comments_response.status_code == 200 else 0
            
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