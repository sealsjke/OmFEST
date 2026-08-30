import sqlite3

conn = sqlite3.connect("users.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    note TEXT
)
""")

conn.execute("DELETE FROM users")

conn.execute("""
INSERT INTO users (username, password, note)
VALUES (?, ?, ?)
""", (
    "admin",
    "SuperSecretAdminPassword123!!",
    "OmFEST{sql_1nj3ct10n_1s_v3ry_34sy}"
))

conn.commit()
conn.close()

print("[+] Database initialized")
print("[+] User: admin")
print("[+] Password: SuperSecretAdminPassword123!!")