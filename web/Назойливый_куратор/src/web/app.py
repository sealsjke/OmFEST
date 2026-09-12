import os
import re
import sqlite3
import hashlib
from datetime import datetime
from functools import wraps
from flask import (
    Flask, request, render_template, redirect,
    url_for, session, jsonify, abort
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "corp_promsvyaz_secret_key_1984")

# CRITICAL CTF VULNERABILITY:
# Session cookie MUST NOT be HttpOnly so that XSS can steal document.cookie!
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = 'session'

DB_PATH = os.environ.get("DB_PATH", "messenger.db")
FLAG = os.environ.get("FLAG") or "OmFEST{c00k13_st34l1ng_xss_l1k3_4_b0ss}"
WELCOME_MESSAGE = os.environ.get(
    "WELCOME_MESSAGE",
    "Здравствуйте! Я ваш новый начальник отдела. Все служебные отчеты и вопросы направлять в данный чат. Бездельников не потерплю, жду результатов!"
)
BOSS_SECRET = os.environ.get("BOSS_SECRET", "boss_internal_secret_token_12345")
BOSS_PASSWORD = os.environ.get("BOSS_PASSWORD", "NachalnikSuperSecretPass2026!")

# ---------------------------------------------------------------------------
# Hardcoded anti-XSS tag blacklist
# ---------------------------------------------------------------------------
# "Security through a hardcoded list": the most common XSS tags/payloads are
# stripped out of every chat message before it is stored in the database.
#
# INTENTIONAL WEAKNESS: the blacklist regexes are case-sensitive, while the
# HTML parser is case-insensitive. A payload that uses different casing for the
# tag name (e.g. <ScRiPt> instead of <script>) is therefore NOT matched and is
# stored/rendered as-is. This keeps the challenge solvable.
BLOCKED_HTML_TAGS = (
    "script", "img", "svg", "iframe", "object", "embed", "applet",
    "body", "input", "textarea", "select", "button", "form", "details",
    "marquee", "video", "audio", "source", "math", "animate",
    "link", "meta", "style", "base", "frame", "frameset", "template",
    "noscript", "title",
)

