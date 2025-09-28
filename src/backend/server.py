import sqlite3
import itertools
from operator import itemgetter
import ollama
import os
import datetime

# --- ADD FLASK IMPORTS ---
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- INITIALIZE THE FLASK APP ---
app = Flask(__name__)
# Allow requests from your React app's origin (http://localhost:3000)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# This is the overall instruction for the AI model, defining its role.
SYSTEM_PROMPT = "You are an assistant that summarizes conversations. Summarize the following conversation concisely, highlighting key topics and important moments."

def apple_time_to_datetime(apple_time: int) -> str:
    """
    Convert Apple's iMessage timestamp (nanoseconds since 2001-01-01) to a
    human-readable string. Returns an empty string if conversion fails.
    """
    # Explicitly check for invalid timestamp values (0, None, etc.)
    if not apple_time or apple_time <= 0:
        return ""
    try:
        # Create the datetime object and format it as a string.
        dt_object = datetime.datetime(2001, 1, 1) + datetime.timedelta(seconds=apple_time / 1e9)
        return dt_object.strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError) as e:
        # Log the error for debugging instead of failing silently.
        print(f"Warning: Could not convert timestamp '{apple_time}'. Error: {e}")
        return ""

def preprocess_messages(cursor: sqlite3.Cursor):
    """
    Generator that yields a dictionary for each row with a pre-calculated datetime object.
    This avoids redundant date calculations later on.
    """
    for row in cursor:
        dt_str = apple_time_to_datetime(row['date'])
        dt_obj = None
        if dt_str:
            try:
                dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"Warning: Failed to parse generated date string: {dt_str}")
        
        # Yield a consistent dictionary structure for easier processing.
        yield {
            'handle_id': row['handle_id'],
            'is_from_me': row['is_from_me'],
            'text': row['text'],
            'datetime': dt_obj,
        }

def process_all_conversations(db_path: str, contact_handle_ids: list[int]) -> str:
    """
    Process conversations for given contacts and return a summary string.
    This function is designed to always return a string, never raising an exception.
    """
    if not os.path.exists(db_path):
        return f"Error: Messages database not found at '{db_path}'. Make sure you're running this on macOS and the path is correct."
    
    # Create a string of '?' placeholders for the SQL query.
    placeholders = ', '.join(['?'] * len(contact_handle_ids))
    
    # CORRECTED SQL QUERY:
    # - Using the correct table name 'message' (not 'messages').
    # - Using the correct date column 'date' (not 'date_time').
    query = f"""
        SELECT
            handle_id,
            date,
            is_from_me,
            text
        FROM message
        WHERE handle_id IN ({placeholders})
            AND text IS NOT NULL
            AND text != ''
        ORDER BY handle_id, date ASC
    """
    
    try:
        # Open the database in read-only mode to prevent accidental writes.
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, contact_handle_ids)
        
        summaries = []
        
        # Use the preprocessor generator for efficiency.
        processed_messages = preprocess_messages(cursor)
        
        # First, group all messages by their contact (handle_id).
        for handle_id, messages_for_contact in itertools.groupby(processed_messages, key=itemgetter('handle_id')):
            contact_summaries = []
            
            # Define key function for grouping by year-month using the pre-calculated datetime object.
            def ym_key(msg):
                if msg['datetime']:
                    return (msg['datetime'].year, msg['datetime'].month)
                return (None, None)
            
            # Second, group that contact's messages by month.
            for month_key, messages_for_month in itertools.groupby(messages_for_contact, key=ym_key):
                year, month = month_key
                if not year:
                    continue
                
                # Convert the iterator to a list to check its length and process it.
                message_list = list(messages_for_month)
                
                # Only summarize if the conversation has a minimum number of messages.
                if len(message_list) < 3:
                    continue
                
                conversation_lines = [
                    f"{'Me' if msg['is_from_me'] else 'Them'}: {msg['text'].strip()}"
                    for msg in message_list if msg['text'] and msg['text'].strip()
                ]
                
                conversation = "\n".join(conversation_lines)
                
                try:
                    # Call the AI model with both system and user prompts.
                    response = ollama.chat(
                        model="llama3",
                        messages=[
                            {'role': 'system', 'content': SYSTEM_PROMPT},
                            {'role': 'user', 'content': f"Summarize this conversation from {year}-{month:02d}:\n\n{conversation}"}
                        ]
                    )
                    
                    summary_text = response['message']['content'].strip()
                    if summary_text:
                        contact_summaries.append(f"**{year}-{month:02d} Summary:**\n{summary_text}")
                        
                except Exception as e:
                    contact_summaries.append(f"**{year}-{month:02d}:** Error generating summary - {str(e)}")
            
            if contact_summaries:
                summaries.append(f"**Contact {handle_id} Conversations:**\n\n" + "\n\n\n".join(contact_summaries))
        
        conn.close()
        
        if summaries:
            return "\n\n\n".join(summaries)
        else:
            return "No conversations found with enough messages to summarize. Try checking different contact IDs or ensure there are sufficient messages."
            
    except sqlite3.Error as e:
        return f"Database error: {str(e)}"
    except Exception as e:
        return f"Unexpected error during summarization: {str(e)}"

# --- CREATE THE API ENDPOINT ---
# This is the new function that will handle requests from your React app
@app.route("/api/ai-response", methods=["POST"])
def handle_ai_response():
    # Get the JSON data sent from the frontend
    data = request.get_json()
    user_message = data.get('message')

    print(f"Received message from frontend: {user_message}")

    # --- TODO: Integrate your AI logic here ---
    # For now, we can call your existing main function as a placeholder.
    # In the future, you'll want to use the `user_message` to decide what to do.
    
    # For example, if the user asks to "summarize", call main().
    if "summarize" in user_message.lower():
        ai_content = main()
        # The main() function already handles DB errors and returns a string
        return jsonify({
            'content': ai_content,
            'is_summarize': True,
            'is_message': False,
            'timestamp': datetime.datetime.now().isoformat()
        })
    else:
        # Placeholder for other AI interactions
        return jsonify({
            'content': f"I received your message: '{user_message}', but I can only summarize for now.",
            'is_summarize': False,
            'is_message': True,
            'timestamp': datetime.datetime.now().isoformat()
        })


def main() -> str:
    """Main function that orchestrates the summarization and returns a string."""
    # This path is relative to the root, which is correct now.
    db_path = os.path.join("out", "output.db")
    
    # Example handle IDs
    handle_ids_to_process = [10]
    
    result = process_all_conversations(db_path, handle_ids_to_process)
    return result

# --- RUN THE SERVER ---
# This block makes the server start when you run `python src/backend/server.py`
if __name__ == "__main__":
    # The host='0.0.0.0' makes it accessible from your network
    # The port=5000 matches what your frontend is trying to call
    app.run(host='0.0.0.0', port=5000, debug=True)