import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем переменные из .env
load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("ОШИБКА: Не найдены SUPABASE_URL или SUPABASE_KEY в .env файле!")
    print("Убедись что файл .env существует и содержит:")
    print("SUPABASE_URL=https://dakrjsufbnnthhlatefc.supabase.co")
    print("SUPABASE_KEY=твой_anon_ключ")
    exit(1)

supabase: Client = create_client(url, key)
print("✅ Подключение к Supabase успешно!")