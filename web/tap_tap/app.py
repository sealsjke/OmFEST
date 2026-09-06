"""Tap Tap: intentionally client-controlled scoring for a beginner CTF."""

import html
import json
import os
import sqlite3
from contextlib import closing
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("DATABASE", ROOT / "users.db"))
FLAG = os.environ.get("FLAG", "OmFEST{1_tri3d_t0_h1d3_th3_fl4g_but_1t_w4s_3v3n_m0r3_0bvi0us}")
TARGET = 100_000


def initialize_database():
    with closing(sqlite3.connect(DATABASE)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL)")


def page(content):
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tap Tap · OmFEST</title><link rel="stylesheet" href="/style.css"></head>
<body><main><nav><a class="brand" href="/">TAP TAP<span> / OmFEST</span></a>
<a href="/register">Регистрация</a><a href="/login">Вход</a></nav>
{content}<footer>OmFEST · Испытание на настойчивость</footer></main></body></html>'''


def form(kind, error=""):
    title = "Регистрация" if kind == "register" else "Вход"
    return page(f'''<section class="panel auth"><p class="eyebrow">TAP TAP CLUB</p><h1>{title}</h1>
<p class="error" role="status">{html.escape(error)}</p>
<form action="/{kind}" method="post">
<label>Имя пользователя<input name="username" autocomplete="username" required></label>
<label>Пароль<input type="password" name="password" autocomplete="{'new-password' if kind == 'register' else 'current-password'}" required></label>
<button class="submit" type="submit">{title}</button></form><a href="/">Вернуться к игре</a></section>''')


class Handler(BaseHTTPRequestHandler):
    def respond(self, body, status=200, content_type="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, cookie):
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ("/game.js", "/style.css"):
            mime = "text/javascript" if path.endswith(".js") else "text/css"
            self.respond((ROOT / path[1:]).read_text(), content_type=mime + "; charset=utf-8")
        elif path in ("/register", "/login"):
            self.respond(form(path[1:]))
        elif path == "/logout":
            self.redirect("username=; Path=/; Max-Age=0")
        elif path == "/":
            cookies = SimpleCookie(self.headers.get("Cookie", ""))
            username = unquote(cookies["username"].value) if "username" in cookies else "Гость"
            self.respond(page(f'''<section class="panel game">
<p class="eyebrow">ОДНА КНОПКА. ОДИН ФЛАГ.</p>
<h1>Нажми 100 000 раз,<br>чтобы получить флаг.</h1>
<p class="player">Игрок: {html.escape(username)} · <a href="/logout">Выйти</a></p>
<div class="counter"><span id="score">0</span><span class="target"> / 100 000</span></div>
<progress id="progress" max="100000" value="0" aria-label="Прогресс"></progress>
<button id="tap" type="button">ЖМИ<span>+1 очко</span></button>
<p class="caption">Каждое нажатие приближает тебя к цели.</p>
<p id="status" role="status"></p>
<div id="reward" hidden><p>Отличная работа! Твой флаг:</p><code id="flag"></code></div>
</section><script src="/game.js"></script>'''))
        else:
            self.respond(page("<h1>Страница не найдена</h1>"), 404)

    def do_POST(self):
        path = urlsplit(self.path).path
        body = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode()
        if path == "/api/claim":
            try:
                score = json.loads(body).get("score", 0)
                won = isinstance(score, (int, float)) and score >= TARGET
            except (ValueError, AttributeError):
                won = False
            # Intentional vulnerability: no verification of clicks or score.
            result = {"flag": FLAG} if won else {"error": "Нужно набрать 100 000 очков."}
            self.respond(json.dumps(result), 200 if won else 403, "application/json; charset=utf-8")
            return
        if path not in ("/register", "/login"):
            self.respond("Not found", 404)
            return
        fields = parse_qs(body)
        username = fields.get("username", [""])[0].strip()
        password = fields.get("password", [""])[0]
        if not username or not password:
            self.respond(form(path[1:], "Заполните оба поля."), 400)
            return
        with closing(sqlite3.connect(DATABASE)) as db, db:
            if path == "/register":
                try:
                    db.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                except sqlite3.IntegrityError:
                    self.respond(form("register", "Это имя уже занято."), 409)
                    return
            elif not db.execute("SELECT 1 FROM users WHERE username = ? AND password = ?", (username, password)).fetchone():
                self.respond(form("login", "Неверное имя или пароль."), 401)
                return
        cookie = SimpleCookie()
        cookie["username"] = quote(username, safe="")
        cookie["username"]["path"] = "/"
        self.redirect(cookie["username"].OutputString())


if __name__ == "__main__":
    initialize_database()
    host, port = os.environ.get("HOST", "0.0.0.0"), int(os.environ.get("PORT", "8001"))
    print(f"Tap Tap: http://{host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
