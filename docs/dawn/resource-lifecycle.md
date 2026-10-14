# Resource lifecycle: host API, wire, backend and shader boundaries

Source baseline: `1ab42ee97300054135e1ec57ac81eedf21da6358`. This focused source review covers selected buffer/queue/compute and shader-reader/writer paths. It does not establish correctness, conformance, portability or complete thread safety. [Component guide](../repository-components.md) · [Inventory and remaining work](../component-inventory.md)

## 1. Encode on the host, submit to a backend

`ComputePassEncoder::APIDispatchWorkgroups(x, y, z)` records a command through `EncodingContext::TryEncode`. With validation enabled it checks dispatch state, workgroup counts against device limits and additional indexing/resource constraints, then records synchronization scope. The counts are workgroups, not host threads. This method is a host-side encoder entry point; it does not directly run each shader invocation on the calling CPU thread.

`QueueBase::SubmitInternal` checks device liveness, validates submitted command buffers when validation is enabled, delegates to `SubmitImpl`, releases temporary buffer-use bookkeeping and ticks the device to flush pending work. Submission is a different boundary from completion. `APIOnSubmittedWorkDone` tracks a work-done event/future against the scheduled serial; callback mode affects when it is delivered, and spontaneous callbacks can occur during event tracking.

Evidence: [compute dispatch encoder](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/ComputePassEncoder.cpp), [SubmitInternal and APIOnSubmittedWorkDone](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/Queue.cpp).

The Vulkan example makes the split concrete: `Queue::SubmitImpl` records backend command buffers into a recording context and submits pending commands. Completion tracking polls fence status in serial order. These are Vulkan implementation details, not a promise that Metal, D3D or OpenGL uses the same objects or synchronization primitives.

Evidence: [Vulkan queue implementation](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/vulkan/QueueVk.cpp).

## 2. Buffer mapping is a state transition

The native buffer implementation distinguishes unmapped, pending-map, mapped, mapped-at-creation, destroyed, shared-memory-no-access and transient in-use states. Queue-use validation rejects mapped, pending, destroyed and unavailable shared-memory buffers. An unmapped buffer enters temporary in-use bookkeeping for submission/write validation; returning that bookkeeping state to unmapped does not mean GPU work has finished.

`APIMapAsync` validates device/object and map parameters, starts backend mapping and tracks a completion event using the buffer's last-usage serial. Successful initiation is not successful completion. Invalid requests and early cancellation report status through the tracked event, and unmap/destroy can abort a pending map. Check the callback status before accessing mapped bytes.

Evidence: [BufferBase state and interfaces](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/Buffer.h), [ValidateCanUseOnQueueNow, APIMapAsync and MapAsyncEvent](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/Buffer.cpp).

### Reviewed input/output constraints

- Map offset must be a multiple of 8; map size must be a multiple of 4, and the range must fit the buffer
- The map mode must be exactly read or write with matching usage; the reviewed path rejects mapping an already host-mapped buffer again
- `GetMappedRange` is writable access and rejects a read-only mapping; use const mapped access for read-only data
- The requested mapped subrange must lie inside the established mapping and satisfy the checked alignment/range constraints
- Invalid mapped-range access returns no range/pointer in these implementation paths; do not dereference an unchecked result
- `Unmap` clears the mapped range and changes availability. A pointer obtained from a mapping must not be used after its mapping ends

Evidence: [ValidateMapAsync, CanGetMappedRange, GetMappedRangeInternal and Unmap](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/Buffer.cpp).

`mappedAtCreation` can use a staging buffer. Unmapping that case can copy staged content to the destination; destroying it skips an unnecessary upload. Therefore mapped host bytes are not universally a direct pointer to device-local memory. `QueueBase::APIWriteBuffer` validates device, object, usage/range and current availability, then uploads and lets the dynamic uploader submit pending work. It is another data-upload path, not a mapping lease.

Evidence: [CopyFromStagingBuffer and UploadData](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/Buffer.cpp), [APIWriteBuffer and WriteBuffer](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/Queue.cpp).

## 3. Destroyed API state and native memory retirement differ

`APIDestroy` obtains the destruction guard and destroys the object. In the Vulkan backend, `Buffer::DestroyImpl` releases allocator state and sends native buffer/device-memory handles to `DeleteWhenUnused`. That deferred retirement protects work already using native resources; it must not be interpreted as permission to continue using a destroyed WebGPU object.

The current Vulkan source also documents a synchronization limitation around explicit destruction concurrent with other uses. This guide does not elevate reference counting, atomics or a guard into a blanket thread-safety promise. Review the selected backend and application synchronization before sharing a buffer across threads or racing destruction with submission.

Evidence: [APIDestroy](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/Buffer.cpp), [DestroyImpl and deferred deletion](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/native/vulkan/BufferVk.cpp).

## 4. Wire mapping is a separate ownership/protocol boundary

The wire client maintains local mapping state and receives asynchronous result messages. The server forwards `DoBufferMapAsync` to the selected API implementation with instance/future/object identity and map range. It requires an explicit size rather than the whole-map sentinel. On callback it checks object generation before replying, so a stale response for a destroyed/replaced buffer is not treated as a response for the new object.

