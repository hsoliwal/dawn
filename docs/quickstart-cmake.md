# Quickstart With CMake

This document is designed to allow you to build Dawn with CMake and link to it from other CMake projects. If you're planning to work on Dawn specifically, please use `gclient` and `depot_tools`. It ensures
that you always get the right dependencies and compilers.

## Prerequisites

- A compatible platform (e.g. Windows, macOS, Linux, etc.). Most platforms are fully supported.
- A compatible C++ compiler supporting at least C++20. Most major compilers are supported.
- Git for interacting with the Dawn source code repository.
- Python 3 for dependency fetching and code generation.
- CMake for building your project and Dawn. Dawn requires CMake 3.22+, as declared in [CMakeLists.txt](../CMakeLists.txt).

## Getting the Dawn Code

The examples below clone upstream Dawn. To evaluate this fork instead, use
`git clone https://github.com/hsoliwal/dawn.git` for the clone step and keep the
remaining commands relative to that checkout. A build of an upstream checkout
does not validate changes in this fork.


```shell
# Change to the directory where you want to create the code repository
$ git clone https://dawn.googlesource.com/dawn
Cloning into 'dawn'...
```

Git will create the repository within a directory named `dawn`. Navigate into this directory and configure the project.

## Build and install Dawn with CMake
```shell
$ cd dawn
$ cmake -S . -B out/Release -DDAWN_FETCH_DEPENDENCIES=ON -DDAWN_ENABLE_INSTALL=ON -DCMAKE_BUILD_TYPE=Release
...
-- Configuring done (34.9s)
-- Generating done (0.8s)
-- Build files have been written to: ${PWD}/out/Release
```

- `DAWN_FETCH_DEPENDENCIES=ON` uses [tools/fetch_dawn_dependencies.py](../tools/fetch_dawn_dependencies.py) as an alternative to fetching dependencies with `gclient`. This downloads external source dependencies and evaluates the checkout's `DEPS` content; use it only with a trusted checkout. See [building.md](building.md) for platform requirements and dependency terms.
- `DAWN_ENABLE_INSTALL=ON` configures the project to install binaries, headers and cmake configuration files in a directory of your choice. This allows other projects to discover Dawn in CMake and link with it.

Now you can build Dawn:

```shell
$ cmake --build out/Release
...
[100%] Linking CXX static library libdawn_utils.a
[100%] Built target dawn_utils
```

Once you have built the Dawn library, install it with `cmake`

```shell
$ cmake --install out/Release --prefix install/Release
```

This installs Dawn from the `out/Release` build tree into `install/Release`.

## Build and test boundaries

The root [CMakeLists.txt](../CMakeLists.txt) controls the available targets and
platform-dependent defaults. `DAWN_BUILD_TESTS` and `TINT_BUILD_TESTS` are
separate options; installing a library does not imply that its tests ran.

To build Dawn's unit-test executable in the same example build tree, explicitly
enable its tests and build the target defined in
[src/dawn/tests/CMakeLists.txt](../src/dawn/tests/CMakeLists.txt):

```sh
cmake -S . -B out/Release -DDAWN_FETCH_DEPENDENCIES=ON -DDAWN_ENABLE_INSTALL=ON -DDAWN_BUILD_TESTS=ON -DCMAKE_BUILD_TYPE=Release
cmake --build out/Release --target dawn_unittests --config Release
```

Run the resulting `dawn_unittests` executable separately; its location and
extension depend on the generator/platform. Use
[Dawn testing](dawn/testing.md), [Tint testing](tint/testing.md), and the
[standalone CTS guide](standalone_cts_runner.md) to choose further checks.
Dawn's GPU end-to-end tests require a usable GPU/backend; unit tests are not a
substitute for those checks.

When reporting results, include the commit, compiler, generator, build options,
operating system, GPU/driver where applicable, test selection, and any skips.
For multi-configuration generators such as Visual Studio, select the same
configuration consistently when building, installing, and running artifacts
(for example `--config Release` for CMake build/install commands).

## Linking your code to the Dawn installation

### Create test code

```shell
$ mkdir TestDawn
$ cd TestDawn
```

