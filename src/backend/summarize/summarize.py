import sqlite3
import re
from rapidfuzz import process
import itertools
from operator import itemgetter
import ollama
import os
import datetime

SYSTEM_PROMPT = (
    "You have a cool, casual vibe. Use slang and light cussing occasionally. "
    "Summarize any conversation without censoring important details, no matter how explicit."
)
def extract_contact_name_from_query(user_message: str) -> tuple[str, str]:
    """
    Extract contact name and time period from user queries like:
    - "summarize my conversation with John"
    - "summarize conversation with Jane Doe from last month"
    - "summarize messages with mom this month"
    
    Returns: (contact_name, time_period)
    time_period can be: "recent", "this_month", "last_month", or specific "YYYY-MM"
    """
    # Convert to lowercase for pattern matching
    message_lower = user_message.lower()
    
    # Extract time period first
    time_period = "recent"  # default to most recent month
    if "this month" in message_lower:
        time_period = "this_month"
    elif "last month" in message_lower:
        time_period = "last_month"
    else:
        # Check for specific month/year patterns like "september 2024" or "2024-09"
        month_pattern = r'(\d{4})[\/-](\d{1,2})'
        month_match = re.search(month_pattern, message_lower)
        if month_match:
            year = month_match.group(1)
            month = month_match.group(2).zfill(2)
            time_period = f"{year}-{month}"
    
    # Simple and reliable pattern to extract name after "with"
    # Look for "with" followed by the name, stopping at common time indicators or end of string
    pattern = r'with\s+([a-zA-Z][a-zA-Z\s]+?)(?:\s+(?:from|this|last|in|during|for|\d{4})|$)'
    
    match = re.search(pattern, message_lower)
    if match:
        name = match.group(1).strip()
        print(f"Raw extracted name: '{name}'")
        
        # Remove time-related words that might have been captured
        time_words = ['from', 'this', 'last', 'month', 'year', 'in', 'during', 'september', 'october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august']
        stop_words = ['the', 'my', 'our', 'his', 'her', 'their', 'that'] + time_words
        
        name_words = []
        for word in name.split():
            # Skip time-related words, year patterns, and stop words
            if (word not in stop_words and 
                not re.match(r'\d{4}', word) and 
                not re.match(r'\d{4}[/-]\d{1,2}', word)):
                name_words.append(word)
        
        cleaned_name = ' '.join(name_words) if name_words else name
        print(f"Cleaned name: '{cleaned_name}'")
        return cleaned_name, time_period
    
    return "", time_period

