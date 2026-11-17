# Dawn repository overview

This repository contains the implementation of Dawn, whose main library is dawn_native, along
with support libraries, tests, and samples. (This fork removed the dawn_wire client-server library.)
Dawn makes heavy use of code-generation based on the `dawn.json` file that describes the native
WebGPU API. It is used to generate the API headers, C++ wrapper, and more!

## Directory structure

- [`dawn.json`](../../src/dawn/dawn.json): contains a description of the native WebGPU in JSON form.
  It is the data model that's used by the code generators.
- [`generator`](../../generator): directory containg the code generators and their templates.
  Generators are based on Jinja2 and parse data-models from JSON files.
    - [`dawn_json_generator.py`](../../generator/dawn_json_generator.py): the main code generator
      that outputs the WebGPU headers, C++ wrapper, proc tables and native helpers.
    - [`templates`](../../generator/templates): Jinja2 templates for the generator, with
      subdirectories for groups of templates that are all used in the same library.
- [`include`](../../include):
    - [`dawn`](../../include/dawn): public headers with subdirectories for each library. Note that
      some headers are auto-generated and not present directly in the directory.
- [`scripts`](../../scripts): contains a grab-bag of files that are used for building Dawn, in
  testing, etc.
- [`src`](../../src):
  - [`dawn`](../../src/dawn): root directory for Dawn code
      - [`common`](../../src/dawn/common): helper code that is allowed to be used by Dawn's core
        library, `dawn_native`. Also allowed for use in all other Dawn targets.
      - [`native`](../../src/dawn/native): code for the implementation of WebGPU on top of graphics
        APIs. Files in this folder are the "frontend" while subdirectories are "backends".
         - `<backend>`: code for the implementation of the backend on a specific graphics API, for
           example `d3d12`, `metal` or `vulkan`.
      - [`samples`](../../src/dawn/samples): a small collection of samples using the native WebGPU
        API. They were mostly used when bringing up Dawn for the first time, and to test the
        `WGPUSurface` object.
      - [`tests`](../../src/dawn/tests):
        - [`end2end`](../../src/dawn/tests/end2end): tests for the execution of the WebGPU API and
          require a GPU to run.
        - [`perf_tests`](../../src/dawn/tests/perf_tests): benchmarks for various aspects of Dawn.
        - [`unittests`](../../src/dawn/tests/unittests): code unittests of internal classes, but
          also by extension WebGPU API tests that don't require a GPU to run.
          - [`validation`](../../src/dawn/tests/unittests/validation): WebGPU validation tests not
            using the GPU (frontend tests)
        - [`white_box`](../../src/dawn/tests/white_box): tests using the GPU that need to access the
          internals of `dawn_native`.
      - [`utils`](../../src/dawn/utils): helper code to use Dawn used by tests and samples but
        disallowed for `dawn_native`.
      - [`platform`](../../src/dawn/platform): definition of interfaces for dependency injection in
        `dawn_native`.
- [`third_party`](../../third_party): directory where dependencies live as well as their
  buildfiles.

## Dawn Native (`dawn_native`)

The largest library in Dawn is `dawn_native` which implements the WebGPU API by translating to
native graphics APIs such as D3D12, Metal or Vulkan. It is composed of a frontend that does all the
state-tracking and validation, and backends that do the actual translation to the native graphics
APIs.

`dawn_native` hosts the [spirv-val](https://github.com/KhronosGroup/SPIRV-Tools) for validation of
SPIR-V shaders and uses [Tint](../../src/tint) shader translator to convert WGSL shaders to an
equivalent shader for use in the native graphics API (HLSL for D3D12, MSL for Metal or Vulkan
SPIR-V for Vulkan).

## Dawn Proc (`dawn_proc`)

Dawn's generated proc table dispatches WebGPU entrypoints to the native implementation. The
`dawn_proc` support forwards C API calls through that table, allowing native callers to use
Dawn without repeatedly resolving each entrypoint with `wgpuGetProcAddress`. The Chromium
client/server `dawn_wire` implementation is absent from this fork.

## Code generation

When the WebGPU API evolves, a lot of places in Dawn have to be updated, so to reduce efforts, Dawn
relies heavily on code generation for headers, proc tables and native validation support. For
more information, see [codegen.md](codegen.md).
