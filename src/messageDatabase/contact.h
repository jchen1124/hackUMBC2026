#pragma once
#include <string>
#include <optional>

class Contact {
public:
    std::optional<std::string> m_phone_number;
    std::optional<std::string> m_email;
    std::optional<std::string> m_first_name;
    std::optional<std::string> m_last_name;

    std::optional<unsigned int> m_imessage_handle_id;
    std::optional<unsigned int> m_sms_handle_id;


    Contact(
        std::optional<std::string> phone_number,
        std::optional<std::string> email,
        std::optional<std::string> first_name,
        std::optional<std::string> last_name,
        std::optional<unsigned int> imessage_handle_id,
        std::optional<unsigned int> sms_handle_id
    );

    std::string get_display_name() const;
};