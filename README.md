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
Dawn is meant to be integrated as part of a larger system and is the underlying implementation of WebGPU in Chromium.

Dawn provides several WebGPU building blocks:
 - **WebGPU C/C++ headers** that applications and other building blocks use.
   - The `webgpu.h` version that Dawn implements.
   - A C++ wrapper for the `webgpu.h`.
 - **A "native" implementation of WebGPU** using platforms' GPU APIs: D3D12, Metal, Vulkan and OpenGL. See [per API support](docs/support.md) for more details.
 - **A client-server implementation of WebGPU** for applications that are in a sandbox without access to native drivers
 - **Tint** is a compiler for the WebGPU Shader Language (WGSL) that can be used in standalone to convert shaders from and to WGSL.

## Working with this fork

This repository is [hsoliwal/dawn](https://github.com/hsoliwal/dawn), forked from
[google/dawn](https://github.com/google/dawn). The build badge, issue trackers,
community links, and upstream contribution process in this README describe the
upstream project. They do not establish the build status or support policy of
this fork.

| Your goal | Start here |
| --- | --- |
| Integrate Dawn into a CMake application | [CMake quickstart](docs/quickstart-cmake.md) |
| Develop Dawn with its primary Chromium toolchain | [Build and dependency setup](docs/building.md), [development tips](docs/development-tips.md) |
| Understand native backends, wire transport, and generated APIs | [Dawn overview](docs/dawn/overview.md), [code generation](docs/dawn/codegen.md) |
| Work on WGSL translation | [Tint architecture](docs/tint/arch.md), [Tint source](src/tint), [Tint tests](docs/tint/testing.md) |
| Evaluate a platform or GPU backend | [Platform/API constraints](docs/support.md), [Dawn tests](docs/dawn/testing.md), [WebGPU CTS runner](docs/standalone_cts_runner.md) |

### Source entrypoints

- [src/dawn/native](src/dawn/native): WebGPU validation/state tracking and native GPU backends
- [src/dawn/wire](src/dawn/wire): client/server command serialization
- [src/dawn/dawn.json](src/dawn/dawn.json) and [generator](generator): API data model and generated-code templates
- [include](include): public header entrypoints; some headers are generated at build time
- [src/dawn/tests](src/dawn/tests): unit, validation, end-to-end, and performance tests
- [DEPS](DEPS) and [CMakeLists.txt](CMakeLists.txt): dependency revisions and build options

A successful library build is not GPU execution or WebGPU conformance evidence.
Availability depends on the selected backend, operating system, driver, and
device. Keep unit-test, end-to-end, CTS, and performance results distinct.

For fork-specific changes, open a pull request against
[hsoliwal/dawn](https://github.com/hsoliwal/dawn/pulls), based on `main`.
For upstream contributions, follow [CONTRIBUTING.md](CONTRIBUTING.md), including
its CLA and Gerrit review process. A fork PR is not an upstream submission.

Helpful links:

 - [Dawn bug tracker](https://issues.chromium.org/savedsearches/6783309) if you find issues with Dawn. Create a new issue [here](https://issues.chromium.org/issues/new?noWizard=true&component=1570784).
 - [Tint bug tracker](https://issues.chromium.org/savedsearches/6783217) if you find issues with Tint. Create a new issue [here](https://issues.chromium.org/issues/new?noWizard=true&component=1571063).
 - [Dawn's mailing list](https://groups.google.com/g/dawn-graphics) for other discussions related to Dawn.
 - [Dawn's source code](https://dawn.googlesource.com/dawn)
 - [Dawn's Matrix chatroom](https://matrix.to/#/#webgpu-dawn:matrix.org) for live discussion around contributing or using Dawn.
 - [WebGPU's Matrix chatroom](https://matrix.to/#/#WebGPU:matrix.org)

## Documentation

Developer documentation:

 - [Dawn overview](docs/dawn/overview.md)
 - [Building](docs/building.md)
 - [Contributing](CONTRIBUTING.md)
 - [Code of Conduct](CODE_OF_CONDUCT.md)
 - [Testing Dawn](docs/dawn/testing.md)
 - [Testing Tint](docs/tint/testing.md)
 - [Running the WebGPU CTS with the standalone runner](docs/standalone_cts_runner.md)
 - [Debugging Dawn](docs/dawn/debugging.md)
 - [Dawn's infrastructure](docs/dawn/infra.md)
 - [Dawn errors](docs/dawn/errors.md)
 - [Tint experimental extensions](docs/tint/experimental_extensions.md)
 - [Quickstart with CMake](docs/quickstart-cmake.md)
 - [Becoming a committer](docs/becoming-committer.md)


For application integration, begin with the [CMake quickstart](docs/quickstart-cmake.md)
and check [platform/API support](docs/support.md) before choosing a backend.

## License

See [LICENSE](LICENSE) for the file-specific license text: the default is BSD
3-Clause, with Apache-2.0 sections for the listed paths. Preserve the
[Dawn and Tint authorship](AUTHORS), source headers, and applicable third-party
notices when redistributing code or artifacts. Dependencies retain their own terms.

## Disclaimer

This is not an officially supported Google product.
