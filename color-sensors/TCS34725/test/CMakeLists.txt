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
# set(PICO_BOARD pico2_w CACHE STRING "Board type")

# # Pull in Raspberry Pi Pico SDK (must be before project)
# include(pico_sdk_import.cmake)

# project(test C CXX ASM)

# # Initialise the Raspberry Pi Pico SDK
# pico_sdk_init()

# # Add executable. Default name is the project name, version 0.1

# add_executable(test test.c )

# pico_set_program_name(test "test")
# pico_set_program_version(test "0.1")



# # Modify the below lines to enable/disable output over UART/USB
# pico_enable_stdio_uart(test 0)
# pico_enable_stdio_usb(test 0)
# pico_enable_stdio_usb(tcs34725_demo 1)
# pico_enable_stdio_uart(tcs34725_demo 0)

# # Add the standard library to the build
# target_link_libraries(test
#         pico_stdlib
#         hardware_i2c)

# # Add the standard include files to the build
# target_include_directories(test PRIVATE
#         ${CMAKE_CURRENT_LIST_DIR}
# )

# # Add any user requested libraries
# target_link_libraries(test 
        
#         )

# pico_add_extra_outputs(test)


cmake_minimum_required(VERSION 3.13)
include(pico_sdk_import.cmake)

project(tcs34725_demo C CXX ASM)
pico_sdk_init()

add_executable(tcs34725_demo
    test.c
)

target_link_libraries(tcs34725_demo
    pico_stdlib
    hardware_i2c
    pico_cyw43_arch_none
)

pico_enable_stdio_usb(tcs34725_demo 1)
pico_enable_stdio_uart(tcs34725_demo 0)
pico_add_extra_outputs(tcs34725_demo)

# ---- demo2 ----
add_executable(tcs34725_demo2
    color.c
)

target_link_libraries(tcs34725_demo2
    pico_stdlib
    hardware_i2c
    pico_cyw43_arch_none
)

pico_enable_stdio_usb(tcs34725_demo2 1)
pico_enable_stdio_uart(tcs34725_demo2 0)
pico_add_extra_outputs(tcs34725_demo2)
