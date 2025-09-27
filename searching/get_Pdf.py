import sqlite3
import os

# Path to iMessage database
db_path = os.path.expanduser("~/Library/Messages/chat.db")

# Connect to the database in read-only mode
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

# Query for PDF attachments
query = """
SELECT attachment.filename
FROM attachment
WHERE attachment.filename LIKE '%.pdf';
"""

cursor.execute(query)
rows = cursor.fetchall()

with open("pdf_files.txt", "w") as txt_file:
    for (filename,) in rows:
        txt_file.write(filename + "\n")

conn.close()