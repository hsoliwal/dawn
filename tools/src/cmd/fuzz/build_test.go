// Copyright 2026 The Dawn & Tint Authors
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
//  1. Redistributions of source code must retain the above copyright notice, this
//     list of conditions and the following disclaimer.
//
//  2. Redistributions in binary form must reproduce the above copyright notice,
//     this list of conditions and the following disclaimer in the documentation
//     and/or other materials provided with the distribution.
//
//  3. Neither the name of the copyright holder nor the names of its
//     contributors may be used to endorse or promote products derived from
//     this software without specific prior written permission.
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

package main

import (
	"context"
	"errors"
	"path/filepath"
	"testing"

	"dawn.googlesource.com/dawn/tools/src/execwrapper"
	"dawn.googlesource.com/dawn/tools/src/fileutils"
	"dawn.googlesource.com/dawn/tools/src/oswrapper"
	"github.com/stretchr/testify/require"
)

type nativeRecordingExec struct {
	calls  [][]string
	failAt int
	err    error
	output map[int]string
}

func (e *nativeRecordingExec) Command(name string, args ...string) execwrapper.CmdWrapper {
	e.calls = append(e.calls, append([]string{name}, args...))
	if len(e.calls) == e.failAt {
		return execwrapper.NewTestExecWrapperForFailure(e.err).Command(name, args...)
	}
	output := "main\n"
	if value, ok := e.output[len(e.calls)]; ok {
		output = value
	}
	return execwrapper.NewTestExecWrapperForSuccess([]byte(output), nil).Command(name, args...)
}

func (e *nativeRecordingExec) CommandContext(_ context.Context, name string, args ...string) execwrapper.CmdWrapper {
	return e.Command(name, args...)
}

func nativeBuildTask(t *testing.T) (*taskConfig, *nativeRecordingExec) {
	t.Helper()
	fs := oswrapper.CreateFSTestOSWrapper()
	require.NoError(t, fs.MkdirAll("/build native", 0755))
	require.NoError(t, fs.WriteFile("/build native/CMakeCache.txt", []byte(
		"CMAKE_HOME_DIRECTORY:INTERNAL=/source native\nCMAKE_CXX_COMPILER:FILEPATH=/toolchain/clang++\n"), 0644))
	exec := &nativeRecordingExec{}
	return &taskConfig{mainConfig: mainConfig{build: "/build native", osWrapper: fs, execWrapper: exec}}, exec
}

func TestNativeFuzzerTargetNames(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	require.NoError(t, cfg.buildTargets([]string{"tint_wgsl_fuzzer", "tint_ir_mesa_fuzzer"}))
	require.Equal(t, [][]string{{"cmake", "--build", "/build native", "--target",
		"tint_cmd_fuzz_wgsl_fuzz_cmd_sanitize_fuzzer",
		"tint_cmd_fuzz_ir_mesa_fuzz_cmd_sanitize_fuzzer"}}, exec.calls)
}

func TestNativeBuildAll(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	require.NoError(t, cfg.buildTargets(nil))
	require.Equal(t, [][]string{{"cmake", "--build", "/build native"}}, exec.calls)
}

func TestNativeSyncBeforeBuild(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	require.NoError(t, cfg.syncAndBuildTargets([]string{"tint_wgsl_fuzzer"}))
	require.Equal(t, []string{"cmake", "-S", "/source native", "-B", "/build native", "-DDAWN_FETCH_DEPENDENCIES=ON"}, exec.calls[0])
	require.Len(t, exec.calls, 2)
	require.Equal(t, []string{"cmake", "--build", "/build native", "--target", "tint_cmd_fuzz_wgsl_fuzz_cmd_sanitize_fuzzer"}, exec.calls[1])
}

func TestNativeSyncFailureStopsBuild(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	exec.failAt = 1
	exec.err = errors.New("native dependency fetch failed")
	err := cfg.syncAndBuildTargets([]string{"tint_wgsl_fuzzer"})
	require.ErrorIs(t, err, exec.err)
	require.Len(t, exec.calls, 1)
}

func TestNativeBuildFailurePropagates(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	exec.failAt = 1
	exec.err = errors.New("compile failed")
	require.ErrorIs(t, cfg.buildTargets(nil), exec.err)
}

func TestNativeSyncRequiresConfiguredSourceRoot(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	require.NoError(t, cfg.osWrapper.WriteFile("/build native/CMakeCache.txt", []byte("TINT_BUILD_FUZZERS:BOOL=ON\n"), 0644))
	require.ErrorContains(t, cfg.syncDependencies(), "CMAKE_HOME_DIRECTORY is missing")
	require.Empty(t, exec.calls)
}

func TestNativeCachePreservesPathValues(t *testing.T) {
	cfg, _ := nativeBuildTask(t)
	require.NoError(t, cfg.osWrapper.WriteFile("/build native/CMakeCache.txt", []byte(
		"# comment\n// comment\nCMAKE_CXX_COMPILER:FILEPATH=C:/LLVM tools/clang++.exe\nSOME_VALUE:STRING=a=b\n"), 0644))
	cache, err := cfg.readCMakeCache()
	require.NoError(t, err)
	require.Equal(t, "C:/LLVM tools/clang++.exe", cache["CMAKE_CXX_COMPILER"])
	require.Equal(t, "a=b", cache["SOME_VALUE"])
}

func TestAtGitHashRestoresNativeDependenciesAfterWorkFailure(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	workErr := errors.New("fuzzer build failed")
	err := cfg.atGitHash("candidate", func() error { return workErr })
	require.ErrorIs(t, err, workErr)
	require.Equal(t, [][]string{
		{"git", "rev-parse", "--abbrev-ref", "HEAD"},
		{"git", "checkout", "candidate"},
		{"git", "checkout", "main"},
		{"cmake", "-S", "/source native", "-B", "/build native", "-DDAWN_FETCH_DEPENDENCIES=ON"},
	}, exec.calls)
}

