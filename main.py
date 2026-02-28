from fastapi import FastAPI, Request, Form, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from werkzeug.security import generate_password_hash, check_password_hash
import database
import os
import shutil
from typing import Optional

app = FastAPI(title="Моя Соцсеть")
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-123", session_cookie="session")

templates = Jinja2Templates(directory="templates")

# Создаем папку для загруженных изображений
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    username = request.session.get("username")
    posts = database.get_all_posts()
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "posts": posts, "username": username}
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if database.get_user(username):
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Такое имя уже занято!"}
        )
    
    password_hash = generate_password_hash(password)
    database.add_user(username, password_hash)
    
    request.session["username"] = username
    return RedirectResponse(url="/", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
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
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
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
        return RedirectResponse(url="/", status_code=303)  # Нельзя удалить чужой пост
    
    database.delete_post(post_id, user['id'])
    return RedirectResponse(url="/", status_code=303)