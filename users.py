# Здесь будем хранить пользователей
users = {}  # Словарь: {username: {'password': хеш_пароля}}

def add_user(username, password):
    """Добавляет нового пользователя"""
    if username in users:
        return False  # Пользователь уже есть
    users[username] = {
        'password': password  # Только пароль, никаких лишних полей
    }
    return True

def get_user(username):
    """Получает данные пользователя"""
    return users.get(username)