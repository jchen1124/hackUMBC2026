#include "contact.h"

Contact::Contact(
    std::optional<std::string> phone_number,
    std::optional<std::string> email,
    std::optional<std::string> first_name,
    std::optional<std::string> last_name,
    std::optional<unsigned int> imessage_handle_id,
    std::optional<unsigned int> sms_handle_id
)
    : m_phone_number(phone_number),
      m_email(email),
      m_first_name(first_name),
      m_last_name(last_name),
      m_imessage_handle_id(imessage_handle_id),
      m_sms_handle_id(sms_handle_id)
{}

std::string Contact::get_display_name() const {
    if (m_first_name.has_value() && m_last_name.has_value()) {
        return m_first_name.value() + " " + m_last_name.value();
    }
    if (m_first_name.has_value()) {
        return m_first_name.value();
    }
    if (m_phone_number.has_value()) {
        return m_phone_number.value();
    }
    if (m_email.has_value()) {
        return m_email.value();
    }
    return "Unknown";
}