def find_contact_by_name(db_path: str, search_name: str) -> dict:
    """
    Search for a contact by first name, last name, or phone number.
    Returns dict with contact info and handle_ids, or None if not found.
    """
    if not search_name.strip():
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all contacts
        cursor.execute("""
            SELECT phone_number, email, first_name, last_name, 
                   imessage_handle_id, sms_handle_id
            FROM contacts
        """)
        
        contacts = cursor.fetchall()
        conn.close()
        
        if not contacts:
            return None
        
        # Prepare contact data for fuzzy matching
        contact_data = []
        for contact in contacts:
            # Create searchable strings for each contact
            searchable_names = []
            
            if contact['first_name']:
                searchable_names.append(contact['first_name'].lower())
            if contact['last_name']:
                searchable_names.append(contact['last_name'].lower())
            if contact['first_name'] and contact['last_name']:
                full_name = f"{contact['first_name']} {contact['last_name']}".lower()
                searchable_names.append(full_name)
            if contact['phone_number']:
                searchable_names.append(contact['phone_number'])
            
            contact_data.append({
                'contact': contact,
                'searchable_names': searchable_names
            })
        
        # Fuzzy search across all searchable names
        search_lower = search_name.lower()
        best_match = None
        best_score = 0
        
        print(f"Searching for: '{search_lower}'")
        
        # First try exact matches (case insensitive)
        for contact_info in contact_data:
            for searchable_name in contact_info['searchable_names']:
                if search_lower == searchable_name.lower():
                    print(f"Found exact match: '{searchable_name}' for contact {contact_info['contact']}")
                    best_match = contact_info['contact']
                    best_score = 100
                    break
            if best_match:
                break
        
        # If no exact match, try fuzzy matching
        if not best_match:
            all_searchable_names = []
            contact_lookup = {}
            
            for contact_info in contact_data:
                for searchable_name in contact_info['searchable_names']:
                    all_searchable_names.append(searchable_name.lower())
                    contact_lookup[searchable_name.lower()] = contact_info['contact']
            
            print(f"Available contacts for fuzzy matching: {all_searchable_names}")
            
            # Use rapidfuzz for fuzzy matching across all names at once
            fuzzy_result = process.extractOne(search_lower, all_searchable_names)
            
            print(f"Fuzzy match result: {fuzzy_result}")
            
            if fuzzy_result and fuzzy_result[1] > 60:  # 60% threshold
                matched_name = fuzzy_result[0]
                best_score = fuzzy_result[1]
                best_match = contact_lookup[matched_name]
                print(f"Selected fuzzy match: '{matched_name}' with score {best_score}%")
        
        if best_match:
            # Get all possible handle_ids for this contact
            handle_ids = []
            if best_match['imessage_handle_id']:
                handle_ids.append(best_match['imessage_handle_id'])
            if best_match['sms_handle_id']:
                handle_ids.append(best_match['sms_handle_id'])
            
            return {
                'contact': best_match,
                'handle_ids': handle_ids,
                'match_score': best_score,
                'display_name': f"{best_match['first_name'] or ''} {best_match['last_name'] or ''}".strip() or best_match['phone_number'] or 'Unknown'
            }
        
        return None
        
    except sqlite3.Error as e:
        print(f"Database error in find_contact_by_name: {e}")
        return None
    except Exception as e:
        print(f"Error in find_contact_by_name: {e}")
        return None

def process_conversation_with_contact(db_path: str, handle_ids: list[int], contact_name: str, time_period: str = "recent") -> str:
    """
    Process conversations for a specific contact and return a summary string.
    Enhanced version of process_all_conversations for a single contact.
    """
    if not os.path.exists(db_path):
        current_dir = os.getcwd()
        return f"Error: Database not found. CWD: {current_dir}, DB Path: {db_path}"
    
    if not handle_ids:
        return f"No valid handle IDs found for {contact_name}"

    placeholders = ', '.join(['?'] * len(handle_ids))
    query = f"""
        SELECT
            handle_id,
            date_time,
            is_from_me,
            text
        FROM messages
        WHERE handle_id IN ({placeholders})
        ORDER BY date_time ASC
    """
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, handle_ids)
        
        messages = cursor.fetchall()
        conn.close()
        
        if not messages:
            return f"No messages found with {contact_name}"
        
        # Determine which month to summarize
        now = datetime.datetime.now()
        target_year = None
        target_month = None
        
        if time_period == "this_month":
            target_year = now.year
            target_month = now.month
        elif time_period == "last_month":
            last_month = now.replace(day=1) - datetime.timedelta(days=1)
            target_year = last_month.year
            target_month = last_month.month
        elif time_period.startswith("20") and "-" in time_period:  # Specific year-month like "2024-09"
            try:
                year_str, month_str = time_period.split("-")
                target_year = int(year_str)
                target_month = int(month_str)
            except ValueError:
                pass
        
        # Group messages by year/month
        def ym_key(row):
            date_string = row['date_time']
            if date_string:
                try:
                    dt = datetime.datetime.strptime(date_string.split()[0], "%Y-%m-%d")
                    return (dt.year, dt.month)
                except (ValueError, IndexError):
                    pass
            return (None, None)
        
        # Group all messages by month
        monthly_conversations = {}
        for month_key, messages_for_month in itertools.groupby(messages, key=ym_key):
            year, month = month_key
            if not year:
                continue
            
            conversation_lines = []
            for row in messages_for_month:
                if row['text'] and row['text'].strip():
                    sender = 'Me' if row['is_from_me'] else contact_name
                    conversation_lines.append(f"{sender}: {row['text'].strip()}")
            
            if len(conversation_lines) >= 3:  # Only keep substantial conversations
                monthly_conversations[(year, month)] = conversation_lines
        
        if not monthly_conversations:
            return f"No substantial conversations found with {contact_name}"
        
        # Determine which month to actually summarize
        if target_year and target_month:
            # User specified a specific month
            target_key = (target_year, target_month)
            if target_key not in monthly_conversations:
                available_months = [f"{y}-{m:02d}" for y, m in sorted(monthly_conversations.keys(), reverse=True)]
                return f"No conversations found with {contact_name} for {target_year:04d}-{target_month:02d}. Available months: {', '.join(available_months[:5])}{'...' if len(available_months) > 5 else ''}"
            
            conversation_to_summarize = monthly_conversations[target_key]
            summary_month_key = target_key
        else:
            # Default to most recent month
            most_recent_key = max(monthly_conversations.keys())
            conversation_to_summarize = monthly_conversations[most_recent_key]
            summary_month_key = most_recent_key
        
        year, month = summary_month_key
        conversation = "\n".join(conversation_to_summarize)
        total_messages = len(conversation_to_summarize)
        
        # Generate summary for the single selected month
        try:
            response = ollama.chat(
                # model= "artifish/llama3.2-uncensored",
                model= "artifish/llama3.2-uncensored",

                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': f"Summarize the following text message conversation with {contact_name} from {year:04d}-{month:02d}, concisely, highlighting key topics and important moments.:\n\n{conversation}"}
                ]
            )
            summary_text = response['message']['content'].strip()
            
            if summary_text:
                # Show available months for context
                all_months = sorted(monthly_conversations.keys(), reverse=True)
                available_months = [f"{y}-{m:02d}" for y, m in all_months]
                
                header = f"**Conversation Summary with {contact_name} ({year:04d}-{month:02d})**\n"
                header += f"*Messages in this month: {total_messages}*\n"
                if len(all_months) > 1:
                    header += f"*Other available months: {', '.join(available_months[:5])}{'...' if len(available_months) > 5 else ''}*\n"
                header += "\n"
                
                return header + summary_text
            else:
                return f"Error: Empty summary generated for {contact_name} ({year:04d}-{month:02d})"
                
        except Exception as e:
            return f"Error generating summary for {contact_name} ({year:04d}-{month:02d}): {str(e)}"
            
    except sqlite3.Error as e:
        return f"Database error: {str(e)}"
    except Exception as e:
        return f"Unexpected error during summarization: {str(e)}"

