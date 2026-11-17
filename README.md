<div align="center">
  <img
      title="Dawn's logo"
      alt="Dawn's logo: a sun rising behind a stylized mountain inspired by the WebGPU logo."
      src="docs/imgs/dawn_logo_notext.png"
      width="50%">

  ![Build Status](https://github.com/google/dawn/actions/workflows/ci.yml/badge.svg?branch=main&event=push)
  [![Matrix Space](https://img.shields.io/static/v1?label=Space&message=%23webgpu-dawn&color=blue&logo=matrix)](https://matrix.to/#/#webgpu-dawn:matrix.org)
</div>

# Dawn, a WebGPU implementation

Dawn is an open-source and cross-platform implementation of the [WebGPU](https://webgpu.dev) standard.
More precisely it implements [`webgpu.h`](https://github.com/webgpu-native/webgpu-headers/blob/main/webgpu.h) that is a one-to-one mapping with the WebGPU IDL.
Upstream Dawn is integrated into Chromium. This fork instead targets native applications: Chromium's GN build, browser/WebAssembly and Node.js targets, and the Dawn Wire client/server library have been removed.

Dawn provides several WebGPU building blocks:
 - **WebGPU C/C++ headers** that applications and other building blocks use.
   - The `webgpu.h` version that Dawn implements.
   - A C++ wrapper for the `webgpu.h`.
 - **A "native" implementation of WebGPU** using platforms' GPU APIs: D3D12, Metal, Vulkan and OpenGL. See [per API support](docs/support.md) for more details.
 - **Tint** is a compiler for the WebGPU Shader Language (WGSL) that can be used in standalone to convert shaders from and to WGSL.

<!-- fork-homepage-guide:begin -->
## Start here in this fork

This is [hsoliwal's fork](https://github.com/hsoliwal/dawn) of
[google/dawn](https://github.com/google/dawn). It is useful for learning the native
WebGPU stack, integrating Dawn into a C++ application, and following a request from
validation through backend execution. The fork retains Dawn Native and Tint while removing browser build paths, Node.js bindings and `dawn_wire` ([browser/Node/Chromium removal](https://github.com/hsoliwal/dawn/pull/9), [Wire removal](https://github.com/hsoliwal/dawn/pull/10), [remaining Emscripten/Node/V8 cleanup](https://github.com/hsoliwal/dawn/pull/12)). These changes do not establish GPU/backend qualification or performance. The build badge above belongs to upstream.

### The architecture in one minute

| Concept | Responsibility | Start reading |
| --- | --- | --- |
| WebGPU API | Application-visible objects, descriptors and operations | [API model](src/dawn/dawn.json) |
| Adapter / device | Discover capabilities, then create the execution/resource context | [CMake application example](docs/quickstart-cmake.md) |
| Dawn Native | Shared validation and backend implementations | [Native source](src/dawn/native/) |
| Tint / WGSL | Compile WebGPU shaders toward backend shader forms | [Tint source](src/tint/) |
| Generated code | Headers, wrappers and dispatch derived from inputs | [Code-generation guide](docs/dawn/codegen.md) |

A useful reading path is application → WebGPU API → native validation → backend
→ driver/GPU. Native dispatch is direct in this fork; the Wire client/server
layer is removed. Tint handles shader translation. This is a component map, not a promise that every
operation follows an identical call stack.

### Quickstart: build a local CMake install

First follow the platform prerequisites in [building.md](docs/building.md):
CMake 3.22+, Git, Python 3, Go 1.23+, a C++20 compiler, and Ninja 1.12+ for the
example below. Dependency fetching uses the network and may download substantial
toolchains; review the dependency-license notice in that guide first.

```sh
git clone https://github.com/hsoliwal/dawn.git
cd dawn
git rev-parse HEAD
cmake -S . -B out/Release -G Ninja \
  -DDAWN_FETCH_DEPENDENCIES=ON -DDAWN_ENABLE_INSTALL=ON \
  -DCMAKE_BUILD_TYPE=Release
cmake --build out/Release
cmake --install out/Release --prefix install/Release
```

This writes to a local install prefix. Use the complete
[consumer quickstart](docs/quickstart-cmake.md) to configure your application with
`find_package(Dawn REQUIRED)` and link `dawn::webgpu_dawn`. A successful build
does not prove that an adapter is available or that every backend works.

### Compact command cheat sheet

| Task | Command / route |
| --- | --- |
| Inspect configured options | `cmake -LA -N out/Release` |
| Find a buffer validation entry | `git grep -n ValidateBufferDescriptor -- src/dawn/native` |
| Find buffer-related unit cases | `git ls-files 'src/dawn/tests/unittests/validation/*Buffer*'` |
| Find device-execution cases | `git ls-files 'src/dawn/tests/end2end/*Buffer*'` |
| Choose tests and test-build options | [Fork guide](docs/FORK_GUIDE.md) and [Dawn testing](docs/dawn/testing.md) |
| Diagnose shader behavior | [Tint testing](docs/tint/testing.md) |
| Check platform/API coverage | [Support matrix](docs/support.md) |

### Worked example: validation is not GPU execution

In [Buffer.cpp](src/dawn/native/Buffer.cpp), `ValidateBufferDescriptor` rejects a
buffer with `mappedAtCreation=true` when its size is not divisible by four.
With otherwise valid inputs, size 6 reaches that rejection; size 8 avoids that
particular check but still needs to satisfy usage, limits and allocation rules.
Turning mapping off removes only this conditional requirement, not later mapping
or resource-use rules. Read the matching
[validation tests](src/dawn/tests/unittests/validation/BufferValidationTests.cpp)
before blaming a driver or bypassing validation.

This walkthrough is source-derived and the commands were not executed for this
homepage update. Unit tests, GPU end-to-end tests, WebGPU conformance and performance
measurements answer different questions. Record revision, toolchain, backend,
GPU/driver, command and the full error context when reporting a result.

<!-- fork-homepage-guide:end -->

Helpful links:

 - [Dawn bug tracker](https://issues.chromium.org/savedsearches/6783309) if you find issues with Dawn. Create a new issue [here](https://issues.chromium.org/issues/new?noWizard=true&component=1570784).
 - [Tint bug tracker](https://issues.chromium.org/savedsearches/6783217) if you find issues with Tint. Create a new issue [here](https://issues.chromium.org/issues/new?noWizard=true&component=1571063).
 - [Dawn's mailing list](https://groups.google.com/g/dawn-graphics) for other discussions related to Dawn.
 - [Dawn's source code](https://dawn.googlesource.com/dawn)
 - [Dawn's Matrix chatroom](https://matrix.to/#/#webgpu-dawn:matrix.org) for live discussion around contributing or using Dawn.
 - [WebGPU's Matrix chatroom](https://matrix.to/#/#WebGPU:matrix.org)

## Documentation table of content

For this fork, start with the [architecture and setup guide](docs/FORK_GUIDE.md): component map, command cheat sheet, test boundaries, and worked exploration.

Developer documentation:

 - [Dawn overview](docs/dawn/overview.md)
 - [Building](docs/building.md)
 - [Contributing](CONTRIBUTING.md)
 - [Code of Conduct](CODE_OF_CONDUCT.md)
 - [Testing Dawn](docs/dawn/testing.md)
 - [Testing Tint](docs/tint/testing.md)
 - [Debugging Dawn](docs/dawn/debugging.md)
 - [Dawn errors](docs/dawn/errors.md)
 - [Tint experimental extensions](docs/tint/experimental_extensions.md)
 - [Quickstart with CMake](docs/quickstart-cmake.md)
 - [Becoming a committer](docs/becoming-committer.md)


User documentation: (TODO, figure out what overlaps with the webgpu.h docs)

## License

BSD 3-Clause License, please see [LICENSE](/LICENSE).

## Disclaimer

This is not an officially supported Google product.
