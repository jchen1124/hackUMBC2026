# Root CMakeLists.txt
cmake_minimum_required(VERSION 3.10)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
project(hackathon2025 LANGUAGES CXX)


# Find all packages here so they are available to subdirectories
find_package(fmt CONFIG REQUIRED)
find_package(pybind11 CONFIG REQUIRED)
find_package(SQLiteCpp CONFIG REQUIRED)
find_package(unofficial-libplist CONFIG REQUIRED) # <-- CORRECTED

add_subdirectory(src/messageDatabase)