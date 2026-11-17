// Copyright 2021 The Dawn & Tint Authors
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// 3. Neither the name of the copyright holder nor the names of its
//    contributors may be used to endorse or promote products derived from
//    this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
// FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
// DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
// CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
// OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#ifndef SRC_DAWN_UTILS_WIREHELPER_H_
#define SRC_DAWN_UTILS_WIREHELPER_H_

#include <webgpu/webgpu_cpp.h>

#include <memory>
#include <utility>

struct DawnProcTable;

namespace dawn::native {
class Instance;
}  // namespace dawn::native

namespace dawn::utils {

// Sets the proc table the tests call through and creates or adopts their instances. Tests call
// dawn::native directly: the wire client/server path was removed from this fork.
class WireHelper {
  public:
    explicit WireHelper(const DawnProcTable& procs);
    ~WireHelper();

    wgpu::Instance RegisterInstance(WGPUInstance backendInstance);

    // Create a native instance and the wgpu::Instance the test uses for it.
    std::pair<wgpu::Instance, std::unique_ptr<dawn::native::Instance>> CreateInstances(
        const wgpu::InstanceDescriptor* nativeDesc = nullptr);

    WGPUDevice GetBackendDevice(const wgpu::Device& device);

    // Process events until the native instance reports no more work.
    void WaitUntilIdle(dawn::native::Instance* serverInstance,
                       wgpu::Instance clientInstance = nullptr);
};

std::unique_ptr<WireHelper> CreateWireHelper(const DawnProcTable& procs);

}  // namespace dawn::utils

#endif  // SRC_DAWN_UTILS_WIREHELPER_H_
