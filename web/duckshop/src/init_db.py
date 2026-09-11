import sqlite3
import os


DB_PATH = os.environ.get(
    "DB_PATH",
    "/app/data/duckshop.db"
)


def initialize_database():

    os.makedirs(
        os.path.dirname(DB_PATH),
        exist_ok=True
    )

    
    if os.path.exists(DB_PATH):

        os.remove(DB_PATH)

        print("[+] Old database removed")

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    # =====================================================
    # USERS
    # =====================================================

    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # =====================================================
    # PRODUCTS
    # =====================================================

    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    products = [

        (
            "Rubber Duck",
            "Classic yellow rubber duck for your bathroom."
        ),

        (
            "Hacker Duck",
            "A mysterious duck wearing a black hoodie."
        ),

        (
            "Golden Duck",
            "An expensive golden duck for collectors."
        ),

        (
            "Pirate Duck",
            "A pirate duck searching for treasure."
        ),

        (
            "Cyber Duck",
            "A duck designed for cybersecurity enthusiasts."
        ),

        (
            "Developer Duck",
            "The perfect companion for long coding sessions."
        ),

        (
            "Detective Duck",
            "A duck that always finds the truth."
        ),

        (
            "Red Duck",
            "A bright red duck with a serious expression."
        ),

        (
            "Space Duck",
            "A duck that has traveled beyond Earth."
        ),

        (
            "Ninja Duck",
            "A silent duck trained in the ancient arts."
        )

    ]

    cursor.executemany(
        """
        INSERT INTO products
        (name, description)
        VALUES (?, ?)
        """,
        products
    )

    # =====================================================
    # DEFAULT USER
    # =====================================================

    cursor.execute(
        """
        INSERT INTO users
        (username, password)
        VALUES (?, ?)
        """,
        (
            "duckadmin",
            "duck123"
        )
    )

    # =====================================================
    # SECRET TABLE
    # =====================================================

    cursor.execute("""
        CREATE TABLE s3cr3t (
            fl4g TEXT NOT NULL
        )
    """)

    cursor.execute(
        """
        INSERT INTO s3cr3t (fl4g)
        VALUES (?)
        """,
        (
            os.environ.get("FLAG", "OmFEST{un10n_b4s3d_duck_sqli}"),
        )
    )

    conn.commit()

    conn.close()

    print("[+] Database initialized")
    print("[+] Tables:")
    print("    - users")
    print("    - products")
    print("    - s3cr3t")


if __name__ == "__main__":
    initialize_database()