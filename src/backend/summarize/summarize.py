import sqlite3
import itertools
from operator import itemgetter
import ollama
import os
import datetime

SYSTEM_PROMPT = "You are an assistant that summarizes conversations. Summarize the following conversation concisely, highlighting key topics and important moments."

def apple_time_to_datetime(apple_time: int) -> str:
    """Convert Apple's iMessage timestamp to human-readable string."""
    try:
        if apple_time and apple_time > 0:
            return (datetime.datetime(2001, 1, 1) +
                    datetime.timedelta(seconds=apple_time/1e9)).strftime("%Y-%m-%d %H:%M:%S")
    except:
        pass
    return ""

def process_all_conversations(db_path: str, contact_handle_ids: list[int]) -> str:
    """
    Process conversations by year/month for given contacts and return a summary string.
    Always returns a string, never None.
    """
    if not os.path.exists(db_path):
        current_dir = os.getcwd()
        return f"Error: Messages database not found. Make sure you're running this on macOS with Messages app enabled. {current_dir}, DB Path: {db_path}"
    
    placeholders = ', '.join(['?'] * len(contact_handle_ids))
    query = f"""
        SELECT
            handle_id,
            date_time,
            is_from_me,
            text
        FROM messages
        WHERE handle_id IN ({placeholders})
            AND text IS NOT NULL
            AND text != ''
        ORDER BY handle_id, date_time ASC
    """
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, contact_handle_ids)
        
        summaries = []
        total_conversations = 0
        
        # Group by contact
        for handle_id, messages_for_contact in itertools.groupby(cursor, key=itemgetter('handle_id')):
            contact_summaries = []
            
            # Group by year-month using converted datetime
            def ym_key(row):
                dt_str = apple_time_to_datetime(row['date'])
                if dt_str:
                    try:
                        dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                        return (dt.year, dt.month)
                    except:
                        pass
                return (None, None)
            
            for month_key, messages_for_month in itertools.groupby(messages_for_contact, key=ym_key):
                year, month = month_key
                if not year:
                    continue
                
                conversation_lines = []
                message_count = 0
                
                for row in messages_for_month:
                    if row['text'] and row['text'].strip():
                        prefix = "Me" if row['is_from_me'] else "Them"
                        conversation_lines.append(f"{prefix}: {row['text'].strip()}")
                        message_count += 1
                
                if message_count < 3:
                    continue
                
                conversation = "\n".join(conversation_lines)
                
                try:
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
                        total_conversations += 1
                        
                except Exception as e:
                    contact_summaries.append(f"**{year}-{month:02d}:** Error generating summary - {str(e)}")
            
            if contact_summaries:
                summaries.append(f"**Contact {handle_id} Conversations:**\n\n" + "\n\n\n".join(contact_summaries))
        
        conn.close()
        
        if summaries:
            return "\n\n\n".join(summaries)
        else:
            return "No conversations found with enough messages to summarize. Try checking different contact IDs or ensure there are sufficient messages in the database."
            
    except sqlite3.Error as e:
        return f"Database error: {str(e)}"
    except Exception as e:
        return f"Unexpected error during summarization: {str(e)}"

def main() -> str:
    """
    Main function that always returns a string summary.
    """
    db_path = os.path.expanduser("../../../out/output.db")
    
    # Example handle IDs - replace with actual ones from your DB
    handle_ids_to_process = [10]
    
    try:
        return process_all_conversations(db_path, handle_ids_to_process)
    except Exception as e:
        return f"Critical error in summarization: {str(e)}"

if __name__ == "__main__":
    print(main())
