"""Tests de connexion a la base de donnees"""

import sqlite3
import os


def test_database_connection():
    """Tests pour verifier les operations de base."""
    db_path = os.getenv("DATABASE_URL", "oxygen.db")

    # 1. Connexion
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 2. Creation d'une table temporaire
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, value TEXT)"
    )

    # 3. Insertion
    cursor.execute("INSERT INTO test_table (value) VALUES ('hello')")
    conn.commit()

    # 4. Lecture
    cursor.execute("SELECT value FROM test_table WHERE id = 1")
    result = cursor.fetchone()

    conn.close()

    # 5. Verification
    assert result[0] == "hello"
