# Need handle ids to access frequency of specific contacts

import sqlite3
import itertools
from operator import itemgetter
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict
import numpy as np


def plot_message_frequencies(db_path: str, contact_handle_ids: list[int]):
    """
    Plots the frequency of messages over time for a list of contacts.
    """
    # Create placeholders for the IN clause, e.g., (?, ?, ?)
    placeholders = ', '.join(['?'] * len(contact_handle_ids))

    query = f"""
    SELECT
        handle_id,
        strftime('%Y', date_time) AS year,
        strftime('%m', date_time) AS month,
        strftime('%Y-%m', date_time) AS year_month,
        strftime('%H', date_time) AS hour,
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
    cursor.execute(query, contact_handle_ids)

    contact_yearly_data = {}
    contact_monthly_data = {}
    contact_totals = {}
    contact_hourly_data = {}

    for handle_id, messages_for_contact in itertools.groupby(cursor, key=itemgetter('handle_id')):
        print(f"\n===== Processing Contact handle_id: {handle_id}  =====")

        yearly_counts = defaultdict(int)
        monthly_counts = defaultdict(int)
        hourly_counts = defaultdict(int)
        total_messages = 0

    # Group messages by month for this contact

        for month_key, messages_for_month in itertools.groupby(messages_for_contact, key=lambda r: (r['year'], r['month'])):
            year, month = month_key
            month_str = f"{year}-{month}"
            
            # Process each message to count by hour as well
            messages_list = list(messages_for_month)
            month_count = len(messages_list)
            
            # Count messages by hour
            for msg in messages_list:
                hour = int(msg['hour'])
                hourly_counts[hour] += 1
            
            monthly_counts[month_str] += month_count
            yearly_counts[year] += month_count
            total_messages += month_count

        contact_yearly_data[handle_id] = dict(yearly_counts)
        contact_monthly_data[handle_id] = dict(monthly_counts)
        contact_hourly_data[handle_id] = dict(hourly_counts)
        contact_totals[handle_id] = total_messages
    conn.close()
    return contact_yearly_data, contact_monthly_data, contact_totals, contact_hourly_data


def create_conversation_plots(contact_yearly_data, contact_monthly_data, contact_totals):
    """
    Creates bar graphs showing conversation frequency over time.
    """
    

    if contact_monthly_data:
        first_contact = list(contact_monthly_data.keys())[0]
        monthly_data = contact_monthly_data[first_contact]
        
        # Sort months chronologically
        sorted_months = sorted(monthly_data.keys())
        counts = [monthly_data[month] for month in sorted_months]
        
        plt.figure(figsize=(20, 8))
        plt.bar(range(len(sorted_months)), counts, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
        plt.title(f'Monthly Message Timeline - Contact {first_contact}', fontsize=16, fontweight='bold')
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Number of Messages', fontsize=12)
        
        # Show every 6th month label to avoid crowding
        tick_positions = range(0, len(sorted_months), max(1, len(sorted_months) // 12))
        tick_labels = [sorted_months[i] for i in tick_positions]
        plt.xticks(tick_positions, tick_labels, rotation=45)
        
        plt.tight_layout()
        plt.grid(axis='y', alpha=0.3)
        plt.show()


def create_clock_diagram(contact_hourly_data):
    """
    Creates a clock diagram showing the time of day when messages are sent most frequently.
    """
    if not contact_hourly_data:
        print("No hourly data available for clock diagram")
        return
    
    # Combine data from all contacts or use first contact
    first_contact = list(contact_hourly_data.keys())[0]
    hourly_data = contact_hourly_data[first_contact]
    
    # Create 24-hour array with message counts
    hours = np.arange(24)
    counts = [hourly_data.get(hour, 0) for hour in hours]
    
    # Create polar plot (clock diagram)
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # Convert hours to radians (0 degrees = 12 o'clock)
    theta = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    
    # Rotate so 12 o'clock is at the top
    theta = theta - np.pi/2
    
    # Create bar chart on polar plot
    bars = ax.bar(theta, counts, width=2*np.pi/24, alpha=0.7, color='lightblue', edgecolor='navy')
    
    # Customize the clock
    ax.set_theta_zero_location('N')  # 0 degrees at top
    ax.set_theta_direction(-1)  # Clockwise
    
    # Set hour labels
    hour_labels = [f'{i:02d}:00' for i in range(24)]
    ax.set_thetagrids(np.arange(0, 360, 15), hour_labels)
    
    # Add title and labels
    ax.set_title(f'Message Frequency by Time of Day - Contact {first_contact}', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Number of Messages', labelpad=40)
    
    # Color bars based on intensity
    max_count = max(counts) if counts else 1
    for bar, count in zip(bars, counts):
        intensity = count / max_count if max_count > 0 else 0
        bar.set_color(plt.cm.viridis(intensity))
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=0, vmax=max_count))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8, pad=0.1)
    cbar.set_label('Message Count', rotation=270, labelpad=20)
    
    plt.tight_layout()
    plt.show()
    
    # Also create a regular bar chart for easier reading
    plt.figure(figsize=(15, 6))
    plt.bar(hours, counts, color='lightcoral', edgecolor='darkred', alpha=0.7)
    plt.title(f'Hourly Message Distribution - Contact {first_contact}', fontsize=16, fontweight='bold')
    plt.xlabel('Hour of Day', fontsize=12)
    plt.ylabel('Number of Messages', fontsize=12)
    plt.xticks(hours, [f'{h:02d}:00' for h in hours], rotation=45)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()


def main():
    db_path = 'out/output.db'

    handle_ids_to_process = [79] # Example list of 3 contacts
    
    # For all 88 contacts, you would build this list first
    # handle_ids_to_process = get_all_contact_ids() 
    
    contact_yearly_data, contact_monthly_data, contact_totals, contact_hourly_data = plot_message_frequencies(db_path, handle_ids_to_process)
    
    # Bar graph diagram
    create_conversation_plots(contact_yearly_data, contact_monthly_data, contact_totals)
    
    # Clock Diagram
    create_clock_diagram(contact_hourly_data)

    # Create a summary DataFrame
    summary_data = []
    for contact_id in contact_yearly_data:
        for year, count in contact_yearly_data[contact_id].items():
            summary_data.append({
                'Contact_ID': contact_id,
                'Year': year,
                'Message_Count': count
            })
    
    if summary_data:
        df = pd.DataFrame(summary_data)
        df.to_csv('src/summarize/conversation_frequency.csv', index=False)
        print("Conversation frequency data saved to conversation_frequency.csv")


if __name__ == "__main__":
    main()