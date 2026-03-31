cmake_minimum_required(VERSION 3.20)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

execute_process(
    COMMAND "${Python3_EXECUTABLE}" -m pybind11 --cmakedir
    OUTPUT_VARIABLE pybind11_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
)

string(REPLACE "\"" "" pybind11_DIR "${pybind11_DIR}")
set(pybind11_DIR "${pybind11_DIR}" CACHE PATH "pybind11 config directory" FORCE)

if(NOT pybind11_DIR)
    message(FATAL_ERROR "pybind11 was not found. Activate the Conda environment from environment.yml before configuring CMake.")
endif()

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(
    meeting_copilot_cpp
    audio_preprocess.cpp
    bindings.cpp
    transcriber.cpp
)

target_include_directories(meeting_copilot_cpp PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
