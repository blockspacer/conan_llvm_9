# About

Release for llvm 9

NOTE: use `-s llvm_9:build_type=Release` during `conan install` or set `llvm_9:build_type=Release` in conan profile `[settings]`.

Use it if you want to:
 * use clang
 * use clang tools (clang-format, include-what-you-use, etc.)
 * use clang libs (libtooling, etc.)
 * use libc++
 * use google sanitizers (asan, msan, etc.)

Features:

* include-what-you-use (only if `LLVM_USE_SANITIZER` disabled)
* clang-tidy
* scan-build
* ccc-analyzer
* c++-analyzer
* clang-format
* supports `LLVM_USE_SANITIZER`, see https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo#instrumented-gtest
* libc++ (will be instrumented if `LLVM_USE_SANITIZER` enabled)
* clang and clang++ as compilers
* etc.

## Environment variables that affect recipe

`llvm_9_llvm_version`. default: "llvmorg-9.0.1"
`llvm_9_iwyu_version`. default: "clang_9.0"
`llvm_9_BUILD_NUMBER` affects conan package version. default: "" (version will be "master")

A lot of LLVM options can be modified by environment variables.
`LLVM_COMPILER_JOBS` - affects cmake definition `LLVM_COMPILER_JOBS`
`LLVM_PARALLEL_LINK_JOBS` - affects cmake definition `LLVM_PARALLEL_LINK_JOBS`
`LLVM_PARALLEL_COMPILE_JOBS` - affects cmake definition `LLVM_PARALLEL_COMPILE_JOBS`
etc.
See `os.getenv` in `conanfile.py` for full list.

## Conan options that affect recipe

`with_LLVMCore`, `with_LLVMAnalysis`,
etc. used to set link libraries (in `self.cpp_info.libs`).
See `llvm_libs` in `conanfile.py` for full list.

`with_X86`, `with_ARM`,
etc. used to set targets (in `LLVM_TARGETS_TO_BUILD`).
See `llvm_targets` in `conanfile.py` for full list.

`with_clang`, `with_clang-tools-extra`, `with_compiler-rt`,
etc. used to set projects (in `LLVM_ENABLE_PROJECTS`).
See `llvm_projects` in `conanfile.py` for full list.

`link_with_llvm_libs` - enable if you want to use LLVM libs i.e. LibTooling, LLVMCore, etc.

Build settings: 'fPIC', 'shared', 'rtti', 'libffi', 'libz', 'lto', etc.

IWYU support: "include_what_you_use"

Sanitizers support: `-o llvm_9:use_sanitizer="Address;Undefined"`

You can change "Address;Undefined" to one of:
  * "Address",
  * "Memory",
  * "MemoryWithOrigins",
  * "Undefined",
  * "Thread",
  * "DataFlow",
  * "Address;Undefined",
  * "None"

See `self.options` in `conanfile.py` for full list.

## Supported platforms

Tested on Ubuntu 18, x86_64.

```bash
# lsb_release -a
Distributor ID: Ubuntu
Description:    Ubuntu 18.04.2 LTS
Release:        18.04
Codename:       bionic

# uname -a
Linux username 4.15.0-96-generic #97-Ubuntu SMP Wed Apr 1 03:25:46 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
```

## LICENSE

MIT for conan package. Packaged source uses own license, see https://releases.llvm.org/2.8/LICENSE.TXT and https://github.com/root-project/root/blob/master/LICENSE

## Best practices

`CONAN_DISABLE_CHECK_COMPILER` is bad practice.

Use approach similar to https://github.com/blockspacer/llvm_9_installer

Best practice is to create separate recipe that depends on llvm package and populate env. vars.

