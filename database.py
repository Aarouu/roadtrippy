import sqlite3

DB_NAME = "roads.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Favorite roads
    c.execute("""
        CREATE TABLE IF NOT EXISTS favorite_roads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            geometry TEXT NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Ratings
    c.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            road_id INTEGER,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            UNIQUE(user_id, road_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(road_id) REFERENCES favorite_roads(id)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
