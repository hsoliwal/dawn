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
	"fmt"
	"path/filepath"
	"strings"

	"dawn.googlesource.com/dawn/tools/src/fileutils"
)

// readCMakeCache reads the configured build without invoking a browser toolchain.
func (t *taskConfig) readCMakeCache() (map[string]string, error) {
	path := filepath.Join(t.build, "CMakeCache.txt")
	data, err := t.osWrapper.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read native CMake cache %s: %w", path, err)
	}
	values := make(map[string]string)
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, "//") {
			continue
		}
		keyType, value, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		key, _, ok := strings.Cut(keyType, ":")
		if ok {
			values[key] = value
		}
	}
	return values, nil
}

// buildTargets builds CMake targets. If targets is empty everything will be built.
func (t *taskConfig) buildTargets(targets []string) error {
	fmt.Printf("Building %v...\n", targets)
	args := []string{"--build", t.build}
	if len(targets) > 0 {
		args = append(args, "--target")
		for _, target := range targets {
			// CMake's logical target differs from the output binary's name.
			if config, ok := fuzzerConfigs[strings.TrimSuffix(target, fileutils.ExeExt)]; ok {
				target = config.cmakeTarget
			}
			args = append(args, target)
		}
	}
	if _, err := t.runCmd("cmake", args...); err != nil {
		return fmt.Errorf("build failed for %v: %w", targets, err)
	}

	return nil
}

// syncDependencies preserves the build's CMake options and fetches native pins
// for the checked-out revision before regenerating the build graph.
func (t *taskConfig) syncDependencies() error {
	cache, err := t.readCMakeCache()
	if err != nil {
		return err
	}
	if cache["CMAKE_CONFIGURATION_TYPES"] != "" {
		return fmt.Errorf("native fuzzing requires a single-configuration CMake build; configure with Ninja or Unix Makefiles")
	}
	root := cache["CMAKE_HOME_DIRECTORY"]
	if root == "" {
		return fmt.Errorf("CMAKE_HOME_DIRECTORY is missing from %s/CMakeCache.txt", t.build)
	}
	if _, err := t.runCmd("cmake", "-S", root, "-B", t.build,
		"-DDAWN_FETCH_DEPENDENCIES=ON"); err != nil {
		return fmt.Errorf("native dependency synchronization failed: %w", err)
	}
	return nil
}

// syncAndBuildTargets synchronizes native dependencies and builds CMake targets.
func (t *taskConfig) syncAndBuildTargets(targets []string) error {
	if err := t.syncDependencies(); err != nil {
		return err
	}
	return t.buildTargets(targets)
}
