import sqlite3
import os
from rapidfuzz import process

def search_imessages(query: str, top_k: int = 5):
    """
    Performs a fuzzy search for messages in the database using rapidfuzz.
    Always returns a string, either with results or a 'not found' message.
    """
    # Clean the query to remove the "search" keyword for better matching
    cleaned_query = query.lower().replace('search', '').strip()

    try:
        # ---------- 1. Connect to the database and load all messages ----------
        db_path = os.path.join("out", "output.db")
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        # Fetching as a dictionary makes it easier to work with the data later
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # We need to fetch all messages to perform the fuzzy search in memory.
        cursor.execute("""
            SELECT date_time, text 
            FROM messages 
            WHERE text IS NOT NULL AND text != ''
        """)
        
        all_messages = cursor.fetchall()
        conn.close()

        if not all_messages:
            return "There are no messages in the database to search."

        # ---------- 2. Perform fuzzy search in memory ----------
        # Create a dictionary mapping the message text to the full row object
        # This allows us to easily retrieve the date after finding a text match
        message_map = {msg['text']: msg for msg in all_messages}
        
        # 'process.extract' finds the best matches from a list of choices.
        # It returns a list of tuples: (text, score, original_index)
        matches = process.extract(cleaned_query, message_map.keys(), limit=top_k, score_cutoff=60)

        if not matches:
            return f"No messages found that closely match your query: '{query}'"

        # ---------- 3. Format results as readable strings ----------
        readable_results = []
        for match_text, score, _ in matches:
            original_message = message_map[match_text]
            date_str = original_message['date_time'].split(' ')[0]  # Get 'YYYY-MM-DD'
            readable_results.append(f"{date_str}: {match_text}")

        return "\n\n".join(readable_results)

    except sqlite3.Error as e:
        print(f"Database error in search_imessages: {e}")
        return f"A database error occurred while searching for messages: {e}"
    except Exception as e:
        print(f"An unexpected error occurred in search_imessages: {e}")
        return f"An unexpected error occurred: {e}"

# --- Example Usage ---
if __name__ == "__main__":
    # You may need to install the fuzzy search library first:
    # pip install rapidfuzz
    user_query = input("Enter your search query: ")
    top_results = search_imessages(user_query, top_k=10)
    print("\nTop matching messages:")
    print(top_results)

