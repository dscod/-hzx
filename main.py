from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from werkzeug.security import generate_password_hash, check_password_hash
import database
import os
import shutil
import uuid
from typing import Optional
from socket_manager import get_socket_app
import socket_manager

app = FastAPI(title="PIZDA MEDIA")
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-123", session_cookie="session")

# Монтируем Socket.IO приложение
socket_app = get_socket_app()
app.mount("/socket.io", socket_app)

# Подключаем статические файлы (для картинок и аватаров)
os.makedirs("static", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/avatars", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    username = request.session.get("username")
    posts = database.get_all_posts()
    
    # Добавляем информацию о лайках и проверяем, админ ли пользователь
    is_admin_user = False
    if username:
        user = database.get_user(username)
        if user:
            for post in posts:
                post['user_liked'] = database.check_user_like(user['id'], post['id'])
            is_admin_user = database.is_admin(username)  # Проверяем, админ ли
    
    response = templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "posts": posts, 
            "username": username,
            "is_admin": is_admin_user  # ← Передаём флаг в шаблон
        }
    )
    
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response

# ===== РЕГИСТРАЦИЯ =====
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    print(f"🔍 Регистрация: username={username}")
    
    # Проверяем, есть ли пользователь
    existing_user = database.get_user(username)
    print(f"🔍 Существующий пользователь: {existing_user}")
    
    if existing_user:
        print("🔍 Имя занято")
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Такое имя уже занято!"}
        )
    
    # Хешируем пароль
    print("🔍 Хешируем пароль")
    password_hash = generate_password_hash(password)
    
    # Добавляем пользователя
    print("🔍 Добавляем в БД")
    result = database.add_user(username, password_hash)
    print(f"🔍 Результат добавления: {result}")
    
    # Сразу логиним
    print("🔍 Устанавливаем сессию")
    request.session["username"] = username
    
    print("🔍 Редирект на главную")
    return RedirectResponse(url="/", status_code=303)

# ===== ВХОД =====
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    print(f"🔍 Вход: username={username}")
    
    user = database.get_user(username)
    print(f"🔍 Найден пользователь: {user}")
    
    if user and check_password_hash(user["password"], password):
        print("🔍 Пароль верный")
        request.session["username"] = username
        print("🔍 Редирект на главную")
        return RedirectResponse(url="/", status_code=303)
    else:
        print("🔍 Неверное имя или пароль")
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Неверное имя или пароль"}
        )

@app.get("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return RedirectResponse(url="/", status_code=303)

@app.post("/add_post")
async def add_post(
    request: Request,
    text: str = Form(...),
    image: UploadFile = File(None)
):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    image_url = None
    if image and image.filename:
        # Сохраняем картинку
        file_extension = os.path.splitext(image.filename)[1]
        file_name = f"{user['id']}_{os.urandom(4).hex()}{file_extension}"
        file_path = os.path.join("static/uploads", file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        image_url = f"/static/uploads/{file_name}"
    
    if text or image_url:
        database.add_post(user["id"], text, image_url)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete_post/{post_id}")
async def delete_post(request: Request, post_id: int):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Проверяем, является ли пользователь админом
    is_admin_user = database.is_admin(username)
    
    # Если не админ, проверяем, что пост принадлежит пользователю
    if not is_admin_user:
        author_id = database.get_post_author(post_id)
        if author_id != user['id']:
            return RedirectResponse(url="/", status_code=303)
    
    # Передаём флаг is_admin_user в функцию удаления
    result = database.delete_post(post_id, user['id'], is_admin_user)
    print(f"Результат удаления: {result}")
    
    return RedirectResponse(url="/", status_code=303)

# ===== МАРШРУТЫ ДЛЯ ЛАЙКОВ =====
@app.post("/like/{post_id}")
async def like_post(request: Request, post_id: int):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    database.like_post(user['id'], post_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/unlike/{post_id}")
async def unlike_post(request: Request, post_id: int):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    database.unlike_post(user['id'], post_id)
    return RedirectResponse(url="/", status_code=303)

# ===== МАРШРУТЫ ДЛЯ КОММЕНТАРИЕВ =====
@app.post("/comment/{post_id}")
async def add_comment(
    request: Request, 
    post_id: int,
    content: str = Form(...)
):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    if content:
        database.add_comment(user['id'], post_id, content)
    
    return RedirectResponse(url="/", status_code=303)

# ===== МАРШРУТЫ ДЛЯ АВАТАРОК =====
@app.post("/upload_avatar")
async def upload_avatar(
    request: Request,
    avatar: UploadFile = File(...)
):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Проверяем, что файл - изображение
    if not avatar.content_type.startswith('image/'):
        return HTMLResponse(content="Можно загружать только изображения", status_code=400)
    
    # Сохраняем картинку
    file_extension = os.path.splitext(avatar.filename)[1]
    file_name = f"avatar_{user['id']}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join("static/avatars", file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(avatar.file, buffer)
    
    avatar_url = f"/static/avatars/{file_name}"
    
    # Обновляем URL в базе данных
    database.update_avatar(user['id'], avatar_url)
    
    return RedirectResponse(url="/profile/" + username, status_code=303)

# ===== МАРШРУТЫ ДЛЯ ПРОФИЛЯ =====
@app.get("/profile/{username}", response_class=HTMLResponse)
async def profile(request: Request, username: str):
    current_user = request.session.get("username")
    
    # Получаем данные пользователя
    user = database.get_user(username)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    # Получаем аватар пользователя
    profile_avatar = database.get_user_avatar(username)
    
    # Получаем все посты и фильтруем по автору
    all_posts = database.get_all_posts()
    user_posts = [post for post in all_posts if post['author'] == username]
    
    # Получаем статистику подписок
    followers_count = database.get_followers_count(user['id'])
    following_count = database.get_following_count(user['id'])
    
    # Проверяем, подписан ли текущий пользователь
    is_following = False
    if current_user and current_user != username:
        current_user_data = database.get_user(current_user)
        if current_user_data:
            is_following = database.is_following(current_user_data['id'], user['id'])
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "username": current_user,
            "profile_user": username,
            "profile_avatar": profile_avatar,
            "posts": user_posts,
            "followers_count": followers_count,
            "following_count": following_count,
            "is_following": is_following
        }
    )

# ===== АДМИН-ПАНЕЛЬ =====
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    username = request.session.get("username")
    
    if not username or not database.is_admin(username):
        return HTMLResponse(content="<h1>403 - Доступ запрещен</h1><p>Только для администраторов</p>", status_code=403)
    
    users = database.get_all_users()
    stats = database.get_site_stats()
    
    # Получаем посты для отображения в админке
    posts = database.get_all_posts()
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "username": username,
            "users": users,
            "stats": stats,
            "posts": posts
        }
    )

