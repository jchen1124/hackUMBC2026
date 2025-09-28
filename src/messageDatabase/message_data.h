#pragma once
#include <string>
#include <chrono>  
#include <vector>
#include <optional>
#include <iostream>
#include <string_view>
#include <span>
#include <algorithm>

#include <SQLiteCpp/Statement.h>
#include <SQLiteCpp/Column.h>

class MessageData
{
private:
    std::string m_text; // Contains text data
    std::chrono::time_point<std::chrono::system_clock> m_date_time; // Timestamp
    unsigned int m_handle_id; // Handle ID, used for lookup in contacts table
    bool m_is_from_me; // Self explenatory

    // Pirvate because we don't want YOU creating messages out of thin air!
    MessageData(std::string text, std::chrono::time_point<std::chrono::system_clock> date_time, unsigned int handle_id, bool is_from_me);
    
    // These handle text extraction
    static std::optional<std::string> parse_attributedText(const void* blob, int size);
    static std::string drop_leading_chars(std::string_view sv, int count);
    static bool invalid_imessage_body(const std::string& text);

    // This one converts the apple timestamp in the SQL database into something usefull
    static std::chrono::system_clock::time_point convert_apple_timestamp(long long apple_timestamp);


public:
    static std::optional<MessageData> from_database_row(const SQLite::Statement& query_row);

    const std::string& get_text() const { return m_text; }
    const std::chrono::time_point<std::chrono::system_clock>& get_date_time() const { return m_date_time; }
    unsigned int get_handle_id() const { return m_handle_id; }
    bool is_from_me() const { return m_is_from_me; }

};