```python
  # see https://docs.conan.io/en/latest/systems_cross_building/cross_building.html
  self.env_info.CXX = os.path.join(llvm_root, "bin", "clang++")
  self.env_info.CC = os.path.join(llvm_root, "bin", "clang")
  self.env_info.AR = os.path.join(llvm_root, "bin", "llvm-ar")
  self.env_info.STRIP = os.path.join(llvm_root, "bin", "llvm-strip")
  self.env_info.LD = os.path.join(llvm_root, "bin", "ld.lld") # llvm-ld replaced by llvm-ld
  self.env_info.NM = os.path.join(llvm_root, "bin", "llvm-nm")
  # TODO: propagate to CMAKE_OBJDUMP?
  self.env_info.OBJDUMP = os.path.join(llvm_root, "bin", "llvm-objdump")
  self.env_info.SYMBOLIZER = os.path.join(llvm_root, "bin", "llvm-symbolizer")
  self.env_info.RANLIB = os.path.join(llvm_root, "bin", "llvm-ranlib")
  self.env_info.AS = os.path.join(llvm_root, "bin", "llvm-as")
  # TODO: llvm-rc-rc or llvm-rc?
  self.env_info.RC = os.path.join(llvm_root, "bin", "llvm-rc")
```

Or better, just use https://github.com/blockspacer/llvm_9_installer

## Usage example (CMake)

