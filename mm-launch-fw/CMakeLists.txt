cmake_minimum_required(VERSION 3.20)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)

set(EXTRA_COMPONENT_DIRS "components/")

project(mm_launcher)

set(CMAKE_CXX_STANDARD 20)
