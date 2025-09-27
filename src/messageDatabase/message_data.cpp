#include "message_data.h"
using namespace std::chrono_literals;

MessageData::MessageData(std::string text, std::chrono::time_point<std::chrono::system_clock> date_time, unsigned int handle_id, bool is_from_me)
    : m_text(text), m_date_time(date_time), m_handle_id(handle_id), m_is_from_me(is_from_me) {}

std::optional<MessageData> MessageData::from_database_row(const SQLite::Statement& query_row) {
    // Get the column value as an integer first
    const int cache_has_attachments_int = query_row.getColumn("cache_has_attachments").getInt();

    // Then, convert the integer to a boolean
    const bool cache_has_attachments = (cache_has_attachments_int != 0);

    // If there are attachments, skip this message for now
    if (cache_has_attachments) {
        return std::nullopt;
    }

    std::optional<std::string> body_opt;

    const auto& text_column = query_row.getColumn("text");
    if (!text_column.isNull()) {
        body_opt = text_column.getString();
    } else {
        const auto& blob_column = query_row.getColumn("attributedBody");
        if (!blob_column.isNull()) {
            const void* blob_data = blob_column.getBlob();
            int blob_size = blob_column.getBytes();
            body_opt = parse_attributedText(blob_data, blob_size);
        }
    }

    if (!body_opt.has_value() || body_opt.value().empty()) {
        std::cerr << "Warning: Attributed string failed to parse message body for row."<< std::endl;
        return std::nullopt;
    }

    if (invalid_imessage_body(body_opt.value())) {
        std::cerr << "Warning: Message body contains invalid iMessage characters, skipping." << std::endl;
        return std::nullopt;
    }

    const long long raw_date = query_row.getColumn("date");
    auto timestamp = convert_apple_timestamp(raw_date);
    const int handle_id = query_row.getColumn("handle_id");
    const bool is_from_me = query_row.getColumn("is_from_me").getInt();

    return MessageData(body_opt.value(), timestamp, handle_id, is_from_me);
}

bool MessageData::invalid_imessage_body(const std::string& text) {
    // The Unicode range U+FFF0 to U+FFFF is encoded in UTF-8 as a 3-byte sequence.
    // The first byte is always 0xEF.
    // The second byte is always 0xBF.
    // The third byte ranges from 0xB0 to 0xBF.
    
    // We can iterate up to length - 2 because we need to read 3 bytes at a time.
    if (text.length() < 3) {
        return false;
    }

    for (size_t i = 0; i <= text.length() - 3; ++i) {
        // To prevent sign extension issues with char, cast to an unsigned type.
        const uint8_t byte1 = static_cast<uint8_t>(text[i]);
        const uint8_t byte2 = static_cast<uint8_t>(text[i+1]);
        const uint8_t byte3 = static_cast<uint8_t>(text[i+2]);

        if (byte1 == 0xEF && byte2 == 0xBF) {
            if (byte3 >= 0xB0 && byte3 <= 0xBF) {
                // Found a character in the U+FFF0 to U+FFFF range.
                return true;
            }
        }
    }

    return false;
}



// It takes a string_view to avoid making unnecessary copies
std::string MessageData::drop_leading_chars(std::string_view sv, int count) {
    auto it = sv.begin();
    for (int i = 0; i < count && it != sv.end(); ++i) {
        ++it;
    }
    return std::string(it, sv.end());
}

std::optional<std::string> MessageData::parse_attributedText(const void* blob, int size) {
    // Treat the raw blob data as a span of bytes for safe access
    std::span<const std::byte> byte_stream{static_cast<const std::byte*>(blob), (size_t)size};

    // Define the start and end patterns
    const std::array<std::byte, 2> start_pattern{std::byte{0x01}, std::byte{0x2b}};
    const std::array<std::byte, 2> end_pattern{std::byte{0x86}, std::byte{0x84}};

    // 1. Find the start pattern
    auto start_it = std::search(byte_stream.begin(), byte_stream.end(), 
                                start_pattern.begin(), start_pattern.end());
    
    // If the start pattern isn't found, parsing fails.
    if (start_it == byte_stream.end()) {
        return std::nullopt;
    }

    // Create a new view of the data that starts *after* the pattern
    std::span<const std::byte> after_start = byte_stream.subspan(start_it - byte_stream.begin() + start_pattern.size());

    // 2. Find the end pattern within the new, smaller view
    auto end_it = std::search(after_start.begin(), after_start.end(), 
                              end_pattern.begin(), end_pattern.end());

    std::span<const std::byte> message_bytes = (end_it == after_start.end()) 
        ? after_start 
        : after_start.subspan(0, end_it - after_start.begin());

    std::string temp_string(reinterpret_cast<const char*>(message_bytes.data()), message_bytes.size());

    // 3. Drop the garbage prefix characters based on the Rust heuristic
    std::string final_string;
    if (temp_string.length() > 0 && (temp_string[0] == '\u0006' || temp_string[0] < 32)) {
         final_string = drop_leading_chars(temp_string, 1);
    }
    else if (temp_string.length() > 2) {
        // This is a more robust check for the "invalid UTF-8" case
        // The Rust code suggests 3 garbage chars in this scenario
        final_string = drop_leading_chars(temp_string, 3);
    } else {
        final_string = temp_string;
    }
    
    // 4. FINAL CHECK: If the resulting string is empty, treat it as a failure.
    if (final_string.empty()) {
        return std::nullopt;
    }

    return final_string;
}


std::chrono::system_clock::time_point MessageData::convert_apple_timestamp(long long apple_timestamp) {
    // Apple's epoch is January 1, 2001, UTC.
    // We define this using C++20's calendar features.
    auto apple_epoch = std::chrono::sys_days{2001y/std::chrono::January/1};

    // The timestamp from the database is in nanoseconds. We need seconds.
    auto seconds_since_epoch = std::chrono::seconds(apple_timestamp / 1000000000LL);

    // The final UTC time is the epoch plus the duration from the database.
    std::chrono::system_clock::time_point utc_time = apple_epoch + seconds_since_epoch;

    return utc_time;
}