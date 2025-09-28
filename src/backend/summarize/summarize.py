import sqlite3
import itertools
from operator import itemgetter
import ollama
import os
import datetime

SYSTEM_PROMPT = "You are an assistant that summarizes conversations. Summarize the following conversation concisely, highlighting key topics and important moments."

def process_all_conversations(db_path: str, contact_handle_ids: list[int]) -> str:
    """
    Process conversations by year/month for given contacts and return a summary string.
    Always returns a string.
    """
    if not os.path.exists(db_path):
        current_dir = os.getcwd()
        return f"Error: Database not found. CWD: {current_dir}, DB Path: {db_path}"

    placeholders = ', '.join(['?'] * len(contact_handle_ids))
    # FIXED QUERY: Added the WHERE clause back in to filter by the correct contact IDs.
    query = f"""
        SELECT
            handle_id,
            date_time,
            is_from_me,
            text
        FROM messages
        WHERE handle_id IN ({placeholders})
        ORDER BY handle_id, date_time ASC
    """
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Pass the contact IDs as parameters to the execute method.
        cursor.execute(query, contact_handle_ids)
        
        summaries = []
        
        # Group by contact
        for handle_id, messages_for_contact in itertools.groupby(cursor, key=itemgetter('handle_id')):
            contact_summaries = []
            
            # FIXED DATE HANDLING: This function now directly parses the TEXT 'date_time' column.
            def ym_key(row):
                # The schema shows 'date_time' is TEXT, not a numeric timestamp.
                date_string = row['date_time']
                if date_string:
                    try:
                        # Assuming a common format like 'YYYY-MM-DD HH:MM:SS'
                        dt = datetime.datetime.strptime(date_string.split()[0], "%Y-%m-%d")
                        return (dt.year, dt.month)
                    except (ValueError, IndexError):
                        # Handle potential parsing errors if the date format is unexpected.
                        pass
                return (None, None)
            
            for month_key, messages_for_month in itertools.groupby(messages_for_contact, key=ym_key):
                year, month = month_key
                if not year:
                    continue
                
                conversation_lines = [
                    f"{'Me' if row['is_from_me'] else 'Them'}: {row['text'].strip()}"
                    for row in messages_for_month if row['text'] and row['text'].strip()
                ]
                
                if len(conversation_lines) < 3:
                    continue
                
                conversation = "\n".join(conversation_lines)
                
                try:
                    response = ollama.chat(
                        model="llama3",
                        messages=[
                            {'role': 'system', 'content': SYSTEM_PROMPT},
                            {'role': 'user', 'content': f"Summarize this conversation from {year:04d}-{month:02d}:\n\n{conversation}"}
                        ]
                    )
                    summary_text = response['message']['content'].strip()
                    if summary_text:
                        contact_summaries.append(f"**{year:04d}-{month:02d} Summary:**\n{summary_text}")
                        
                except Exception as e:
                    contact_summaries.append(f"**{year:04d}-{month:02d}:** Error generating summary - {str(e)}")
            
            if contact_summaries:
                summaries.append(f"**Contact {handle_id} Conversations:**\n\n" + "\n\n---\n\n".join(contact_summaries))
        
        conn.close()
        
        return "\n\n".join(summaries) if summaries else "No conversations found with enough messages to summarize."
            
    except sqlite3.Error as e:
        return f"Database error: {str(e)}"
    except Exception as e:
        return f"Unexpected error during summarization: {str(e)}"

def main() -> str:
    """Main function that orchestrates the summarization and returns a string."""
    # FIXED PATH: Use a direct relative path from the project root.
    db_path = os.path.join("out", "output.db")
    
    # Example handle IDs
    handle_ids_to_process = [10]
    
    return process_all_conversations(db_path, handle_ids_to_process)

if __name__ == "__main__":
    print(main())

