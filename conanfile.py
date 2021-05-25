import os, re, stat, fnmatch, platform, glob, traceback, shutil
from conans import ConanFile, CMake, tools
from conans.tools import Version
from conans.errors import ConanInvalidConfiguration
from conans.model.version import Version

# see LLVM_ENABLE_PROJECTS
llvm_projects = [
  'all',
  'clang',
  'clang-tools-extra',
  'compiler-rt',
  'debuginfo-tests',
  'libc',
  'libclc',
  'libcxx',
  'libcxxabi',
  'libunwind',
  'lld',
  'lldb',
  'mlir',
  'openmp',
  'parallel-libs',
  'polly',
  'pstl'
]

# see LLVM_ENABLE_PROJECTS
default_llvm_projects = [
  'clang',
  'clang-tools-extra',
  'compiler-rt',
  'libcxx',
  'libcxxabi',
  'libunwind',
  'lld',
  'lldb'
]

# see LLVM_TARGETS_TO_BUILD
llvm_targets = [
  'all',
  'AArch64',
  'AMDGPU',
  'ARM',
  'BPF',
  'Hexagon',
  'Lanai',
  'Mips',
  'MSP430',
  'NVPTX',
  'RISCV',
  'SystemZ',
  'WebAssembly',
  'X86',
  'XCore'
]

# see LLVM_TARGETS_TO_BUILD
default_llvm_targets = [
  'X86'
]

# used by self.cpp_info.libs
llvm_libs = [
  'LLVMCore',
  'LLVMAnalysis',
  'LLVMSupport',
  'LLVMipo',
  'LLVMIRReader',
  'LLVMBinaryFormat',
  'LLVMBitReader',
  'LLVMBitWriter',
  'LLVMMC',
  'LLVMMCParser',
  'LLVMTransformUtils',
  'LLVMScalarOpts',
  'LLVMLTO',
  'LLVMCoroutines',
  'LLVMCoverage',
  'LLVMInstCombine',
  'LLVMInstrumentation',
  'LLVMLinker',
  'LLVMObjCARCOpts',
  'LLVMObject',
  'LLVMPasses',
  'LLVMProfileData',
  'LLVMTarget',
  'LLVMLibDriver',
  'LLVMLineEditor',
  'LLVMMIRParser',
  'LLVMOption',
  'LLVMRuntimeDyld',
  'LLVMSelectionDAG',
  'LLVMSymbolize',
  'LLVMTableGen',
  'LLVMVectorize',
  'clangToolingRefactoring',
  'clangStaticAnalyzerCore',
  'clangDynamicASTMatchers',
  'clangCodeGen',
  'clangFrontendTool',
  'clang',
  'clangEdit',
  'clangRewriteFrontend',
  'clangDriver',
  'clangSema',
  'clangASTMatchers',
  'clangSerialization',
  'clangBasic',
  'clangAST',
  'clangTooling',
  'clangStaticAnalyzerFrontend',
  'clangFormat',
  'clangLex',
  'clangFrontend',
  'clangRewrite',
  'clangToolingCore',
  'clangIndex',
  'clangAnalysis',
  'clangParse',
  'clangStaticAnalyzerCheckers',
  'clangARCMigrate',
]

# used by self.cpp_info.libs
# If your project does not depend on LLVM libs (LibTooling, etc.),
# than you can clear default_llvm_libs (just disable in options all libs)
default_llvm_libs = llvm_libs

# see LLVM_COMPILER_RT_SANITIZERS_TO_BUILD
compiler_rt_sanitizers = [
  'all',
  'asan',
  'dfsan',
  'msan',
  'hwasan',
  'tsan',
  'safestack',
  'cfi',
  'esan',
  'scudo',
  'ubsan_minimal',
  'gwp_asan'
]

# see LLVM_COMPILER_RT_SANITIZERS_TO_BUILD
default_compiler_rt_sanitizers = [
  'asan',
  'msan',
  'tsan',
  'safestack',
  'cfi',
  'esan'
]

# dict `llvm_env` can store only boolean values (True/False)
# and None (bool(None) returns False)
# because we want to use values in conditions
# i.e. can use `if llvm_env["COMPILER_RT_BUILD_CRT"]`
# None means that value has no default
# i.e. it will use default value provided by LLVM if env. var. not set.
llvm_env = {
  # Generate build targets for the LLVM tools.
  # Defaults to ON.
  # You can use this option to disable the generation of build targets
  # for the LLVM tools.
  "LLVM_INCLUDE_TOOLS": True,
  # Enable building OProfile JIT support. Defaults to OFF.
  #
  "LLVM_USE_OPROFILE": False,
  #
  "LLVM_USE_NEWPM": False,
  #
  # build compiler-rt, libcxx etc.
  "LLVM_BUILD_RUNTIME": None,
  #
  # Build crtbegin.o/crtend.o
  # NOTE: OFF by default due to
  # stage_runtime/lib/clang/9.0.1/lib/linux/clang_rt.crtbegin-x86_64.o
  # that requires clang by clang_rt.crtbegin-x86_64.o
  "COMPILER_RT_BUILD_CRT": False,
  #
  # builtins - a simple library that provides an implementation of the low-level target-specific hooks required by code generation and other runtime components. For example, when compiling for a 32-bit target, converting a double to a 64-bit unsigned integer is compiling into a runtime call to the "__fixunsdfdi" function. The builtins library provides optimized implementations of this and other low-level routines, either in target-independent C form, or as a heavily-optimized assembly.
  # builtins provides full support for the libgcc interfaces on supported targets and high performance hand tuned implementations of commonly used functions like __floatundidf in assembly that are dramatically faster than the libgcc implementations. It should be very easy to bring builtins to support a new target by adding the new routines needed by that target.
  "COMPILER_RT_BUILD_BUILTINS": False,
  #
  # Use eh_frame in crtbegin.o/crtend.o
  "COMPILER_RT_CRT_USE_EH_FRAME_REGISTRY": None,
  #
  "COMPILER_RT_BUILD_XRAY": None,
  #
  # Build xray with no preinit patching
  "COMPILER_RT_BUILD_XRAY_NO_PREINIT": None,
  #
  # profile - library which is used to collect coverage information.
  "COMPILER_RT_BUILD_PROFILE": None,
  #
  "COMPILER_RT_BUILD_LIBFUZZER": None,
  #
  # Build memory profiling runtime
  "COMPILER_RT_BUILD_MEMPROF": None,
  #
  # NOTE: must match LLVM_LINK_LLVM_DYLIB
  # NOTE: This cannot be used in conjunction with BUILD_SHARED_LIBS.
  # If enabled, the target for building the libLLVM shared library is added.
  # This library contains all of LLVM’s components in a single shared library.
  # Defaults to OFF.
  # Tools will only be linked to the libLLVM shared library
  # if LLVM_LINK_LLVM_DYLIB is also ON.
  # The components in the library can be customised
  # by setting LLVM_DYLIB_COMPONENTS to a list of the desired components.
  "LLVM_BUILD_LLVM_DYLIB": None,
  #
  # If enabled, tools will be linked with the libLLVM shared library.
  # Defaults to OFF.
  # Setting LLVM_LINK_LLVM_DYLIB to ON also sets LLVM_BUILD_LLVM_DYLIB to ON.
  "LLVM_LINK_LLVM_DYLIB": None,
  #
  # If disabled, do not try to build the OCaml and go bindings.
  "LLVM_ENABLE_BINDINGS": None,
  #
  # Install symlinks from the binutils tool names
  # to the corresponding LLVM tools.
  # For example, ar will be symlinked to llvm-ar.
  "LLVM_INSTALL_BINUTILS_SYMLINKS": False,
  #
  "LLVM_INSTALL_CCTOOLS_SYMLINKS": False,
  #
  # LLVM target to use for native code generation.
  # This is required for JIT generation.
  # Example: "x86_64"
  "LLVM_TARGET_ARCH": None,
  #
  "LLVM_COMPILER_RT_DEFAULT_TARGET_TRIPLE": None,
  #
  "LLVM_DEFAULT_TARGET_TRIPLE": None,
  #
  "PYTHON_EXECUTABLE": None,
  #
  # Embed version control revision info (svn revision number or Git revision id).
  # The version info is provided by the LLVM_REVISION macro
  # in llvm/include/llvm/Support/VCSRevision.h.
  # Developers using git who don’t need revision info
  # can disable this option to avoid re-linking most binaries
  # after a branch switch. Defaults to ON.
  "LLVM_APPEND_VC_REV": None,
  # Usually /usr/include
  "LLVM_BINUTILS_INCDIR": None,
  #
  # Build 32-bit executables and libraries on 64-bit systems.
  # This option is available only on some 64-bit Unix systems.
  # Defaults to OFF.
  "LLVM_BUILD_32_BITS": False,
  #
  # Enable additional time/memory expensive checking. Defaults to OFF.
  "LLVM_ENABLE_EXPENSIVE_CHECKS": False,
  #
  # Tell the build system that an IDE is being used.
  # This in turn disables the creation of certain
  # convenience build system targets,
  # such as the various install-* and check-* targets,
  # since IDEs don’t always deal well with a large number of targets.
  # This is usually autodetected, but it can be configured manually
  # to explicitly control the generation of those targets.
  # One scenario where a manual override may be desirable
  # is when using Visual Studio 2017’s CMake integration,
  # which would not be detected as an IDE otherwise.
  "LLVM_ENABLE_IDE": False,
  #
  "COMPILER_RT_INCLUDE_TESTS": False,
  #
  "LLDB_INCLUDE_TESTS": False,
  #
  "CLANG_INCLUDE_TESTS": False,
  #
  "LIBCXXABI_INCLUDE_TESTS": False,
  #
  "LIBCXX_INCLUDE_TESTS": False,
  #
  # Python scripting
  # https://lldb.llvm.org/resources/build.html
  "LLDB_ENABLE_PYTHON": False,
  #
  # Generic line editing, history, Emacs and Vi bindings
  # https://lldb.llvm.org/resources/build.html
  "LLDB_ENABLE_LIBEDIT": False,
  #
  # Text user interface
  # https://lldb.llvm.org/resources/build.html
  "LLDB_ENABLE_CURSES": False,
  #
  # XML
  # https://lldb.llvm.org/resources/build.html
  "LLDB_ENABLE_LIBXML2": False,
  #
  # Lua scripting
  # https://lldb.llvm.org/resources/build.html
  "LLDB_ENABLE_LUA": False,
  #
  # Lossless data compression
  # https://lldb.llvm.org/resources/build.html
  "LLDB_ENABLE_LZMA": False,
  #
  # Generate build targets for the LLVM unit tests.
  # Defaults to ON.
  # You can use this option to disable the generation
  # of build targets for the LLVM unit tests.
  "LLVM_INCLUDE_TESTS": False,
  #
  # Build LLVM unit tests. Defaults to OFF.
  # Targets for building each unit test are generated in any case.
  # You can build a specific unit test using
  # the targets defined under unittests,
  # such as ADTTests, IRTests, SupportTests, etc.
  # (Search for add_llvm_unittest in the subdirectories of unittests
  # for a complete list of unit tests.)
  # It is possible to build all unit tests with the target UnitTests.
  #
  "LLVM_BUILD_TESTS": False,
  #
  # See LLVM_BUILD_TESTS
  "BUILD_TESTS": False,
  #
  "LLVM_BUILD_EXAMPLES": False,
  #
  "LLVM_INCLUDE_EXAMPLES": False,
  #
  "LLVM_BUILD_BENCHMARKS": False,
  #
  "LLVM_INCLUDE_BENCHMARKS": False,
  #
  "LLVM_ENABLE_DOXYGEN": False,
  #
  "LLVM_ENABLE_DOXYGEN_QT_HELP": False,
  #
  "LLVM_DOXYGEN_SVG": False,
  #
  "LLVM_ENABLE_OCAMLDOC": False,
  #
  "LLVM_ENABLE_SPHINX": False,
  #
  # Enable all compiler warnings. Defaults to ON.
  "LLVM_ENABLE_WARNINGS": None,
  #
  # when making a debug or asserts build speed it up by building a release tablegen
  "LLVM_OPTIMIZED_TABLEGEN": True,
  #
  "LLVM_STATIC_LINK_CXX_STDLIB": None,
}

