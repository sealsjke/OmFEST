from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "secret"
)

DB_PATH = os.environ.get(
    "DB_PATH",
    "/app/data/duckshop.db"
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    products = conn.execute(
        "SELECT id, name, description FROM products"
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        products=products,
        username=session.get("username"),
        search_term=""
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:
            flash("Заполните все поля")
            return redirect(url_for("register"))

        conn = get_db()

        try:

            conn.execute(
                """
                INSERT INTO users (username, password)
                VALUES (?, ?)
                """,
                (username, password)
            )

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            flash("Такой пользователь уже существует")

            return redirect(url_for("register"))

        conn.close()

        flash("Регистрация успешна")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        )

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db()

        user = conn.execute(
            """
            SELECT id, username
            FROM users
            WHERE username = ?
            AND password = ?
            """,
            (username, password)
        ).fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("index"))

        flash("Неверный логин или пароль")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


@app.route("/search")
def search():
    if "user_id" not in session:
        return redirect(url_for("login"))

    search_term = request.args.get("q", "")

    conn = get_db()

    # INTENTIONAL UNION-BASED SQL INJECTION
    query = f"""
        SELECT id, name, description
        FROM products
        WHERE name LIKE '%{search_term}%'
    """

    print("=" * 70)
    print("[SEARCH]")
    print("Input:", repr(search_term))
    print("SQL:")
    print(query)
    print("=" * 70)

    try:
        products = conn.execute(query).fetchall()
        error = None

    except sqlite3.Error as e:
        print("[SQLITE ERROR]", e)

        products = []
        error = str(e)

    finally:
        conn.close()

    return render_template(
        "index.html",
        products=products,
        username=session.get("username"),
        search_term=search_term,
        error=error
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "7777")),
        debug=False
    )