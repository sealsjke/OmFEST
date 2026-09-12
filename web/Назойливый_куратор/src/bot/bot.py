import os
import sys
import time
import json
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

WEB_URL = os.environ.get("WEB_URL", "http://web:5000")
LIGHTPANDA_URL = os.environ.get("LIGHTPANDA_URL", "ws://lightpanda:9222")
BOSS_SECRET = os.environ.get("BOSS_SECRET", "boss_internal_secret_token_12345")
WELCOME_MESSAGE = os.environ.get(
    "WELCOME_MESSAGE",
    "Здравствуйте! Я ваш новый начальник отдела. Все служебные отчеты и вопросы направлять в данный чат. Бездельников не потерплю, жду результатов!"
)
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "15"))

def wait_for_web():
    print(f"[BOT-PY] Waiting for web service at {WEB_URL}/health...", flush=True)
    while True:
        try:
            req = urllib.request.Request(f"{WEB_URL}/health")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    print("[BOT-PY] Web service is up and healthy!", flush=True)
                    return
        except Exception:
            pass
        time.sleep(2)

def get_tasks():
    url = f"{WEB_URL}/api/internal/bot/tasks?secret={urllib.parse.quote(BOSS_SECRET)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode('utf-8'))

def send_welcome(user_id):
    url = f"{WEB_URL}/api/internal/bot/send-welcome"
    payload = json.dumps({
        "secret": BOSS_SECRET,
        "user_id": user_id,
        "message": WELCOME_MESSAGE
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status == 200

def get_pending_memos():
    url = f"{WEB_URL}/api/internal/bot/pending-memos?secret={urllib.parse.quote(BOSS_SECRET)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode('utf-8'))

def mark_memo_visited(memo_id):
    url = f"{WEB_URL}/api/internal/bot/memo-visited"
    payload = json.dumps({
        "secret": BOSS_SECRET,
        "memo_id": memo_id
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status == 200

def main():
    print("[BOT-PY] Starting Python-based Начальник & Директор bot...", flush=True)
    wait_for_web()

    with sync_playwright() as p:
        print(f"[BOT-PY] Connecting to Lightpanda at {LIGHTPANDA_URL}...", flush=True)
        browser = None
        while not browser:
            try:
                browser = p.chromium.connect_over_cdp(LIGHTPANDA_URL, headers={"Host": "localhost:9222"})
                print("[BOT-PY] Connected to Lightpanda browser successfully!", flush=True)
            except Exception as e:
                print(f"[BOT-PY] Waiting for Lightpanda ({e}), retrying in 2s...", flush=True)
                time.sleep(2)

        while True:
            try:
                tasks = get_tasks()

                for user in tasks.get("new_users", []):
                    print(f"[BOT-PY] Sending welcome message to: {user['username']}", flush=True)
                    send_welcome(user["id"])

                for user in tasks.get("active_users", []):
                    username = user["username"]
                    print(f"[BOT-PY] Visiting chat with {username}...", flush=True)
                    page = browser.new_page()
                    try:
                        target = f"{WEB_URL}/quick-auth?token={urllib.parse.quote(BOSS_SECRET)}&as=boss&redirect={urllib.parse.quote('/chat/' + username)}"
                        page.goto(target, timeout=12000)
                        time.sleep(5)
                        print(f"[BOT-PY] Checked chat with {username}.", flush=True)
                    except Exception as err:
                        print(f"[BOT-PY] Error during visit: {err}", flush=True)
                    finally:
                        try:
                            page.close()
                        except Exception:
                            pass

                memos = get_pending_memos()
                for memo in memos.get("pending_memos", []):
                    memo_id = memo["id"]
                    memo_url = memo["url"]
                    print(f"[BOT-PY] [Директор] Reviewing memo #{memo_id}: {memo_url}...", flush=True)
                    page = browser.new_page()
                    try:
                        auth_url = f"{WEB_URL}/quick-auth?token={urllib.parse.quote(BOSS_SECRET)}&as=director&redirect={urllib.parse.quote('/memos')}"
                        page.goto(auth_url, timeout=12000)
                        target_url = memo_url.strip()
                        if not target_url.startswith('http://') and not target_url.startswith('https://'):
                            target_url = f"{WEB_URL}{'' if target_url.startswith('/') else '/'}{target_url}"
                        page.goto(target_url, timeout=12000)
                        time.sleep(6)
                        mark_memo_visited(memo_id)
                        print(f"[BOT-PY] [Директор] Visited memo #{memo_id}.", flush=True)
                    except Exception as err:
                        print(f"[BOT-PY] Error reviewing memo #{memo_id}: {err}", flush=True)
                    finally:
                        try:
                            page.close()
                        except Exception:
                            pass

            except Exception as e:
                print(f"[BOT-PY] Cycle error: {e}", flush=True)

            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