def sanitize_message(content: str) -> str:
    """Strip hardcoded "dangerous" HTML tags from a chat message.

    Only well-formed lowercase tags are removed; the matching is deliberately
    case-sensitive (see the note above).
    """
    if not content:
        return content
    for tag in BLOCKED_HTML_TAGS:
        content = re.sub(r"</?" + tag + r"(?:\s[^>]*)?>", "", content)
    return content

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT DEFAULT 'employee',
            department TEXT DEFAULT 'Общий отдел',
            avatar TEXT DEFAULT '👤',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_welcomed (
            user_id INTEGER PRIMARY KEY,
            welcomed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            comment TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            FOREIGN KEY (author_id) REFERENCES users(id)
        )
    """)

    conn.commit()

    # Seed director
    director = cursor.execute("SELECT id FROM users WHERE username = 'директор'").fetchone()
    if not director:
        cursor.execute("""
            INSERT INTO users (username, password_hash, display_name, role, department, avatar)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            'директор',
            hash_password(os.urandom(24).hex()),
            'Смирнов В.С. (Генеральный директор)',
            'director',
            'Директорат предприятия',
            '⭐'
        ))
        director_id = cursor.lastrowid
    else:
        director_id = director['id']

    # Seed boss ("Начальник")
    boss = cursor.execute("SELECT id FROM users WHERE username = 'Начальник'").fetchone()
    if not boss:
        cursor.execute("""
            INSERT INTO users (username, password_hash, display_name, role, department, avatar)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            'Начальник',
            hash_password(BOSS_PASSWORD),
            'Громов И.П. (Начальник отдела)',
            'boss',
            'Отдел материально-технического снабжения',
            '👔'
        ))
        boss_id = cursor.lastrowid
    else:
        boss_id = boss['id']

    # Seed direct messages between Director and Boss
    existing_initial_msg = cursor.execute("""
        SELECT id FROM messages
        WHERE sender_id = ? AND receiver_id = ?
    """, (director_id, boss_id)).fetchone()

    if not existing_initial_msg:
        # Message from Director explaining that secret codes are no longer in open chat
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            director_id,
            boss_id,
            "Иван Петрович, приветствую! В связи с усилением мер информационной безопасности передача секретных кодов в открытой переписке строго запрещена регламентом предприятия. Секретный код доступа перенесен в защищенный реестр.<br><br>Для запроса доступа к закрытому реестру оформляйте служебные записки через новый раздел <b>«Служебные записки»</b> (кнопка в главном меню). Обязательно прикрепляйте ссылку на материалы проверки/аудита: я лично перейду по ссылке на своем терминале, изучу документацию и подтвержу выдачу допуска через служебную форму согласования.",
            datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        ))

        # Boss response
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            boss_id,
            director_id,
            "Виктор Сергеевич, вас понял! Буду направлять материалы и ссылки на проверку через раздел «Служебные записки».",
            datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        ))

    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/quick-auth')
def quick_auth():
    token = request.args.get('token', '')
    target_role = request.args.get('as', 'boss')
    redirect_target = request.args.get('redirect', '/')
    if token != BOSS_SECRET:
        abort(403)

    conn = get_db()
    if target_role == 'director':
        user = conn.execute("SELECT * FROM users WHERE username = 'директор'").fetchone()
    else:
        user = conn.execute("SELECT * FROM users WHERE username = 'Начальник'").fetchone()
    conn.close()

    if not user:
        abort(500)

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['display_name'] = user['display_name']
    session['role'] = user['role']

    return redirect(redirect_target)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        if user and user['password_hash'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['display_name'] = user['display_name']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            error = "Неверное имя пользователя или пароль! Попытка несанкционированного входа зафиксирована СБ."

    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        display_name = request.form.get('display_name', '').strip()
        department = request.form.get('department', 'Отдел снабжения').strip()

        if not username or not password or not display_name:
            error = "Все обязательные поля формы должны быть заполнены!"
        elif len(username) < 3 or len(username) > 30:
            error = "Длина логина должна составлять от 3 до 30 символов!"
        elif username.lower() in ['начальник', 'директор', 'admin', 'root']:
            error = "Регистрация под зарезервированными служебными именами строго запрещена!"
        else:
            conn = get_db()
            existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if existing:
                error = "Сотрудник с таким логином уже зарегистрирован в корпоративной сети!"
                conn.close()
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password_hash, display_name, role, department, avatar)
                    VALUES (?, ?, ?, 'employee', ?, '👤')
                """, (username, hash_password(password), display_name, department))
                new_user_id = cursor.lastrowid
                conn.commit()
                conn.close()

                session['user_id'] = new_user_id
                session['username'] = username
                session['display_name'] = display_name
                session['role'] = 'employee'
                return redirect(url_for('index'))

    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/chat/<username>')
