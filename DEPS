# Native dependency pins for tools/fetch_dawn_dependencies.py and CMake.
# Only explicitly requested dependencies are fetched. Optional native SDKs,
# software drivers, Mesa fuzzing dependencies and LiteRT benchmark data remain
# pinned here; this manifest contains no Chromium checkout or toolchain hooks.
# Chromium-hosted mirrors below contain individual native libraries, not a
# Chromium browser checkout.

vars = {
  'chromium_git': 'https://chromium.googlesource.com',
  'swiftshader_git': 'https://swiftshader.googlesource.com',
  'dawn_agility_sdk_version': 'version:2@1.722.0-preview',
  'dawn_direct3d_warp_version': 'version:3@1.0.21.chromium.1',
  'dawn_llvm-dev_version': 'version:3@22.1.0',
  'dawn_zstd_version': 'Lf-seQJdussz81cZXnez5xIxEdkejDRxKumQpHbHMOUC',
}

deps = {
  'third_party/googletest/src': {
    'url': '{chromium_git}/external/github.com/google/googletest@e882c36410197464e3429546e6a7d5e217bde51e',
  },

  'third_party/google_benchmark/src': {
    'url': '{chromium_git}/external/github.com/google/benchmark.git' + '@' + 'a6b4a9f00b36c19af9997d68a1cf6e0b5b3d032c',
  },

  'third_party/mesa/src': {
    'url': '{chromium_git}/external/gitlab.freedesktop.org/mesa/mesa/@e9fe5b472b74e652b0cff4b304b88e4c799d7902',
  },

  'third_party/llvm-dev': {
    'packages': [{
      'package': 'infra/3pp/tools/llvm-dev/linux-amd64',
      'version': Var('dawn_llvm-dev_version'),
    }],
    'dep_type': 'cipd',
  },

  'third_party/zstd': {
    'packages': [{
      'package': 'infra/3pp/static_libs/libzstd/linux-amd64',
      'version': Var('dawn_zstd_version'),
    }],
    'dep_type': 'cipd',
  },

  'third_party/jinja2': {
    'url': '{chromium_git}/chromium/src/third_party/jinja2@fde3c16799bd5937e4f15aedc9037c89f96236b9',
  },

  'third_party/markupsafe': {
    'url': '{chromium_git}/chromium/src/third_party/markupsafe@4256084ae14175d38a3ff7d739dca83ae49ccec6',
  },

  'third_party/glfw3/src': {
    'url': '{chromium_git}/external/github.com/glfw/glfw@92dcf4ce74f2e2554a98fea09be7c705c17daa5a',
  },

  'third_party/swiftshader': {
    'url': '{swiftshader_git}/SwiftShader@708e9e77773860bbb2ad9bb2d61b451de4b84e31',
  },

  'third_party/glslang/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/glslang@385445a87d21d7a5c7bee2f7bef8a87850f6bf28',
  },

  'third_party/spirv-headers/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/SPIRV-Headers@5c6004e758e0c80185ef2cee93ae5c10fa342a5b',
  },

  'third_party/spirv-tools/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/SPIRV-Tools@3e73ae769e684f17b283250f803a231a830d45e3',
  },

  'third_party/vulkan-headers/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/Vulkan-Headers@b26454f3ccd67e704117a39295fa13935fd3804c',
  },

  'third_party/vulkan-loader/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/Vulkan-Loader@0b137080f608a1f99527f1b123424545f2d9ba49',
  },

  'third_party/vulkan-utility-libraries/src': {
    'url': '{chromium_git}/external/github.com/KhronosGroup/Vulkan-Utility-Libraries@5a873d3b75d38ef6a0833589ce3603d63f3f6a9c',
  },

  'third_party/abseil-cpp': {
    'url': '{chromium_git}/chromium/src/third_party/abseil-cpp@ecb00cc74a6251b273c78789f947d3eb280dd093',
  },

  'third_party/directx-shader-compiler/src': {
    'url': '{chromium_git}/external/github.com/microsoft/DirectXShaderCompiler@5ed39344cdccd97c02e37001669e80e7f9444e5f',
  },

  'third_party/directx-headers/src': {
    'url': '{chromium_git}/external/github.com/microsoft/DirectX-Headers@980971e835876dc0cde415e8f9bc646e64667bf7',
  },

  'third_party/agility-sdk/src': {
    'packages': [
      {
        'package': 'chromium/third_party/agility-sdk',
        'version': Var('dawn_agility_sdk_version'),
      },
    ],
    'dep_type': 'cipd',
  },

  'third_party/direct3d-warp/bin/': {
    'packages': [
      {
        'package': 'infra/3pp/direct3d-warp',
        'version': Var('dawn_direct3d_warp_version'),
      },
    ],
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

  'third_party/protobuf': {
    'url': '{chromium_git}/chromium/src/third_party/protobuf@3813fd5b3029807583e5d2549a40d78fa499c3e8',
  },

  'third_party/libprotobuf-mutator/src': {
    'url': '{chromium_git}/external/github.com/google/libprotobuf-mutator.git@a0448e5055e4740774e00d496f016d9fcd572200',
  },

  'third_party/litert-lm/src': {
    'url': '{chromium_git}/external/github.com/google-ai-edge/LiteRT-LM.git@2f8284d5ea323278989facfaaed1c476b174760a',
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
  },

}
