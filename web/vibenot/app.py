from flask import Flask, request, render_template, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "stfa-secret-key")

DB = "users.db"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        conn = get_db()


        query = f"""
            SELECT id, username
            FROM users
            WHERE username = '{username}'
            AND password = '{password}'
        """

        try:
            user = conn.execute(query).fetchone()
        except sqlite3.Error:
            user = None

        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/account")

        error = "Login or password incorrect"

    return render_template("login.html", error=error)


@app.route("/account")
def account():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()

    user = conn.execute(
        "SELECT username, note FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if not user:
        session.clear()
        return redirect("/")

    return render_template(
        "account.html",
        username=user["username"],
        note=user["note"]
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5555")))