@login_required
def index(username=None):
    current_user_id = session['user_id']
    conn = get_db()
    current_user = conn.execute("SELECT * FROM users WHERE id = ?", (current_user_id,)).fetchone()

    if not current_user:
        session.clear()
        return redirect(url_for('login'))

    is_boss = (current_user['role'] == 'boss')

    # Fetch contacts list
    if is_boss:
        # Boss sees Director and all registered employees
        contacts = conn.execute("""
            SELECT id, username, display_name, role, department, avatar,
                (SELECT content FROM messages
                 WHERE (sender_id = users.id AND receiver_id = ?)
                    OR (sender_id = ? AND receiver_id = users.id)
                 ORDER BY id DESC LIMIT 1) AS last_message,
                (SELECT created_at FROM messages
                 WHERE (sender_id = users.id AND receiver_id = ?)
                    OR (sender_id = ? AND receiver_id = users.id)
                 ORDER BY id DESC LIMIT 1) AS last_time,
                (SELECT COUNT(*) FROM messages
                 WHERE sender_id = users.id AND receiver_id = ? AND is_read = 0) AS unread_count
            FROM users
            WHERE id != ?
            ORDER BY CASE WHEN role = 'director' THEN 0 ELSE 1 END, id ASC
        """, (current_user_id, current_user_id, current_user_id, current_user_id, current_user_id, current_user_id)).fetchall()
    else:
        # Regular employee only sees Boss ("Начальник")
        contacts = conn.execute("""
            SELECT id, username, display_name, role, department, avatar,
                (SELECT content FROM messages
                 WHERE (sender_id = users.id AND receiver_id = ?)
                    OR (sender_id = ? AND receiver_id = users.id)
                 ORDER BY id DESC LIMIT 1) AS last_message,
                (SELECT created_at FROM messages
                 WHERE (sender_id = users.id AND receiver_id = ?)
                    OR (sender_id = ? AND receiver_id = users.id)
                 ORDER BY id DESC LIMIT 1) AS last_time,
                (SELECT COUNT(*) FROM messages
                 WHERE sender_id = users.id AND receiver_id = ? AND is_read = 0) AS unread_count
            FROM users
            WHERE role = 'boss'
        """, (current_user_id, current_user_id, current_user_id, current_user_id, current_user_id)).fetchall()

    # Determine active chat target
    active_target = None
    if username:
        active_target = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if not active_target and contacts:
        # Default to first contact (for employee: Начальник; for boss: директор or requested user)
        active_target = contacts[0]

    # If target is found but normal employee tries to open director's chat directly, prevent it
    if active_target and not is_boss and active_target['role'] == 'director':
        conn.close()
        abort(403)

    messages = []
    if active_target:
        # Mark messages as read
        conn.execute("""
            UPDATE messages SET is_read = 1
            WHERE sender_id = ? AND receiver_id = ?
        """, (active_target['id'], current_user_id))
        conn.commit()

        # Load chat messages between current_user and active_target
        messages = conn.execute("""
            SELECT m.id, m.sender_id, m.receiver_id, m.content, m.created_at,
                   u.username AS sender_username, u.display_name AS sender_name, u.avatar AS sender_avatar
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?)
               OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.id ASC
        """, (current_user_id, active_target['id'], active_target['id'], current_user_id)).fetchall()

    conn.close()

    return render_template(
        'chat.html',
        current_user=current_user,
        contacts=contacts,
        active_target=active_target,
        messages=messages
    )

@app.route('/send', methods=['POST'])
@login_required
def send_message():
    current_user_id = session['user_id']
    receiver_username = request.form.get('receiver_username', '').strip()
    content = sanitize_message(request.form.get('content', ''))

    if not receiver_username or not content.strip():
        return redirect(url_for('index', username=receiver_username))

    conn = get_db()
    receiver = None
    if receiver_username and receiver_username.strip().upper() not in [
        'YOUR_USERNAME', '{YOUR_USERNAME}', '$YOUR_USERNAME', '<YOUR_USERNAME>',
        'YOUR_LOGIN', 'YOUR_NAME', '{USERNAME}', '<USERNAME>'
    ]:
        receiver = conn.execute("SELECT * FROM users WHERE username = ?", (receiver_username,)).fetchone()

    if not receiver:
        # Fallback 1: Extract username from referrer (e.g. /chat/<username>)
        if request.referrer:
            ref_match = re.search(r'/chat/([^/?#]+)', request.referrer)
            if ref_match:
                ref_user = conn.execute("SELECT * FROM users WHERE username = ?", (ref_match.group(1),)).fetchone()
                if ref_user:
                    receiver = ref_user

        # Fallback 2: If sender is boss (e.g. Начальник bot executing XSS in employee's dialogue),
        # route to the employee whose chat the boss was inspecting
        if not receiver and session.get('role') == 'boss':
            last_msg = conn.execute("""
                SELECT sender_id FROM messages
                WHERE receiver_id = ? AND sender_id != ?
                ORDER BY id DESC LIMIT 1
            """, (current_user_id, current_user_id)).fetchone()
            if last_msg:
                receiver = conn.execute("SELECT * FROM users WHERE id = ?", (last_msg['sender_id'],)).fetchone()

        # Fallback 3: If sender is employee, route to self
        if not receiver:
            receiver = conn.execute("SELECT * FROM users WHERE id = ?", (current_user_id,)).fetchone()

    if not receiver:
        conn.close()
        abort(404)

    receiver_username = receiver['username']

    # If regular user attempts to send message to director
    if session.get('role') != 'boss' and receiver['role'] == 'director':
        conn.close()
        abort(403)

    now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    conn.execute("""
        INSERT INTO messages (sender_id, receiver_id, content, created_at)
        VALUES (?, ?, ?, ?)
    """, (current_user_id, receiver['id'], content, now_str))
    conn.commit()
    conn.close()

    return redirect(url_for('index', username=receiver_username))

