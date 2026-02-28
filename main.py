from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from werkzeug.security import generate_password_hash, check_password_hash
import database
import os
from typing import Optional

# Создаем приложение FastAPI
app = FastAPI(title="Моя Соцсеть")

# Добавляем поддержку сессий (как в Flask)
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-123", session_cookie="session")

# Настраиваем шаблоны (аналогично render_template в Flask)
templates = Jinja2Templates(directory="templates")

# Добавляем поддержку статических файлов (CSS, картинки)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница"""
    username = request.session.get("username")
    posts = database.get_all_posts()
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "posts": posts, "username": username}
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Обработка регистрации"""
    # Проверяем, есть ли пользователь
    if database.get_user(username):
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Такое имя уже занято!"}
        )
    
    # Хешируем пароль и сохраняем
    password_hash = generate_password_hash(password)
    database.add_user(username, password_hash)
    
    # Сразу логиним
    request.session["username"] = username
    return RedirectResponse(url="/", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Обработка входа"""
    user = database.get_user(username)
    
    if user and check_password_hash(user["password"], password):
        request.session["username"] = username
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Неверное имя или пароль"}
        )

@app.get("/logout")
async def logout(request: Request):
    """Выход из системы"""
    request.session.pop("username", None)
    return RedirectResponse(url="/", status_code=303)

@app.post("/add_post")
async def add_post(
    request: Request,
    text: str = Form(...)
):
    """Добавление нового поста"""
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)
    
    user = database.get_user(username)
    if text and user:
        database.add_post(user["id"], text)
    
    return RedirectResponse(url="/", status_code=303)

# Для запуска: uvicorn main:app --reload