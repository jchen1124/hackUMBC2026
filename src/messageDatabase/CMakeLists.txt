# src/messageDatabase/CMakeLists.txt

# Create a single list containing ALL C++ source files for the module
set(SOURCES
    contact.cpp
    database.cpp
    message_data.cpp
    bindings.cpp 
)

# Compile all sources into one Python module.
pybind11_add_module(IMessageDatabase ${SOURCES})

# Link all the necessary libraries to your module
target_link_libraries(IMessageDatabase PRIVATE
    fmt::fmt
    SQLiteCpp
    unofficial::libplist::libplist
    unofficial::libplist::libplist++ # <-- REMOVED STRAY PARENTHESIS HERE
)

# Install the final compiled module into the Python source directory
install(TARGETS IMessageDatabase DESTINATION ${CMAKE_SOURCE_DIR}/src/frontEnd)