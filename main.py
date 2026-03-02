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

app = FastAPI(title="PIZDA MEDIA")
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-123", session_cookie="session")

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
    
    # Добавляем информацию о том, лайкнул ли пользователь каждый пост
    if username:
        user = database.get_user(username)
        if user:
            for post in posts:
                post['user_liked'] = database.check_user_like(user['id'], post['id'])
    
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "posts": posts, "username": username}
    )

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
    
    # Проверяем, что пост принадлежит пользователю
    author_id = database.get_post_author(post_id)
    if author_id != user['id']:
        return RedirectResponse(url="/", status_code=303)
    
    database.delete_post(post_id, user['id'])
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
    
    # Получаем аватар пользователя
    profile_avatar = database.get_user_avatar(username)
    
    # Получаем все посты и фильтруем по автору
    all_posts = database.get_all_posts()
    user_posts = [post for post in all_posts if post['author'] == username]
    
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "username": current_user,
            "profile_user": username,
            "profile_avatar": profile_avatar,
            "posts": user_posts
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