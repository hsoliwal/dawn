# Building Dawn

Dawn builds as a standalone C++ project with CMake. This fork has no
Chromium (`GN`, `depot_tools`, `gclient`) build and no browser (Emscripten,
emdawnwebgpu) or Node.js (`dawn.node`) targets.

If you are developing Dawn itself, see also
[development-tips.md](development-tips.md).

## System requirements

 * Git
 * `CMake` 3.22 or later
 * Ninja 1.12 (or another build tool supported by CMake)
 * Python 3, for fetching dependencies
 * Go 1.26 or later, as declared by `go.mod`: https://go.dev/
 * A C++20 compiler
    * Check the platform details below.

- Linux
  - CPU:
    - x86-64 (also known as amd64)
    - arm64
    - x86: untested
    - mips, mips64: untested
  - The `pkg-config` command:
    ```sh
    # Install pkg-config on Ubuntu
    sudo apt-get install pkg-config
    ```
  - C++20 compiler:
    - Clang 19 or later. This the primary supported compiler.
    - GCC 12 or later

- Mac
  - CPU:
    - Apple Silicon
    - Intel x86-64
  - [Xcode](https://developer.apple.com/xcode/) 12.2+.
  - The macOS 13.0 SDK. Run `xcode-select` to check whether you have it.
    ```sh
    ls `xcode-select -p`/SDKs
    ```

- Windows
  - CPU:
    - x86-64 (also known as amd64)
    - arm64 support is experimental
  - Windows SDK 10.0.26100.x or a later version.
  - C++20 compiler:
    - Clang 19 or later.
    - MSVC 19.41, or Visual Studio 2022 v17.11 or later.
      Note: Dawn is tested daily with MSVC 19.43 or VS 2022 v17.13


## Get the code and its dependencies

Use `tools/fetch_dawn_dependencies.py` to clone the dependencies' repositories:

```sh
# Clone the repo as "dawn"
git clone https://github.com/hsoliwal/dawn.git
cd dawn

# Fetch dependencies
python tools/fetch_dawn_dependencies.py
```

Use `python tools/fetch_dawn_dependencies.py -h` to know more about the available options. The script
does not figure out option-dependent requirements automatically.

The checkout's gitlinks pin native source commits, and `.gitmodules` records
their repository URLs. The CMake dependency fetcher uses an explicit native
dependency list without a `DEPS` file, `gclient` configuration, or recursive
submodule fetching. Source mirrors hosted on `chromium.googlesource.com` still
provide some native dependencies; their host name does not introduce a browser
runtime. Use `python tools/fetch_dawn_dependencies.py --list` to inspect the pins
without downloading dependencies.

On Windows, configuring CMake with both `DAWN_FETCH_DEPENDENCIES=ON` and
`DAWN_USE_AGILITY_SDK=ON` downloads the Agility SDK version pinned in
`tools/fetch_dawn_dependencies.py`. The same script holds the Linux LLVM/Zstd
package pins needed by optional Mesa builds. CMake passes `--fetch-swiftshader`
or `--fetch-mesa` when those native drivers are enabled.

### Linux dependencies

The following packages are needed to build Dawn. (Package names are the Ubuntu names).

* `libfuse2`
* `libxrandr-dev`
* `libxinerama-dev`
* `libxcursor-dev`
* `libxkbcommon-dev`
* `libxi-dev`
* `mesa-common-dev`
* `libx11-xcb-dev`
* `pkg-config`

```sh
sudo apt-get install libfuse2 libxrandr-dev libxinerama-dev libxcursor-dev libxkbcommon-dev libxi-dev mesa-common-dev libx11-xcb-dev pkg-config
```


## Build Dawn

### Compiling using CMake + Ninja

```sh
cmake -S . -B out/Debug -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build out/Debug --parallel 2
```

### Compiling using CMake + make

```sh
cmake -S . -B out/Debug -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Debug
cmake --build out/Debug --parallel 2
```

For CMake builds, you can enable installation with the `DAWN_ENABLE_INSTALL` option
and use `find_package(Dawn)` in your CMake project to discover Dawn and link with
the `dawn::webgpu_dawn` target. Please see [Quickstart with CMake](./quickstart-cmake.md)
for step-by-step instructions.

Use a fresh build directory for a different generator or toolchain. Browser
configurations (`EMSCRIPTEN`, `CMAKE_SYSTEM_NAME=Emscripten`, or
`DAWN_BUILD_NODE_BINDINGS=ON`) are rejected before dependency fetching. Native
Android builds still use the Android NDK toolchain and retain JNI bindings.

For headless compute builds, disable the sample/window-system integration:

```sh
cmake -S . -B out/Compute -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DDAWN_FETCH_DEPENDENCIES=ON \
  -DDAWN_ENABLE_INSTALL=ON -DDAWN_BUILD_SAMPLES=OFF \
  -DDAWN_USE_GLFW=OFF -DDAWN_USE_X11=OFF -DDAWN_USE_WAYLAND=OFF \
  -DDAWN_BUILD_TESTS=OFF -DTINT_BUILD_TESTS=OFF
cmake --build out/Compute --target webgpu_dawn --parallel 2
cmake --install out/Compute --prefix install/Compute
```

GPU backends and their platform SDKs remain native build inputs. Disabling
window-system integration does not remove Vulkan, Metal, or Direct3D compute.

### Cross-Compilation

Cross-compile with a CMake toolchain file. The `mobile-android` job of
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) shows the Android NDK
configuration for arm64-v8a, armeabi-v7a and x86.

