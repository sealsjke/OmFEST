import os
import time
from datetime import datetime, timedelta

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from werkzeug.security import generate_password_hash, check_password_hash

from db import get_db


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

CLAIM_COOLDOWN = timedelta(hours=24)
FLAG_PRICE = 367
FLAG = os.getenv("FLAG", "OmFEST{F4K3_FL4G}")


def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    db = get_db()
    cur = db.cursor()

    cur.execute(
        """
        SELECT id, username, password_hash, coins, last_claim
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )

    user = cur.fetchone()
    cur.close()
    db.close()

    return user


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        flash("Заполните все поля.")
        return redirect(url_for("register"))

    if len(username) > 32:
        flash("Слишком длинный ник.")
        return redirect(url_for("register"))

    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT id FROM users WHERE username = %s",
        (username,),
    )

    if cur.fetchone():
        cur.close()
        db.close()

        flash("Пользователь уже существует.")
        return redirect(url_for("register"))

    password_hash = generate_password_hash(password)

    cur.execute(
        """
        INSERT INTO users
            (username, password_hash, coins, last_claim)
        VALUES
            (%s, %s, 0, NULL)
        RETURNING id
        """,
        (username, password_hash),
    )

    user_id = cur.fetchone()[0]

    db.commit()
    cur.close()
    db.close()

    session["user_id"] = user_id

    return redirect(url_for("dashboard"))


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    db = get_db()
    cur = db.cursor()

    cur.execute(
        """
        SELECT id, username, password_hash
        FROM users
        WHERE username = %s
        """,
        (username,),
    )

    user = cur.fetchone()

    cur.close()
    db.close()

    if not user or not check_password_hash(user[2], password):
        flash("Неверный логин или пароль.")
        return redirect(url_for("login"))

    session["user_id"] = user[0]

    return redirect(url_for("dashboard"))


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    user = current_user()

    if not user:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        user=user,
        cooldown=CLAIM_COOLDOWN.total_seconds(),
    )


# =========================
# CLAIM
# =========================

@app.route("/claim", methods=["POST"])
def claim():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()

    cur.execute(
        """
        SELECT coins, last_claim
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )

    user = cur.fetchone()

    if not user:
        cur.close()
        db.close()
        return "User not found", 404

    coins, last_claim = user
    now = datetime.utcnow()

    # Аккаунт уже использовал ежедневную награду
    if last_claim is not None:
        if now - last_claim < CLAIM_COOLDOWN:

            cur.close()
            db.close()

            return redirect(url_for("dashboard"))

    time.sleep(0.1)

    cur.execute(
        """
        UPDATE users
        SET coins = coins + 1,
            last_claim = %s
        WHERE id = %s
        """,
        (now, user_id),
    )

    db.commit()

    cur.close()
    db.close()

    return redirect(url_for("dashboard"))


# =========================
# PROFILE
# =========================

@app.route("/profile")
def profile():

    user = current_user()

    if not user:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()

    cur.execute(
        """
        SELECT username, coins
        FROM users
        WHERE id = %s
        """,
        (user[0],),
    )

    profile_user = cur.fetchone()

    cur.close()
    db.close()

    return render_template(
        "profile.html",
        user=profile_user,
        flag_price=FLAG_PRICE,
    )


# =========================
# TRANSFER
# =========================

@app.route("/transfer", methods=["POST"])
def transfer():

    sender_id = session.get("user_id")

    if not sender_id:
        return redirect(url_for("login"))

    recipient_username = request.form.get("username", "").strip()

    try:
        amount = int(request.form.get("amount", "0"))
    except ValueError:
        amount = 0

    if amount <= 0:
        flash("Некорректное количество монет.")
        return redirect(url_for("profile"))

    db = get_db()
    cur = db.cursor()

    cur.execute(
        """
        SELECT id, username, coins
        FROM users
        WHERE id = %s
        """,
        (sender_id,),
    )

    sender = cur.fetchone()

    cur.execute(
        """
        SELECT id, username, coins
        FROM users
        WHERE username = %s
        """,
        (recipient_username,),
    )

    recipient = cur.fetchone()

    if not recipient:
        cur.close()
        db.close()

        flash("Пользователь не найден.")
        return redirect(url_for("profile"))

    if recipient[0] == sender[0]:
        cur.close()
        db.close()

        flash("Нельзя отправить монеты самому себе.")
        return redirect(url_for("profile"))

    if sender[2] < amount:
        cur.close()
        db.close()

        flash("Недостаточно монет.")
        return redirect(url_for("profile"))

    cur.execute(
        """
        UPDATE users
        SET coins = coins - %s
        WHERE id = %s
        """,
        (amount, sender_id),
    )

    cur.execute(
        """
        UPDATE users
        SET coins = coins + %s
        WHERE id = %s
        """,
        (amount, recipient[0]),
    )

    db.commit()

    cur.close()
    db.close()

    flash(
        f"Переведено {amount} монет пользователю "
        f"{recipient_username}."
    )

    return redirect(url_for("profile"))


# =========================
# BUY FLAG
# =========================

@app.route("/buy-flag", methods=["POST"])
def buy_flag():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()

    cur.execute(
        """
        SELECT coins
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )

    user = cur.fetchone()

    if not user:
        cur.close()
        db.close()

        return "User not found", 404

    if user[0] < FLAG_PRICE:
        cur.close()
        db.close()

        flash(
            f"Недостаточно монет. "
            f"Необходимо: {FLAG_PRICE}."
        )

        return redirect(url_for("profile"))

    cur.execute(
        """
        UPDATE users
        SET coins = coins - %s
        WHERE id = %s
        """,
        (FLAG_PRICE, user_id),
    )

    db.commit()

    cur.close()
    db.close()

    return render_template(
        "profile.html",
        user=(current_user()[1], user[0] - FLAG_PRICE),
        flag=FLAG,
        flag_price=FLAG_PRICE,
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
    )