@app.post("/admin/delete_post/{post_id}")
async def admin_delete_post(request: Request, post_id: int):
    username = request.session.get("username")
    
    if not username or not database.is_admin(username):
        return RedirectResponse(url="/", status_code=303)
    
    database.admin_delete_post(post_id)
    return RedirectResponse(url="/admin", status_code=303)

@app.post("/admin/set_role")
async def admin_set_role(
    request: Request,
    target_user: str = Form(...),
    new_role: str = Form(...)
):
    username = request.session.get("username")
    
    if not username or not database.is_admin(username):
        return RedirectResponse(url="/", status_code=303)
    
    if new_role in ['user', 'admin']:
        database.set_user_role(target_user, new_role)
    
    return RedirectResponse(url="/admin", status_code=303)

# ===== МЕССЕНДЖЕР =====

@app.get("/chats", response_class=HTMLResponse)
async def chats_page(request: Request):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Пока возвращаем пустой список, чтобы проверить остальное
    chats = []
    
    return templates.TemplateResponse(
        "chats.html",
        {
            "request": request,
            "username": username,
            "chats": chats
        }
    )

@app.get("/chat/{chat_id}", response_class=HTMLResponse)
async def chat_page(request: Request, chat_id: int):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    messages = database.get_chat_messages(chat_id)
    
    # Получаем информацию о другом участнике
    # (для личных чатов)
    from database import get_user_chats
    chats = database.get_user_chats(user['id'])
    other_user = None
    other_avatar = None
    
    for chat in chats:
        if chat['id'] == chat_id:
            other_user = chat['other_user']
            other_avatar = chat['other_avatar']
            break
    
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "username": username,
            "user_id": user['id'],
            "chat_id": chat_id,
            "messages": messages,
            "other_user": other_user,
            "other_avatar": other_avatar
        }
    )

@app.get("/start_chat/{other_username}")
async def start_chat(request: Request, other_username: str):
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    other = database.get_user(other_username)
    
    if not user or not other:
        return RedirectResponse(url="/", status_code=303)
    
    chat_id = database.get_or_create_private_chat(user['id'], other['id'])
    
    if chat_id:
        return RedirectResponse(url=f"/chat/{chat_id}", status_code=303)
    else:
        return RedirectResponse(url="/chats", status_code=303)
    
# ===== ПОДПИСКИ =====

@app.post("/follow/{username}")
async def follow_user(request: Request, username: str):
    current_username = request.session.get("username")
    if not current_username:
        return RedirectResponse(url="/login", status_code=303)
    
    current_user = database.get_user(current_username)
    target_user = database.get_user(username)
    
    if not current_user or not target_user or current_user['id'] == target_user['id']:
        return RedirectResponse(url=f"/profile/{username}", status_code=303)
    
    database.follow_user(current_user['id'], target_user['id'])
    return RedirectResponse(url=f"/profile/{username}", status_code=303)

@app.post("/unfollow/{username}")
async def unfollow_user(request: Request, username: str):
    current_username = request.session.get("username")
    if not current_username:
        return RedirectResponse(url="/login", status_code=303)
    
    current_user = database.get_user(current_username)
    target_user = database.get_user(username)
    
    if not current_user or not target_user:
        return RedirectResponse(url=f"/profile/{username}", status_code=303)
    
    database.unfollow_user(current_user['id'], target_user['id'])
    return RedirectResponse(url=f"/profile/{username}", status_code=303)

@app.get("/followers/{username}", response_class=HTMLResponse)
async def followers_page(request: Request, username: str):
    current_user = request.session.get("username")
    user = database.get_user(username)
    
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    followers = database.get_followers(user['id'])
    
    return templates.TemplateResponse(
        "followers.html",
        {
            "request": request,
            "username": current_user,
            "profile_user": username,
            "users": followers,
            "type": "followers"
        }
    )

@app.get("/following/{username}", response_class=HTMLResponse)
async def following_page(request: Request, username: str):
    current_user = request.session.get("username")
    user = database.get_user(username)
    
    if not user:
        return RedirectResponse(url="/", status_code=303)
    
    following = database.get_following(user['id'])
    
    return templates.TemplateResponse(
        "followers.html",
        {
            "request": request,
            "username": current_user,
            "profile_user": username,
            "users": following,
            "type": "following"
        }
    )

@app.get("/api/search_users")
async def search_users(request: Request, q: str):
    username = request.session.get("username")
    if not username:
        return {"users": []}
    
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=database.HEADERS,
                params={
                    "username": f"ilike.*{q}*",
                    "select": "username,avatar_url",
                    "limit": 10
                }
            )
            if response.status_code == 200:
                return {"users": response.json()}
    except Exception as e:
        print(f"Ошибка поиска: {e}")
    
    return {"users": []}