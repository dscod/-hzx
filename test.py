import httpx
import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("https://dakrjsufbnnthhlatefc.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRha3Jqc3VmYm5udGhobGF0ZWZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIzMDU5MDEsImV4cCI6MjA4Nzg4MTkwMX0.SXKot8s-U5ejjwkBoPFNVQ4yHWXPRjrpjpBbf8lVKfs")

# Получаем переменные
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"URL: {SUPABASE_URL}")
print(f"KEY: {SUPABASE_KEY}")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Ошибка: не найдены ключи в .env")
    exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

with httpx.Client() as client:
    response = client.delete(
        f"{SUPABASE_URL}/rest/v1/posts",
        headers=headers,
        params={"id": "eq.4"}
    )
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.text}")