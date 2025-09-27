#include "message_data.h"
using namespace std::chrono_literals;

MessageData::MessageData(std::string text, std::chrono::time_point<std::chrono::system_clock> date_time, unsigned int handle_id, bool is_from_me)
    : m_text(text), m_date_time(date_time), m_handle_id(handle_id), m_is_from_me(is_from_me) {}

std::optional<MessageData> MessageData::from_database_row(const SQLite::Statement& query_row) {
    // --- GETTING THE TEXT ---
    // ------------------------
    std::optional<std::string> body_opt;

    // First, try to get text from the 'text' column
    const auto& text_column = query_row.getColumn("text");
    if (!text_column.isNull()) {
        body_opt = text_column.getString();
    }
    // If that fails, try to parse the 'attributedBody' BLOB
    else {
        const auto& blob_column = query_row.getColumn("attributedBody");
        if (!blob_column.isNull()) {
            // Get the BLOB data as a pointer and its size
            const void* blob_data = blob_column.getBlob();
            int blob_size = blob_column.getBytes();

            // Since they are both optional if `parse_attributedText` then this function will be empty too!
            body_opt = parse_attributedText(blob_data, blob_size);
        }
    }

    // If we still don't have a body, print a warning and return an empty optional
    if (!body_opt.has_value()) {
        std::cerr << "Warning: Row found with no body or blob content." << std::endl;
        return std::nullopt; // Use std::nullopt to return an empty optional
    }

    // --- GETTING THE DATE ---
    // ------------------------
    const long long raw_date = query_row.getColumn("date");
    auto timestamp = convert_apple_timestamp(raw_date);

    // --- This is simple  ---
    // -----------------------
    const int handle_id = query_row.getColumn("handle_id");
    const bool is_from_me = query_row.getColumn("is_from_me").getInt();

    return MessageData(body_opt.value(), timestamp, handle_id, is_from_me);
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
    
    // If the start pattern isn't found, we can't proceed.
    if (start_it == byte_stream.end()) {
        std::cerr << "Warning: Start pattern not found in BLOB." << std::endl;
        return std::nullopt;
    }

    // Create a new view of the data that starts *after* the pattern
    std::span<const std::byte> after_start = byte_stream.subspan(start_it - byte_stream.begin() + start_pattern.size());

    // 2. Find the end pattern within the new, smaller view
    auto end_it = std::search(after_start.begin(), after_start.end(), 
                              end_pattern.begin(), end_pattern.end());

    // If the end pattern isn't found, just use the rest of the data.
    // Otherwise, create a view that stops *before* the end pattern.
    std::span<const std::byte> message_bytes = (end_it == after_start.end()) 
        ? after_start 
        : after_start.subspan(0, end_it - after_start.begin());

    // 3. Attempt to convert the bytes to a UTF-8 string
    // In C++, we directly create a string. C++ strings handle UTF-8 well.
    // The Rust code's logic about valid/invalid UTF-8 suggests a simple heuristic:
    // a certain number of garbage characters exist at the front.
    std::string temp_string(reinterpret_cast<const char*>(message_bytes.data()), message_bytes.size());

    // 4. Drop the garbage prefix characters.
    // This part is a direct translation of the Rust code's logic.
    // It seems the original author found through trial-and-error that
    // there are either 1 or 3 garbage characters at the beginning.
    // We'll replicate the check, but C++ doesn't have a direct equivalent of
    // `from_utf8` vs `from_utf8_lossy` in this context. A simple length check
    // or inspection of the first few bytes would be a more robust C++ approach,
    // but to translate the original logic faithfully:
    if (temp_string.length() > 0 && (temp_string[0] == '\u0006' || temp_string[0] < 32)) {
         return drop_leading_chars(temp_string, 1);
    }
    // The Rust code's fallback to `from_utf8_lossy` often happens when there's
    // some invalid byte sequence at the start.
    else if (temp_string.length() > 2) {
        return drop_leading_chars(temp_string, 3);
    }
    
    return temp_string;
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