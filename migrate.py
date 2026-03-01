import sqlite3
import os

DB_FILE = 'social_network.db'

def migrate():
    print("Начинаем миграцию базы данных...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Проверяем, есть ли колонка image_url
    cursor.execute("PRAGMA table_info(posts)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'image_url' not in column_names:
        print("Добавляем колонку image_url...")
        cursor.execute("ALTER TABLE posts ADD COLUMN image_url TEXT")
        print("Колонка добавлена!")
    else:
        print("Колонка image_url уже существует")
    
    conn.commit()
    conn.close()
    print("Миграция завершена!")

if __name__ == "__main__":
    if os.path.exists(DB_FILE):
        migrate()
    else:
        print("База данных не найдена. Запустите приложение, чтобы создать новую.")