Mappable buffers use `MemoryTransferService` handles. Depending on backing, mapped bytes may be shared with the client or transferred through serialized update data. A client mapping is therefore not a universal raw server address or GPU pointer. Successful wire deserialization does not replace native WebGPU validation.

Evidence: [client map event and mapped access](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/wire/client/Buffer.cpp), [server mapping, handle deserialization and callback generation checks](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/wire/server/ServerBuffer.cpp).

The transport embedding determines process boundaries and trust. This review does not prove a particular deployment is sandboxed or secure just because it links `dawn_wire`. The [existing overview](overview.md) explains client/server responsibilities and proc-table selection.

## 5. Tint compiles shader representations on the host

The current `tint::wgsl::reader` interface exposes:

- `Parse(const Source::File*, const Options&) -> Program`: parse source then resolve with the allowed features; inspect diagnostics for invalid input
- `WgslToIR(...) -> Result<core::ir::Module>`: parse, convert/lower to core IR and validate successful IR results
- `ProgramToLoweredIR(const Program&, const IROptions&)`: convert a program, carry diagnostic/validation settings and lower WGSL dialect into core dialect; the header states the valid/resolved program precondition

The reviewed parser rejects a source larger than the uint32-sized source limit. Conversion/validation failures propagate as `Result` failures. A valid parser result is not evidence that a requested backend supports every extension or can generate the requested entry point.

Evidence: [reader contract](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/tint/lang/wgsl/reader/reader.h), [reader implementation](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/tint/lang/wgsl/reader/reader.cc).

`tint::spirv::writer::Generate(core::ir::Module&, const Options&) -> Result<Output>` accepts mutable IR. It checks options and entry-point constraints, gathers subgroup-matrix information, runs the SPIR-V dialect raising pass, prints output and attaches supplementary metadata. Treat the IR as transformation input, not an immutable value reusable without regard to mutation. The generated output still needs a graphics backend and device execution path.

Examples of checked failure cases in this revision include unsupported SPIR-V versions, missing entry points, subgroup matrices without the Vulkan memory-model option, unsupported pixel-local address space and `print` builtins. These are source observations for this writer, not a complete language-support matrix for every target.

Evidence: [writer signature](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/tint/lang/spirv/writer/writer.h), [CanGenerate and Generate](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/tint/lang/spirv/writer/writer.cc).

The generated `BUILD.cmake` manifests distinguish reader/writer, common/type/IR, tests and fuzz targets. An IR `Module`, a source namespace and a build target are different identities. [Tint architecture](../tint/arch.md) and [IR guide](../tint/ir.md) provide broader background; current source signatures take precedence if an older overview shows different file layout.

## 6. Example and test navigation

The existing [ComputeBoids sample](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/samples/ComputeBoids.cpp) demonstrates a complete application context: host-side buffers and bind groups, a compute pipeline, workgroup dispatch and queue submission, followed by rendering. Start from the checked-in sample rather than copying a context-free dispatch fragment; adapter/device setup, resource usages and pipeline layout are necessary parts of the contract.

Test entrypoints below were located in the pinned tree; no test result is claimed:

| Boundary | Source to inspect | What still needs execution |
| --- | --- | --- |
| Native buffer validation | [src/dawn/tests/unittests/validation/BufferValidationTests.cpp](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/tests/unittests/validation/BufferValidationTests.cpp) | Frontend/unit validation tests |
| Queue uploads | [src/dawn/tests/unittests/validation/QueueWriteBufferValidationTests.cpp](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/tests/unittests/validation/QueueWriteBufferValidationTests.cpp) | Write range/usage/state cases |
| Wire mapping | [src/dawn/tests/unittests/wire/WireBufferMappingTests.cpp](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/tests/unittests/wire/WireBufferMappingTests.cpp) | Client/server callback and map state cases |
| Buffer device behavior | [src/dawn/tests/end2end/BufferTests.cpp](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/tests/end2end/BufferTests.cpp) | Selected real backend/device execution |
| Compute dispatch | [src/dawn/tests/end2end/ComputeDispatchTests.cpp](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/dawn/tests/end2end/ComputeDispatchTests.cpp) | Device workgroup dispatch cases |
| Tint writer cases | [src/tint/lang/spirv/writer/binary_test.cc](https://github.com/hsoliwal/dawn/blob/1ab42ee97300054135e1ec57ac81eedf21da6358/src/tint/lang/spirv/writer/binary_test.cc) | Compiler output checks; separate from device correctness |

Follow [Dawn testing](testing.md), [Tint testing](../tint/testing.md), and the [CTS runner](../standalone_cts_runner.md) for the distinct validation levels. No build, test, presubmit, CTS, shader runtime or benchmark was executed in this documentation pass.

## Open review boundaries

This guide covers selected entry points in native/wire/Vulkan and WGSL/SPIR-V. Texture/shared-memory ownership, every backend, all callback modes, cancellation races, every Tint transform/writer, generated API leaves, Node/Emscripten/Android bindings and tool packages still need dedicated review. Existing source comments and inline API documentation are unchanged. The [ledger](../component-inventory.md) deliberately reports zero reviewed-complete modules/packages.
