# Dawn fork: architecture, setup, and exploration

[Repository README](../README.md) · [Overview](dawn/overview.md) · [Build guide](building.md) · [CMake integration](quickstart-cmake.md)

## What is in this fork?

Upstream Dawn implements WebGPU for native applications and larger systems such as Chromium. This fork retains Dawn Native and Tint, but has removed browser targets, the Chromium GN build, Node.js bindings and `dawn_wire`; this guide adds navigation, not a new backend, support promise, or benchmark result. Read the upstream [contribution process](../CONTRIBUTING.md), [license](../LICENSE), and README disclaimer before reusing or contributing material.

Choose a route:

- **Understand the code:** read the component map below, then [Dawn overview](dawn/overview.md).
- **Link an application:** follow [Quickstart with CMake](quickstart-cmake.md), including its adapter example and `dawn::webgpu_dawn` link target.
- **Develop Dawn:** use the [build guide](building.md) and its CMake dependency workflow.
- **Investigate shaders:** start with [Tint tests](tint/testing.md) and [src/tint](../src/tint).
- **Check GPU/backend coverage:** consult [support.md](support.md); a successful compile does not establish device support.

## Component map

| Component | Job | Source |
| --- | --- | --- |
| API model and generators | Describe the API and produce headers, wrappers, proc tables and native helpers | [dawn.json](../src/dawn/dawn.json), [generator](../generator) |
| Dawn Native frontend | Shared API validation and state tracking | [src/dawn/native](../src/dawn/native) |
| Native backends | Translate work to platform GPU APIs | Backend subdirectories under native |
| Dawn Proc | Dispatch through a function table to a selected implementation | [Overview: Dawn Proc](dawn/overview.md#dawn-proc-dawn_proc) |
| Tint | Translate WGSL into shader forms used by native backends | [src/tint](../src/tint) |
| Tests and samples | Exercise internal behavior, validation, GPU execution, and examples | [src/dawn/tests](../src/dawn/tests), [samples](../src/dawn/samples) |

A useful mental model is application -> WebGPU API -> native frontend -> selected backend -> driver/GPU. This fork has no wire client/server boundary; Tint supplies shader translation within the native path. These are responsibilities, not a literal stack trace for every call.

Some headers and implementations are generated. If a header is missing from a source-only checkout, read [code generation](dawn/codegen.md) and the build rules before assuming it was deleted.

## Setup checklist

The checked-out [CMakeLists.txt](../CMakeLists.txt) requires **CMake 3.22 or later**. Prefer the build-system requirement if prose from another revision disagrees.

The [build guide](building.md) also specifies Git, Python 3, Go 1.26+, a C++20 compiler, and Ninja 1.12 or an alternative CMake-supported build tool. This fork builds with CMake, not GN/depot_tools, and has no `dawn.node` target. Platform SDKs, compiler versions and Linux packages are detailed in the guide.

Dependency fetching uses network access for the pinned native dependencies in `DEPS`. Review each dependency's license when distributing native outputs; optional SDK assets retain their own terms.

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
| Inspect the revision | `git rev-parse HEAD` |
| Review a docs-only edit | `git diff --check` and `git diff --stat` |

Do not mix generators or toolchain configurations in one output directory. The dependency-fetch script does not resolve option-dependent setup.

## Tests: choose the evidence you need

| Question | Test layer | What it does not establish |
| --- | --- | --- |
| Internal logic or API validation? | Dawn unit/validation tests | Actual GPU execution |
| Native execution? | Dawn end-to-end tests | All GPUs or operating systems |
| Shader translation? | Tint unit and end-to-end tests | Whole-application correctness |
| Speed? | [Native benchmarks](dawn/testing.md#native-benchmarks) | Comparable results without controlled settings |

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

The original documentation inspection was on 2026-10-14. Browser-removal references here have since been reconciled with merged fork changes on 2026-11-17. The commands shown in this guide were not executed for this documentation change, and no build, test, conformance, or performance success is claimed. Fork documentation PRs do not replace upstream Gerrit review or its contributor requirements.

## Worked diagnosis and analysis notes

Notes about the fork work are kept in hsoliwal/com.synexia under `forks/dawn/`:

- [Worked diagnosis: a mapped-at-creation buffer is rejected](https://github.com/hsoliwal/com.synexia/blob/develop/forks/dawn/docs/buffer-validation-diagnosis.md)
- [Component inventory](https://github.com/hsoliwal/com.synexia/blob/develop/forks/dawn/docs/component-inventory.md) and [component guide](https://github.com/hsoliwal/com.synexia/blob/develop/forks/dawn/docs/repository-components.md)
- [Host-device resource lifecycle trace](https://github.com/hsoliwal/com.synexia/blob/develop/forks/dawn/docs/dawn/resource-lifecycle.md)

## Keeping commands and examples current

On a dependency or source update, compare the top-level CMake minimum, options, generated Tint target/output names, and the cited validator at the same commit. Update commands when those declarations change. Re-run relevant checks before replacing a source-reviewed statement with a runtime claim, and include GPU/backend details for any newly measured result.
