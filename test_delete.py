import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print(f"URL: {SUPABASE_URL}")
print(f"KEY: {SUPABASE_KEY}")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

with httpx.Client() as client:
    # 1. Проверим, есть ли пост
    check = client.get(
        f"{SUPABASE_URL}/rest/v1/posts",
        headers=headers,
        params={"id": "eq.5"}
    )
    print(f"Пост до удаления: {check.json()}")
    
    # 2. Удаляем
    response = client.delete(
        f"{SUPABASE_URL}/rest/v1/posts",
        headers=headers,
        params={"id": "eq.5"}
    )
    print(f"Статус удаления: {response.status_code}")
    print(f"Ответ: {response.text}")
    
    # 3. Проверяем снова
    check_after = client.get(
        f"{SUPABASE_URL}/rest/v1/posts",
        headers=headers,
        params={"id": "eq.5"}
    )
    print(f"Пост после удаления: {check_after.json()}")