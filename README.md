[![MSVC Conan](https://github.com/sintef-ocean/conan-openblas/workflows/MSVC%20Conan/badge.svg)](https://github.com/sintef-ocean/conan-openblas/actions?query=workflow%3A"MSVC+Conan")
[![Download](https://api.bintray.com/packages/sintef-ocean/conan/openblas%3Asintef/images/download.svg)](https://bintray.com/sintef-ocean/conan/openblas%3Asintef/_latestVersion)


[Conan.io](https://conan.io) recipe for [openblas](https://www.openblas.net/).

The recipe builds library packages, which might be found at [Bintray](https://bintray.com/sintef-ocean/conan/openblas%3Asintef).
The package is usually consumed using the `conan install` command or a *conanfile.txt*.
*Note* This recipe is handcrafted to compile OpenBLAS on Windows with LAPACK, with native support for MSVC. It follows instructions given here: [OpenBLAS MSVC](https://github.com/xianyi/OpenBLAS/wiki/How-to-use-OpenBLAS-in-Microsoft-Visual-Studio).
Under normal circumstances you should use OpenBLAS recipe on [Conan center](https://conan.io/center/openblas)
This recipe is based on the openblas recipe found on conan center.

## How to use this package

1. Add remote to conan's package [remotes](https://docs.conan.io/en/latest/reference/commands/misc/remote.html?highlight=remotes):

   ```bash
   $ conan remote add sintef https://api.bintray.com/conan/sintef-ocean/conan
   ```

2. Using *conanfile.txt* in your project with *cmake*

   Add a [*conanfile.txt*](http://docs.conan.io/en/latest/reference/conanfile_txt.html) to your project. This file describes dependencies and your configuration of choice, e.g.:

   ```
   [requires]
   openblas/[>=0.3.13]@sintef/testing

   [options]
   openblas:shared=True
   openblas:build_lapack=True
   openblas:dynamic_arch=True

   [imports]
   licenses, * -> ./licenses @ folder=True

   [generators]
   cmake_paths
   cmake_find_package
   ```

   Insert into your *CMakeLists.txt* something like the following lines:
   ```cmake
   cmake_minimum_required(VERSION 3.13)
   project(TheProject CXX)

   include(${CMAKE_BINARY_DIR}/conan_paths.cmake)
   find_package(OpenBLAS MODULE REQUIRED)

   add_executable(the_executor code.cpp)
   target_link_libraries(the_executor OpenBLAS::OpenBLAS)
   ```
   Then, do
   ```bash
   $ mkdir build && cd build
   $ conan install .. -s build_type=<build_type>
   ```
   where `<build_type>` is e.g. `Debug` or `Release`.
   You can now continue with the usual dance with cmake commands for configuration and compilation. For details on how to use conan, please consult [Conan.io docs](http://docs.conan.io/en/latest/)

## Package options

Option | Default | Domain
---|---|---
shared | False | [True, False]
fPIC | True | [True, False] (ignored)
build_lapack | True | [True, False]
use_thread | True | [True, False]
dynamic_arch | False | [True, False]

## Known recipe issues

- The recipe developer has modified `cmake/system.cmake` to be able to compile with option `dynamic_arch=True`. This may have implications for `COOPERLAKE` architecture.