### Using ccache for CMake builds

There is a substantial number of source files that are needed to be
built for Dawn and its dependencies (~thousands), which can lead to
long compile times on resource bound machines (i.e. laptops),
especially when performing clean builds. Use
[ccache](https://ccache.dev/) with the native CMake build to avoid rebuilding targets. For full
details on using ccache see the project's documentation, but below is
an example of how to use it on a Debian based Linux dev env.

```sh
# One time Install and setup of ccache
apt-get install ccache
ccache -F 0 -M 0  # Sets the number of files and size of the cache to unlimited, the default is 5 GiB. Choose values that make sense for your situation.

# Setup CMake + Ninja building using cccache
cmake -S . -B out/cache -G Ninja \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
cmake --build out/cache --parallel 2

# Optional: In another terminal, monitor the status of the cache. (Will have a lot of misses on the first run)
watch ccache -s
```

Using ccache will not help with the initial build of Dawn, since the
targets still need to be built at least once locally, but subsequent
builds, even after a clean operation should be much faster. Some
operations like linking are not cache-able, so will need to be run on
every build, but the bulk of file compilations should be
cache-able. Updating the repo, editing source files, and changing build
flags will all cause misses, since entries in the cache are based on
flags + contents of the source file.

### Weird CMake build breaks on Linux

If you see errors like this:

```
error: satisfaction of constraint 'is_constructible_v<_Tp, _Up>' depends on itself
  && is_constructible_v<_Tp, _Up>
     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~
```
or similar complaints about constraints depending on themselves, this
is a known [issue](https://github.com/llvm/llvm-project/issues/62096)
with older versions of Clang (17ish through 19ish) and newer versions
of GCC (15+).

Specifically Clang by default uses the standard library from GCC, and
GCC 15 introduces a construct that older Clang thinks is out of spec,
thought it is not.

Currently there is no provided hermetic Linux build for CMake to be
used to avoid this problem, so you either need to use a newer version
of Clang or use an older version of GCC for your entire system.

For some environments currently, Clang 19.x is the newest version
available, and GCC 15 is the default compiler, so it cannot be
down-rev'd.

In this case you will need to install a parallel GCC toolchain and
tell Clang to use that.

For Debian based systems this can be done as follows:

```sh
sudo apt-get install gcc-14 libgcc-14-dev
...
cmake -DCMAKE_CXX_FLAGS="--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/14" <other cmake flags> <path to repo root>
```

This assumes gcc-14 is installed to
`/usr/lib/gcc/x86_64-linux-gnu/14`, which may not be true depending on
your specific distro and architecture.

It is likely CMake will not correctly pick up this type of dev env
change if you run this in an existing build directory, so it is
recommended that you setup a new build directory to use this.

### Fuzzers on MacOS

As of Late Oct 2025, fuzzing on a dev Mac is not in a good state.

The old workaround for fuzzing with XCode 16.X should still work, but that is
not the Chromium supported version of XCode so there may be other issues. That
workaround does not work for XCode 26.X, which is supported by Chromium.

If you attempt to build and run the fuzzers without a workaround, you will
either get build failures like this:

```sh
ld: file not found:/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/clang/11.0.0/lib/darwin/libclang_rt.fuzzer_osx.a
```

or if using a component build, you will get a similar runtime issue for a
missing `.dylib`.

The root cause for this is that the build of llvm shipped as part of the XCode
SDK does not include the standard support libraries for fuzzing.

The workaround for this depends on which version of XCode you are trying to use.

#### Using XCode 16.X

The workaround for 16.X has been to install a fully featured version llvm onto
your system, for example via Homebrew, `brew install llvm`, (you might have to
use `llvm@XX` where `XX` is the major version of llvm in the XCode SDK). And
then using environment variables, i.e. `CC=<path to Homebrew clang> cmake
-GNinja ../..`, to set up the build including the full llvm toolchain to get the
missing libraries onto the search path. This will actually create a hybrid
toolchain using some elements of the XCode SDK and the llvm SDK, because there
is some Apple specific framework stuff that isn't in mainstream llvm.

#### Using XCode 26.X

As mentioned above, the 16.X workaround appears to no longer work due to drift
between Apple's llvm and the mainline version. Trying to create a hybrid
toolchain will lead to compiling issues from the XCode standard headers using
deprecated functions according to mainstream llvm, even when using the same
major version.

For 26.X there is workaround done by installing `llvm@17` (since AppleClang is
version 17) from Homebrew, and then copying over the missing library files
(i.e. `libclang_rt.fuzzer_osx.a`) from the Homebrew directory to the
CommandLineTools toolchain directory. (Cannot be the XCode toolchain directory,
because that is write protected).

You will then need to be using the CLT toolchain as your active toolchain

```sh
sudo xcode-select -s /Library/Developer/CommandLineTools
```

This allows for building and debugging the fuzzers, but the impact of this on
other builds and/or system stability is unknown. It shouldn't have a significant
impact, since the standard SDK doesn't ship with these libraries, so nothing
else should be using them, but the Homebrew version of llvm will not have all of
Apple's patches, so may be incompatible in subtle ways if these libraries do get
used somehow.
