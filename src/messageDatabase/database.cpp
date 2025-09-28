#include "database.h"
#include <iostream>
#include <fstream>
#include <memory>
#include <unordered_map>
#include <algorithm>
#include <plist/plist++.h>
#include <SQLiteCpp/Transaction.h> // <-- ADD THIS INCLUDE for SQLite::Transaction

// We need the C header for the memory parsing function and enums
extern "C" {
#include <plist/plist.h>
}

namespace fs = std::filesystem;

// Helper to safely get a string from a Plist node pointer
std::optional<std::string> get_string(PList::Node* node) {
    if (node && node->GetType() == PLIST_STRING) {
        // Safely cast the generic Node* to a String* to access its value
        if (auto* string_node = dynamic_cast<PList::String*>(node)) {
            return string_node->GetValue();
        }
    }
    return std::nullopt;
}

// Helper function to normalize phone numbers
std::string normalize_phone(std::string phone) {
    // Remove common formatting characters
    phone.erase(std::remove_if(phone.begin(), phone.end(),
        [](char c) { return std::isspace(c) || c == '(' || c == ')' || c == '-'; }), phone.end());

    // If number starts with '1' but not '+1', remove the '1' before adding '+1'
    if (phone.rfind("1", 0) == 0 && phone.length() > 1) {
        phone.erase(0, 1);
    }
    
    // Add US country code if missing
    if (!phone.empty() && phone[0] != '+') {
        phone.insert(0, "+1");
    }
    return phone;
}

Database::Database(std::string pList_folder, std::string chat_db_path)
    : m_pList_folder(pList_folder),
      m_chat_db_path(chat_db_path),
      m_db(chat_db_path, SQLite::OPEN_READONLY)
{}

std::optional<Contact> Database::parse_plist_file(const fs::path& file_path) {
    plist_t root_c_node = nullptr;
    try {
        std::ifstream file(file_path, std::ios::binary);
        if (!file) return std::nullopt;
        std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

        plist_from_memory(content.c_str(), content.length(), &root_c_node, nullptr);
        if (!root_c_node) return std::nullopt;

        if (plist_get_node_type(root_c_node) != PLIST_DICT) {
            plist_free(root_c_node);
            return std::nullopt;
        }

        std::unique_ptr<PList::Dictionary> dict{new PList::Dictionary(root_c_node)};

        // --- CORRECTED LINES ---
        // Dereference the unique_ptr with (*) before using the [] operator
        PList::Node* first_name_node = (*dict)["First"];
        PList::Node* last_name_node = (*dict)["Last"];
        
        std::optional<std::string> first_name = get_string(first_name_node);
        std::optional<std::string> last_name = get_string(last_name_node);
        std::optional<std::string> phone;

        PList::Node* phone_node = (*dict)["Phone"];
        // --- END CORRECTIONS ---

        if (auto* phone_dict = dynamic_cast<PList::Dictionary*>(phone_node)) {
            PList::Node* values_node = (*phone_dict)["values"];
            if (auto* values_array = dynamic_cast<PList::Array*>(values_node)) {
                if (values_array->GetSize() > 0) {
                    phone = get_string((*values_array)[0]);
                }
            }
        }

        if (phone.has_value()) {
            return Contact(phone, std::nullopt, first_name, last_name, std::nullopt, std::nullopt);
        }

    } catch (const std::exception& e) {
        if (root_c_node) {
            plist_free(root_c_node);
        }
        std::cerr << "Warning: Plist parsing error in " << file_path << ": " << e.what() << std::endl;
    }
    
    return std::nullopt;
}

void Database::populate_contacts() {
    for (const auto& entry : fs::recursive_directory_iterator(m_pList_folder)) {
        if (entry.is_regular_file() && entry.path().extension() == ".abcdp") {
            if (auto contact_opt = parse_plist_file(entry.path())) {
                m_contacts.push_back(contact_opt.value());
            }
        }
    }
    std::cout << "Successfully populated " << m_contacts.size() << " contacts from plists." << std::endl;

    // After loading from plists, enrich them with database info
    enrich_contacts_from_db();
}

void Database::enrich_contacts_from_db() {
    struct HandleInfo {
        std::optional<unsigned int> imessage_id;
        std::optional<unsigned int> sms_id;
    };

    std::unordered_map<std::string, HandleInfo> handle_map;

    SQLite::Statement query(m_db, "SELECT ROWID, id, service FROM handle");
    
    while (query.executeStep()) {
        unsigned int handle_id = query.getColumn(0).getUInt();
        std::string identifier = query.getColumn(1).getString();
        std::string service = query.getColumn(2).getString();

        // **NORMALIZE IT IMMEDIATELY**
        if (identifier.find('@') == std::string::npos) { // It's a phone number
            identifier = normalize_phone(identifier);
        }

        // Now the map key is guaranteed to be in the same format
        if (service == "iMessage") {
            handle_map[identifier].imessage_id = handle_id;
        } else if (service == "SMS") {
            handle_map[identifier].sms_id = handle_id;
        }
    }

    // Now, the lookup will be reliable because both the contact's phone
    // and the map's key have been normalized in the exact same way.
    for (auto& contact : m_contacts) {
        if (contact.m_phone_number.has_value()) {
            // No need to normalize here again, since it's already clean
            auto it = handle_map.find(contact.m_phone_number.value());
            if (it != handle_map.end()) {
                contact.m_imessage_handle_id = it->second.imessage_id;
                contact.m_sms_handle_id = it->second.sms_id;
            }
        }
    }
    std::cout << "Successfully enriched contacts with handle IDs from chat.db." << std::endl;
}