# Users locally they get the 1.0.0 version,
# without defining any env-var at all,
# and CI servers will append the build number.
# USAGE
# version = get_version("1.0.0")
# BUILD_NUMBER=-pre1+build2 conan export-pkg . my_channel/release
def get_version(name, version):
    envvar = os.getenv("{}_BUILD_NUMBER".format(name))
    return (version + envvar) if envvar else version

def get_branch(name, env_name, branch):
    envvar = os.getenv("{}_{}".format(name, env_name))
    return (branch + envvar) if envvar else branch

# stage_tmp_compiler - build compiler with static link to re-build other code, without install step
# (optional) build IWYU, before LLVM_USE_SANITIZER enabled
# stage_runtime - build "libcxx", "libcxxabi", "compiler-rt".
# If LLVM_USE_SANITIZER enabled, than libcxx and libcxxabi will be sanitized.
# stage_llvm - build all code without "libcxx", "libcxxabi".
# Re-build "compiler-rt" (but keep libclang_rt.*san*.so).
# If COMPILER_RT_BUILD_SANITIZERS enabled, than libclang_rt.*san*.so will be created on stage_llvm.
#
# For sanitized builds we expect
# `nm lib/libc++.so* | grep san` - sanitized
# `nm lib/libc++abi.so* | grep san` - sanitized
# `nm bin/llvm-tblgen | grep san` - NOT sanitized
# `nm bin/llvm-ar | grep san` - NOT sanitized
# `nm bin/llvm-config | grep san` - NOT sanitized
# `nm bin/llvm-symbolizer | grep san` - NOT sanitized
# `nm bin/clang | grep san` - NOT sanitized
# `nm lib/libLLVMDemangle.so* | grep san` - NOT sanitized
# `find . -name libclang_rt.*san*.so` - exists
#
# TODO: Optimize and check symbols
# see https://github.com/llvm-mirror/compiler-rt/blob/master/lib/sanitizer_common/symbolizer/scripts/build_symbolizer.sh
#
class LLVM9Conan(ConanFile):
    name = "llvm_9"

    version = get_version(name, "master")

    llvm_version = get_branch(name, "llvm_version", "llvmorg-9.0.1")
    iwyu_version = get_branch(name, "iwyu_version", "clang_9.0")

    description = 'The LLVM Project is a collection of modular and reusable compiler and toolchain technologies'
    topics = ("c++", "conan", "clang", "include-what-you-use", "llvm", "iwyu", "tooling", "compiler")
    #url = "https://github.com/bincrafters/conan-folly" # TODO
    #homepage = "https://github.com/facebook/folly" # TODO
    license = "MIT"

    # Constrains build_type inside a recipe to Release!
    settings = "os_build", "build_type", "arch_build", "compiler", "arch"

    options = {
      **{
        'with_' + library : [True, False] for library in llvm_libs },
      **{
        'with_' + project : [True, False] for project in llvm_projects },
      **{
        'with_' + target : [True, False] for target in llvm_targets },
      **{
        # see LLVM_USE_SANITIZER
        # Sanitizer is well supported on Linux
        # see https://clang.llvm.org/docs/MemorySanitizer.html#handling-external-code
        'use_sanitizer': [
            "Address",
            "Memory",
            "MemoryWithOrigins",
            "Undefined",
            "Thread",
            "DataFlow",
            "Address;Undefined",
            "None"
        ],
        # Enable unwind tables in the binary.
        # Disabling unwind tables can reduce the size of the libraries.
        # Defaults to ON.
        'unwind_tables': [True, False],
        # Add -flto or -flto= flags to the compile and link command lines, enabling link-time optimization.
        # Possible values are Off, On, Thin and Full. Defaults to OFF.
        # TODO: BUG when LTO ON: https://bugs.gentoo.org/show_bug.cgi?format=multiple&id=667108
        # You can set the LLVM_ENABLE_LTO option on your stage-2 build
        # to Thin or Full to enable building LLVM with LTO.
        # These options will significantly increase link time of the binaries
        # in the distribution, but it will create much faster binaries.
        # This option should not be used if your distribution includes static archives,
        # as the objects inside the archive will be LLVM bitcode,
        # which is not portable.
        'lto': ['On', 'Off', 'Full', 'Thin'],
        'fPIC': [True, False],
        'shared': [True, False],
        'rtti': [True, False],
        'threads': [True, False],
        # Build LLVM with exception-handling support.
        # This is necessary if you wish to link against LLVM libraries
        # and make use of C++ exceptions in your own code
        # that need to propagate through LLVM code. Defaults to OFF.
        'exceptions': [True, False],
        'libffi': [True, False],
        # Enable building with zlib to support compression/uncompression in LLVM tools.
        # Defaults to ON.
        'libz': [True, False],
        "include_what_you_use": [True, False]
    }}

    default_options = {
      **{
        'with_' + library : library in default_llvm_libs for library in llvm_libs },
      **{
        'with_' + project : project in default_llvm_projects for project in llvm_projects },
      **{
        'with_' + target : target in default_llvm_targets for target in llvm_targets },
      **{
        'use_sanitizer': 'None',
        'fPIC': True,
        'shared': True,
        'exceptions': False,
        'unwind_tables': True,
        'rtti': False,
        'threads': True,
        'libffi': False,
        'libz': True,
        'lto': 'Off',
        "include_what_you_use": True
    }}

    exports = ["LICENSE.md"]

    exports_sources = ["LICENSE", "README.md", "include/*", "src/*",
                       "cmake/*", "CMakeLists.txt", "tests/*", "benchmarks/*",
                       "scripts/*", "patches/*"]

    generators = 'cmake_find_package', "cmake", "cmake_paths"

    llvm_repo_url = "https://github.com/llvm/llvm-project.git"
    iwyu_repo_url = "https://github.com/include-what-you-use/include-what-you-use.git"

    @property
    def _clang_ver(self):
        return "9.0.1"

    @property
    def _llvm_source_subfolder(self):
        return "llvm_project"

    @property
    def _iwyu_source_subfolder(self):
        return "iwyu"

    @property
    def _libcxx(self):
      return str(self.settings.get_safe("compiler.libcxx"))

    @property
    def _has_sanitizers(self):
      return self.options.use_sanitizer != 'None'

    @property
    def _lower_build_type(self):
      return str(self.settings.build_type).lower()

    # TODO: failed to change compiler
    # llvm-ar: warning: creating t.a
    # llvm-ranlib: error: Exactly one archive should be specified.
    #
    # stage_tmp_compiler builds clang that will be used to build LLVM.
    # If stage_tmp_compiler disabled, than system compiler will be used.
    @property
    def _stage_tmp_compiler_enabled(self):
      return self.flag_to_cmake(os.getenv("LLVM_stage_tmp_compiler_ENABLED", "ON")) == "ON"

    @property
    def _stage_tmp_compiler_folder(self):
      return '{}/stage_tmp_compiler'.format(self.build_folder)

    @property
    def _stage_runtime_folder(self):
      return '{}/stage_runtime'.format(self.build_folder)

    @property
    def _stage_llvm_folder(self):
      return '{}/stage_llvm'.format(self.build_folder)

    @property
    def _iwyu_folder(self):
      return '{}/iwyu'.format(self.build_folder)

    def llvm_env_flag_to_cmake(self, name):
     return self.env_flag_to_cmake(name, llvm_env[name])

    def env_flag_to_cmake(self, name, default):
     return self.flag_to_cmake(os.getenv(name, default))

    def flag_to_cmake(self, value):
     return "ON" if (value == True \
                     or str(value).lower() == "on" \
                     or str(value).lower() == "true") else "OFF"

    def prepend_to_definition(self, cmake, name, value):
      cmake.definitions[name]=value \
        + (" " + cmake.definitions[name] if name in cmake.definitions else "")

    def project_allowed_on_stage_tmp_compiler(self, project):
      return True;

    def runtime_allowed_on_stage_tmp_compiler(self, project):
      return False

    # clang or some clang-tool requires libLLVMDemangle or other llvm lib
    # -> we build sanitized libLLVMDemangle -> clang must be sanitized too.
    # (or link statically to avoid issues)
    def project_allowed_on_stage_runtime(self, project):
      arr = ["libcxx", "libcxxabi", "compiler-rt"]
      if llvm_env["COMPILER_RT_BUILD_CRT"]:
        # clang required due to stage_runtime/lib/clang/9.0.1/lib/linux/clang_rt.crtbegin-x86_64.o
        # by clang_rt.crtbegin-x86_64.o
        arr.extend(["clang"]) # TODO: point to external, not sanitized clang
        if not self.resolve_option("clang"):
          # clang from stage_tmp_compiler required for next stages (it will be used to compile code)
          raise ConanInvalidConfiguration("enable project clang required by COMPILER_RT_BUILD_CRT")
      return project in arr

    def runtime_allowed_on_stage_runtime(self, project):
      return False

    def project_allowed_on_stage_llvm(self, project):
      if (self._has_sanitizers):
        # First, we need to build compiler,
        # than we will be able to build runtimes.
        # We will build runtimes separately if sanitizer enabled.
        return project not in ["libcxx", "libcxxabi"]
      return True;

    def runtime_allowed_on_stage_llvm(self, project):
      return False

    def resolve_option(self, name):
      if name in llvm_projects:
        return getattr(self.options, 'with_' + name)
      if name in llvm_targets:
        return getattr(self.options, 'with_' + name)
      if name in llvm_libs:
        return getattr(self.options, 'with_' + name)
      return getattr(self.options, name)

    # NOTE: If you set global CXX_FLAGS it will affect all projects.
    # Prefer to set project-specific CMAKE_CXX_FLAGS using some env. var.
    def set_definition_from_env(self, cmake, cmake_name, env_name, default_value):
        envvar = os.getenv(env_name, default_value)
        cmake.definitions[cmake_name]=envvar
        self.output.info('{} = {}'.format(env_name, envvar))
        return envvar

    @property
    def _stage_tmp_compiler_llvm_projects(self):
      # NOTE: ignores getattr(self.options, 'with_' + project)
      stage_tmp_compiler_llvm_projects = [project for project in llvm_projects \
        if self.project_allowed_on_stage_tmp_compiler(project)]
      self.output.info('Enabled LLVM stage_tmp_compiler subprojects: {}'.format(', '.join(stage_tmp_compiler_llvm_projects)))
      return stage_tmp_compiler_llvm_projects

    @property
    def _stage_tmp_compiler_llvm_runtimes(self):
      stage_tmp_compiler_llvm_runtimes = [project for project in llvm_projects \
        if getattr(self.options, 'with_' + project) \
        and self.runtime_allowed_on_stage_tmp_compiler(project)]
      self.output.info('Enabled LLVM stage_tmp_compiler runtimes: {}'.format(', '.join(stage_tmp_compiler_llvm_runtimes)))
      return stage_tmp_compiler_llvm_runtimes

    @property
    def _stage_runtime_llvm_projects(self):
      stage_runtime_llvm_projects = [project for project in llvm_projects \
        if getattr(self.options, 'with_' + project) \
        and self.project_allowed_on_stage_runtime(project)]
      self.output.info('Enabled LLVM stage_runtime subprojects: {}'.format(', '.join(stage_runtime_llvm_projects)))
      return stage_runtime_llvm_projects

    @property
    def _stage_runtime_llvm_runtimes(self):
      stage_runtime_llvm_runtimes = [project for project in llvm_projects \
        if getattr(self.options, 'with_' + project) \
        and self.runtime_allowed_on_stage_runtime(project)]
      self.output.info('Enabled LLVM stage_runtime runtimes: {}'.format(', '.join(stage_runtime_llvm_runtimes)))
      return stage_runtime_llvm_runtimes

    @property
    def _stage_llvm_llvm_projects(self):
      stage_llvm_llvm_projects = [project for project in llvm_projects \
        if getattr(self.options, 'with_' + project) \
        and self.project_allowed_on_stage_llvm(project)]
      self.output.info('Enabled LLVM stage_llvm subprojects: {}'.format(', '.join(stage_llvm_llvm_projects)))
      return stage_llvm_llvm_projects

    @property
    def _stage_llvm_llvm_runtimes(self):
      stage_llvm_llvm_runtimes = [project for project in llvm_projects \
        if getattr(self.options, 'with_' + project) \
        and self.runtime_allowed_on_stage_llvm(project)]
      self.output.info('Enabled LLVM stage_llvm runtimes: {}'.format(', '.join(stage_llvm_llvm_runtimes)))
      return stage_llvm_llvm_runtimes

    def use_stage_tmp_compiler_compiler(self, cmake):
        # NOTE: use uninstrumented llvm-tblgen https://stackoverflow.com/q/56454026
        llvm_tblgen = "{}/bin/llvm-tblgen".format(self._stage_tmp_compiler_folder)
        if not os.path.exists(llvm_tblgen):
            raise Exception("Unable to find path: {}".format(llvm_tblgen))
        # Full path to a native TableGen executable (usually named llvm-tblgen).
        # This is intended for cross-compiling: if the user sets this variable,
        # no native TableGen will be created.
        cmake.definitions["LLVM_TABLEGEN"]=llvm_tblgen

        llvm_clang = "{}/bin/clang".format(self._stage_tmp_compiler_folder)
        if not os.path.exists(llvm_clang):
            raise Exception("Unable to find path: {}".format(llvm_clang))
        cmake.definitions["CMAKE_C_COMPILER"]=llvm_clang

        llvm_clangpp = "{}/bin/clang++".format(self._stage_tmp_compiler_folder)
        if not os.path.exists(llvm_clangpp):
            raise Exception("Unable to find path: {}".format(llvm_clangpp))
        cmake.definitions["CMAKE_CXX_COMPILER"]=llvm_clangpp

        # TODO: use llvm-ar or llvm-lib?
        # llvm_ar = "{}/bin/llvm-ar".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_ar):
        #     raise Exception("Unable to find path: {}".format(llvm_ar))
        # cmake.definitions["CMAKE_AR"]=llvm_ar

        # llvm_strip = "{}/bin/llvm-strip".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_strip):
        #     raise Exception("Unable to find path: {}".format(llvm_strip))
        # cmake.definitions["CMAKE_STRIP"]=llvm_strip
        #
        # llvm_objcopy = "{}/bin/llvm-objcopy".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_objcopy):
        #     raise Exception("Unable to find path: {}".format(llvm_objcopy))
        # cmake.definitions["CMAKE_OBJCOPY"]=llvm_objcopy
        #
        # llvm_objdump = "{}/bin/llvm-objdump".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_objdump):
        #     raise Exception("Unable to find path: {}".format(llvm_objdump))
        # cmake.definitions["CMAKE_OBJDUMP"]=llvm_objdump
        #
        # llvm_nm = "{}/bin/llvm-nm".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_nm):
        #     raise Exception("Unable to find path: {}".format(llvm_nm))
        # cmake.definitions["CMAKE_NM"]=llvm_nm
        #
        # llvm_size = "{}/bin/llvm-size".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_size):
        #     raise Exception("Unable to find path: {}".format(llvm_size))
        # cmake.definitions["CMAKE_SIZE"]=llvm_size
        #
        # llvm_readelf = "{}/bin/llvm-readelf".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_readelf):
        #     raise Exception("Unable to find path: {}".format(llvm_readelf))
        # cmake.definitions["CMAKE_READELF"]=llvm_readelf

        # TODO: use lld-link or ld.lld?
        # llvm_ld = "{}/bin/lld-link".format(self._stage_tmp_compiler_folder)
        # #llvm_ld = "{}/bin/ld.lld".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_ld):
        #     raise Exception("Unable to find path: {}".format(llvm_ld))
        # cmake.definitions["CMAKE_LINKER"]=llvm_ld

        # see lld in LLVM_ENABLE_PROJECTS
        # This option is equivalent to -DLLVM_USE_LINKER=lld,
        # except during a 2-stage build where a dependency
        # is added from the first stage to the second ensuring
        # that lld is built before stage_runtime begins.
        # cmake.definitions["LLVM_ENABLE_LLD"]="ON"

        # LLVM_ENABLE_LLD and LLVM_USE_LINKER can't be set at the same time
        # if (not "LLVM_ENABLE_LLD" in cmake.definitions) \
        #     or cmake.definitions["LLVM_ENABLE_LLD"] != "ON":
        #   cmake.definitions["LLVM_USE_LINKER"]=llvm_ld

        # TODO: use llvm-as or clang?
        # llvm_asm = "{}/bin/llvm-as".format(self._stage_tmp_compiler_folder)
        # llvm_asm = "{}/bin/clang".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_asm):
        #     raise Exception("Unable to find path: {}".format(llvm_asm))
        # cmake.definitions["CMAKE_ASM_COMPILER"]=llvm_asm

        # TODO: use llvm-rc-rc or llvm-rc
        # llvm_rc = "{}/bin/llvm-rc".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_rc):
        #     raise Exception("Unable to find path: {}".format(llvm_rc))
        # cmake.definitions["CMAKE_RC_COMPILER"]=llvm_rc
        #
        # llvm_ranlib = "{}/bin/llvm-ranlib".format(self._stage_tmp_compiler_folder)
        # if not os.path.exists(llvm_ranlib):
        #     raise Exception("Unable to find path: {}".format(llvm_ranlib))
        # cmake.definitions["CMAKE_RANLIB"]=llvm_ranlib

        llvm_symbolizer = "{}/bin/llvm-symbolizer".format(self._stage_tmp_compiler_folder)
        if not os.path.exists(llvm_symbolizer):
            raise Exception("Unable to find path: {}".format(llvm_symbolizer))
        cmake.definitions['LLVM_SYMBOLIZER_PATH'] = llvm_symbolizer
        os.environ.update({"SYMBOLIZER": llvm_symbolizer})

        llvm_config = "{}/bin/llvm-config".format(self._stage_tmp_compiler_folder)
        if not os.path.exists(llvm_config):
            raise Exception("Unable to find path: {}".format(llvm_config))
        cmake.definitions['LLVM_CONFIG_PATH'] = llvm_config
        os.environ.update({"LLVM_CONFIG_PATH": llvm_config})

        # To prevent cmake from checking libstdcxx version.
        # cmake.definitions['LLVM_ENABLE_LIBCXX'] = 'ON'

        # Don't depend on the host libatomic library.
        # cmake.definitions['LIBCXX_HAS_ATOMIC_LIB'] = 'OFF'

        # # LLVM_LIBDIR_SUFFIX
        #
        # # -nostdinc++ FIXES /usr/include/c++/9/bits/cxxabi_init_exception.h:38:10:
        # # fatal error: 'stddef.h' file not found
        # cflags = []
        # cflags.append('-nostdinc++')
        # #cflags.append('-nodefaultlibs++')
        # #cflags.append('-std=c++11')
        # cflags.append("-cxx-isystem{}/include/c++".format(self._stage_tmp_compiler_folder))
        # cflags.append("-isystem{}/include/c++/v1".format(self._stage_tmp_compiler_folder))
        # #cflags.append("-cxx-isystem{}/include/c++/v1".format(self._stage_tmp_compiler_folder))
        # #cflags.append("-isystem{}/projects/libcxx/include".format(self._stage_tmp_compiler_folder))
        # cflags.append("-isystem{}/lib/clang/9.0.1/include".format(self._stage_tmp_compiler_folder))
        # cflags.append("-isystem{}/include".format(self._stage_tmp_compiler_folder))
        # cflags.append("-resource-dir {}/lib/clang/9.0.1".format(self._stage_tmp_compiler_folder))
        # cflags.append("-L\"{}/lib\"".format(self._stage_tmp_compiler_folder))
        # cflags.append("-Wl,-rpath,{}/lib".format(self._stage_tmp_compiler_folder))
        # # -stdlib=libc++ is a Clang (not GCC) option
        # cflags.append("-stdlib=libc++")
        # cflags.append("-lc++abi")
        # cflags.append("-lc++")
        # cflags.append("-latomic")
        # cflags.append("-lpthread")
        # cflags.append("-fuse-ld=lld")
        # cflags.append("-print-search-dirs")
        #
        # # TODO
        # # cflags.append("-m64")
        #
        # # Static linking libc++
        # #cflags.append("-static")
        # #
        # #cflags.append("-cxx-isystem{}/projects/libcxx/include".format(self._stage_tmp_compiler_folder))
        # #cflags.append("-L{}/projects/libcxx/lib".format(self._stage_tmp_compiler_folder))
        # #cflags.append("-Wl,-rpath,{}/projects/libcxx/lib".format(self._stage_tmp_compiler_folder))
        # #
        # #cflags.append("-lc++abi -lunwind -lc++ -lm -lc")
        # #cflags.append("-Wno-unused-command-line-argument")
        # #cflags.append("-Wno-error=unused-command-line-argument")
        # #cflags.append("-nostdinc++")
        # #cflags.append("-nodefaultlibs")
        # #cflags.append("-lunwind")
        # #cflags.append("-lc++")
        # #cflags.append("-lm")
        # #cflags.append("-lc")
        # for item in cflags:
        #   self.prepend_to_definition(cmake, "CMAKE_CXX_FLAGS", item)
        #   self.prepend_to_definition(cmake, "CMAKE_C_FLAGS", item)
        #   self.prepend_to_definition(cmake, "CMAKE_ASM_FLAGS", item)
        #   self.prepend_to_definition(cmake, "COMPILER_RT_TEST_COMPILER_CFLAGS", item)
        #
        # ldflags = []
        # ldflags.append("-stdlib=libc++")
        # ldflags.append("-lc++abi")
        # ldflags.append("-lc++")
        # ldflags.append("-latomic")
        # ldflags.append("-lpthread")
        # ldflags.append("-fuse-ld=lld")
        # #ldflags.append("-L{}/projects/libcxx/lib".format(self._stage_tmp_compiler_folder))
        # ldflags.append("-L{}/lib".format(self._stage_tmp_compiler_folder))
        # ldflags.append("-resource-dir {}/lib/clang/9.0.1".format(self._stage_tmp_compiler_folder))
        # ldflags.append("-Wl,-rpath,{}/lib".format(self._stage_tmp_compiler_folder))
        # for item in ldflags:
        #   self.prepend_to_definition(cmake, "CMAKE_EXE_LINKER_FLAGS", item)
        #   self.prepend_to_definition(cmake, "CMAKE_SHARED_LINKER_FLAGS", item)
        #   self.prepend_to_definition(cmake, "CMAKE_MODULE_LINKER_FLAGS", item)

    # Do not copy large files
    # https://stackoverflow.com/a/13814557
    def copytree(self, src, dst, symlinks=False, ignore=None, verbose=False):
        if not os.path.exists(dst):
            os.makedirs(dst)
        ignore_list = ['.travis.yml', '.git', '.make', '.o', '.obj', '.marks', \
                       '.internal', 'CMakeFiles', 'CMakeCache', 'static_test_env', \
                       'test']
        for item in os.listdir(src):
            if item not in ignore_list:
              s = os.path.join(src, item)
              d = os.path.join(dst, item)
              if verbose:
                self.output.info('copying %s into %d' % (s, d))
              if os.path.isdir(s):
                  self.copytree(s, d, symlinks, ignore)
              else:
                  if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                      shutil.copy2(s, d)
            elif verbose:
              self.output.info('IGNORED copying %s' % (item))

    # stage_tmp_compiler: build compiler to re-build other code.
    # * Force static linking
    # * Do not run install
    def build_stage_tmp_compiler(self):
        self.output.info('stage_tmp_compiler')

        if not self.resolve_option("clang"):
          # clang from stage_tmp_compiler required for next stages (it will be used to compile code)
          raise ConanInvalidConfiguration("enable project clang for stage_tmp_compiler")

        # don't hang all CPUs and force OS to kill build process
        cpu_count = max(tools.cpu_count() - 2, 1)
        self.output.info('Detected %s CPUs' % (cpu_count))

        # useful if you run `conan build` multiple times during development
        if os.path.exists("CMakeCache.txt"):
          os.remove("CMakeCache.txt")
          self.output.info("removed CMakeCache.txt")

        # NOTE: builds `libcxx;libcxxabi` separately (for sanitizers support)
        cmake = self._configure_cmake(\
            llvm_enable_projects = ';'.join(self._stage_tmp_compiler_llvm_projects), \
            llvm_runtimes = ';'.join(self._stage_tmp_compiler_llvm_runtimes), \
        )

        # NOTE: Force static linking
        cmake.definitions["BUILD_SHARED_LIBS"]="OFF"
        cmake.definitions["SHARED_LIBS"]="OFF"
        cmake.definitions["SHARED"]="OFF"

        # see lld in LLVM_ENABLE_PROJECTS
        # This option is equivalent to -DLLVM_USE_LINKER=lld,
        # except during a 2-stage build where a dependency
        # is added from the first stage to the second ensuring
        # that lld is built before stage_runtime begins.
        # cmake.definitions["LLVM_ENABLE_LLD"]="ON"

        if not os.path.exists(self._stage_tmp_compiler_folder):
            os.makedirs(self._stage_tmp_compiler_folder)

        llvm_src_dir = os.path.join(self._llvm_source_subfolder, "llvm")
        self.output.info('llvm_src_dir is {}'.format(llvm_src_dir))
        # The CMakeLists.txt file must be in `source_folder`
        cmake.configure(source_folder=llvm_src_dir, build_folder=self._stage_tmp_compiler_folder)

        # see https://fuchsia.googlesource.com/fuchsia/+/HEAD/docs/development/build/toolchain.md
        # -j flag for parallel builds
        cmake.build(args=["--", "-j%s" % cpu_count])

        # NOTE: No install for stage_tmp_compiler
        # cmake.install()

        #self.copytree('{}'.format(self.build_folder), '{}'.format(self._stage_tmp_compiler_folder))
        llvm_clang = "{}/bin/clang".format(self._stage_tmp_compiler_folder)
        if not os.path.exists(llvm_clang):
            raise Exception("ERROR: Unable to find path: {}".format(llvm_clang))

    def build_iwyu(self):
        self.output.info('stage iwyu')

        if not os.path.exists(self._iwyu_folder):
            os.makedirs(self._iwyu_folder)

        # NOTE: builds before sanitized `libcxx;libcxxabi;compiler-rt;`
        if self.options.include_what_you_use:
            # Using the helper attributes cmake.command_line and cmake.build_config
            # because cmake.definitions["CMAKE_PREFIX_PATH"] failed
            with tools.chdir(self._iwyu_source_subfolder):
                cmake = CMake(self)
                # cmake.command_line - Arguments and flags calculated by
                # the build helper that will be applied.
                # It indicates the generator, the Conan definitions
                # and the flags converted from the specified Conan settings.
                # For example:
                # -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release ... -DCONAN_C_FLAGS=-m64 -Wno-dev
                self.run("cmake -B build -S . %s -DCMAKE_PREFIX_PATH=%s -DIWYU_LLVM_ROOT_PATH=%s" %
                                (cmake.command_line, self._iwyu_folder, self._stage_llvm_folder))
                with tools.chdir('build'):
                    # cmake.build_config - Value for --config option
                    # for Multi-configuration IDEs.
                    # This flag will only be set
                    # if the generator is_multi_configuration
                    # and build_type was not forced in constructor class.
                    # An example of the value of this property could be:
                    # --config Release
                    self.run('cmake --build . %s' % (cmake.build_config))
                    self.run('cmake --build . --target install')

    def build_stage_runtime(self):
        self.output.info('stage_runtime')

        self.old_env = dict(os.environ)

        # useful if you run `conan build` multiple times during development
        if os.path.exists("CMakeCache.txt"):
          os.remove("CMakeCache.txt")
          self.output.info("removed CMakeCache.txt")

        # We want to enable sanitizers on `libcxx;libcxxabi;compiler-rt`,
        # but NOT on whole LLVM.
        # Sanitizer requires that all program code is instrumented.
        # This also includes any libraries that the program depends on, even libc.
        # NOTE: To build with MSan support you first need to build libc++ with MSan support.
        # MemoryWithOrigins enables both -fsanitize=memory and -fsanitize-memory-track-origins
        # see https://github.com/google/sanitizers/wiki/MemorySanitizer#origins-tracking
        llvm_sanitizer_key = str(self.options.use_sanitizer)
        self.output.info('llvm_sanitizer_key = {}'.format(llvm_sanitizer_key))

        # Build runtimes separately
        # NOTE: builds `libcxx;libcxxabi` separately (for sanitizers support)
        cmake = self._configure_cmake( \
            llvm_enable_projects = ';'.join(self._stage_runtime_llvm_projects), \
            llvm_runtimes = ';'.join(self._stage_runtime_llvm_runtimes), \
            llvm_sanitizer=llvm_sanitizer_key)

        if self._stage_tmp_compiler_enabled:
          self.use_stage_tmp_compiler_compiler(cmake)

        # LLVM_TOOLCHAIN_TOOLS = "dsymutil;llc;opt;llvm-ar;llvm-ranlib;llvm-lib;llvm-nm;llvm-objcopy;llvm-objdump;llvm-rc;llvm-profdata;llvm-symbolizer"

        # LLVM_INSTALL_TOOLCHAIN_ONLY

        # Distribution is a target building only
        # the components selected by the
        # LLVM_DISTRIBUTION_COMPONENTS variable, see ninja install-distribution
        # LLVM_DISTRIBUTION_COMPONENTS = "clang;lld;clang-resource-headers;builtins-armv6m-none-eabi;builtins-armv7m-none-eabi;builtins-armv7em-none-eabi;runtimes;${LLVM_TOOLCHAIN_TOOLS}"

        # Use the LLVM_RUNTIME_TARGETS to specify
        # the runtimes targets to be built.
        # LLVM_RUNTIME_TARGETS="x86_64-fuchsia;aarch64-fuchsia"

        # Use the LLVM_BUILTIN_TARGETS to specify
        # the compiler-rt builtin targets.
        # LLVM_BUILTIN_TARGETS = "x86_64-fuchsia;aarch64-fuchsia"

        # LLVM_CONFIG_EXE

        # CLANG_TABLEGEN

        # LLVM_EXTERNAL_{CLANG,LLD,POLLY}_SOURCE_DIR:PATH

        # -j flag for parallel builds
        # don't hang all CPUs and force OS to kill build process
        cpu_count = max(tools.cpu_count() - 2, 1)
        self.output.info('Detected %s CPUs' % (cpu_count))

        if not os.path.exists(self._stage_runtime_folder):
            os.makedirs(self._stage_runtime_folder)

        llvm_src_dir = os.path.join(self._llvm_source_subfolder, "llvm")
        self.output.info('llvm_src_dir is {}'.format(llvm_src_dir))

        # NOTE: builds both static and shared runtime libraries
        cmake.definitions["BUILD_SHARED_LIBS"]="ON"
        cmake.definitions["SHARED_LIBS"]="ON"
        cmake.definitions["SHARED"]="ON"

        # The CMakeLists.txt file must be in `source_folder`
        cmake.configure(source_folder=llvm_src_dir, build_folder=self._stage_runtime_folder)

        # We assume that no one need recipe with whole LLVM codebase sanitized
        # but a lot of people may want to have sanitized libc++ and libc++abi
        # https://github.com/awslabs/amazon-kinesis-video-streams-webrtc-sdk-c/blob/master/.github/msan-tester.Dockerfile
        cmake.build(args=["--", "cxx", "cxxabi", "-j%s" % cpu_count])
        cmake.install(args=["--", "cxx", "cxxabi"])

        # NOTE: builds both static and shared runtime libraries
        cmake.definitions["BUILD_SHARED_LIBS"]="OFF"
        cmake.definitions["SHARED_LIBS"]="OFF"
        cmake.definitions["SHARED"]="OFF"

        # The CMakeLists.txt file must be in `source_folder`
        cmake.configure(source_folder=llvm_src_dir, build_folder=self._stage_runtime_folder)

        # We assume that no one need recipe with whole LLVM codebase sanitized
        # but a lot of people may want to have sanitized libc++ and libc++abi
        # https://github.com/awslabs/amazon-kinesis-video-streams-webrtc-sdk-c/blob/master/.github/msan-tester.Dockerfile
        cmake.build(args=["--", "cxx", "cxxabi", "-j%s" % cpu_count])
        cmake.install(args=["--", "cxx", "cxxabi"])

        os.environ.clear()
        os.environ.update(self.old_env)

    def build_stage_llvm(self):
        self.output.info('stage_llvm')

        # don't hang all CPUs and force OS to kill build process
        cpu_count = max(tools.cpu_count() - 2, 1)
        self.output.info('Detected %s CPUs' % (cpu_count))

        # useful if you run `conan build` multiple times during development
        if os.path.exists("CMakeCache.txt"):
          os.remove("CMakeCache.txt")
          self.output.info("removed CMakeCache.txt")

        # NOTE: builds `libcxx;libcxxabi` separately (for sanitizers support)
        cmake = self._configure_cmake(\
            llvm_enable_projects = ';'.join(self._stage_llvm_llvm_projects), \
            llvm_runtimes = ';'.join(self._stage_llvm_llvm_runtimes), \
        )

        if self._stage_tmp_compiler_enabled:
          self.use_stage_tmp_compiler_compiler(cmake)

        # see lld in LLVM_ENABLE_PROJECTS
        # This option is equivalent to -DLLVM_USE_LINKER=lld,
        # except during a 2-stage build where a dependency
        # is added from the first stage to the second ensuring
        # that lld is built before stage_runtime begins.
        # cmake.definitions["LLVM_ENABLE_LLD"]="ON"

        if not os.path.exists(self._stage_llvm_folder):
            os.makedirs(self._stage_llvm_folder)

        llvm_src_dir = os.path.join(self._llvm_source_subfolder, "llvm")
        self.output.info('llvm_src_dir is {}'.format(llvm_src_dir))
        # The CMakeLists.txt file must be in `source_folder`
        cmake.configure(source_folder=llvm_src_dir, build_folder=self._stage_llvm_folder)

        # see https://fuchsia.googlesource.com/fuchsia/+/HEAD/docs/development/build/toolchain.md
        # -j flag for parallel builds
        cmake.build(args=["--", "-j%s" % cpu_count])
        cmake.install()

    def _supports_compiler(self):
        compiler = self.settings.compiler.value
        version = tools.Version(self.settings.compiler.version)
        major_rev, minor_rev = int(version.major), int(version.minor)

        unsupported_combinations = [
            [compiler == 'gcc', major_rev == 5, minor_rev < 1],
            [compiler == 'gcc', major_rev < 5],
            [compiler == 'clang', major_rev < 4],
            [compiler == 'apple-clang', major_rev < 9],
            [compiler == 'Visual Studio', major_rev < 15]
        ]
        if any(all(combination) for combination in unsupported_combinations):
            message = 'unsupported compiler: "{}", version "{}"'
            raise ConanInvalidConfiguration(message.format(compiler, version))

    def configure(self):
        if self.options.exceptions and not self.options.rtti:
            message = 'Cannot enable exceptions without rtti support'
            raise ConanInvalidConfiguration(message)

        self._supports_compiler()

        if self.settings.build_type != "Release":
          raise ConanInvalidConfiguration("This library is compatible only with Release builds. Debug build of llvm may take a lot of time or crash due to lack of RAM or CPU")

        # To build llvm with sanitizers:
        # * build compiler-rt without LLVM_USE_SANITIZER,
        #   but with COMPILER_RT_BUILD_SANITIZERS="ON".
        #   Check that libclang_rt.*san*.so exists: `find . -name libclang_rt.*so*`.
        # * build sanitized cxx cxxabi compiler-rt with LLVM_USE_SANITIZER.
        #   Check that libc++ sanitized: `nm lib/libc++.so.1 | grep san`.
        if not self.resolve_option("compiler-rt") and self._has_sanitizers:
          raise ConanInvalidConfiguration("sanitizers require compiler-rt")

        # see https://clang.llvm.org/docs/MemorySanitizer.html
        if self.options.use_sanitizer=="Memory" \
           or self.options.use_sanitizer=="MemoryWithOrigins" \
           and not self.options.shared:
          raise ConanInvalidConfiguration("Static linking is not supported with MemorySanitizer.")

        # Memory Sanitizer requires that all of the code compiled into your program is instrumented,
        # including the C++ standard library libstdc++ or libc++.
        # You need to build both libc++ and libc++abi with *San.
        # Thankfully, it does carve out the C stdlib as an exception
        # see https://clang.llvm.org/docs/MemorySanitizer.html
        # see https://github.com/google/sanitizers/wiki/MemorySanitizerLibcxxHowTo#instrumented-libc
        if self._has_sanitizers and not self.options.with_libcxx:
          raise ConanInvalidConfiguration("Sanitizer requires libcxx project.")

        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, '14')

        if self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version) < "19.1":
            raise ConanInvalidConfiguration("Need MSVC >= 19.1")

        if self._has_sanitizers \
            and not self.settings.compiler in ['clang', 'apple-clang', 'clang-cl']:
            raise ConanInvalidConfiguration("Sanitized package is only compatible with clang")

        if self.options.include_what_you_use and self._has_sanitizers:
            raise ConanInvalidConfiguration("disable include_what_you_use when sanitizers enabled")

    def requirements(self):
        self.output.info('self.settings.compiler {}'.format(self.settings.compiler))

    def source(self):
        # LLVM
        self.run('git clone -b {} --progress --depth 100 --recursive --recurse-submodules {} {}'.format(self.llvm_version, self.llvm_repo_url, self._llvm_source_subfolder))

        # IWYU
        if self.options.include_what_you_use:
            self.run('git clone -b {} --progress --depth 100 --recursive --recurse-submodules {} {}'.format(self.iwyu_version, self.iwyu_repo_url, self._iwyu_source_subfolder))

    # see https://releases.llvm.org/9.0.0/docs/CMake.html
    def _configure_cmake(self, llvm_enable_projects, llvm_runtimes, llvm_sanitizer="None"):
        self.output.info('configuring LLVM')

        llvm_src_dir = os.path.join(self._llvm_source_subfolder, "llvm")
        self.output.info('llvm_src_dir is {}'.format(llvm_src_dir))

        compiler_rt_src_dir = os.path.join(self._llvm_source_subfolder, "compiler-rt")
        self.output.info('compiler_rt_src_dir is {}'.format(compiler_rt_src_dir))

        for patch in os.listdir(os.path.join(self.source_folder, "patches")):
            patchpath = os.path.join(self.source_folder, "patches", patch)
            self.output.info('patch is {}'.format(patchpath))
            tools.patch(base_path=compiler_rt_src_dir, patch_file=patchpath)

        cmake = CMake(self, set_cmake_flags=True)
        cmake.verbose = True

        # don't hang all CPUs and force OS to kill build process
        cpu_count = max(tools.cpu_count() - 3, 1)
        self.output.info('Detected %s CPUs' % (cpu_count))

        # https://bugs.llvm.org/show_bug.cgi?id=44074
        # cmake.definitions["EXECUTION_ENGINE_USE_LLVM_UNWINDER"]="ON"

        # Semicolon-separated list of projects to build
        # (clang;clang-tools-extra;compiler-rt;debuginfo-tests;libc;libclc;libcxx;libcxxabi;libunwind;lld;lldb;llgo;mlir;openmp;parallel-libs;polly;pstl),
        # or "all".
        # This flag assumes that projects are checked out side-by-side and not nested,
        # i.e. clang needs to be in parallel of llvm instead of nested in llvm/tools.
        # This feature allows to have one build for only LLVM and another
        # for clang+llvm using the same source checkout.
        cmake.definitions["LLVM_ENABLE_PROJECTS"]=llvm_enable_projects

        # see Building LLVM with CMake https://llvm.org/docs/CMake.html
        cmake.definitions["LLVM_PARALLEL_COMPILE_JOBS"]=\
          self.flag_to_cmake(os.getenv("LLVM_PARALLEL_COMPILE_JOBS", str(cpu_count)))

        # Microsoft Visual C++ specific
        # Specifies the maximum number of parallel compiler jobs
        # to use per project when building with msbuild or Visual Studio.
        # Only supported for the Visual Studio 2010 CMake generator.
        # 0 means use all processors. Default is 0.
        cmake.definitions["LLVM_COMPILER_JOBS"]=\
          self.flag_to_cmake(os.getenv("LLVM_COMPILER_JOBS", str(cpu_count)))

        cmake.definitions["LLVM_PARALLEL_LINK_JOBS"]=\
          self.flag_to_cmake(os.getenv("LLVM_PARALLEL_LINK_JOBS", "1"))

        # TODO: make customizable
        # This should speed up building debug builds
        # see https://www.productive-cpp.com/improving-cpp-builds-with-split-dwarf/
        #cmake.definitions["LLVM_USE_SPLIT_DWARF"]="ON"

        # force Release build
        #cmake.definitions["CMAKE_BUILD_TYPE"]="Release"

        if len(llvm_runtimes) > 0:
          # Semicolon-separated list of runtimes to build
          # (libcxx;libcxxabi;libunwind;compiler-rt;...), or "all".
          # Enable some projects to be built as runtimes
          # which means these projects will be built using the just-built rather
          # than the host compiler
          cmake.definitions["LLVM_ENABLE_RUNTIMES"]=llvm_runtimes

        # sanitizer runtimes - runtime libraries that are required
        # to run the code with sanitizer instrumentation.
        # This includes runtimes for:
        # AddressSanitizer ThreadSanitizer UndefinedBehaviorSanitizer
        # MemorySanitizer LeakSanitizer DataFlowSanitizer
        self.output.info('llvm_sanitizer = {}'.format(llvm_sanitizer))
        if len(llvm_sanitizer) > 0 and llvm_sanitizer != 'None':
            cmake.definitions["LLVM_USE_SANITIZER"]=str(llvm_sanitizer)
            self.output.info('LLVM_USE_SANITIZER = {}'.format(llvm_sanitizer))

            # see libcxx in LLVM_ENABLE_PROJECTS
            # compile using libc++ instead of the system default
            if os.getenv("LLVM_ENABLE_LIBCXX"):
              cmake.definitions["LLVM_ENABLE_LIBCXX"]="ON"

            # LIBCXXABI_ENABLE_ASSERTIONS=OFF
            # LIBCXXABI_ENABLE_EXCEPTIONS=OFF
            # LIBCXXABI_ENABLE_SHARED=OFF
            # LIBCXX_ENABLE_ASSERTIONS=OFF
            # LIBCXX_ENABLE_EXCEPTIONS=OFF
            # LIBCXX_ENABLE_RTTI=OFF
            # LIBCXX_ENABLE_SHARED=OFF
            # LIBCXX_HAS_ATOMIC_LIB

            # Build clang-tidy/clang-format
            cmake.definitions["LLVM_TOOL_CLANG_TOOLS_EXTRA_BUILD"]="OFF"

            cmake.definitions["LLVM_TOOL_OPENMP_BUILD"]="OFF"

            cmake.definitions["CLANG_ENABLE_ARCMT"]="OFF"
            cmake.definitions["CLANG_ENABLE_STATIC_ANALYZER"]="OFF"
            cmake.definitions["CLANG_ENABLE_FORMAT"]="OFF"
            #cmake.definitions["CLANG_TOOL_CLANG_CHECK_BUILD"]="OFF"
            #cmake.definitions["CLANG_PLUGIN_SUPPORT"]="OFF"
            cmake.definitions["CLANG_TOOL_CLANG_FORMAT_BUILD"]="OFF"
            cmake.definitions["CLANG_TOOL_CLANG_FUZZER_BUILD"]="OFF"

            # TODO: make customizable
            # LLVM_BUILD_EXTERNAL_COMPILER_RT:BOOL

            # use uninstrumented llvm-tblgen
            # see https://stackoverflow.com/questions/56454026/building-libc-with-memorysanitizer-instrumentation-fails-due-to-memorysanitize
            #llvm_tblgen=os.path.join(self.package_folder, "bin", "llvm-tblgen")
            #cmake.definitions["LLVM_TABLEGEN"]="{}".format(llvm_tblgen)
            #if not os.path.exists(llvm_tblgen):
            #    raise Exception("Unable to find path: {}".format(llvm_tblgen))
        else:
            # use UNINSTRUMENTED llvm-ar, llvml-symbolizer, etc.
            cmake.definitions["LLVM_USE_SANITIZER"]=""
            #cmake.definitions["LLVM_TOOL_CLANG_TOOLS_EXTRA_BUILD"]="ON"
            cmake.definitions["CLANG_ENABLE_STATIC_ANALYZER"]=\
              self.flag_to_cmake(os.getenv("CLANG_ENABLE_STATIC_ANALYZER", "ON"))
            cmake.definitions["CLANG_TOOL_CLANG_CHECK_BUILD"]=\
              self.flag_to_cmake(os.getenv("CLANG_TOOL_CLANG_CHECK_BUILD", "ON"))
            cmake.definitions["CLANG_PLUGIN_SUPPORT"]=\
              self.flag_to_cmake(os.getenv("CLANG_PLUGIN_SUPPORT", "ON"))
            cmake.definitions["CLANG_TOOL_CLANG_FORMAT_BUILD"]=\
              self.flag_to_cmake(os.getenv("CLANG_TOOL_CLANG_FORMAT_BUILD", "ON"))
            cmake.definitions["CLANG_ENABLE_FORMAT"]=\
              self.flag_to_cmake(os.getenv("CLANG_ENABLE_FORMAT", "ON"))
            cmake.definitions["CLANG_TOOL_CLANG_FUZZER_BUILD"]=\
              self.flag_to_cmake(os.getenv("CLANG_TOOL_CLANG_FUZZER_BUILD", "ON"))

        # Build LLVM and tools with PGO instrumentation
        # If enabled, source-based code coverage instrumentation
        # is enabled while building llvm.
        # To enable building with -fprofile-instr-generate
        if os.getenv("LLVM_BUILD_INSTRUMENTED"):
          self.set_definition_from_env(cmake, cmake_name = "LLVM_BUILD_INSTRUMENTED", \
            env_name = "LLVM_BUILD_INSTRUMENTED", default_value = "OFF")

        # This is either directly the C++ ABI library or the full C++ library
        # which pulls in the ABI transitively.
        # crt_defines['SANITIZER_CXX_ABI'] = 'libcxxabi'

        # Specify C++ library to use for tests.
        # SANITIZER_TEST_CXX

        # Make libc++.so a symlink to libc++.so.x instead of a linker script that
        # also adds -lc++abi.  Statically link libc++abi to libc++ so it is not
        # necessary to pass -lc++abi explicitly.  This is needed only for Linux.
        # if utils.host_is_linux():
        #     stage_runtime_extra_defines['LIBCXX_ENABLE_STATIC_ABI_LIBRARY'] = 'ON'
        #     stage_runtime_extra_defines['LIBCXX_ENABLE_ABI_LINKER_SCRIPT'] = 'OFF'

        # LLVM_DYLIB_EXPORT_ALL

        # LLVM_BUILD_LLVM_C_DYLIB

        cmake.definitions['LLVM_ENABLE_LTO'] = self.options.lto

        cmake.definitions["LLVM_ENABLE_ZLIB"]="ON" if self.options.libz else "OFF"

        # TODO
        # cmake.definitions["LLVM_ENABLE_TERMINFO"]="ON" if self.options.terminfo else "OFF"

        cmake.definitions["LLVM_ENABLE_THREADS"]="ON" if self.options.threads else "OFF"

        # Indicates whether the LLVM Interpreter will be linked with
        # the Foreign Function Interface library (libffi)
        # in order to enable calling external functions.
        # If the library or its headers are installed in a custom location,
        # you can also set the variables FFI_INCLUDE_DIR and FFI_LIBRARY_DIR
        # to the directories where ffi.h and libffi.so can be found, respectively.
        # Defaults to OFF.
        cmake.definitions["LLVM_ENABLE_FFI"]="ON" if self.options.libffi else "OFF"

        # FFI_LIBRARY_DIR

        # Build LLVM tools. Defaults to ON.
        # Targets for building each tool are generated in any case.
        # You can build a tool separately by invoking its target.
        # For example, you can build llvm-as
        # with a Makefile-based system
        # by executing make llvm-as at the root of your build directory.
        cmake.definitions["LLVM_BUILD_TOOLS"]="OFF" \
          if (len(llvm_sanitizer) > 0 and llvm_sanitizer != 'None') \
          else self.flag_to_cmake(os.getenv("LLVM_BUILD_TOOLS", "ON"))

        #cmake.definitions["LLVM_INCLUDE_UTILS"]="ON"
        #cmake.definitions["LLVM_BUILD_UTILS"]="ON"
        # LLVM_INSTALL_UTILS
        # LLVM_TOOLS_INSTALL_DIR

        # NOTE: msan build requires
        # existing file ~/.conan/data/.../master/conan/stable/package/.../lib/clang/x.x.x/lib/linux/libclang_rt.msan_cxx-x86_64.a
        # same for tsan\ubsan\asan\etc.
        COMPILER_RT_BUILD_SANITIZERS = self.set_definition_from_env(cmake, cmake_name = "COMPILER_RT_BUILD_SANITIZERS", \
          env_name = "COMPILER_RT_BUILD_SANITIZERS", default_value = "ON")
        if COMPILER_RT_BUILD_SANITIZERS != "ON" and self._has_sanitizers:
            raise Exception("sanitizers require COMPILER_RT_BUILD_SANITIZERS=ON")

        # propagate cmake vars based on env. vars with defaults from `llvm_env`
        for key, default_value in llvm_env.items():
          if default_value is None:
            # None means that default value not overriden i.e. same as in LLVM
            continue
          # dict `llvm_env` can store only boolean values
          if not isinstance(default_value, bool):
            raise Exception("not boolean default value in env. option: {}={}".format(key, str(default_value)))
          value = self.llvm_env_flag_to_cmake(key)
          cmake.definitions[key] = value
          self.output.info('%s -> %s' % (key, value))

        # To build debug version of *San runtime library.
        # cmake.definitions["COMPILER_RT_DEBUG"]="ON" if self._has_sanitizers else "OFF"

        # enable stats collection and extended debug output
        # (including memory accesses and function entry/exit events,
        # be careful it can be enormous
        # COMPILER_RT_TSAN_DEBUG_OUTPUT

        # TODO
        # SANITIZER_ALLOW_CXXABI # Allow use of C++ ABI details in ubsan
        #
        # COMPILER_RT_ASAN_SHADOW_SCALE
        #'COMPILER_RT_BAREMETAL_BUILD:BOOL': 'ON',
        #'COMPILER_RT_DEFAULT_TARGET_ONLY': 'ON',
        # COMPILER_RT_HWASAN_WITH_INTERCEPTORS
        # COMPILER_RT_OS_DIR

        # TODO: make customizable
        #cmake.definitions["CMAKE_CXX_STANDARD"]="17"

        cmake.definitions["BUILD_SHARED_LIBS"]="ON" if self.options.shared else "OFF"

        enabled_llvm_targets = [target for target in llvm_targets \
          if getattr(self.options, 'with_' + target)]
        if not len(enabled_llvm_targets):
            raise Exception("enable some llvm targets")
        self.output.info('Enabled LLVM targets: {}'.format(', '.join(enabled_llvm_targets)))

        # Semicolon-separated list of targets to build,
        # or all for building all targets.
        # Case-sensitive. Defaults to all.
        # Example: -DLLVM_TARGETS_TO_BUILD="X86;PowerPC".
        cmake.definitions["LLVM_TARGETS_TO_BUILD"]=', '.join(enabled_llvm_targets)

        # Add the -fPIC flag to the compiler command-line,
        # if the compiler supports this flag.
        # Some systems, like Windows, do not need this flag. Defaults to ON.
        cmake.definitions["LLVM_ENABLE_PIC"]="ON" \
          if (self.options.fPIC or self.options.shared) else "OFF"
        # ^ see above ^
        cmake.definitions["CMAKE_POSITION_INDEPENDENT_CODE"]="ON" \
          if (self.options.fPIC or self.options.shared) else "OFF"

        # Build LLVM with run-time type information. Defaults to OFF.
        cmake.definitions["LLVM_ENABLE_RTTI"]="ON" if self.options.rtti else "OFF"

        cmake.definitions['LLVM_ENABLE_UNWIND_TABLES'] = \
            self.options.unwind_tables

        cmake.definitions['LLVM_ENABLE_EH'] = self.options.exceptions

        # Used to decide if LLVM should be built with ABI breaking checks or not.
        # Allowed values are WITH_ASSERTS (default), FORCE_ON and FORCE_OFF.
        # WITH_ASSERTS turns on ABI breaking checks in an assertion enabled build.
        # FORCE_ON (FORCE_OFF) turns them on (off) irrespective
        # of whether normal (NDEBUG-based) assertions are enabled or not.
        # A version of LLVM built with ABI breaking checks is not ABI compatible
        # with a version built without it.
        #cmake.definitions["LLVM_ABI_BREAKING_CHECKS"]="FORCE_ON" \
        #  if (len(llvm_sanitizer) > 0 and llvm_sanitizer != 'None') else "WITH_ASSERTS"

        # Whether to build compiler-rt as part of LLVM
        # cmake.definitions["LLVM_TOOL_COMPILER_RT_BUILD"]="ON"

        # TODO: make customizable
        # Whether to build gold as part of LLVM
        #cmake.definitions["LLVM_TOOL_GOLD_BUILD"]="ON"

        # Whether to build libcxxabi as part of LLVM
        #cmake.definitions["LLVM_TOOL_LIBCXXABI_BUILD"]="ON"

        # FIXME: No rule to make target 'projects/libc/src/math/round.o'
        # see https://github.com/fwsGonzo/libriscv/issues/4
        # Whether to build libc as part of LLVM
        #cmake.definitions["LLVM_TOOL_LIBC_BUILD"]="ON"

        # Whether to build libcxx as part of LLVM
        #cmake.definitions["LLVM_TOOL_LIBCXX_BUILD"]="ON"

        # Whether to build libunwind as part of LLVM
        #cmake.definitions["LLVM_TOOL_LIBUNWIND_BUILD"]="ON"

        # sanitizers to build if supported on the target
        # (all;asan;dfsan;msan;hwasan;tsan;safestack;cfi;esan;scudo;ubsan_minimal;gwp_asan)
        LLVM_COMPILER_RT_SANITIZERS_TO_BUILD \
          = os.getenv("LLVM_COMPILER_RT_SANITIZERS_TO_BUILD", ';'.join(default_compiler_rt_sanitizers))
        cmake.definitions["COMPILER_RT_SANITIZERS_TO_BUILD"]= \
          LLVM_COMPILER_RT_SANITIZERS_TO_BUILD
        self.output.info('LLVM_COMPILER_RT_SANITIZERS_TO_BUILD: {}'\
          .format(LLVM_COMPILER_RT_SANITIZERS_TO_BUILD))
        # check that provided sanitizer names valid
        rt_sanitizers = LLVM_COMPILER_RT_SANITIZERS_TO_BUILD.split(";")
        for x in rt_sanitizers:
          if not x in compiler_rt_sanitizers:
            raise Exception("Unknown compiler_rt sanitizer: {}. Allowed sanitizers: ".format(x, str(compiler_rt_sanitizers)))

        # TODO: custom C++ stdlib requires custom include paths
        # Default C++ stdlib to use ("libstdc++" or "libc++", empty for platform default
        #cmake.definitions["CLANG_DEFAULT_CXX_STDLIB"]="libc++"
        # Default runtime library to use ("libgcc" or "compiler-rt", empty for platform default)
        #cmake.definitions["CLANG_DEFAULT_RTLIB"]="compiler-rt"
        # Default linker to use (linker name or absolute path, empty for platform default)
        #cmake.definitions["CLANG_DEFAULT_LINKER"]="lld"
        # Use compiler-rt instead of libgcc
        #cmake.definitions["LIBCXX_USE_COMPILER_RT"]="ON"

        # Use compiler-rt instead of libgcc
        # cmake.definitions["LIBUNWIND_USE_COMPILER_RT"]="ON"

        # TODO: make customizable
        # LIBCXXABI_USE_COMPILER_RT

        # TODO: make customizable
        # LIBCXXABI_USE_LLVM_UNWINDER

        # TODO: make customizable
        # Host on which LLVM binaries will run
        #LLVM_HOST_TRIPLE:STRING=x86_64-unknown-linux-gnu

        # TODO: make customizable
        #//Whether to build llc as part of LLVM
        #LLVM_TOOL_LLC_BUILD:BOOL=ON

        # TODO: make customizable
        #//Whether to build lldb as part of LLVM
        #LLVM_TOOL_LLDB_BUILD:BOOL=OFF

        # TODO: make customizable
        #//Whether to build lld as part of LLVM
        #LLVM_TOOL_LLD_BUILD:BOOL=OFF

        # Use compiler-rt builtins instead of libgcc
        #COMPILER_RT_USE_BUILTINS_LIBRARY

        # COMPILER_RT_STANDALONE_BUILD

        # COMPILER_RT_USE_LIBCXX # Enable compiler-rt to use libc++ from the source tree

        # Use static libc++abi.
        #cmake.definitions["SANITIZER_USE_STATIC_CXX_ABI"]="ON"

        # Use static LLVM unwinder.
        #cmake.definitions["SANITIZER_USE_STATIC_LLVM_UNWINDER"]="ON"

        # TODO
        #cmake.definitions["LLVM_ENABLE_PLUGINS"]="ON"

        # Enables code assertions.
        # Defaults to ON if and only if CMAKE_BUILD_TYPE is Debug.
        if os.getenv("LLVM_ENABLE_ASSERTIONS"):
          cmake.definitions["LLVM_ENABLE_ASSERTIONS"]=\
            self.flag_to_cmake(os.getenv("LLVM_ENABLE_ASSERTIONS"))
        else:
          cmake.definitions["LLVM_ENABLE_ASSERTIONS"]="ON" \
            if self._lower_build_type == "debug" else "OFF"

        return cmake

    # Importing files copies files from the local store to your project.
    def imports(self):
        CONAN_IMPORT_PATH = os.getenv("CONAN_IMPORT_PATH", "bin")
        self.output.info("CONAN_IMPORT_PATH is %s" % CONAN_IMPORT_PATH)

    # When building a distribution of a compiler
    # it is generally advised to perform a bootstrap build of the compiler.
    # That means building a stage 1 compiler with your host toolchain,
    # then building the stage 2 compiler using the stage 1 compiler.
    # When performing a bootstrap build it is not beneficial to do anything other
    # than setting CMAKE_BUILD_TYPE to Release for the stage-1 compiler.
    # This is because the more intensive optimizations are expensive to perform
    # and the stage-1 compiler is thrown away.
    # See docs https://llvm.org/docs/AdvancedBuilds.html
    # See docs https://llvm.org/docs/HowToBuildWithPGO.html
    # Multi-stage example https://android.googlesource.com/toolchain/llvm_android/+/bd22d9779676661ae9571972dcd744c42c70ffd0/build.py
    def build(self):
        if self._stage_tmp_compiler_enabled:
          self.build_stage_tmp_compiler()
        self.build_stage_runtime()
        self.build_stage_llvm()
        self.build_iwyu()

    def package_iwyu(self):
        package_bin_dir = os.path.join(self.package_folder, "bin")

        if self.options.include_what_you_use:
          iwyu_bin_dir = os.path.join(self._iwyu_source_subfolder, "build", "bin")
          self.output.info('copying %s into %s' % (iwyu_bin_dir, package_bin_dir))
          self.copytree( \
            iwyu_bin_dir, \
            package_bin_dir)
          if os.path.exists(self._iwyu_folder):
            self.copytree( \
              '{}/bin'.format(self._iwyu_folder), \
              '{}/bin'.format(self.package_folder))

    def package_stage_llvm(self):
      if not os.path.exists(self._stage_llvm_folder):
          raise Exception("Unable to find path: {}".format(self._stage_llvm_folder))

      llvm_src_dir = os.path.join(self._llvm_source_subfolder, "llvm")

      self.copytree( \
        '{}/bin'.format(self._stage_llvm_folder), \
        '{}/bin'.format(self.package_folder))

      # keep_path=True required by `/include/c++/v1/`
      #self.copy('*', src='%s/include' % (self._stage_llvm_folder), dst='include', keep_path=True)
      self.copytree( \
        '{}/include'.format(self._stage_llvm_folder), \
        '{}/include'.format(self.package_folder))

      clang_src_dir = os.path.join(self._llvm_source_subfolder, "clang")
      self.copytree( \
        '{}'.format(clang_src_dir), \
        '{}/clang'.format(self.package_folder))

      tools_src_dir = os.path.join(self._stage_llvm_folder, "tools")
      self.copytree( \
        '{}'.format(tools_src_dir), \
        '{}/tools'.format(self.package_folder))

      # keep_path=True required by `/lib/clang/x.x.x/include/`
      #self.copy('*', src='%s/lib' % (self._stage_llvm_folder), dst='lib', keep_path=True)
      self.copytree( \
        '{}/lib'.format(self._stage_llvm_folder), \
        '{}/lib'.format(self.package_folder))

      self.copytree( \
        '{}/libexec'.format(self._stage_llvm_folder), \
        '{}/libexec'.format(self.package_folder))

      if not os.path.exists(self._stage_runtime_folder):
          raise Exception("Unable to find path: {}".format(self._stage_runtime_folder))

      if self._has_sanitizers:
        # Must remove files:
        # libc++.so, libc++.so.1.0, libc++.so.1
        # libc++.a
        # libc++abi.so, libc++abi.so.1.0, libc++abi.so.1
        # libc++abi.a
        # libc++experimental.so
        # libc++experimental.a
        # etc.
        # Make sure that stage_runtime will provide that files!
        fileList = glob.glob('{}/lib/*c++*'.format(self.package_folder), recursive=False)
        for filePath in fileList:
          try:
            self.output.info("removing file %s" % filePath)
            os.remove(filePath)
          except:
            raise Exception("Error while deleting file: {}".format(filePath))

    def package_stage_runtime(self):
      if not os.path.exists(self._stage_runtime_folder):
          raise Exception("Unable to find path: {}".format(self._stage_runtime_folder))

      # keep_path=True required by `/lib/clang/x.x.x/include/`
      #self.copy('*', src='%s/lib' % (self._stage_runtime_folder), dst='lib', keep_path=True)
      self.copytree( \
        '{}/lib'.format(self._stage_runtime_folder), \
        '{}/lib'.format(self.package_folder))

      if os.path.exists('{}/libexec'.format(self._stage_runtime_folder)):
        self.copytree( \
          '{}/libexec'.format(self._stage_runtime_folder), \
          '{}/libexec'.format(self.package_folder))

      if os.path.exists('{}/include'.format(self._stage_runtime_folder)):
        self.copytree( \
          '{}/include'.format(self._stage_runtime_folder), \
          '{}/include'.format(self.package_folder))

    def package(self):
      llvm_src_dir = os.path.join(self._llvm_source_subfolder, "llvm")

      self.package_stage_llvm()

      # stage_runtime builds sanitized (or normal if sanitizers disabled) libs:
      # "libcxx", "libcxxabi", "compiler-rt".
      self.package_stage_runtime()

      if self.options.include_what_you_use:
        self.package_iwyu()

      include_iostream = '{}/include/c++/v1/iostream'.format(self.package_folder)
      if not os.path.exists(include_iostream):
        raise Exception("Unable to find path: {}".format(include_iostream))

      if self._has_sanitizers:
        cxxabiList = glob.glob('{}/lib/*c++abi*'.format(self.package_folder), recursive=False)
        if len(cxxabiList) <= 0:
          raise Exception("Unable to find *c++abi*")

        clang_libpath = '{}/lib/clang/{}/lib'.format(self.package_folder, self._clang_ver)
        if not os.path.exists(clang_libpath):
          raise Exception("Unable to find path: {}".format(clang_libpath))
        clangrtList = []
        for path in os.listdir(clang_libpath):
            clang_rt_libs = glob.glob('{}/{}/*clang_rt.*san*'.format(clang_libpath, path), recursive=False)
            clangrtList.extend(clang_rt_libs)
            self.output.info('clang_rt_libs: %s in path: %s/%s' % (str(clang_rt_libs), clang_libpath, path))
        if len(clangrtList) <= 0:
          raise Exception("Unable to find *clang_rt.*asan*")

      self.output.info('packaged for os: %s' % (self.settings.os_build))

    # NOTE: do not append packaged paths to env_info.PATH, env_info.LD_LIBRARY_PATH, etc.
    # because it can conflict with system compiler
    # https://stackoverflow.com/q/54273632
    def package_info(self):
        self.cpp_info.includedirs = ["include", "clang/include", "tools/clang/include"]
        self.cpp_info.libdirs = ["lib", "clang/lib", "tools/clang/lib"]
        self.cpp_info.bindirs = ["bin", "libexec", "clang", "tools", "tools/clang"]
        #self.env_info.LD_LIBRARY_PATH.append(
        #    os.path.join(self.package_folder, "lib"))
        #self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
        #self.env_info.PATH.append(os.path.join(self.package_folder, "libexec"))
        #for libpath in self.deps_cpp_info.lib_paths:
        #    self.env_info.LD_LIBRARY_PATH.append(libpath)

        if self.settings.os_build == "Linux":
            self.cpp_info.libs.extend(["pthread", "unwind", "z", "m", "dl", "ncurses", "tinfo"])
            if self.settings.compiler == "clang" and self._libcxx == "libstdc++":
                self.cpp_info.libs.append("atomic")
        elif self.settings.os_build == "Windows" and self.settings.compiler == "Visual Studio":
            self.cpp_info.libs.extend(["ws2_32", "Iphlpapi", "Crypt32"])

        if (self.settings.os_build == "Linux" and self.settings.compiler == "clang" and
           Version(self.settings.compiler.version.value) == "6" and self._libcxx == "libstdc++") or \
           (self.settings.os_build == "Macos" and self.settings.compiler == "apple-clang" and
           Version(self.settings.compiler.version.value) == "9.0" and self._libcxx == "libc++"):
            self.cpp_info.libs.append("atomic")

        self.cpp_info.includedirs.append(os.path.join(self.package_folder, "include"))
        self.cpp_info.includedirs.append(self.package_folder)

        bindir = os.path.join(self.package_folder, "bin")
        libexec = os.path.join(self.package_folder, "libexec")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        #self.env_info.PATH.append(bindir)
        self.output.info("Appending PATH environment variable: {}".format(libexec))
        #self.env_info.PATH.append(libexec)

        libdir = os.path.join(self.package_folder, "lib")
        self.output.info("Appending PATH environment variable: {}".format(libdir))
        #self.env_info.PATH.append(libdir)

        if not "clang" in llvm_projects:
            raise Exception("enable project clang")

        enabled_llvm_libs = [library for library in llvm_libs \
          if getattr(self.options, 'with_' + library)]
        self.output.info('Enabled LLVM libs: {}'.format(', '.join(enabled_llvm_libs)))
        self.cpp_info.libs.extend(enabled_llvm_libs)

        self.output.info("LIBRARIES: %s" % self.cpp_info.libs)
        self.output.info("Package folder: %s" % self.package_folder)

    # If your project does not depend on LLVM libs (LibTooling, etc.),
    # than you can delete arch_build, arch, compiler, etc.
    # Otherwise change env. vars to keep arch_build, arch, compiler, etc.
    #
    # In case of link error with some LLVM libs:
    # clang++ does not depend on arch,
    # but tooling libs depend on arch...
    # You must use same CXX ABI as LLVM libs
    # otherwise you will get link errors!
    def package_id(self):
      if self.flag_to_cmake(os.getenv("LLVM_CONAN_FORCE_INCLUDE_SETTINGS", "ON")) == "ON":
        self.info.include_build_settings()
      if self.flag_to_cmake(os.getenv("LLVM_CONAN_IGNORE_ARCH_BUILD", "ON")) == "ON":
        if self.settings.os_build == "Windows":
            del self.info.settings.arch_build # same build is used for x86 and x86_64
      if self.flag_to_cmake(os.getenv("LLVM_CONAN_IGNORE_ARCH", "ON")) == "ON":
        del self.info.settings.arch
      if self.flag_to_cmake(os.getenv("LLVM_CONAN_IGNORE_COMPILER", "ON")) == "ON":
        del self.info.settings.compiler
