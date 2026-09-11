from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.environ.get(
    "DB_PATH",
    "/app/data/nftducks.db"
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():

    category = request.args.get("category", "All")

    conn = get_db()


    if category == "All":
        query = """
            SELECT id, name, description
            FROM ducks
        """
    else:
        query = f"""
            SELECT id, name, description
            FROM ducks
            WHERE category = '{category}'
        """

    print("=" * 70)
    print("[NFT SEARCH]")
    print("Category:", repr(category))
    print("SQL:")
    print(query)
    print("=" * 70)

    try:
        ducks = conn.execute(query).fetchall()
        error = None

    except sqlite3.Error as e:
        print("[SQLITE ERROR]", e)

        ducks = []
        error = str(e)

    finally:
        conn.close()

    return render_template(
        "index.html",
        ducks=ducks,
        category=category,
        error=error
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5555")),
        debug=False
    )