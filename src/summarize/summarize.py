from collections import defaultdict
from datetime import datetime
import os
import sqlite3

connection = sqlite3.connect('jason.db')


def main():
    db_path = "out/output.db"
    summarize_messages_by_contact(db_path)


def summarize_messages_by_contact(db_path: str):
    """
    This function will take a path to the SQLite database and
    summarize the messages by contact and by month.
    
    Args:
        db_path: The path to the SQLite database.
    """
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"The database file {db_path} does not exist.")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # First we're gonna get a list of the contacts
    cursor.execute("SELECT phone_number, first_name, last_name, imessage_handle_id FROM contacts WHERE imessage_handle_id IS NOT NULL")    
    contacts = cursor.fetchall()

    print(contacts)

    # Now we're gonna get the messages for each contact
    # We need to query the messages table by imessage_handle_id
    for contact in contacts[:1]:
        cursor.execute("SELECT text, date_time, is_from_me FROM messages WHERE handle_id = ?", (contact[3],))
        messages = cursor.fetchall()
        for msg in messages:
            print(msg)


def partition_messages_by_month(messages_vec, contact_name) -> list:
    """
    This function will take a vector of messages and partition them by month.
    It will then return a list of indexes where each index represents the start of a new month.
    This is so that we don't have to copy the entire vector of messages for each month each time.

    Args:
        messages_vec: A sorted vector of messages in descending order.
        contact_name: The name of the contact.
    """
    month_starts = []
    current_month = None

    # Date time looks like this:
    # 2025-04-24 15:05:11.000000

    for i, msg in enumerate(messages_vec):
        msg_date = datetime.fromtimestamp(msg['date_time'])
        msg_month = msg_date.strftime('%Y-%m')

        if msg_month != current_month:
            month_starts.append(i)
            current_month = msg_month

    return month_starts

if __name__ == "__main__":
    main()