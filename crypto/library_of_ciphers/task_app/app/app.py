import json
import os
import random
import secrets

from flask import Flask, jsonify, render_template, request, session

from encodings_data import ENCODINGS, make_question

def load_env(path: str | None = None) -> None:
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
    except FileNotFoundError:
        pass


load_env()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
TOTAL_QUESTIONS = 32

_progress: dict[str, dict] = {}
_MAX_SESSIONS = 10_000


def new_state() -> dict:
    if len(_progress) >= _MAX_SESSIONS:
        for old in list(_progress)[: _MAX_SESSIONS // 2]:
            _progress.pop(old, None)
    token = secrets.token_urlsafe(32)
    state = {"streak": 0, "answered": 0}
    _progress[token] = state
    session["token"] = token
    return state


def get_state() -> dict | None:
    token = session.get("token")
    if not isinstance(token, str):
        return None
    return _progress.get(token)


def get_flag() -> str:
    return os.environ["FLAG"]


@app.route("/")
def index():
    session.clear()
    return render_template("index.html", total=TOTAL_QUESTIONS)


@app.route("/api/question")
def question():
    state = get_state() or new_state()
    q = make_question()
    state["current_encoding"] = q["encoding"]
    return jsonify(
        {
            "number": state["answered"] + 1,
            "total": TOTAL_QUESTIONS,
            "streak": state["streak"],
            "data": q["data"],
            "options": list(ENCODINGS.keys()),
        }
    )


@app.route("/api/answer", methods=["POST"])
def answer():
    state = get_state()
    correct = state.pop("current_encoding", None) if state else None

    if not correct:
        return jsonify({"error": "no active question"}), 400

    data = request.get_json(silent=True) or {}
    choice = data.get("choice")

    if choice == correct:
        state["streak"] += 1
        state["answered"] += 1
        result = {"correct": True, "streak": state["streak"]}
        if state["answered"] >= TOTAL_QUESTIONS:
            result["flag"] = get_flag()
            _progress.pop(session["token"], None)
            session.clear()
        return jsonify(result)

    state["streak"] = 0
    state["answered"] = 0
    return jsonify({"correct": False, "reset": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555)
