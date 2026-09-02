cmake_minimum_required(VERSION 3.20)
project(infinity_telemetry LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
add_library(infinity_telemetry SHARED telemetry.cpp)