@app.route('/api/messages/<username>')
@login_required
def api_messages(username):
    current_user_id = session['user_id']
    conn = get_db()
    target = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if not target:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    if session.get('role') != 'boss' and target['role'] == 'director':
        conn.close()
        return jsonify({"error": "Forbidden"}), 403

    messages = conn.execute("""
        SELECT m.id, m.sender_id, m.receiver_id, m.content, m.created_at,
               u.username AS sender_username, u.display_name AS sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?)
           OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.id ASC
    """, (current_user_id, target['id'], target['id'], current_user_id)).fetchall()
    conn.close()

    return jsonify({
        "messages": [
            {
                "id": m["id"],
                "sender_id": m["sender_id"],
                "receiver_id": m["receiver_id"],
                "content": m["content"],
                "created_at": m["created_at"],
                "sender_username": m["sender_username"],
                "sender_name": m["sender_name"],
                "is_mine": (m["sender_id"] == current_user_id)
            }
            for m in messages
        ]
    })

# --- Memos & Approvals (Phase 2) ---
@app.route('/memos', methods=['GET', 'POST'])
@login_required
def memos():
    current_user_id = session['user_id']
    conn = get_db()
    current_user = conn.execute("SELECT * FROM users WHERE id = ?", (current_user_id,)).fetchone()
    if not current_user:
        conn.close()
        session.clear()
        return redirect(url_for('login'))

    # Only department heads (boss) and directorate (director) have access
    if current_user['role'] not in ['boss', 'director']:
        conn.close()
        return "<h3>403 Доступ запрещен</h3><p>Подсистема «Служебные записки» доступна только руководящему составу предприятия (Начальникам отделов и Директорату)!</p>", 403

    error = None
    success = None

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        url = request.form.get('url', '').strip()
        comment = request.form.get('comment', '').strip()

        if not title or not url:
            error = "Необходимо заполнить тему служебной записки и ссылку на материалы!"
        elif not (url.startswith('http://') or url.startswith('https://') or url.startswith('/')):
            error = "Ссылка на материалы должна начинаться с http://, https:// или /!"
        else:
            conn.execute("""
                INSERT INTO memos (author_id, title, url, comment, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (current_user_id, title, url, comment))
            conn.commit()
            success = "Служебная записка успешно зарегистрирована! Генеральный директор лично перейдет по указанной ссылке на своем терминале и рассмотрит запрос."

    memos_list = conn.execute("""
        SELECT m.id, m.title, m.url, m.comment, m.status, m.created_at, m.approved_at,
               u.display_name AS author_name, u.username AS author_username
        FROM memos m
        JOIN users u ON m.author_id = u.id
        ORDER BY m.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        'memos.html',
        current_user=current_user,
        memos=memos_list,
        error=error,
        success=success
    )

