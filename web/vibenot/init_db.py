import os
import sqlite3

DB = "users.db"
FLAG = os.getenv("FLAG", "OmFEST{F4K3_FL4G}")

conn = sqlite3.connect(DB)

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
    FLAG
))

conn.commit()
conn.close()

print("[+] Database initialized")
