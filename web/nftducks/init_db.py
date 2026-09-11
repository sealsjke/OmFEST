import sqlite3
import os


DB_PATH = os.environ.get(
    "DB_PATH",
    "/app/data/nftducks.db"
)


def initialize_database():

    os.makedirs(
        os.path.dirname(DB_PATH),
        exist_ok=True
    )

    # Каждый запуск контейнера получает чистую БД
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("[+] Old database removed")

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    # =====================================================
    # NFT DUCKS
    # =====================================================

    cursor.execute("""
        CREATE TABLE ducks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)

    ducks = [

        (
            "Sunny Duck #001",
            "The classic duck. Simple, bright and always happy.",
            "Common"
        ),

        (
            "Rubber Duck #014",
            "A legendary bathroom companion from the old days.",
            "Common"
        ),

        (
            "Beach Duck #027",
            "A duck that spends all day somewhere near the ocean.",
            "Common"
        ),

        (
            "Plush Duck #042",
            "Soft, fluffy and extremely comfortable.",
            "Common"
        ),

        (
            "Cyber Duck #1337",
            "A duck equipped with a mysterious cybernetic implant.",
            "Rare"
        ),

        (
            "Pirate Duck #404",
            "Captain of the seven virtual seas.",
            "Rare"
        ),

        (
            "Samurai Duck #808",
            "A silent warrior carrying an ancient digital blade.",
            "Rare"
        ),

        (
            "Neon Duck #777",
            "A glowing duck from the deepest part of the metaverse.",
            "Rare"
        ),

        (
            "Golden Duck #001",
            "A golden duck owned by collectors around the world.",
            "Legendary"
        ),

        (
            "Diamond Duck #007",
            "One of the rarest ducks ever discovered.",
            "Legendary"
        ),

        (
            "Genesis Duck #000",
            "The first duck. Nobody knows who created it.",
            "Legendary"
        ),

        (
            "Cosmic Duck #999",
            "A duck that supposedly came from another dimension.",
            "Legendary"
        )

    ]

    cursor.executemany(
        """
        INSERT INTO ducks
        (name, description, category)
        VALUES (?, ?, ?)
        """,
        ducks
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
            os.environ.get("FLAG", "OmFEST{n3w_0n3_un10n_1nj3c710n_c00l}"),
        )
    )

    conn.commit()
    conn.close()

    print("[+] Database initialized")
    print("[+] Tables created:")
    print("    - ducks")
    print("    - s3cr3t")


if __name__ == "__main__":
    initialize_database()