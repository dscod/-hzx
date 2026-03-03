import socketio
import database
from typing import Dict, Set

# Создаем Socket.IO сервер с правильными настройками CORS
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'https://hzx-41d6.onrender.com'  # если есть продакшен
    ],
    logger=True,  # Включаем логи для отладки
    engineio_logger=True
)

# Хранилище подключенных пользователей: user_id -> sid
connected_users: Dict[str, str] = {}

# Хранилище комнат чата: chat_id -> {user_id: sid}
chat_rooms: Dict[int, Dict[str, str]] = {}

@sio.event
async def connect(sid, environ, auth=None):
    """Клиент подключился"""
    print(f"🔌 Попытка подключения: {sid}")
    # Разрешаем подключение
    return True

@sio.event
async def disconnect(sid):
    """Клиент отключился"""
    print(f"🔌 Отключение: {sid}")
    # Удаляем пользователя из всех хранилищ
    for user_id, user_sid in list(connected_users.items()):
        if user_sid == sid:
            del connected_users[user_id]
            print(f"👋 Пользователь {user_id} вышел")
            
            # Удаляем из комнат
            for chat_id, members in chat_rooms.items():
                if user_id in members:
                    del members[user_id]
            break

@sio.event
async def authenticate(sid, data):
    """Аутентификация пользователя"""
    print(f"🔐 Аутентификация: {data}")
    user_id = data.get('user_id')
    if user_id:
        connected_users[user_id] = sid
        print(f"✅ Пользователь {user_id} аутентифицирован (sid: {sid})")
        await sio.emit('authenticated', {'status': 'ok'}, room=sid)

@sio.event
async def join_chat(sid, data):
    """Подключение к комнате чата"""
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')
    
    if not chat_id or not user_id:
        return
    
    # Добавляем пользователя в комнату чата
    room_name = f"chat_{chat_id}"
    await sio.enter_room(sid, room_name)
    
    if chat_id not in chat_rooms:
        chat_rooms[chat_id] = {}
    chat_rooms[chat_id][user_id] = sid
    
    print(f"👥 Пользователь {user_id} зашел в чат {chat_id}")
    
    # Оповещаем других участников
    await sio.emit(
        'user_joined',
        {'user_id': user_id},
        room=room_name,
        skip_sid=sid
    )

@sio.event
async def leave_chat(sid, data):
    """Выход из комнаты чата"""
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')
    
    if not chat_id or not user_id:
        return
    
    room_name = f"chat_{chat_id}"
    await sio.leave_room(sid, room_name)
    
    if chat_id in chat_rooms and user_id in chat_rooms[chat_id]:
        del chat_rooms[chat_id][user_id]
    
    print(f"👋 Пользователь {user_id} вышел из чата {chat_id}")

@sio.event
async def send_message(sid, data):
    """Отправка сообщения"""
    print(f"📨 Попытка отправки сообщения: {data}")
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')
    content = data.get('content')
    
    if not all([chat_id, user_id, content]):
        return
    
    # Сохраняем в базу
    success = database.send_message(chat_id, user_id, content)
    
    if success:
        # Получаем имя отправителя
        user = database.get_user_by_id(user_id)
        username = user['username'] if user else 'Неизвестный'
        
        # Рассылаем всем в комнате
        room_name = f"chat_{chat_id}"
        await sio.emit(
            'new_message',
            {
                'chat_id': chat_id,
                'user_id': user_id,
                'username': username,
                'content': content,
                'timestamp': 'только что'
            },
            room=room_name
        )
        print(f"✅ Сообщение в чат {chat_id} от {username} отправлено")

@sio.event
async def typing(sid, data):
    """Пользователь печатает"""
    chat_id = data.get('chat_id')
    user_id = data.get('user_id')
    is_typing = data.get('typing', False)
    
    if not chat_id or not user_id:
        return
    
    # Рассылаем всем кроме отправителя
    room_name = f"chat_{chat_id}"
    await sio.emit(
        'user_typing',
        {
            'chat_id': chat_id,
            'user_id': user_id,
            'typing': is_typing
        },
        room=room_name,
        skip_sid=sid
    )

# Функция для получения Socket.IO приложения
def get_socket_app():
    return socketio.ASGIApp(sio, socketio_path='socket.io')