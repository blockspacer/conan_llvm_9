from conans import ConanFile, CMake
import os

def get_name(default):
    envvar = os.getenv("LLVM_PACKAGE_NAME", default)
    return envvar

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "cmake_find_package"

    def build(self):
        cmake = CMake(self)
        cmake.definitions["CONAN_DISABLE_CHECK_COMPILER"] = "ON"
        cmake.definitions["CMAKE_C_COMPILER_FORCED"] = "TRUE"
        cmake.definitions["CMAKE_CXX_COMPILER_FORCED"] = "TRUE"
        cmake.definitions["LLVM_PACKAGE_NAME"] = get_name("llvm_9")
        cmake.configure()
        cmake.build()

#    def requirements(self):

#        self.requires("llvm_9::clang_core")
#
        #self.requires("double-conversion/3.1.1@bincrafters/stable")
#
        #self.requires("gflags/2.2.2@bincrafters/stable")
#
        #self.requires("glog/0.4.0@bincrafters/stable")
#
        #self.requires("libevent/2.1.11@bincrafters/stable")
#
        #self.requires("lz4/1.8.3@bincrafters/stable")
#
        #self.requires("openssl/1.1.1c")
#
        #self.requires("zlib/1.2.11@conan/stable")
#
        #self.requires("lzma/5.2.4@bincrafters/stable")
#
        #self.requires("zstd/1.3.8@bincrafters/stable")
#
        #self.requires("snappy/1.1.7@bincrafters/stable")
#
        #self.requires("bzip2/1.0.8@conan/stable")
#
        #self.requires("libsodium/1.0.18@bincrafters/stable")
#
        #self.requires("libelf/0.8.13@bincrafters/stable")
#
        #self.requires("libdwarf/20190505@bincrafters/stable")

    def test(self):
        bin_path = os.path.join("bin", "test_package")
        self.run(command=bin_path, run_environment=True)
