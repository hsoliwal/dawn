# Native dependency pins consumed by tools/fetch_dawn_dependencies.py.
# Optional native SDK, fuzzing and LiteRT-LM dependencies remain pinned.
# Chromium GN/gclient bootstrap dependencies and hooks are retired.

vars = {
  'chromium_git': 'https://chromium.googlesource.com',
  'swiftshader_git': 'https://swiftshader.googlesource.com',
  'dawn_standalone': True,
  'dawn_cmake_version': 'version:2@3.23.3',
  'dawn_ninja_version': 'version:3@1.12.1.chromium.4',
  'dawn_go_version': 'version:3@1.26.6',
  'dawn_agility_sdk_version': 'version:2@1.722.0-preview',
  'dawn_direct3d_warp_version': 'version:3@1.0.21.chromium.1',
  'dawn_bazelisk_version': 'version:3@1.29.0',
  'dawn_llvm-dev_version': 'version:3@22.1.0',
  'dawn_zstd_version': 'Lf-seQJdussz81cZXnez5xIxEdkejDRxKumQpHbHMOUC',
  'fetch_cmake': False,
  'fetch_bazel': False,
  'non_git_source': 'True',
  'checkout_mesa': False,
  'checkout_litert_lm': False,
  'android_ndk_version': Str('2@30.0.16248370'),
  'android_sdk_build-tools_version': 'version_37.0.0',
  'android_sdk_emulator_version': '9lGp8nTUCRRWGMnI_96HcKfzjnxEJKUcfvfwmA3wXNkC',
  'android_sdk_platform-tools_version': 'qTD9QdBlBf3dyHsN1lJ0RH6AhHxR42Hmg2Ih-Vj4zIEC',
  'android_sdk_platforms_version': 'AAswZ5rZBFDhMaH4QbKPmVtP4vnjiNUW_zPhdWvNe6wC',
}

