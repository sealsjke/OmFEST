"""An intentionally vulnerable cookie-role CTF challenge."""

import html
import os
import sqlite3
from contextlib import closing
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


DATABASE = Path(os.environ.get("DATABASE", Path(__file__).with_name("users.db")))
FLAG = os.environ.get("FLAG", "OmFEST{c4n_1_b3_4_g00d_4dm1n?}")


def initialize_database():
    with closing(sqlite3.connect(DATABASE)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT DEFAULT 'user')")


def page(title, content):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} · Cookie Club</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f5f1e8; color: #232820; font: 17px/1.6 system-ui, sans-serif; }}
    main {{ max-width: 540px; margin: 9vh auto; padding: 32px; }}
    nav {{ display: flex; flex-wrap: wrap; gap: 18px; margin-bottom: 40px; }}
    a {{ color: #38623f; }}
    .brand {{ font-weight: 800; margin-right: auto; text-decoration: none; }}
    .card {{ background: white; padding: 30px; border: 1px solid #dedbce; border-radius: 18px; }}
    h1 {{ font-size: 32px; line-height: 1.2; margin-top: 0; }}
    label {{ display: block; margin: 18px 0; font-weight: 600; }}
    input {{ width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #aaa; border-radius: 7px; font: inherit; }}
    button, .button {{ display: inline-block; padding: 11px 19px; border: 0; border-radius: 7px; background: #38623f; color: white; font: inherit; cursor: pointer; text-decoration: none; }}
    .message {{ color: #9b3928; }}
    code {{ overflow-wrap: anywhere; }}
    footer {{ margin-top: 24px; color: #686c62; font-size: 13px; }}
  </style>
</head>
<body><main>
  <nav><a class="brand" href="/">Cookie Club</a><a href="/register">Register</a><a href="/login">Log in</a></nav>
  <section class="card">{content}</section>
  <footer>Cookie Club · CTF challenge</footer>
</main></body></html>"""


def form(kind, message=""):
    title = "Create an account" if kind == "register" else "Welcome back"
    button = "Register" if kind == "register" else "Log in"
    return page(title, f"""<h1>{title}</h1>
    <p class="message" role="status">{html.escape(message)}</p>
    <form method="post" action="/{kind}">
      <label>Username<input name="username" autocomplete="username" required></label>
      <label>Password<input name="password" type="password" autocomplete="{'new-password' if kind == 'register' else 'current-password'}" required></label>
      <button type="submit">{button}</button>
    </form>""")


class Handler(BaseHTTPRequestHandler):
    def respond(self, body, status=200):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location, cookies=()):
        self.send_response(303)
        self.send_header("Location", location)
        for cookie in cookies:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        cookies = SimpleCookie()
        cookies.load(self.headers.get("Cookie", ""))
        username = cookies["username"].value if "username" in cookies else ""
        role = cookies["role"].value if "role" in cookies else "user"

        if path in ("/register", "/login"):
            self.respond(form(path[1:]))
        elif path == "/logout":
            self.redirect("/", ["username=; Path=/; Max-Age=0", "role=; Path=/; Max-Age=0"])
        elif path == "/flag":
            # The challenge vulnerability: trust an unsigned client-controlled role.
            # Deliberately do not consult the account's stored role.
            if role == "admin":
                self.respond(page("Flag", f'<h1>Welcome, admin.</h1><p>Your flag:</p><code>{html.escape(FLAG)}</code><p><a href="/">Back home</a></p>'))
            else:
                self.respond(page("Access denied", '<h1>Members only?</h1><p>This page is reserved for administrators.</p><p><a href="/">Back home</a></p>'), 403)
        elif path == "/":
            if username:
                content = f'<h1>Hello, {html.escape(username)}.</h1><p>Your role: <strong>{html.escape(role)}</strong></p><p>There is something special waiting in the admin area.</p><a class="button" href="/flag">Visit the flag page</a><p><a href="/logout">Log out</a></p>'
            else:
                content = '<h1>A little club.<br>A little secret.</h1><p>Create an account, explore the club, and find the flag.</p><a class="button" href="/register">Create an account</a><p>Already a member? <a href="/login">Log in</a></p><p><a href="/flag">Visit the flag page</a></p>'
            self.respond(page("Home", content))
        else:
            self.respond(page("Not found", '<h1>Page not found</h1><a href="/">Back home</a>'), 404)

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ("/register", "/login"):
            self.respond(page("Not found", "<h1>Page not found</h1>"), 404)
            return
        fields = parse_qs(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode())
        username = fields.get("username", [""])[0].strip()
        password = fields.get("password", [""])[0]
        if not username or not password:
            self.respond(form(path[1:], "Enter a username and password."), 400)
            return
        with closing(sqlite3.connect(DATABASE)) as db, db:
            if path == "/register":
                try:
                    db.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'user')", (username, password))
                except sqlite3.IntegrityError:
                    self.respond(form("register", "That username is already taken."), 409)
                    return
            elif not db.execute("SELECT 1 FROM users WHERE username = ? AND password = ?", (username, password)).fetchone():
                self.respond(form("login", "Incorrect username or password."), 401)
                return
        cookie = SimpleCookie()
        cookie["username"] = username
        cookie["username"]["path"] = "/"
        self.redirect("/", [cookie["username"].OutputString(), "role=user; Path=/"])


if __name__ == "__main__":
    initialize_database()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    print(f"Cookie Club listening on http://{host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