@app.route('/memos/approve', methods=['GET', 'POST'])
@login_required
def approve_memo():
    current_user_id = session['user_id']
    conn = get_db()
    current_user = conn.execute("SELECT * FROM users WHERE id = ?", (current_user_id,)).fetchone()

    # CRITICAL CTF VULNERABILITY:
    # Endpoint lacks CSRF token!
    # Only Director has authorization to approve.
    if not current_user or current_user['role'] != 'director':
        conn.close()
        return "<h3>403 Доступ запрещен</h3><p>Утверждать выдачу допуска к закрытому реестру имеет полномочия исключительно Генеральный директор (Смирнов В.С.)!</p>", 403

    memo_id = request.values.get('memo_id')
    boss = conn.execute("SELECT * FROM users WHERE username = 'Начальник'").fetchone()
    if not boss:
        conn.close()
        return jsonify({"error": "Boss account not found"}), 500

    now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    # Update memo status in DB
    if memo_id:
        conn.execute("""
            UPDATE memos
            SET status = 'approved', approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (memo_id,))
    else:
        conn.execute("""
            UPDATE memos
            SET status = 'approved', approved_at = CURRENT_TIMESTAMP
            WHERE status = 'pending' OR status = 'visited'
        """)

    # Director sends the flag in chat to Boss!
    approval_msg = f"Уведомление о согласовании допуска: Служебная записка и прикрепленные материалы успешно проверены на моем терминале. Допуск к закрытому реестру спец-оборудования утвержден. Секретный код доступа: <b>{FLAG}</b>. Гриф: «Особая важность», третьим лицам не разглашать!"
    conn.execute("""
        INSERT INTO messages (sender_id, receiver_id, content, created_at, is_read)
        VALUES (?, ?, ?, ?, 0)
    """, (current_user['id'], boss['id'], approval_msg, now_str))

    conn.commit()
    conn.close()

    if request.headers.get('Accept') == 'application/json' or request.is_json:
        return jsonify({"status": "approved", "message": "Допуск успешно утвержден"})
    return redirect(url_for('memos'))

# --- Bot Internal API ---
@app.route('/api/internal/bot/tasks')
def bot_tasks():
    secret = request.args.get('secret', '')
    if secret != BOSS_SECRET:
        abort(403)

    conn = get_db()
    # Users who haven't received the welcoming message yet
    new_users = conn.execute("""
        SELECT id, username, display_name FROM users
        WHERE role = 'employee'
          AND id NOT IN (SELECT user_id FROM bot_welcomed)
        ORDER BY id ASC
    """).fetchall()

    # All active employee users whose chats need to be inspected
    active_users = conn.execute("""
        SELECT id, username, display_name FROM users
        WHERE role = 'employee'
        ORDER BY id ASC
    """).fetchall()

    conn.close()

    return jsonify({
        "new_users": [{"id": u["id"], "username": u["username"], "display_name": u["display_name"]} for u in new_users],
        "active_users": [{"id": u["id"], "username": u["username"], "display_name": u["display_name"]} for u in active_users]
    })

@app.route('/api/internal/bot/send-welcome', methods=['POST'])
def bot_send_welcome():
    data = request.get_json(force=True, silent=True) or {}
    secret = data.get('secret', '')
    if secret != BOSS_SECRET:
        abort(403)

    user_id = data.get('user_id')
    welcome_text = sanitize_message(data.get('message', WELCOME_MESSAGE))

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    conn = get_db()
    boss = conn.execute("SELECT id FROM users WHERE username = 'Начальник'").fetchone()
    if not boss:
        conn.close()
        return jsonify({"error": "Boss account not found"}), 500

    now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    # Send welcome message from boss to user
    conn.execute("""
        INSERT INTO messages (sender_id, receiver_id, content, created_at)
        VALUES (?, ?, ?, ?)
    """, (boss['id'], user_id, welcome_text, now_str))

    # Record as welcomed
    conn.execute("""
        INSERT OR REPLACE INTO bot_welcomed (user_id, welcomed_at)
        VALUES (?, CURRENT_TIMESTAMP)
    """, (user_id,))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route('/api/internal/bot/pending-memos')
def bot_pending_memos():
    secret = request.args.get('secret', '')
    if secret != BOSS_SECRET:
        abort(403)

    conn = get_db()
    pending = conn.execute("""
        SELECT id, url, title, author_id
        FROM memos
        WHERE status = 'pending'
        ORDER BY id ASC
    """).fetchall()
    conn.close()

    return jsonify({
        "pending_memos": [{"id": m["id"], "url": m["url"], "title": m["title"]} for m in pending]
    })

@app.route('/api/internal/bot/memo-visited', methods=['POST'])
def bot_memo_visited():
    data = request.get_json(force=True, silent=True) or {}
    secret = data.get('secret', '')
    if secret != BOSS_SECRET:
        abort(403)

    memo_id = data.get('memo_id')
    if not memo_id:
        return jsonify({"error": "Missing memo_id"}), 400

    conn = get_db()
    conn.execute("""
        UPDATE memos
        SET status = 'visited'
        WHERE id = ? AND status = 'pending'
    """, (memo_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT") or 5000)
    app.run(host='0.0.0.0', port=port, debug=False)