deps = {
  'third_party/clang-format/script': {
    'url': '{chromium_git}/external/github.com/llvm/llvm-project/clang/tools/clang-format.git@0ca48e889615842946cdcc09c4e7ee976dc36444',
    'condition': 'dawn_standalone',
  },
  'third_party/libc++/src': {
    'url': '{chromium_git}/external/github.com/llvm/llvm-project/libcxx.git@64f64c14ae2f4653af875bd172462a4c5e6afe18',
    'condition': 'dawn_standalone',
  },
  'third_party/libc++abi/src': {
    'url': '{chromium_git}/external/github.com/llvm/llvm-project/libcxxabi.git@8e42446dd61148a66220123297964bd3856e7cf9',
    'condition': 'dawn_standalone',
  },
  'third_party/llvm-libc/src': {
    'url': '{chromium_git}/external/github.com/llvm/llvm-project/libc.git@7d33739396cb4cfdebcbc02958c8fa133411d69f',
    'condition': 'dawn_standalone',
  },
  'third_party/libdrm/src': {
    'url': '{chromium_git}/chromiumos/third_party/libdrm.git@e984d448b8b17aab853369e6c203e53719f46de1',
    'condition': 'dawn_standalone and host_os == "linux"',
  },
  'third_party/libFuzzer/src': {
    'url': '{chromium_git}/external/github.com/llvm/llvm-project/compiler-rt/lib/fuzzer.git' + '@' + 'c7ea90fb61105752fa78e257e77a7c5d62fff7d3',
    'condition': 'dawn_standalone',
  },
  'third_party/googletest/src': {
    'url': '{chromium_git}/external/github.com/google/googletest@e882c36410197464e3429546e6a7d5e217bde51e',
    'condition': 'dawn_standalone',
  },
  'third_party/google_benchmark/src': {
    'url': '{chromium_git}/external/github.com/google/benchmark.git' + '@' + 'a6b4a9f00b36c19af9997d68a1cf6e0b5b3d032c',
    'condition': 'dawn_standalone',
  },
  'third_party/perfetto': {
    'url': '{chromium_git}/external/github.com/google/perfetto.git@831d3934ff48880e397db63866b9c951b8aa3f53',
    'condition': 'dawn_standalone',
  },
  'third_party/mesa/src': {
    'url': '{chromium_git}/external/gitlab.freedesktop.org/mesa/mesa/@e9fe5b472b74e652b0cff4b304b88e4c799d7902',
    'condition': 'checkout_mesa and host_os == "linux"',
  },
  'third_party/llvm-dev': {
    'packages': [{
      'package': 'infra/3pp/tools/llvm-dev/linux-amd64',
      'version': Var('dawn_llvm-dev_version'),
    }],
    'dep_type': 'cipd',
    'condition': 'checkout_mesa and host_os == "linux"',
  },
  'third_party/zstd': {
    'packages': [{
      'package': 'infra/3pp/static_libs/libzstd/linux-amd64',
      'version': Var('dawn_zstd_version'),
    }],
    'dep_type': 'cipd',
    'condition': 'checkout_mesa and host_os == "linux"',
  },
  'third_party/jinja2': {
    'url': '{chromium_git}/chromium/src/third_party/jinja2@fde3c16799bd5937e4f15aedc9037c89f96236b9',
    'condition': 'dawn_standalone',
  },
  'third_party/markupsafe': {
    'url': '{chromium_git}/chromium/src/third_party/markupsafe@4256084ae14175d38a3ff7d739dca83ae49ccec6',
    'condition': 'dawn_standalone',
  },
  'third_party/glfw3/src': {
    'url': '{chromium_git}/external/github.com/glfw/glfw@92dcf4ce74f2e2554a98fea09be7c705c17daa5a',
  },
  'third_party/vulkan_memory_allocator': {
    'url': '{chromium_git}/external/github.com/GPUOpen-LibrariesAndSDKs/VulkanMemoryAllocator@7e55b011e16182fc349149abbd3aaf3b1db46421',
    'condition': 'dawn_standalone',
  },
  'third_party/angle': {
    'url': '{chromium_git}/angle/angle@42f176bb624d858668ba3931953f220be101d024',
    'condition': 'dawn_standalone',
  },
  'third_party/swiftshader': {
    'url': '{swiftshader_git}/SwiftShader@708e9e77773860bbb2ad9bb2d61b451de4b84e31',
    'condition': 'dawn_standalone',
  },
  'third_party/vulkan-deps': {
    'url': '{chromium_git}/vulkan-deps@6007f6f90b2ec270300b4b3975a23db4cfa8b4a9',
    'condition': 'dawn_standalone',
  },
  'third_party/glslang/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/glslang@385445a87d21d7a5c7bee2f7bef8a87850f6bf28',
    'condition': 'dawn_standalone',
  },
  'third_party/spirv-headers/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/SPIRV-Headers@5c6004e758e0c80185ef2cee93ae5c10fa342a5b',
    'condition': 'dawn_standalone',
  },
  'third_party/spirv-tools/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/SPIRV-Tools@3e73ae769e684f17b283250f803a231a830d45e3',
    'condition': 'dawn_standalone',
  },
  'third_party/vulkan-headers/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/Vulkan-Headers@b26454f3ccd67e704117a39295fa13935fd3804c',
    'condition': 'dawn_standalone',
  },
  'third_party/vulkan-loader/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/Vulkan-Loader@0b137080f608a1f99527f1b123424545f2d9ba49',
    'condition': 'dawn_standalone',
  },
  'third_party/vulkan-tools/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/Vulkan-Tools@1d3fbab1ff5abce9f3eb9f3e7fcf66f455ae4475',
    'condition': 'dawn_standalone',
  },
  'third_party/vulkan-utility-libraries/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/Vulkan-Utility-Libraries@5a873d3b75d38ef6a0833589ce3603d63f3f6a9c',
    'condition': 'dawn_standalone',
  },
  'third_party/vulkan-validation-layers/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/Vulkan-ValidationLayers@d63b17612002fdbf0ba08d12b1574b8f422a70f0',
    'condition': 'dawn_standalone',
  },
  'third_party/zlib': {
    'url': '{chromium_git}/chromium/src/third_party/zlib@401d1853956d408bfd327ee5e54c1c7b67086f87',
    'condition': 'dawn_standalone',
  },
  'third_party/abseil-cpp': {
    'url': '{chromium_git}/chromium/src/third_party/abseil-cpp@ecb00cc74a6251b273c78789f947d3eb280dd093',
    'condition': 'dawn_standalone',
  },
  'third_party/directx-shader-compiler/src': {
    'url': '{chromium_git}/external/github.com/microsoft/DirectXShaderCompiler@5ed39344cdccd97c02e37001669e80e7f9444e5f',
  },
  'third_party/directx-headers/src': {
    # The non-Windows build of DXC depends on DirectX-Headers, and at a specific commit (not ToT)
    'url': '{chromium_git}/external/github.com/microsoft/DirectX-Headers@980971e835876dc0cde415e8f9bc646e64667bf7',
    'condition': 'host_os != "win"',
  },
  'third_party/agility-sdk/src': {
    'packages': [
      {
        'package': 'chromium/third_party/agility-sdk',
        'version': Var('dawn_agility_sdk_version'),
      },
    ],
    'condition': 'checkout_win',
    'dep_type': 'cipd',
  },
  'third_party/direct3d-warp/bin/': {
    'packages': [
      {
        'package': 'infra/3pp/direct3d-warp',
        'version': Var('dawn_direct3d_warp_version'),
      },
    ],
    'condition': 'dawn_standalone and checkout_win',
    'dep_type': 'cipd',
  },
  'third_party/OpenGL-Registry/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/OpenGL-Registry@6af574a14089ccfee87efe230ebcdd8742859813',
  },
  'third_party/EGL-Registry/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/EGL-Registry@8e56e86e65687697ef54114cdb1afabdfac756bf',
  },
  'third_party/webgpu-headers/src': {
    'url': '{chromium_git}/external/github.com/webgpu-native/webgpu-headers@a1dc77409bb2b8bd80540cbf4b8db219e123e909',
  },
  'tools/golang/linux-amd64': {
    'packages': [{
      'package': 'infra/3pp/tools/go/linux-amd64',
      'version': Var('dawn_go_version'),
    }],
    'dep_type': 'cipd',
    'condition': '(checkout_android or checkout_linux) and non_git_source',
  },
  'tools/golang/linux-arm64': {
    'packages': [{
      'package': 'infra/3pp/tools/go/linux-arm64',
      'version': Var('dawn_go_version'),
    }],
    'dep_type': 'cipd',
    'condition': '(checkout_android or checkout_linux) and non_git_source',
  },
  'tools/golang/mac-amd64': {
    'packages': [{
      'package': 'infra/3pp/tools/go/mac-amd64',
      'version': Var('dawn_go_version'),
    }],
    'dep_type': 'cipd',
    'condition': '(checkout_ios or checkout_mac) and non_git_source',
  },
  'tools/golang/mac-arm64': {
    'packages': [{
      'package': 'infra/3pp/tools/go/mac-arm64',
      'version': Var('dawn_go_version'),
    }],
    'dep_type': 'cipd',
    'condition': '(checkout_ios or checkout_mac) and non_git_source',
  },
  'tools/golang/windows-amd64': {
    'packages': [{
      'package': 'infra/3pp/tools/go/windows-amd64',
      'version': Var('dawn_go_version'),
    }],
    'dep_type': 'cipd',
    'condition': 'checkout_win and non_git_source',
  },
  'tools/golang/windows-arm64': {
    'packages': [{
      'package': 'infra/3pp/tools/go/windows-arm64',
      'version': Var('dawn_go_version'),
    }],
    'dep_type': 'cipd',
    'condition': 'checkout_win and non_git_source',
  },
  'tools/cmake': {
    'condition': 'fetch_cmake',
    'packages': [{
      'package': 'infra/3pp/tools/cmake/${{platform}}',
      'version': Var('dawn_cmake_version'),
    }],
    'dep_type': 'cipd',
  },
  'tools/bazelisk': {
    'condition': 'fetch_bazel or checkout_litert_lm',
    'packages': [{
      'package': 'infra/3pp/tools/bazelisk/${{platform}}',
      'version': Var('dawn_bazelisk_version'),
    }],
    'dep_type': 'cipd',
  },
  'third_party/ninja': {
    'packages': [
      {
        'package': 'infra/3pp/tools/ninja/${{platform}}',
        'version': Var('dawn_ninja_version'),
      }
    ],
    'dep_type': 'cipd',
  },
  'third_party/protobuf': {
    'url': '{chromium_git}/chromium/src/third_party/protobuf@3813fd5b3029807583e5d2549a40d78fa499c3e8',
    'condition': 'dawn_standalone',
  },
  'tools/protoc_wrapper': {
    'url': '{chromium_git}/chromium/src/tools/protoc_wrapper@5c77c0c9fdebb2d87378bcea183e4c6937fd8c53',
    'condition': 'dawn_standalone',
  },
  'third_party/libprotobuf-mutator/src': {
    'url': '{chromium_git}/external/github.com/google/libprotobuf-mutator.git@a0448e5055e4740774e00d496f016d9fcd572200',
    'condition': 'dawn_standalone',
  },
  'third_party/partition_alloc': {
    'url': '{chromium_git}/chromium/src/base/allocator/partition_allocator.git@01906ada20b59e7e9a690a75ae7830f4080b3a78',
    'condition': 'dawn_standalone',
  },
  'third_party/android_sdk': {
    'url': Var('chromium_git') + '/chromium/src/third_party/android_sdk@c4d16bfe5cf8720e6dba6f571110deb14a51d6cf',
    'condition': 'checkout_android and dawn_standalone',
  },
  'third_party/android_sdk/public': {
    'packages': [
      {
        'package': 'chromium/third_party/android_sdk/public/build-tools/37.0.0/${{os}}',
        'version': Var('android_sdk_build-tools_version'),
      },
      {
        'package': 'chromium/third_party/android_sdk/public/emulator',
        'version': Var('android_sdk_emulator_version'),
      },
      {
        'package': 'chromium/third_party/android_sdk/public/platform-tools',
        'version': Var('android_sdk_platform-tools_version'),
      },
      {
        'package': 'chromium/third_party/android_sdk/public/platforms/android-37.2',
        'version': Var('android_sdk_platforms_version'),
      },
      {
        'package': 'chromium/third_party/android_sdk/public/cmdline-tools/${{os}}',
        'version': 'version:23.0.0',
      },
    ],
    'condition': 'checkout_android and dawn_standalone',
    'dep_type': 'cipd',
  },
  'third_party/android_toolchain/ndk': {
    'packages': [
      {
        'package': 'chromium/third_party/android_toolchain/android_toolchain/${{platform}}',
        'version': 'version:' + Var('android_ndk_version'),
      },
    ],
    'condition': 'checkout_android and dawn_standalone and '
                 '((host_os == "linux" and host_cpu == "x64") or '
                 '(host_os == "mac" and host_cpu == "arm64"))',
    'dep_type': 'cipd',
  },
  'third_party/jdk/current': {
    'packages': [
      {
        'package': 'chromium/third_party/jdk/${{platform}}',
        'version': 'version:2@jdk-25.0.5+8.f32c55fd1a.cr0',
      },
    ],
    'condition': 'checkout_android and dawn_standalone and non_git_source and '
                 '((host_os == "linux" and host_cpu == "x64") or '
                 '(host_os == "mac" and host_cpu == "arm64"))',
    'dep_type': 'cipd',
  },
  'third_party/android_build_tools': {
    'url': Var('chromium_git') + '/chromium/src/third_party/android_build_tools@ef683eac750f64c3cccf8b36ebcb840e038e35cf',
    'condition': 'checkout_android and dawn_standalone',
  },
  'third_party/android_build_tools/aapt2/cipd': {
    'packages': [
      {
        'package': 'chromium/third_party/android_build_tools/aapt2/${{platform}}',
        'version': 'version:2@9.6.0-alpha01-16666295',
      },
    ],
    'condition': 'checkout_android and dawn_standalone',
    'dep_type': 'cipd',
  },
  'third_party/android_build_tools/manifest_merger/cipd': {
    'packages': [
      {
        'package': 'chromium/third_party/android_build_tools/manifest_merger',
        'version': '-PBjbltAiPy21733nduNO7Cd5GoG3jHC44PuSN_kJ3wC',
      },
    ],
    'condition': 'checkout_android and dawn_standalone',
    'dep_type': 'cipd',
  },
  'third_party/cpu_features/src': {
    'url': Var('chromium_git') + '/external/github.com/google/cpu_features.git' + '@' + '81d13c49649f0714dd41fb56bb246398b6584085',
    'condition': 'checkout_android and dawn_standalone',
  },
  'third_party/ijar': {
    'url': Var('chromium_git') + '/chromium/src/third_party/ijar@94af60a05b33f9acb33477a8d969e48eb1c3029f',
    'condition': 'checkout_android and dawn_standalone',
  },
  'third_party/libunwind/src': {
    'url': Var('chromium_git') + '/external/github.com/llvm/llvm-project/libunwind.git@9e44ea2ff4f53a60c2a3d2b6f511d7bab9ab12f0',
    'condition': 'checkout_android and dawn_standalone',
  },
  'third_party/litert-lm/src': {
    'url': '{chromium_git}/external/github.com/google-ai-edge/LiteRT-LM.git@2f8284d5ea323278989facfaaed1c476b174760a',
    'condition': 'checkout_litert_lm',
  },
  'third_party/litert-lm/data': {
    'packages': [
      {
        # TODO(crbug.com/527944617): Replace experimental CIPD dependency.
        'package': 'experimental/chouinard_at_google.com/litert_lm_benchmark_data',
 'version': 'MfFYLUhIzajgKbb0NIc_KPoe5_r8qf9dwAi_Ndgy-nMC',
      }
    ],
    'dep_type': 'cipd',
    'condition': 'checkout_litert_lm',
  },
  'third_party/litert-lm/models/gemma4_2b': {
    'packages': [
      {
        # TODO(crbug.com/527944617): Replace experimental CIPD dependency.
        'package': 'experimental/ohjerry_at_google.com/gemma4_2b',
        'version': '8BbbFJuxlNAt7We_SL3apsoXv9KF3tOoQXGp0DNFQE8C',
      }
    ],
    'dep_type': 'cipd',
    'condition': 'checkout_litert_lm',
  },
}