func TestAtGitHashReportsFailedRestore(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	exec.failAt = 3
	exec.err = errors.New("restore checkout failed")
	workErr := errors.New("fuzzer build failed")
	err := cfg.atGitHash("candidate", func() error { return workErr })
	require.ErrorIs(t, err, exec.err)
	require.ErrorIs(t, err, workErr)
	require.Len(t, exec.calls, 3)
}

func TestAtGitHashRestoresOriginalDetachedCommit(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	exec.output = map[int]string{1: "HEAD\n", 2: "original-commit\n"}
	require.NoError(t, cfg.atGitHash("candidate", func() error { return nil }))
	require.Equal(t, []string{"git", "rev-parse", "HEAD"}, exec.calls[1])
	require.Equal(t, []string{"git", "checkout", "original-commit"}, exec.calls[3])
	require.Len(t, exec.calls, 5)
}

func TestNativeSyncRejectsMultipleConfigurations(t *testing.T) {
	cfg, exec := nativeBuildTask(t)
	require.NoError(t, cfg.osWrapper.WriteFile("/build native/CMakeCache.txt", []byte(
		"CMAKE_HOME_DIRECTORY:INTERNAL=/source\nCMAKE_CONFIGURATION_TYPES:STRING=Debug;Release\n"), 0644))
	require.ErrorContains(t, cfg.syncDependencies(), "single-configuration")
	require.Empty(t, exec.calls)
}

func TestNativeRuntimeLibrariesWithoutManifest(t *testing.T) {
	fs := oswrapper.CreateFSTestOSWrapper()
	require.NoError(t, fs.MkdirAll("/build/lib", 0755))
	require.NoError(t, fs.MkdirAll("/saved", 0755))
	files := map[string]string{
		"tint_wgsl_fuzzer":      "binary",
		"lib/libdriver.so.1":    "native driver",
		"lib/lvp_icd.json":      `{"ICD":{"library_path":"libdriver.so.1"}}`,
		"compile_commands.json": "[]",
		"notes.txt":             "not a runtime library",
	}
	for path, data := range files {
		require.NoError(t, fs.WriteFile(filepath.Join("/build", path), []byte(data), 0755))
	}
	cfg := &taskConfig{mainConfig: mainConfig{build: "/build", osWrapper: fs}}
	require.NoError(t, copyFuzzerAndDependencies(cfg, "tint_wgsl_fuzzer", "/saved"))
	require.True(t, fileutils.IsFile("/saved/lib/libdriver.so.1", fs))
	icd, err := fs.ReadFile("/saved/lib/lvp_icd.json")
	require.NoError(t, err)
	require.Contains(t, string(icd), "/saved/lib/libdriver.so.1")
	require.False(t, fileutils.IsFile("/saved/compile_commands.json", fs))
	require.False(t, fileutils.IsFile("/saved/notes.txt", fs))
}

func TestNativeRuntimeCopyExcludesNestedDestination(t *testing.T) {
	fs := oswrapper.CreateFSTestOSWrapper()
	require.NoError(t, fs.MkdirAll("/build/experiment/bin", 0755))
	require.NoError(t, fs.WriteFile("/build/tint_wgsl_fuzzer", []byte("binary"), 0755))
	require.NoError(t, fs.WriteFile("/build/libdriver.so", []byte("native driver"), 0755))
	cfg := &taskConfig{mainConfig: mainConfig{build: "/build", osWrapper: fs}}
	for i := 0; i < 2; i++ {
		require.NoError(t, copyFuzzerAndDependencies(cfg, "tint_wgsl_fuzzer", "/build/experiment/bin"))
	}
	require.True(t, fileutils.IsFile("/build/experiment/bin/libdriver.so", fs))
	require.False(t, fileutils.IsFile("/build/experiment/bin/experiment/bin/libdriver.so", fs))
}

func TestNativeRuntimeCopyRejectsBuildRootDestination(t *testing.T) {
	fs := oswrapper.CreateFSTestOSWrapper()
	require.NoError(t, fs.MkdirAll("/build", 0755))
	require.NoError(t, fs.WriteFile("/build/tint_wgsl_fuzzer", []byte("binary"), 0755))
	cfg := &taskConfig{mainConfig: mainConfig{build: "/build", osWrapper: fs}}
	require.ErrorContains(t, copyFuzzerAndDependencies(cfg, "tint_wgsl_fuzzer", "/build"), "separate")
	binary, err := fs.ReadFile("/build/tint_wgsl_fuzzer")
	require.NoError(t, err)
	require.Equal(t, "binary", string(binary))
}

func TestNativeLLVMToolsOverride(t *testing.T) {
	fs := oswrapper.CreateFSTestOSWrapper()
	fs.Setenv("LLVM_BIN_DIR", "/native-llvm")
	require.NoError(t, fs.MkdirAll("/native-llvm", 0755))
	require.NoError(t, fs.MkdirAll("/saved", 0755))
	for _, tool := range []string{"llvm-profdata", "llvm-cov"} {
		require.NoError(t, fs.WriteFile(filepath.Join("/native-llvm", tool+fileutils.ExeExt), []byte(tool), 0755))
	}
	cfg := &taskConfig{mainConfig: mainConfig{osWrapper: fs}}
	require.NoError(t, copyLlvmTools(cfg, "/saved"))
	require.True(t, fileutils.IsFile("/saved/llvm-profdata"+fileutils.ExeExt, fs))
	require.True(t, fileutils.IsFile("/saved/llvm-cov"+fileutils.ExeExt, fs))
}