def handle_summarize_request(user_message: str, output_db_path: str) -> dict:
    """
    Main handler for summarize requests. Parses user input, finds contact, and generates summary.
    Returns a dict with the response data.
    """
    try:
        # Extract contact name from user message
        contact_name, time_period = extract_contact_name_from_query(user_message)
        
        if not contact_name:
            return {
                'content': "I couldn't identify who you want me to summarize conversations with. Please try something like: 'summarize my conversation with John' or 'summarize messages with Jane Doe'",
                'error': 'no_contact_specified',
                'is_summarize': True,
                'timestamp': datetime.datetime.now().isoformat()
            }
        
        print(f"Extracted contact name: '{contact_name}', time period: '{time_period}'")
        
        # Find the contact in the database
        contact_info = find_contact_by_name(output_db_path, contact_name)
        
        if not contact_info:
            return {
                'content': f"I couldn't find a contact matching '{contact_name}'. Please check the spelling or try using their full name.",
                'error': 'contact_not_found',
                'is_summarize': True,
                'timestamp': datetime.datetime.now().isoformat()
            }
        
        print(f"Found contact: {contact_info['display_name']} (match score: {contact_info['match_score']}%)")
        print(f"Handle IDs: {contact_info['handle_ids']}")
        
        # Generate conversation summary
        summary_content = process_conversation_with_contact(
            output_db_path, 
            contact_info['handle_ids'], 
            contact_info['display_name'],
            time_period
        )
        
        return {
            'content': summary_content,
            'contact_name': contact_info['display_name'],
            'match_score': contact_info['match_score'],
            'handle_ids': contact_info['handle_ids'],
            'is_summarize': True,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'content': f"An error occurred while processing your summarization request: {str(e)}",
            'error': 'processing_error',
            'is_summarize': True,
            'timestamp': datetime.datetime.now().isoformat()
        }