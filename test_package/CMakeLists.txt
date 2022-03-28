project(test_package)
cmake_minimum_required(VERSION 2.8.11)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules")
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/build/") # for conan

# do not check compile in conanbuildinfo
# cause we will switch to other compiler after conan install
set(CONAN_DISABLE_CHECK_COMPILER ON)

if(EXISTS "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
  list(APPEND CMAKE_MODULE_PATH ${CMAKE_BINARY_DIR}/)
  include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
  include(${CMAKE_BINARY_DIR}/conan_paths.cmake OPTIONAL)
  conan_basic_setup(
    # prevent conan_basic_setup from resetting cmake variables
    TARGETS
    KEEP_RPATHS
    # see https://github.com/conan-io/conan/issues/6012
    NO_OUTPUT_DIRS
  )
else()
  message (FATAL_ERROR "must use conan")
endif()

if(NOT TARGET CONAN_PKG::${LLVM_PACKAGE_NAME})
  message(FATAL_ERROR "Use CONAN_PKG::${LLVM_PACKAGE_NAME} from conan")
endif()

find_library(${LLVM_PACKAGE_NAME}::llvm_tools REQUIRED)

string(TOUPPER "${LLVM_PACKAGE_NAME}" LLVM_PACKAGE_NAME_UPPER)

message(STATUS "CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT=${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}")
message(STATUS "CONAN_LIB_DIRS_${LLVM_PACKAGE_NAME_UPPER}=${CONAN_LIB_DIRS_${LLVM_PACKAGE_NAME_UPPER}}")
message(STATUS "CONAN_BUILD_DIRS_${LLVM_PACKAGE_NAME_UPPER}=${CONAN_BUILD_DIRS_${LLVM_PACKAGE_NAME_UPPER}}")
message(STATUS "CONAN_INCLUDE_DIRS_${LLVM_PACKAGE_NAME_UPPER}=${CONAN_INCLUDE_DIRS_${LLVM_PACKAGE_NAME_UPPER}}")
message(STATUS "CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}=${CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}}")

find_path(LLVMConfig_DIR LLVMConfig.cmake
          HINTS
                ${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}
                ${CONAN_LIB_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
                ${CONAN_BUILD_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
                ${CONAN_INCLUDE_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
                ${CONAN_${LLVM_PACKAGE_NAME_UPPER}_ROOT}/lib/cmake/llvm
          NO_DEFAULT_PATH)

message(STATUS "LLVMConfig_DIR: ${LLVMConfig_DIR}")

include(
  ${LLVMConfig_DIR}/LLVMConfig.cmake
)

if(LLVM_BINARY_DIR)
  message(STATUS "LLVM_BINARY_DIR: ${LLVM_BINARY_DIR}")
else()
  message(FATAL_ERROR "LLVM_BINARY_DIR not found: ${LLVM_BINARY_DIR}")
endif()

list(APPEND ${LLVM_PACKAGE_NAME_UPPER}_DEFINITIONS LLVMDIR="${LLVM_BINARY_DIR}")

find_package( Threads REQUIRED )
message(STATUS "CMAKE_THREAD_LIBS_INIT = ${CMAKE_THREAD_LIBS_INIT}")

message(STATUS "CMAKE_DL_LIBS = ${CMAKE_DL_LIBS}")

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PUBLIC
    Threads::Threads
    ${CMAKE_DL_LIBS}
)

target_compile_definitions(${PROJECT_NAME} PUBLIC
  ${${LLVM_PACKAGE_NAME_UPPER}_DEFINITIONS}
)

# POSITION_INDEPENDENT_CODE for -fPIC
set_property(TARGET ${PROJECT_NAME} PROPERTY POSITION_INDEPENDENT_CODE ON)

#set_property(TARGET ${PROJECT_NAME} PROPERTY
#  COMPILE_FLAGS -fno-rtti
#)

target_compile_options(${PROJECT_NAME} PRIVATE
  -fno-rtti)

set_target_properties( ${PROJECT_NAME} PROPERTIES
  OUTPUT_NAME ${PROJECT_NAME}
  #CXX_STANDARD 17
  CXX_EXTENSIONS OFF
  CMAKE_CXX_STANDARD_REQUIRED ON
  RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
  LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib )


list(APPEND CMAKE_PROGRAM_PATH ${CONAN_BIN_DIRS})
list(APPEND CMAKE_PROGRAM_PATH ${CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}})

find_program(CLANG_TIDY clang-tidy
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CLANG_TIDY)
  message(FATAL_ERROR "CLANG_TIDY not found")
endif()

find_program(SCAN_BUILD scan-build
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT SCAN_BUILD)
  message(FATAL_ERROR "scan-build not found")
endif()

find_program(CLANG clang
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CLANG)
  message(FATAL_ERROR "clang not found")
endif()

find_program(CCC_ANALYZER ccc-analyzer
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CCC_ANALYZER)
  message(FATAL_ERROR "ccc-analyzer not found")
endif()

find_program(CPP_ANALYZER c++-analyzer
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CPP_ANALYZER)
  message(FATAL_ERROR "c++-analyzer not found")
endif()

find_program(CLANG_FORMAT clang-format
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CLANG_FORMAT)
  message(FATAL_ERROR "clang-format not found")
endif()

find_program(IWYU include-what-you-use
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_${LLVM_PACKAGE_NAME_UPPER}}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT IWYU)
  # NOTE: not FATAL_ERROR, IWYU optional
  message(WARNING "IWYU not found")
endif()

