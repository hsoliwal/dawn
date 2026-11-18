# Testing Dawn

This fork uses CMake for native testing. Chromium GN/depot_tools, browser/Node.js tests and
the removed `dawn_wire` tests are not available.

## Native test targets

With the platform toolchain and dependencies installed, configure a dedicated CMake build:

```sh
cmake -S . -B out/Tests -G Ninja -DDAWN_FETCH_DEPENDENCIES=ON -DDAWN_BUILD_TESTS=ON -DTINT_BUILD_TESTS=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build out/Tests --target dawn_unittests dawn_end2end_tests tint_cmd_test_test_cmd --parallel 2
./out/Tests/dawn_unittests
./out/Tests/tint_unittests
```

`dawn_unittests` includes native validation tests; `dawn_end2end_tests` requires an
appropriate GPU/backend/driver environment. These commands are examples, not executed
verification results.

The Tint target `tint_cmd_test_test_cmd` produces `tint_unittests`. For a
multi-configuration generator, pass `--config Debug` and use its configuration
output directory. Windows executables have the `.exe` suffix. Discover native
GPU cases with `dawn_end2end_tests --gtest_list_tests`, then execute a selected
case with `--gtest_filter`; listing tests is not execution.

## Native build regression checks

Check native dependency selection, dependency-fetch failures, build-helper
arguments, and rejected browser configurations without downloading dependencies
or accessing a GPU:

```sh
python3 tools/native_build_test.py
cd tools/src
go test ./cmd/fuzz
```

Use native GTest options such as `--gtest_filter` and `--gtest_output` directly.
Chromium test-launcher argument translation and its compatibility helper have
been removed. The generator regression checks require Jinja2 in the selected
Python environment.

## Native benchmarks

The CMake target `dawn_benchmarks` measures native object creation and related
host work using the null backend:

```sh
cmake -S . -B out/Benchmarks -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DDAWN_FETCH_DEPENDENCIES=ON \
  -DDAWN_BUILD_BENCHMARKS=ON -DDAWN_BUILD_TESTS=OFF \
  -DTINT_BUILD_TESTS=OFF -DDAWN_BUILD_SAMPLES=OFF
cmake --build out/Benchmarks --target dawn_benchmarks --parallel 2
./out/Benchmarks/dawn_benchmarks
```

Null-backend timings do not measure GPU throughput. Compare results with the
same compiler, dependency revisions, configuration, machine, and benchmark
selection.

## Performance-test sources (not a current CMake target)

Sources under [perf_tests](../../src/dawn/tests/perf_tests) describe Dawn performance
metrics and benchmarks. The current [test CMake configuration](../../src/dawn/tests/CMakeLists.txt)
does not define `dawn_perf_tests`, so historical Chromium/GN runner instructions
must not be used as native build commands.


### Terminology

 - Iteration: The unit of work being measured. It could be a frame, a draw call, a data upload, a
   computation, etc. `dawn_perf_tests` metrics are reported as time per iteration.
 - Step: A group of Iterations run together. The number of `iterationsPerStep` is provided to the
   constructor of `DawnPerfTestBase`.
 - Trial: A group of Steps run consecutively. `kNumTrials` are run for each test. A Step in a Trial
   is run repetitively for approximately `kCalibrationRunTimeSeconds`. Metrics are accumulated
   per-trial and reported as the total time divided by `numSteps * iterationsPerStep`.
   `maxStepsInFlight` is passed to the `DawnPerfTestsBase` constructor to limit the number of Steps
   pipelined.

(See [DawnPerfTest.h](../../src/dawn/tests/perf_tests/DawnPerfTest.h) for the definitions of these constants.)

### Metrics

`dawn_perf_tests` measures the following metrics:
 - `wall_time`: The time per iteration, including time waiting for the GPU between Steps in a
   Trial.
 - `cpu_time`: The time per iteration, not including time waiting for the GPU between Steps in a
   Trial.
 - `validation_time`: The time for CommandBuffer / RenderBundle validation.
 - `recording_time`: The time to convert Dawn commands to native commands.

These metrics describe historical benchmark source conventions; no Chromium reporting pipeline
or browser tracing tool is required by the native CMake build.

### Tests

**BufferUploadPerf**

Tests repetitively uploading data to the GPU using either `WriteBuffer` or `CreateBuffer` with
`mappedAtCreation = true`.

**DrawCallPerf**

DrawCallPerf tests drawing a simple triangle with many ways of encoding commands,
binding, and uploading data to the GPU. The rationale for this is the following:
  - Static/Multiple/Dynamic vertex buffers: Tests switching buffer bindings. This has
    a state tracking cost as well as a GPU driver cost.
  - Static/Multiple/Dynamic bind groups: Same rationale as vertex buffers
  - Static/Dynamic pipelines: In addition to a change to GPU state, changing the pipeline
    layout incurs additional state tracking costs in Dawn.
  - With/Without render bundles: All of the above can have lower validation costs if
    precomputed in a render bundle.
  - Static/Dynamic data: Updating data for each draw is a common use case. It also tests
    the efficiency of resource transitions.
