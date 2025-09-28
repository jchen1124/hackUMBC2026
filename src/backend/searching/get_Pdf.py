import sqlite3
import os

# Path to iMessage database
db_path = os.path.expanduser("~/Library/Messages/chat.db")

# Connect to the database in read-only mode
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

# Query to list all table names
cursor.execute("SELECT text FROM message")
tables = cursor.fetchall()

print("Tables in chat.db:")
for (table_name,) in tables:
    print(table_name)

conn.close()
