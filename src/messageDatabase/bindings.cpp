#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // For automatic conversion of std::vector, std::optional, etc.
#include <pybind11/chrono.h> // For automatic conversion of std::chrono types

#include "database.h"
#include "contact.h"
#include "message_data.h"

namespace py = pybind11;

// This is the single entry point for the entire Python module.
PYBIND11_MODULE(IMessageDatabase, m) {
    m.doc() = "A C++ library for parsing and analyzing iMessage data.";

    // 1. Define the Contact class for Python
    // We must do this before it can be used as a return type.
    py::class_<Contact>(m, "Contact")
        .def(py::init<
            std::optional<std::string>,
            std::optional<std::string>,
            std::optional<std::string>,
            std::optional<std::string>,
            std::optional<unsigned int>,
            std::optional<unsigned int>
        >())
        .def("get_display_name", &Contact::get_display_name)
        // Expose member variables so you can access them in Python
        .def_readonly("phone_number", &Contact::m_phone_number)
        .def_readonly("email", &Contact::m_email)
        .def_readonly("first_name", &Contact::m_first_name)
        .def_readonly("last_name", &Contact::m_last_name)
        .def_readonly("imessage_handle_id", &Contact::m_imessage_handle_id)
        .def_readonly("sms_handle_id", &Contact::m_sms_handle_id);

    // 2. Define the message_data class for Python
    // Note: We don't bind the constructor since it's private.
    py::class_<MessageData>(m, "MessageData")
        // TODO: Expose members of message_data if you need them in Python,
        // for example: .def_readonly("text", &message_data::m_text);
        .def("get_text", &MessageData::get_text);


    // 3. Now we can define the Database class that uses the types above
    py::class_<Database>(m, "Database")
        .def(py::init<std::string, std::string>())
        .def("populate_database", &Database::populate_database)
        // Add getters so Python can get the results.
        // The return_value_policy::copy tells pybind11 to copy the vector
        // into a new Python list, which is the safest approach.
        .def("get_contacts", &Database::get_contacts, py::return_value_policy::copy)
        .def("get_messages", &Database::get_messages, py::return_value_policy::copy)
        .def("save_to_sql", &Database::save_to_sql);
}