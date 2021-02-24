from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
from contextlib import contextmanager
import os
import re

class OpenblasConan(ConanFile):
    name = "openblas"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.openblas.net"
    description = "An optimized BLAS library based on GotoBLAS2 1.13 BSD version"
    topics = (
        "openblas",
        "blas",
        "lapack"
    )
    settings = {
        "os" : ["Windows"],
        "compiler" : ["Visual Studio"],
        "build_type" : ["Debug", "Release"],
        "arch" : ["x86_64"]
    }
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_lapack": [True, False],
        "use_thread": [True, False],
        "dynamic_arch": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_lapack": True,
        "use_thread": True,
        "dynamic_arch": False  #  True failed for me
    }
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    keep_imports = True
    _cmake = None
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    @contextmanager
    def _build_context(self):
        env_build = tools.RunEnvironment(self)
        with tools.vcvars(self.settings):
            with tools.environment_append(env_build.vars):
                env = {
                "LIB": [os.path.join(self.deps_cpp_info["miniconda"].rootpath, "Library", "lib")],
                "CPATH": [os.path.join(self.deps_cpp_info["miniconda"].rootpath, "Library", "include")]
                }
                with tools.environment_append(env):
                    yield

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.settings.compiler != "Visual Studio":
            raise ConanInvalidConfiguration(
                "This recipe is hand-crafted for clang-cl toolset")

    def source(self):
        _git = tools.Git(folder=self._source_subfolder)
        _git.clone("https://github.com/xianyi/OpenBLAS.git",
            branch="v{}".format(self.version),
            shallow=True)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        cmake = CMake(self)
        if self.options.build_lapack:
            self.output.warn("Building with lapack support requires a Fortran compiler.")
            cmake.definitions["CMAKE_Fortran_COMPILER"] = "flang"
            cmake.definitions["CMAKE_C_COMPILER"] = "clang-cl"

        cmake.definitions["NOFORTRAN"] = not self.options.build_lapack
        cmake.definitions["BUILD_WITHOUT_LAPACK"] = not self.options.build_lapack
        cmake.definitions["DYNAMIC_ARCH"] = self.options.dynamic_arch
        cmake.definitions["USE_THREAD"] = self.options.use_thread

        # Required for safe concurrent calls to OpenBLAS routines
        cmake.definitions["USE_LOCKING"] = not self.options.use_thread
        cmake.definitions["MSVC_STATIC_CRT"] = False # don't, may lie to consumer, /MD or /MT is managed by conan

        # lazy hack to resuse flags setup by conan (some are wrong)
        what = cmake.command_line
        what = what.replace('-T "ClangCL"', '')
        what = re.sub('-G "Visual Studio .*-A "x64"', '-G "Ninja"', what)
       
        with self._build_context():
            self.run('conda activate && cmake %s %s' % (
                os.path.join(self.source_folder, self._source_subfolder), what))

        self._cmake = dict()
        self._cmake['cmake'] = cmake
        self._cmake['build_cmd'] = "conda activate && cmake --build . %s" % cmake.build_config
        self._cmake['install_cmd'] = 'conda activate && cmake --build . --target install %s' % cmake.build_config

        return self._cmake

    def build_requirements(self):
        self.build_requires("miniconda/[>=4.9.2]@sintef/testing")
        self.build_requires("ninja/[>=1.10.0]")

    def build(self):
        cmake = self._configure_cmake()
        with self._build_context():
            self.run(cmake['build_cmd'])

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        with self._build_context():
            self.run(cmake['install_cmd'])#, cwd=self._build_subfolder)
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "share"))

        # Bundle runtime dependencies
        self.copy(pattern="flang*.dll", src="flangs", dst="bin")
        self.copy(pattern="pgmath.dll", src="flangs", dst="bin")
        self.copy(pattern="libomp.dll", src="flangs", dst="bin")

    def package_info(self):
        # CMake config file:
        # - OpenBLAS always has one and only one of these components: openmp, pthread or serial.
        # - Whatever if this component is requested or not, official CMake imported target is always OpenBLAS::OpenBLAS
        # - TODO: add openmp component when implemented in this recipe
        self.cpp_info.names["cmake_find_package"] = "OpenBLAS"
        self.cpp_info.names["cmake_find_package_multi"] = "OpenBLAS"
        self.cpp_info.names["pkg_config"] = "openblas"
        cmake_component_name = "pthread" if self.options.use_thread else "serial"
        self.cpp_info.components["openblas_component"].names["cmake_find_package"] = cmake_component_name
        self.cpp_info.components["openblas_component"].names["cmake_find_package_multi"] = cmake_component_name
        self.cpp_info.components["openblas_component"].names["pkg_config"] = "openblas"
        self.cpp_info.components["openblas_component"].includedirs.append(os.path.join("include", "openblas"))
        self.cpp_info.components["openblas_component"].libs = tools.collect_libs(self)

        self.output.info("Setting OpenBLAS_HOME environment variable: {}".format(self.package_folder))
        self.env_info.OpenBLAS_HOME = self.package_folder

    def package_id(self):
        self.info.vs_toolset_compatible()

    def imports(self):
        self.copy(pattern="flang*.dll", src="Library/bin", root_package="miniconda", dst="flangs")
        self.copy(pattern="pgmath.dll", src="Library/bin", root_package="miniconda", dst="flangs")
        self.copy(pattern="libomp.dll", src="Library/bin", root_package="miniconda", dst="flangs")