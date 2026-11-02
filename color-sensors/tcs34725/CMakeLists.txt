# TCS34725 colour sensor programs - Raspberry Pi Pico 2 W (RP2350)
#
# Two executables are built from this folder:
#   tcs34725_raw       - prints raw C/R/G/B counts (wiring check)
#   tcs34725_classify  - prints a colour name plus normalised ratios
#
# Build with the Raspberry Pi Pico VS Code extension (open this folder), or:
#   cmake -S . -B build -G Ninja && ninja -C build
# then copy the wanted build/*.uf2 to the board in BOOTSEL mode.
# For a different board change PICO_BOARD below (e.g. pico, pico_w, pico2).

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

set(PICO_BOARD pico2_w CACHE STRING "Board type")

# Pull in Raspberry Pi Pico SDK (must be before project)
include(pico_sdk_import.cmake)

project(tcs34725 C CXX ASM)

pico_sdk_init()

# Shared settings for both programs: I2C driver, USB serial for printf().
function(add_tcs34725_program target source)
    add_executable(${target} ${source})
    pico_set_program_name(${target} "${target}")
    pico_set_program_version(${target} "0.1")
    target_link_libraries(${target}
        pico_stdlib
        hardware_i2c
    )
    target_include_directories(${target} PRIVATE ${CMAKE_CURRENT_LIST_DIR})
    pico_enable_stdio_usb(${target} 1)
    pico_enable_stdio_uart(${target} 0)
    pico_add_extra_outputs(${target})
endfunction()

add_tcs34725_program(tcs34725_raw      tcs34725_raw.c)
add_tcs34725_program(tcs34725_classify tcs34725_classify.c)
