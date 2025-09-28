import sqlite3
import itertools
from operator import itemgetter

def process_all_conversations(db_path: str, contact_handle_ids: list[int]):
    """
    Fetches all messages for a list of contacts in a single query
    and processes them by month.
    """
    # Create placeholders for the IN clause, e.g., (?, ?, ?)
    placeholders = ', '.join(['?'] * len(contact_handle_ids))
    
    query = f"""
        SELECT
            handle_id,
            strftime('%Y', date_time) AS year,
            strftime('%m', date_time) AS month,
            is_from_me,
            text,
            date_time
        FROM
            messages
        WHERE
            handle_id IN ({placeholders})
        ORDER BY
            handle_id, year, month, date_time ASC
    """

    conn = sqlite3.connect(db_path)
    # This makes the cursor return rows that can be accessed by column name
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Execute the single, powerful query
    cursor.execute(query, contact_handle_ids)

    # Group all messages by contact (handle_id)
    for handle_id, messages_for_contact in itertools.groupby(cursor, key=itemgetter('handle_id')):
        print(f"\n===== Processing Contact handle_id: {handle_id} =====")
        
        # Now, group this contact's messages by month
        for month_key, messages_for_month in itertools.groupby(messages_for_contact, key=lambda r: (r['year'], r['month'])):
            year, month = month_key
            print(f"--- Processing messages for {year}-{month} ---")

            conversation_lines = []
            for row in messages_for_month:
                if not row['text'] or not row['text'].strip():
                    continue
                
                prefix = "Me: " if row['is_from_me'] else "Them: "
                conversation_lines.append(f"{row['date_time']}\t{prefix}{row['text']}")
            
            conversation = "\n".join(conversation_lines)
            print(conversation)
            
            # Here is where you would call Ollama for this specific conversation chunk
            # summary = ollama.chat(...)
            # print(f"Summary: ...\n")

    conn.close()


def main():
    db_path = 'out/output.db'
    
    # In a real scenario, you would fetch these from your contacts table
    handle_ids_to_process = [10, 4, 500] # Example list of 3 contacts
    
    # For all 88 contacts, you would build this list first
    # handle_ids_to_process = get_all_contact_ids() 
    
    process_all_conversations(db_path, handle_ids_to_process)


if __name__ == "__main__":
    main()