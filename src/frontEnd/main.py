# src/frontEnd/main.py
import IMessageDatabase
import os

def main():
    # Define the paths to your test data files.
    # Assumes a 'res' folder in your project root, like in the Rust project.
    contacts_path = os.path.join(os.getcwd(), "res", "contacts")
    chat_db_path = os.path.join(os.getcwd(), "res", "chat.db")

    print(f"Loading contacts from: {contacts_path}")
    print(f"Loading database from: {chat_db_path}")

    try:
        # 1. Create an instance of your C++ Database class
        db = IMessageDatabase.Database(contacts_path, chat_db_path)

        # 2. Call the main function to load and process all the data
        print("\nPopulating database... (This might take a moment)")
        db.populate_database()

        # 3. Retrieve and print contacts        
        db.save_to_sql("output.db")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

    print("\n--- Test Complete ---")


if __name__ == "__main__":
    main()