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

#include "src/dawn/utils/WireHelper.h"

#include "dawn/dawn_proc.h"
#include "dawn/native/DawnNative.h"
#include "src/utils/assert.h"

namespace dawn::utils {

WireHelper::WireHelper(const DawnProcTable& procs) {
    dawnProcSetProcs(&procs);
}

WireHelper::~WireHelper() {
    dawnProcSetProcs(nullptr);
}

wgpu::Instance WireHelper::RegisterInstance(WGPUInstance backendInstance) {
    DAWN_ASSERT(backendInstance != nullptr);
    return wgpu::Instance(backendInstance);
}

std::pair<wgpu::Instance, std::unique_ptr<dawn::native::Instance>> WireHelper::CreateInstances(
    const wgpu::InstanceDescriptor* nativeDesc) {
    auto nativeInstance = std::make_unique<dawn::native::Instance>(
        reinterpret_cast<const WGPUInstanceDescriptor*>(nativeDesc));
    return {RegisterInstance(nativeInstance->Get()), std::move(nativeInstance)};
}

WGPUDevice WireHelper::GetBackendDevice(const wgpu::Device& device) {
    return device.Get();
}

void WireHelper::WaitUntilIdle(dawn::native::Instance* serverInstance,
                               wgpu::Instance clientInstance) {
    while (dawn::native::InstanceProcessEvents(serverInstance->Get())) {
        if (clientInstance != nullptr) {
            clientInstance.ProcessEvents();
        }
    }
    if (clientInstance != nullptr) {
        clientInstance.ProcessEvents();
    }
}

std::unique_ptr<WireHelper> CreateWireHelper(const DawnProcTable& procs) {
    return std::make_unique<WireHelper>(procs);
}

}  // namespace dawn::utils
