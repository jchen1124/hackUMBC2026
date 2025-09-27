#pragma once
#include <string>
#include <vector>
#include <optional>
#include <SQLiteCpp/Database.h>
#include <filesystem>
#include "contact.h"
#include "message_data.h"

class Database {
private:
    std::string m_pList_folder;
    std::string m_chat_db_path;
    SQLite::Database m_db;

    std::vector<Contact> m_contacts;
    std::vector<MessageData> m_messages;



public:
    Database(std::string pList_folder, std::string chat_db_path);
    void populate_database();
    std::optional<Contact> parse_plist_file(const std::filesystem::path& file_path);

    // Add getters so Python can access the data
    const std::vector<Contact>& get_contacts() const { return m_contacts; }
    const std::vector<MessageData>& get_messages() const { return m_messages; }
        // Private helpers
    void populate_contacts();
    void enrich_contacts_from_db(); // You should add this from our last conversation
    
    // New helper for populating messages
    void populate_messages();

    void save_to_sql(const std::string& output_path);
};