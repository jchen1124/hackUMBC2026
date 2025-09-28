import sqlite3
import os

def get_recent_conversations(db_path="out/output.db"):
    """
    Fetch the most recent message for each contact from iMessage chat.db.
    
    Args:
        db_path (str): Path to the chat.db SQLite file.
        
    Returns:
        list of dict: Each dict contains contact, last_message, sender, and message_date.
    """
    db_path = os.path.expanduser(db_path)

    # Connect to database
    conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    cursor = conn.cursor()

    query = """
    SELECT
        h.id AS contact,
        m.text AS last_message,
        CASE m.is_from_me WHEN 1 THEN 'You' ELSE h.id END AS sender,
        datetime(m.date / 1000000000 + strftime('%s','2001-01-01'), 'unixepoch') AS message_date
    FROM message m
    JOIN handle h ON m.handle_id = h.ROWID
    WHERE m.date = (
        SELECT MAX(m2.date)
        FROM message m2
        WHERE m2.handle_id = m.handle_id
    )
    GROUP BY h.id
    ORDER BY message_date DESC;
    """

    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    # Format results as list of dicts
    formatted = [
        {
            "contact": row[0],
            "last_message": row[1] if row[1] else "[No Text]",
            "sender": row[2],
            "message_date": row[3]
        }
        for row in results
    ]

    return formatted

get_recent_conversations()