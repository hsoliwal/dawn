# Dawn fork: architecture, setup, and exploration

[Repository README](../README.md) · [Overview](dawn/overview.md) · [Build guide](building.md) · [CMake integration](quickstart-cmake.md)

## What is in this fork?

Dawn implements WebGPU for native applications and larger systems such as Chromium. This public fork inherits Dawn and Tint; this guide adds navigation, not a new backend, support promise, or benchmark result. Read the upstream [contribution process](../CONTRIBUTING.md), [license](../LICENSE), and README disclaimer before reusing or contributing material.

Choose a route:

- **Understand the code:** read the component map below, then [Dawn overview](dawn/overview.md).
- **Link an application:** follow [Quickstart with CMake](quickstart-cmake.md), including its adapter example and `dawn::webgpu_dawn` link target.
- **Develop Dawn:** use the [build guide](building.md) and its recommended Chromium/depot_tools dependency workflow.
- **Investigate shaders:** start with [Tint tests](tint/testing.md) and [src/tint](../src/tint).
- **Check GPU/backend coverage:** consult [support.md](support.md); a successful compile does not establish device support.

## Component map

| Component | Job | Source |
| --- | --- | --- |
| API model and generators | Describe the API and produce headers, wrappers, proc tables, and wire code | [dawn.json](../src/dawn/dawn.json), [generator](../generator) |
| Dawn Native frontend | Shared API validation and state tracking | [src/dawn/native](../src/dawn/native) |
| Native backends | Translate work to platform GPU APIs | Backend subdirectories under native |
| Dawn Wire | Serialize client commands and dispatch them on the server; return callbacks | [src/dawn/wire](../src/dawn/wire) |
| Dawn Proc | Dispatch through a function table to a selected implementation | [Overview: Dawn Proc](dawn/overview.md#dawn-proc-dawn_proc) |
| Tint | Translate WGSL into shader forms used by native backends | [src/tint](../src/tint) |
| Tests and samples | Exercise internal behavior, validation, GPU execution, and examples | [src/dawn/tests](../src/dawn/tests), [samples](../src/dawn/samples) |

A useful mental model is application -> WebGPU API -> native frontend -> selected backend -> driver/GPU. A wire client/server boundary may sit before the native implementation. Tint supplies shader translation within this larger path. These are responsibilities, not a literal stack trace for every call.

Some headers and implementations are generated. If a header is missing from a source-only checkout, read [code generation](dawn/codegen.md) and the build rules before assuming it was deleted.

## Setup checklist

The checked-out [CMakeLists.txt](../CMakeLists.txt) requires **CMake 3.22 or later**. Prefer the build-system requirement if prose from another revision disagrees.

The [build guide](building.md) also specifies Git, Python 3, Go 1.23+, a C++20 compiler, and Ninja 1.12 or an alternative CMake-supported build tool. GN development uses depot_tools; platform SDKs, compiler versions, and Linux packages are detailed in that guide. Node.js/npm are needed for `dawn.node`, not for every native use.

Dependency fetching uses network access and can download substantial toolchains. Read the build guide's dependency license notice, including Direct3D WARP, before fetching. This guide does not accept those terms for you.

## CMake command cheat sheet

The following is an adaptation of the existing quickstart for this fork, using a single-config generator such as Ninja. Install the applicable platform prerequisites first.

```sh
git clone https://github.com/hsoliwal/dawn.git
cd dawn
git rev-parse HEAD
cmake -S . -B out/Release -G Ninja -DDAWN_FETCH_DEPENDENCIES=ON -DDAWN_ENABLE_INSTALL=ON -DCMAKE_BUILD_TYPE=Release
cmake --build out/Release
cmake --install out/Release --prefix install/Release
```

`DAWN_FETCH_DEPENDENCIES=ON` invokes dependency fetching; it is not an offline build. Installation above writes to a local prefix. For Visual Studio or another multi-configuration generator, use the generator's configuration selection and output layout rather than assuming these executable paths.

| Need | Entry point |
| --- | --- |
| Integrate a consumer | `find_package(Dawn REQUIRED)` and link `dawn::webgpu_dawn`; see the full quickstart |
| Inspect build options | `cmake -LA -N out/Release` after successful configuration |
| Use the main GN workflow | Follow dependency setup in [building.md](building.md), then `gn gen out/Debug` and `autoninja -C out/Debug` |
| Inspect the revision | `git rev-parse HEAD` |
| Review a docs-only edit | `git diff --check` and `git diff --stat` |

Do not mix generators or toolchain configurations in one output directory. The dependency-fetch script is not equivalent to all of gclient's option-dependent setup.

## Tests: choose the evidence you need

| Question | Test layer | What it does not establish |
| --- | --- | --- |
| Internal logic or API validation? | Dawn unit/validation tests | Actual GPU execution |
| Wire behavior? | Wire unit tests | Every native driver/backend combination |
| Native execution? | Dawn end-to-end tests | All GPUs or operating systems |
| Shader translation? | Tint unit and end-to-end tests | Whole-application correctness |
| WebGPU conformance? | [Standalone CTS runner](standalone_cts_runner.md) or documented dawn.node route | A passing subset is not a full conformance result |
| Speed? | [Performance tests](dawn/testing.md#dawn-perf-tests) | Comparable results without controlled settings |

Dawn's CMake test build is optional. For a dedicated single-config test tree, after the same prerequisites and dependency review:

```sh
cmake -S . -B out/Tests -G Ninja -DDAWN_FETCH_DEPENDENCIES=ON -DDAWN_BUILD_TESTS=ON -DTINT_BUILD_TESTS=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build out/Tests --target dawn_unittests tint_cmd_test_test_cmd
./out/Tests/dawn_unittests --gtest_list_tests
./out/Tests/tint_unittests --gtest_list_tests
```

Listing tests is discovery, not execution. Select a name from that output and run the executable with `--gtest_filter='SelectedSuite.SelectedTest'`, replacing the example. On Windows use the corresponding `.exe`; multi-configuration generators may place binaries in a configuration subdirectory. The Tint CMake target is `tint_cmd_test_test_cmd`, whose output name is `tint_unittests` in [its generated build description](../src/tint/cmd/test/BUILD.cmake). Target declarations are in [Dawn test CMake](../src/dawn/tests/CMakeLists.txt), and Tint's [testing guide](tint/testing.md) explains its separate test layers.

## Worked exploration: buffer validation versus execution

```sh
git grep -n 'create buffer' -- src/dawn/dawn.json
git grep -n 'ValidateBufferDescriptor' -- src/dawn/native
git ls-files 'src/dawn/tests/unittests/validation/*Buffer*'
git ls-files 'src/dawn/tests/end2end/*Buffer*'
```

Start with the API model, find validation in the native frontend, and compare validation tests with GPU execution tests. Follow the actual call sites before concluding where a failure originates. Record whether the symptom is descriptor rejection, generated API mismatch, shader compilation, or backend execution.

For an application-level smoke check, use the complete adapter-request example in [quickstart-cmake.md](quickstart-cmake.md). Successful adapter discovery establishes only that the example found an adapter in that environment; it does not validate rendering, all backends, or performance.

## Troubleshooting and reporting

- **CMake rejects the version:** check the top-level minimum; old 3.16 guidance does not override the current 3.22 requirement.
- **Missing dependencies:** distinguish an incomplete fetch from a compiler error; do not assume a shallow source clone includes dependencies.
- **Missing test target:** inspect `DAWN_BUILD_TESTS`, `TINT_BUILD_TESTS`, platform conditions, and the selected generator.
- **No adapter or backend:** record OS, GPU/driver, enabled backend, and the exact example; consult the support matrix.
- **Linux compiler/standard-library mismatch:** the build guide documents this case; use a fresh output directory after changing toolchains.
- **Generated source is absent:** inspect generation inputs and build steps instead of hand-editing output.

A useful report includes commit, dependency/setup route, compiler and CMake versions, build options, OS/GPU/backend, exact command, expected/actual result, and the smallest relevant log excerpt. Remove credentials and private paths.

Public source and documentation were inspected on 2026-10-14. These commands were not executed, and no build, test, conformance, or performance success is claimed. Fork documentation PRs do not replace upstream Gerrit review or its contributor requirements.