void Database::populate_messages() {
    try {
        // Use the new, more robust query
        SQLite::Statement query(m_db, "SELECT "
                    "T1.text, T1.attributedBody, T1.date, T1.is_from_me, "
                    "T1.cache_has_attachments, T1.is_audio_message, T1.was_data_detected, T1.item_type, "
                    "CASE "
                        "WHEN T1.is_from_me = 1 THEN ( "
                            "SELECT T4.handle_id "
                            "FROM chat_handle_join AS T4 "
                            "WHERE T4.chat_id = T2.chat_id AND T4.handle_id != 0 "
                            "LIMIT 1 "
                        ") "
                        "ELSE T1.handle_id "
                    "END AS effective_handle_id "
                    "FROM message AS T1 "
                    "JOIN chat_message_join AS T2 ON T1.ROWID = T2.message_id "
                    "JOIN ( "
                        "SELECT chat_id FROM chat_handle_join "
                        "GROUP BY chat_id "
                        "HAVING COUNT(handle_id) <= 2 "
                    ") AS T3 ON T2.chat_id = T3.chat_id "
                    "WHERE T1.balloon_bundle_id IS NULL");
            
        while (query.executeStep()) {
            if (auto msg_opt = MessageData::from_database_row(query)) {
                m_messages.push_back(msg_opt.value());
            }
        }
        std::cout << "Successfully populated " << m_messages.size() << " messages from chat.db." << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Error populating messages: " << e.what() << std::endl;
    }
}

void Database::populate_database() {
    populate_contacts();
    populate_messages();
}


void Database::save_to_sql(const std::string& output_path) {
    try {
        SQLite::Database db(output_path, SQLite::OPEN_READWRITE | SQLite::OPEN_CREATE);
        std::cout << "Opened new database for writing at: " << output_path << std::endl;

        SQLite::Transaction transaction(db);

        db.exec("DROP TABLE IF EXISTS contacts");
        db.exec("CREATE TABLE contacts ("
                "phone_number TEXT, "
                "email TEXT, "
                "first_name TEXT, "
                "last_name TEXT, "
                "imessage_handle_id INTEGER, "
                "sms_handle_id INTEGER)");

        db.exec("DROP TABLE IF EXISTS messages");
        db.exec("CREATE TABLE messages ("
                "text TEXT, "
                "date_time TEXT, "
                "handle_id INTEGER, "
                "is_from_me INTEGER)");

        SQLite::Statement contact_query(db, "INSERT INTO contacts VALUES (?, ?, ?, ?, ?, ?)");
        SQLite::Statement message_query(db, "INSERT INTO messages VALUES (?, ?, ?, ?)");

        // Insert all contacts
        for (const auto& contact : m_contacts) {
            // --- CORRECTED BINDING LOGIC ---
            // Use if/else for optional values
            if (contact.m_phone_number.has_value()) contact_query.bind(1, contact.m_phone_number.value()); else contact_query.bind(1);
            if (contact.m_email.has_value()) contact_query.bind(2, contact.m_email.value()); else contact_query.bind(2);
            if (contact.m_first_name.has_value()) contact_query.bind(3, contact.m_first_name.value()); else contact_query.bind(3);
            if (contact.m_last_name.has_value()) contact_query.bind(4, contact.m_last_name.value()); else contact_query.bind(4);
            if (contact.m_imessage_handle_id.has_value()) contact_query.bind(5, (int)contact.m_imessage_handle_id.value()); else contact_query.bind(5);
            if (contact.m_sms_handle_id.has_value()) contact_query.bind(6, (int)contact.m_sms_handle_id.value()); else contact_query.bind(6);
            
            contact_query.exec();
            contact_query.reset();
        }
        std::cout << "Inserted " << m_contacts.size() << " contacts." << std::endl;

        // Insert all messages
        for (const auto& message : m_messages) {
            auto formatted_time = std::format("{:%Y-%m-%d %H:%M:%S}", message.get_date_time());

            message_query.bind(1, message.get_text());
            message_query.bind(2, formatted_time);
            message_query.bind(3, (int)message.get_handle_id());
            message_query.bind(4, message.is_from_me());

            message_query.exec();
            message_query.reset();
        }
        std::cout << "Inserted " << m_messages.size() << " messages." << std::endl;

        transaction.commit();
        std::cout << "Database saved successfully." << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error saving to SQL database: " << e.what() << std::endl;
    }
}
