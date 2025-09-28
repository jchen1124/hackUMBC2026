# file: inspect_messages.py
import sqlite3
import os

def list_message_columns(db_path: str):
    """
    Connects to the iMessage chat.db and lists all column names in the 'message' table.
    """
    db_path = os.path.expanduser(db_path)

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # PRAGMA returns info about columns in the table
    cursor.execute("PRAGMA table_info(message)")
    columns = cursor.fetchall()

    print("📋 Columns in 'message' table:")
    for col in columns:
        # col tuple = (cid, name, type, notnull, dflt_value, pk)
        print(f"- {col[1]} ({col[2]})")

    conn.close()

if __name__ == "__main__":
    # Path to your Messages DB on macOS
    db_path = "out/output.db"
    list_message_columns(db_path)
