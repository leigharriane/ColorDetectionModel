# TCS3200 colour classifier - Raspberry Pi Pico (RP2040)
#
# Build with the Raspberry Pi Pico VS Code extension (open this folder), or:
#   cmake -S . -B build -G Ninja && ninja -C build
# then copy build/tcs3200_classify.uf2 to the Pico in BOOTSEL mode.

cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.2.0)
set(toolchainVersion 14_2_Rel1)
set(picotoolVersion 2.2.0-a4)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================

set(PICO_BOARD pico CACHE STRING "Board type")

# Pull in Raspberry Pi Pico SDK (must be before project)
include(pico_sdk_import.cmake)

project(tcs3200_classify C CXX ASM)

pico_sdk_init()

add_executable(tcs3200_classify
    tcs3200_classify.c
)

pico_set_program_name(tcs3200_classify "tcs3200_classify")
pico_set_program_version(tcs3200_classify "0.1")

# printf() goes over the USB cable, not the UART pins.
pico_enable_stdio_usb(tcs3200_classify 1)
pico_enable_stdio_uart(tcs3200_classify 0)

# The TCS3200 is a frequency-output sensor: only GPIO is needed (part of pico_stdlib).
target_link_libraries(tcs3200_classify
    pico_stdlib
)

target_include_directories(tcs3200_classify PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
)

pico_add_extra_outputs(tcs3200_classify)
