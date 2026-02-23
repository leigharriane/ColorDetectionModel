# # Generated Cmake Pico project file

# cmake_minimum_required(VERSION 3.13)

# set(CMAKE_C_STANDARD 11)
# set(CMAKE_CXX_STANDARD 17)
# set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# # Initialise pico_sdk from installed location
# # (note this can come from environment, CMake cache etc)

# # == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
# if(WIN32)
#     set(USERHOME $ENV{USERPROFILE})
# else()
#     set(USERHOME $ENV{HOME})
# endif()
# set(sdkVersion 2.2.0)
# set(toolchainVersion 14_2_Rel1)
# set(picotoolVersion 2.2.0-a4)
# set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
# if (EXISTS ${picoVscode})
#     include(${picoVscode})
# endif()
# # ====================================================================================
# set(PICO_BOARD pico CACHE STRING "Board type")

# # Pull in Raspberry Pi Pico SDK (must be before project)
# include(pico_sdk_import.cmake)

# project(test-tcs3200 C CXX ASM)

# # Initialise the Raspberry Pi Pico SDK
# pico_sdk_init()

# # Add executable. Default name is the project name, version 0.1

# add_executable(test-tcs3200 test-tcs3200.c )

# pico_set_program_name(test-tcs3200 "test-tcs3200")
# pico_set_program_version(test-tcs3200 "0.1")

# # Modify the below lines to enable/disable output over UART/USB
# pico_enable_stdio_uart(test-tcs3200 0)
# pico_enable_stdio_usb(test-tcs3200 0)

# # Add the standard library to the build
# target_link_libraries(test-tcs3200
#         pico_stdlib
#         hardware_gpio)

# # Add the standard include files to the build
# target_include_directories(test-tcs3200 PRIVATE
#         ${CMAKE_CURRENT_LIST_DIR}
# )

# pico_add_extra_outputs(test-tcs3200)

# Generated Cmake Pico project file (Revised for TCS230/TCS3200)

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

# ✅ Regular Pico (RP2040)
set(PICO_BOARD pico CACHE STRING "Board type")

# Pull in Raspberry Pi Pico SDK (must be before project)
include(pico_sdk_import.cmake)

project(test-tcs3200 C CXX ASM)

# Initialise the Raspberry Pi Pico SDK
pico_sdk_init()

# Build your program (rename file if needed)
add_executable(test-tcs3200
    test-tcs3200.c
)

pico_set_program_name(test-tcs3200 "test-tcs3200")
pico_set_program_version(test-tcs3200 "0.1")

# ✅ Enable USB serial so printf() works over the USB cable
pico_enable_stdio_usb(test-tcs3200 1)
pico_enable_stdio_uart(test-tcs3200 0)

# ✅ No hardware_i2c needed for TCS3200 (it’s frequency output, not I2C)
target_link_libraries(test-tcs3200
    pico_stdlib
)

target_include_directories(test-tcs3200 PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}
)

pico_add_extra_outputs(test-tcs3200)