See [https://github.com/include-what-you-use/include-what-you-use/issues/802#issuecomment-661058223](https://github.com/include-what-you-use/include-what-you-use/issues/802#issuecomment-661058223)

See `test_package/CMakeLists.txt` for usage example

NOTE: use `find_program` with `${CONAN_BIN_DIRS}` or `${CONAN_BIN_DIRS_LLVM_9}` like below:

```cmake
list(APPEND CMAKE_PROGRAM_PATH ${CONAN_BIN_DIRS})
list(APPEND CMAKE_PROGRAM_PATH ${CONAN_BIN_DIRS_LLVM_9})

find_program(CLANG_TIDY clang-tidy
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CLANG_TIDY)
  message(FATAL_ERROR "CLANG_TIDY not found")
endif()

find_program(SCAN_BUILD scan-build
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT SCAN_BUILD)
  message(FATAL_ERROR "scan-build not found")
endif()

find_program(CLANG clang
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CLANG)
  message(FATAL_ERROR "clang not found")
endif()

find_program(CCC_ANALYZER ccc-analyzer
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CCC_ANALYZER)
  message(FATAL_ERROR "ccc-analyzer not found")
endif()

find_program(CPP_ANALYZER c++-analyzer
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CPP_ANALYZER)
  message(FATAL_ERROR "c++-analyzer not found")
endif()

find_program(CLANG_FORMAT clang-format
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT CLANG_FORMAT)
  message(FATAL_ERROR "clang-format not found")
endif()

find_program(IWYU include-what-you-use
  PATHS
    ${CONAN_BIN_DIRS}
    ${CONAN_BIN_DIRS_LLVM_9}
  NO_SYSTEM_ENVIRONMENT_PATH
  NO_CMAKE_SYSTEM_PATH
)
if(NOT IWYU)
  message(FATAL_ERROR "IWYU not found")
endif()
```

You can change compiler to clang from conan package like so:

```cmake
  # use llvm_9 from conan
  find_program(CLANG_PROGRAM clang
    PATHS
      #${CONAN_BIN_DIRS}
      ${CONAN_BIN_DIRS_LLVM_9}
    NO_SYSTEM_ENVIRONMENT_PATH
    NO_CMAKE_SYSTEM_PATH
  )

  # we can NOT change CMAKE_C_COMPILER dynamically
  # (it will corrupt cmake cache), but we can check CC env. var
  if(NOT "${CMAKE_C_COMPILER}" STREQUAL "${CLANG_PROGRAM}")
    message(WARNING "CMAKE_C_COMPILER=${CMAKE_C_COMPILER} does not match ${CLANG_PROGRAM}. Run command:")
    message(FATAL_ERROR "export CC=${CLANG_PROGRAM}")
  endif()

  # ...
  # use find_program for CMAKE_CXX_COMPILER, llvm-ar, etc.
  # ...

  # we can NOT change CMAKE_CXX_COMPILER dynamically
  # (it will corrupt cmake cache), but we can check CXX env. var
  if(NOT "${CMAKE_CXX_COMPILER}" STREQUAL "${CLANGPP_PROGRAM}")
    message(WARNING "CMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER} does not match ${CLANGPP_PROGRAM}. Run command:")
    message(FATAL_ERROR "export CXX=${CLANGPP_PROGRAM}")
  endif()

  # Set linkers and other build tools.
  # Related documentation
  # https://cmake.org/cmake/help/latest/variable/CMAKE_LANG_COMPILER.html
  # https://cmake.org/cmake/help/latest/variable/CMAKE_LANG_FLAGS_INIT.html
  # https://cmake.org/cmake/help/latest/variable/CMAKE_LINKER.html
  # https://cmake.org/cmake/help/latest/variable/CMAKE_AR.html
  # https://cmake.org/cmake/help/latest/variable/CMAKE_RANLIB.html
  set(CMAKE_AR      "${LLVM_AR_PROGRAM}")
  set(CMAKE_LINKER  "${LLVM_LD_PROGRAM}")
  set(CMAKE_NM      "${LLVM_NM_PROGRAM}")
  set(CMAKE_OBJDUMP "${LLVM_OBJDUMP_PROGRAM}")
  set(CMAKE_RANLIB  "${LLVM_RANLIB_PROGRAM}")
  set(CMAKE_ASM_COMPILER  "${LLVM_ASM_PROGRAM}")
  set(CMAKE_RC_COMPILER  "${LLVM_RC_PROGRAM}")
```

Add before `include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)`:

```cmake
  # do not check compile in conanbuildinfo
  # cause we will switch to other compiler after conan install
  set(CONAN_DISABLE_CHECK_COMPILER ON)
  set(CMAKE_C_COMPILER_FORCED TRUE)
  set(CMAKE_CXX_COMPILER_FORCED TRUE)
```

You can use `libc++` from conan package like so:

```cmake
  find_path(
    LIBCXX_LIBCXXABI_INCLUDE_FILE cxxabi.h
    PATHS
      ${CONAN_LLVM_9_ROOT}/include/c++/v1
      ${CONAN_INCLUDE_DIRS_LLVM_9}
    NO_DEFAULT_PATH
    NO_CMAKE_FIND_ROOT_PATH
  )

  get_filename_component(LIBCXX_LIBCXXABI_INCLUDE_FILE_DIR
    ${LIBCXX_LIBCXXABI_INCLUDE_FILE}
    DIRECTORY)

  find_library(CLANG_LIBCPP
    NAMES
      c++
    PATHS
      ${CONAN_LIB_DIRS_LLVM_9}
      ${CONAN_BIN_DIRS_LLVM_9}
    NO_SYSTEM_ENVIRONMENT_PATH
    NO_CMAKE_SYSTEM_PATH
  )

  get_filename_component(CLANG_LIBCPP_DIR
    ${CLANG_LIBCPP}
    DIRECTORY)

  find_library(CLANG_LIBCPPABI
    NAMES
    c++abi
    PATHS
      ${CONAN_LIB_DIRS_LLVM_9}
      ${CONAN_BIN_DIRS_LLVM_9}
    NO_SYSTEM_ENVIRONMENT_PATH
    NO_CMAKE_SYSTEM_PATH
  )

  get_filename_component(CLANG_LIBCPPABI_DIR
    ${CLANG_LIBCPPABI}
    DIRECTORY)

  include_directories(
    "${CONAN_LLVM_9_ROOT}/include"
    "${CONAN_LLVM_9_ROOT}/include/c++/v1")

  set(CMAKE_CXX_FLAGS
    "${CMAKE_CXX_FLAGS} \
    -I${CONAN_LLVM_9_ROOT}/include/c++/v1 \
    -I${CONAN_LLVM_9_ROOT}/include")

  link_directories("${CONAN_LLVM_9_ROOT}/lib")
  link_directories("${CLANG_LIBCPP_DIR}")

  set(CMAKE_CXX_FLAGS
    "${CMAKE_CXX_FLAGS} \
    -Wno-unused-command-line-argument \
    -L${CONAN_LLVM_9_ROOT}/lib \
    -L${CLANG_LIBCPP_DIR} \
    -Wl,-rpath,${CLANG_LIBCPPABI_DIR} \
    -Wl,-rpath,${CONAN_LLVM_9_ROOT}/lib \
    -stdlib=libc++ -lc++abi -lc++ -lm -lc -fuse-ld=lld")

  add_compile_options(
      "-stdlib=libc++"
      "-lc++abi"
      "-nostdinc++"
      "-nodefaultlibs"
      "-v")
```

See for example `macro(compile_with_llvm_9)` from [https://github.com/blockspacer/cmake_helper_utils_conan/blob/master/cmake/Findcmake_helper_utils.cmake](https://github.com/blockspacer/cmake_helper_utils_conan/blob/master/cmake/Findcmake_helper_utils.cmake)

## Before build

Based on https://lldb.llvm.org/resources/build.html

```bash
sudo apt-get update

sudo apt-get -y install autoconf automake bison build-essential \
ca-certificates llvm-dev libtool libtool-bin \
libglib2.0-dev make nasm wget

sudo apt-get install build-essential subversion swig python3-dev libedit-dev libncurses5-dev

sudo apt-get install libncurses5-dev libncursesw5-dev libtinfo-dev

# Tested with clang 10 and gcc 7
sudo apt-get -y install clang-10 g++-7 gcc-7

sudo apt-get install -y libunwind-dev

# llvm-config binary that coresponds to the same clang you are using to compile
export LLVM_CONFIG=/usr/bin/llvm-config-10
$LLVM_CONFIG --cxxflags

# use python3
sudo update-alternatives --config python
python --version
```

read https://llvm.org/docs/CMake.html and https://fuchsia.dev/fuchsia-src/development/build/toolchain and https://github.com/deepinwiki/wiki/wiki/%E7%94%A8LLVM%E7%BC%96%E8%AF%91%E5%86%85%E6%A0%B8

## BUGFIX: 92247 (libsanitizer/sanitizer_common/sanitizer_linux compilation failed)

Bugfix for https://gcc.gnu.org/bugzilla/show_bug.cgi?id=92247

Fixes `asm/errno.h: No such file or directory` or ... `was not declared in this scope`

```bash
sudo apt install linux-libc-dev

# NOTE: NOT /usr/include/asm-generic
sudo ln -s /usr/include/x86_64-linux-gnu/asm/ /usr/include/asm
```

## BUGFIX (i386 instead of x86_64)

Fixes `sanitizer_allocator.cpp.o' is incompatible with i386:x86-64 output`, see https://bugs.llvm.org/show_bug.cgi?id=42463 and section about i386 on https://reviews.llvm.org/D58184

```bash
export CXXFLAGS=-m64
export CFLAGS=-m64
export LDFLAGS=-m64
```

Or you can remove `test_target_arch(i386 __i386__ "-m32")` from `compiler-rt/cmake/base-config-ix.cmake`

## Local build

```bash
# https://www.pclinuxos.com/forum/index.php?topic=129566.0
# export LDFLAGS="$LDFLAGS -ltinfo -lncurses"

export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10

export CC=gcc
export CXX=g++

$CC --version
$CXX --version

conan remote add conan-center https://api.bintray.com/conan/conan/conan-center False

export PKG_NAME=llvm_9/master@conan/stable

(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force $PKG_NAME || true)

# see BUGFIX (i386 instead of x86_64)
export CXXFLAGS=-m64
export CFLAGS=-m64
export LDFLAGS=-m64

conan create . conan/stable -s build_type=Release --profile clang --build missing --build cascade

conan upload $PKG_NAME --all -r=conan-local -c --retry 3 --retry-wait 10 --force
```

## Build with sanitizers support

Use `-o llvm_9:use_sanitizer="Address;Undefined"` like so:

```bash
# https://www.pclinuxos.com/forum/index.php?topic=129566.0
# export LDFLAGS="$LDFLAGS -ltinfo -lncurses"

export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10

export CC=gcc
export CXX=g++

$CC --version
$CXX --version

# see BUGFIX (i386 instead of x86_64)
export CXXFLAGS=-m64
export CFLAGS=-m64
export LDFLAGS=-m64

conan create . conan/stable \
  -s build_type=Release \
  --profile clang \
  -o llvm_9:include_what_you_use=False \
  -o llvm_9:use_sanitizer="Address;Undefined"
```

You can change "Address;Undefined" to one of:
  * "Address",
  * "Memory",
  * "MemoryWithOrigins",
  * "Undefined",
  * "Thread",
  * "DataFlow",
  * "Address;Undefined",
  * "None"

NOTE: msan requires to set `-stdlib=libc++ -lc++abi` and use include and lib paths from conan package (see above).
See https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo#instrumented-gtest

Perform checks:

```bash
# must exist
find ~/.conan -name libclang_rt.msan_cxx-x86_64.a

# see https://stackoverflow.com/a/47705420
nm -an $(find ~/.conan -name *libc++.so.1 | grep "llvm_9/master/conan/stable/package/") | grep san
```

## Check that compilers works

```bash
$(find ~/.conan/data/llvm_9 -name llvm-config) --libs --system-libs

$(find ~/.conan/data/llvm_9 -name llvm-config) --cxxflags --ldflags

echo '#include <new>' | $(find ~/.conan/data/llvm_9 -name clang) -x c++ -fsyntax-only -v -
```

## Avoid Debug build, prefer Release builds

Debug build of llvm may take a lot of time or crash due to lack of RAM or CPU

## How to keep multiple llvm_9 package revisions in local cache

Usually you want to build LLVM in multiple configurations and re-use pre-built packages. Approach below allows to avoid full re-builds via `conan create` on each change in options.

Option 1: Create conan server. Solves problem because only conan client can have only one revision installed simultaneously (see https://github.com/conan-io/conan/issues/6836 )

Option 2: Store on disk multiple pre-built llvm_9 packages. Export desired version and work with that version globally.

Example below shows how to install multiple LLVM revisions: both with default options and with sanitizer (MSAN) enabled (not that you can enable only one of them globally using `conan export-pkg`).

## How to check that sanitizers enabled

```bash
# see https://stackoverflow.com/a/47705420
nm -an $(find ~/.conan -name *libc++.so.1 | grep "llvm_9/master/conan/stable/package/") | grep san
```

Validate that `ldd` points to instrumented `libc++`, see https://stackoverflow.com/a/35197295

Validate that compile log contains `-fsanitize=`

You can test that sanitizer can catch error by adding into `SalutationTest` from `test_package/test_package.cpp` code:

```cpp
  // MSAN test
  int r;
  int* a = new int[10];
  a[5] = 0;
  if (a[r])
    printf("xx\n");
```

## Build locally (revision with default options):

NOTE: options below disable both IWYU and sanitizers (but clang compiler, llvm libs, scan-build, clang-tidy, clang-format, etc. will be enabled).

```bash
# https://www.pclinuxos.com/forum/index.php?topic=129566.0
# export LDFLAGS="$LDFLAGS -ltinfo -lncurses"

export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10

export CC=gcc
export CXX=g++

$CC --version
$CXX --version

# see BUGFIX (i386 instead of x86_64)
export CXXFLAGS=-m64
export CFLAGS=-m64
export LDFLAGS=-m64

rm -rf local_build

cmake -E time \
  conan install . \
  --install-folder local_build \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang

cmake -E time \
  conan source . \
  --source-folder local_build \
  --install-folder local_build

conan build . \
  --build-folder local_build \
  --source-folder local_build \
  --install-folder local_build

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force llvm_9 || true)

conan package . \
  --build-folder local_build \
  --package-folder local_build/package_dir \
  --source-folder local_build \
  --install-folder local_build

conan export-pkg . \
  conan/stable \
  --package-folder local_build/package_dir \
  --settings build_type=Release \
  --force \
  --profile clang

cmake -E time \
  conan test test_package llvm_9/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang

rm -rf local_build/package_dir
```

## Build locally (revision with include_what_you_use enabled):

```bash
# https://www.pclinuxos.com/forum/index.php?topic=129566.0
# export LDFLAGS="$LDFLAGS -ltinfo -lncurses"

export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10

export CC=gcc
export CXX=g++

$CC --version
$CXX --version

# see BUGFIX (i386 instead of x86_64)
export CXXFLAGS=-m64
export CFLAGS=-m64
export LDFLAGS=-m64

rm -rf local_build_iwyu

cmake -E time \
  conan install . \
  --install-folder local_build_iwyu \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang \
    -o llvm_9:include_what_you_use=True

cmake -E time \
  conan source . \
  --source-folder local_build_iwyu \
  --install-folder local_build_iwyu

conan build . \
  --build-folder local_build_iwyu \
  --source-folder local_build_iwyu \
  --install-folder local_build_iwyu

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force llvm_9 || true)

conan package . \
  --build-folder local_build_iwyu \
  --package-folder local_build_iwyu/package_dir \
  --source-folder local_build_iwyu \
  --install-folder local_build_iwyu

conan export-pkg . \
  conan/stable \
  --package-folder local_build_iwyu/package_dir \
  --settings build_type=Release \
  --force \
  --profile clang \
    -o llvm_9:include_what_you_use=True

cmake -E time \
  conan test test_package llvm_9/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang \
      -o llvm_9:include_what_you_use=True

rm -rf local_build_iwyu/package_dir
```

## Build locally (revision with llvm libs enabled):

```bash
# https://www.pclinuxos.com/forum/index.php?topic=129566.0
# export LDFLAGS="$LDFLAGS -ltinfo -lncurses"

export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10

export CC=gcc
export CXX=g++

$CC --version
$CXX --version

# see BUGFIX (i386 instead of x86_64)
export CXXFLAGS=-m64
export CFLAGS=-m64
export LDFLAGS=-m64

rm -rf local_build_llvm_libs

cmake -E time \
  conan install . \
  --install-folder local_build_llvm_libs \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang \
    -o llvm_9:include_what_you_use=False \
    -o llvm_9:link_with_llvm_libs=True

cmake -E time \
  conan source . \
  --source-folder local_build_llvm_libs \
  --install-folder local_build_llvm_libs

conan build . \
  --build-folder local_build_llvm_libs \
  --source-folder local_build_llvm_libs \
  --install-folder local_build_llvm_libs

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force llvm_9 || true)

conan package . \
  --build-folder local_build_llvm_libs \
  --package-folder local_build_llvm_libs/package_dir \
  --source-folder local_build_llvm_libs \
  --install-folder local_build_llvm_libs

conan export-pkg . \
  conan/stable \
  --package-folder local_build_llvm_libs/package_dir \
  --settings build_type=Release \
  --force \
  --profile clang \
    -o llvm_9:include_what_you_use=False \
    -o llvm_9:link_with_llvm_libs=True

cmake -E time \
  conan test test_package llvm_9/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang \
    -o llvm_9:include_what_you_use=False \
    -o llvm_9:link_with_llvm_libs=True

rm -rf local_build_llvm_libs/package_dir
```

## Build locally (revision with asan enabled):

```bash
# https://www.pclinuxos.com/forum/index.php?topic=129566.0
# export LDFLAGS="$LDFLAGS -ltinfo -lncurses"

export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10

export CC=gcc
export CXX=g++

$CC --version
$CXX --version

# see BUGFIX (i386 instead of x86_64)
export CXXFLAGS=-m64
export CFLAGS=-m64
export LDFLAGS=-m64

rm -rf local_build_asan

cmake -E time \
  conan install . \
  --install-folder local_build_asan \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang \
    -o llvm_9:include_what_you_use=False \
    -o llvm_9:use_sanitizer="Address;Undefined"

cmake -E time \
  conan source . \
  --source-folder local_build_asan \
  --install-folder local_build_asan

conan build . \
  --build-folder local_build_asan \
  --source-folder local_build_asan \
  --install-folder local_build_asan

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force llvm_9 || true)

conan package . \
  --build-folder local_build_asan \
  --package-folder local_build_asan/package_dir \
  --source-folder local_build_asan \
  --install-folder local_build_asan

conan export-pkg . \
  conan/stable \
  --package-folder local_build_asan/package_dir \
  --settings build_type=Release \
  --force \
  --profile clang \
    -o llvm_9:include_what_you_use=False \
    -o llvm_9:use_sanitizer="Address;Undefined"

cmake -E time \
  conan test test_package llvm_9/master@conan/stable \
  -s build_type=Release \
  -s llvm_9:build_type=Release \
  --profile clang \
    -o llvm_9:include_what_you_use=False \
    -o llvm_9:use_sanitizer="Address;Undefined"

# llvm-ar, llvm-symbolizer, etc. must be NOT sanitized
nm -an local_build_asan/package_dir/bin/llvm-ar | grep asan

# must be NOT sanitized
nm -an  local_build_asan/package_dir/lib/libclangTooling.so | grep san

# must be NOT sanitized
nm -an  local_build_asan/package_dir/lib/libLLVMDemangle.so | grep san

# libc++, libc++abi must be sanitized
nm -an  local_build_asan/package_dir/lib/libc++abi.so | grep san

# must exist
find local_build_asan/package_dir/lib/clang/ -name "*clang_rt.*san*"

rm -rf local_build_asan/package_dir
```

You can change "Address;Undefined" to one of:
  * "Address",
  * "Memory",
  * "MemoryWithOrigins",
  * "Undefined",
  * "Thread",
  * "DataFlow",
  * "Address;Undefined",
  * "None"

## Build other llvm branch:

```bash
# https://www.pclinuxos.com/forum/index.php?topic=129566.0
# export LDFLAGS="$LDFLAGS -ltinfo -lncurses"

export CONAN_REVISIONS_ENABLED=1
export CONAN_VERBOSE_TRACEBACK=1
export CONAN_PRINT_RUN_COMMANDS=1
export CONAN_LOGGING_LEVEL=10

export CC=gcc
export CXX=g++

$CC --version
$CXX --version

# see BUGFIX (i386 instead of x86_64)
export CXXFLAGS=-m64
export CFLAGS=-m64
export LDFLAGS=-m64

export LLVM_PACKAGE_NAME="llvm_12"

export $LLVM_PACKAGE_NAME\_llvm_version="release/12.x"
export $LLVM_PACKAGE_NAME\_iwyu_version="clang_12"
export $LLVM_PACKAGE_NAME\_BUILD_NUMBER="-clang_12"
export CONAN_LLVM_SKIP_PATCH=True

export BUILD_NUMBER="-clang_12"

export LLVM_CONAN_PACKAGE_ID_COMILER_VER="12"
export LLVM_CONAN_CLANG_VER="12.0.1"

rm -rf local_build_iwyu_clang_12

cmake -E time \
  conan install . \
  --install-folder local_build_iwyu_clang_12 \
  -s build_type=Release \
  -s $LLVM_PACKAGE_NAME:build_type=Release \
  --profile clang \
    -o $LLVM_PACKAGE_NAME:include_what_you_use=True

cmake -E time \
  conan source . \
  --source-folder local_build_iwyu_clang_12 \
  --install-folder local_build_iwyu_clang_12

conan build . \
  --build-folder local_build_iwyu_clang_12 \
  --source-folder local_build_iwyu_clang_12 \
  --install-folder local_build_iwyu_clang_12

# remove before `conan export-pkg`
(CONAN_REVISIONS_ENABLED=1 \
    conan remove --force $LLVM_PACKAGE_NAME || true)

conan package . \
  --build-folder local_build_iwyu_clang_12 \
  --package-folder local_build_iwyu_clang_12/package_dir \
  --source-folder local_build_iwyu_clang_12 \
  --install-folder local_build_iwyu_clang_12

conan export-pkg . \
  conan/stable \
  --package-folder local_build_iwyu_clang_12/package_dir \
  --settings build_type=Release \
  --force \
  --profile clang \
    -o $LLVM_PACKAGE_NAME:include_what_you_use=True

cmake -E time \
  conan test test_package $LLVM_PACKAGE_NAME/master$BUILD_NUMBER@conan/stable \
  -s build_type=Release \
  -s $LLVM_PACKAGE_NAME:build_type=Release \
  --profile clang \
      -o $LLVM_PACKAGE_NAME:include_what_you_use=True

rm -rf local_build_iwyu_clang_12/package_dir
```

Now you can depend on conan package `$LLVM_PACKAGE_NAME/master$BUILD_NUMBER@conan/stable`

## FIXME: No rule to make target 'projects/libc/src/math/round.o'

Please file a bug report or suggest solution. Unable to add `libc` to `LLVM_ENABLE_PROJECTS`:

```bash
No rule to make target 'projects/libc/src/math/round.o'
```

see https://github.com/fwsGonzo/libriscv/issues/4