Now, create a `hello_webgpu.cpp` C++ file within the `TestDawn` directory.

```cpp
#include <webgpu/webgpu_cpp.h>
#include <webgpu/webgpu_cpp_print.h>

#include <cstdlib>
#include <iostream>

int main(int argc, char *argv[]) {
  static constexpr auto kTimedWaitAny = wgpu::InstanceFeatureName::TimedWaitAny;
  wgpu::InstanceDescriptor instanceDescriptor{
    .requiredFeatureCount = 1,
    .requiredFeatures = &kTimedWaitAny
  };

  wgpu::Instance instance = wgpu::CreateInstance(&instanceDescriptor);
  if (instance == nullptr) {
    std::cerr << "Instance creation failed!\n";
    return EXIT_FAILURE;
  }
  // Synchronously request the adapter.
  wgpu::RequestAdapterOptions options = {};
  wgpu::Adapter adapter;

  auto callback = [](wgpu::RequestAdapterStatus status, wgpu::Adapter adapter, wgpu::StringView message, void *userdata) {
    if (status != wgpu::RequestAdapterStatus::Success) {
      std::cerr << "Failed to get an adapter:" << message;
      return;
    }
    *static_cast<wgpu::Adapter *>(userdata) = adapter;
  };


  auto callbackMode = wgpu::CallbackMode::WaitAnyOnly;
  void *userdata = &adapter;
  instance.WaitAny(instance.RequestAdapter(&options, callbackMode, callback, userdata), UINT64_MAX);
  if (adapter == nullptr) {
    std::cerr << "RequestAdapter failed!\n";
    return EXIT_FAILURE;
  }

  wgpu::DawnAdapterPropertiesPowerPreference power_props{};

  wgpu::AdapterInfo info{};
  info.nextInChain = &power_props;

  adapter.GetInfo(&info);
  std::cout << "VendorID: " << std::hex << info.vendorID << std::dec << "\n";
  std::cout << "Vendor: " << info.vendor << "\n";
  std::cout << "Architecture: " << info.architecture << "\n";
  std::cout << "DeviceID: " << std::hex << info.deviceID << std::dec << "\n";
  std::cout << "Name: " << info.device << "\n";
  std::cout << "Driver description: " << info.description << "\n";
  return EXIT_SUCCESS;
}
```

### Create CMakeLists.txt file

Now, create a `CMakeLists.txt` file within the `TestDawn` directory like the following:

```cmake
cmake_minimum_required(VERSION 3.13)

project(hello_webgpu)

set(CMAKE_CXX_STANDARD 20)

find_package(Dawn REQUIRED)
add_executable(hello_webgpu hello_webgpu.cpp)

# Declare dependency on the dawn::webgpu_dawn library
target_link_libraries(hello_webgpu dawn::webgpu_dawn)
```

For more information on how to create CMakeLists.txt files, consult the [CMake Tutorial](https://cmake.org/getting-started/).

### Build test project

Configure the CMake build from a fresh binary directory. This configuration is called an “out of source” build and is the preferred method for CMake projects.

```shell
$ export CMAKE_PREFIX_PATH=/path/to/dawn/install/Release
$ cmake -S . -B out/Release -DCMAKE_BUILD_TYPE=Release
...
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: ${PWD}/out/Release
```

Now build our test application:

```shell
$ cmake --build out/Release
[ 50%] Building CXX object CMakeFiles/hello_webgpu.dir/hello_webgpu.cpp.o
[100%] Linking CXX executable hello_webgpu
[100%] Built target hello_webgpu
```

Now run your binary:

```shell
$ ./out/Release/hello_webgpu
VendorID: 8086
Vendor: intel
Architecture: gen-12lp
DeviceID: 9a60
Name: Intel(R) UHD Graphics (TGL GT1)
Driver description: Intel open-source Mesa driver: Mesa 23.2.1-1ubuntu3.1~22.04.2
```

Note: You may move the contents of `install/Release` to any other directory and `cmake` will still be able to discover dawn as long as `CMAKE_PREFIX_PATH` points to the new install tree.
