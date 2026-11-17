# Copyright 2026 The Dawn & Tint Authors
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Regression tests for the standalone native build, without network access."""

import argparse
import configparser
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import fetch_dawn_dependencies as fetch


ROOT = Path(__file__).resolve().parents[1]
CMAKE = os.environ.get('DAWN_TEST_CMAKE') or shutil.which('cmake')


class NativeDependenciesTest(unittest.TestCase):

    def setUp(self):
        self.manifest = {}
        exec((ROOT / 'DEPS').read_text(), {'Var': fetch.Var}, self.manifest)

    def test_manifest_keeps_native_pins_without_browser_tooling(self):
        modules = configparser.ConfigParser()
        modules.read(ROOT / '.gitmodules')
        native_sources = {modules[s]['path'] for s in modules.sections()}
        optional_native = {
            'third_party/agility-sdk/src',
            'third_party/direct3d-warp/bin/',
            'third_party/llvm-dev',
            'third_party/zstd',
            'third_party/litert-lm/src',
            'third_party/litert-lm/data',
            'third_party/litert-lm/models/gemma4_2b',
        }
        self.assertEqual(set(self.manifest['deps']),
                         native_sources | optional_native)
        self.assertNotIn('hooks', self.manifest)
        self.assertNotIn('recursedeps', self.manifest)
        self.assertNotIn('gclient_gn_args', self.manifest)
        removed = ('build', 'buildtools', 'testing', 'tools/clang', 'tools/mb',
                   'third_party/catapult', 'third_party/depot_tools',
                   'third_party/partition_alloc', 'third_party/perfetto',
                   'third_party/placeholder_chromium', 'third_party/v8',
                   'third_party/node', 'third_party/emscripten',
                   'third_party/emdawnwebgpu')
        for path, dep in self.manifest['deps'].items():
            self.assertFalse(any(path == prefix or path.startswith(prefix + '/')
                                 for prefix in removed), path)
            if 'url' in dep:
                with self.subTest(path=path):
                    self.assertRegex(dep['url'].rsplit('@', 1)[1],
                                     r'^[0-9a-f]{40}$')

    def test_default_fetch_selects_only_native_dependencies(self):
        args = fetch.parser.parse_args(['--directory', str(ROOT)])
        with mock.patch.object(fetch, 'fetch_git_dependency') as git_fetch:
            with mock.patch.object(fetch, 'fetch_cipd_dependency') as cipd_fetch:
                fetch.main(args)
        selected = {
            call.args[3].relative_to(ROOT).as_posix()
            for call in git_fetch.call_args_list
        }
        self.assertTrue(selected <= self.manifest['deps'].keys())
        self.assertTrue({
            'third_party/abseil-cpp',
            'third_party/jinja2',
            'third_party/spirv-tools/src',
            'third_party/vulkan-headers/src',
            'third_party/webgpu-headers/src',
        } <= selected)
        cipd_fetch.assert_not_called()

    def test_optional_native_drivers_fetch_their_pinned_dependencies(self):
        args = fetch.parser.parse_args([
            '--directory', str(ROOT), '--fetch-swiftshader', '--fetch-mesa',
            '--fetch-agility-sdk'
        ])
        with mock.patch.object(fetch, 'fetch_git_dependency') as git_fetch:
            with mock.patch.object(fetch, 'fetch_cipd_dependency') as cipd_fetch:
                fetch.main(args)
        source_paths = {call.args[3].relative_to(ROOT).as_posix()
                        for call in git_fetch.call_args_list}
        sdk_paths = {call.args[2].relative_to(ROOT).as_posix()
                     for call in cipd_fetch.call_args_list}
        self.assertTrue({'third_party/swiftshader', 'third_party/mesa/src'} <= source_paths)
        self.assertEqual(sdk_paths, {'third_party/agility-sdk/src',
                                    'third_party/llvm-dev', 'third_party/zstd'})

    def test_full_clone_does_not_reintroduce_transitive_submodules(self):
        args = argparse.Namespace(git='git', shallow=False)
        dep = {'url': 'https://example.invalid/native.git@' + 'a' * 40}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'native'
            completed = subprocess.CompletedProcess([], 0, stdout=('a' * 40).encode())
            with mock.patch.object(fetch.subprocess, 'run', return_value=completed) as run:
                fetch.fetch_git_dependency(args, dep, {}, target)
        self.assertEqual(run.call_args_list[0].args[0], [
            'git', 'clone', 'https://example.invalid/native.git', target
        ])
        self.assertEqual(run.call_args_list[1].args[0],
                         ['git', '-C', target, 'checkout', '--detach', 'a' * 40])

    def test_native_fetch_failures_stop_before_success(self):
        args = argparse.Namespace(git='git', shallow=True)
        dep = {'url': 'https://example.invalid/native.git@' + 'a' * 40}
        for failing_command in ('init', 'fetch', 'checkout'):
            with self.subTest(command=failing_command):
                with tempfile.TemporaryDirectory() as directory:
                    target = Path(directory) / 'native'
                    commands = []

                    def run(command, **kwargs):
                        commands.append(command)
                        self.assertTrue(kwargs['check'])
                        if command[3] == failing_command:
                            raise subprocess.CalledProcessError(1, command)
                        return subprocess.CompletedProcess(command, 0,
                                                           stdout=('a' * 40).encode())

                    with mock.patch.object(fetch.subprocess, 'run', side_effect=run):
                        with self.assertRaises(subprocess.CalledProcessError):
                            fetch.fetch_git_dependency(args, dep, {}, target)
                    self.assertEqual(commands[-1][3], failing_command)

    def test_full_clone_failure_propagates(self):
        args = argparse.Namespace(git='git', shallow=False)
        dep = {'url': 'https://example.invalid/native.git@' + 'a' * 40}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'native'

            def clone(command, **kwargs):
                self.assertTrue(kwargs['check'])
                raise subprocess.CalledProcessError(1, command)

            with mock.patch.object(fetch.subprocess, 'run', side_effect=clone) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    fetch.fetch_git_dependency(args, dep, {}, target)
            run.assert_called_once()

    def test_existing_git_submodule_updates_to_pin_without_recloning(self):
        args = argparse.Namespace(git='git', shallow=True)
        dep = {'url': 'https://example.invalid/native.git@' + 'a' * 40}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / '.git').write_text('gitdir: ../modules/native')
            before = subprocess.CompletedProcess([], 0, stdout=('b' * 40).encode())
            after = subprocess.CompletedProcess([], 0, stdout=('a' * 40).encode())
            with mock.patch.object(fetch.subprocess, 'run',
                                   side_effect=[before, after, after, after, after]) as run:
                fetch.fetch_git_dependency(args, dep, {}, target)
            self.assertFalse(any('clone' in call.args[0] for call in run.call_args_list))
            self.assertIn('checkout', run.call_args_list[2].args[0])

    @unittest.skipUnless(shutil.which('git'), 'Git is required for retry regression')
    def test_interrupted_shallow_fetch_can_retry_without_head(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            target = root / 'dependency'
            source.mkdir()
            subprocess.run(['git', '-C', source, 'init'], check=True, capture_output=True)
            subprocess.run(['git', '-C', source, '-c', 'user.name=Native build test',
                            '-c', 'user.email=native-build-test@example.invalid',
                            'commit', '--allow-empty', '-m', 'Native dependency fixture'],
                           check=True, capture_output=True)
            pin = subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'],
                                          text=True).strip()
            dep = {'url': str(source) + '@' + pin}
            args = argparse.Namespace(git='git', shallow=True)
            real_run = subprocess.run

            def interrupted_fetch(command, **kwargs):
                if command[3] == 'fetch':
                    raise subprocess.CalledProcessError(1, command)
                return real_run(command, **kwargs)

            with mock.patch.object(fetch.subprocess, 'run', side_effect=interrupted_fetch):
                with self.assertRaises(subprocess.CalledProcessError):
                    fetch.fetch_git_dependency(args, dep, {}, target)
            self.assertTrue((target / '.git').exists())
            fetch.fetch_git_dependency(args, dep, {}, target)
            actual = subprocess.check_output(['git', '-C', target, 'rev-parse', 'HEAD'],
                                             text=True).strip()
            self.assertEqual(actual, pin)

    def test_unrequested_dependency_manifests_are_not_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / 'third_party/native'
            nested.mkdir(parents=True)
            (root / 'DEPS').write_text(
                "deps = {'third_party/native': {'url': 'native@pin'}}")
            (nested / 'DEPS').write_text(
                "raise RuntimeError('unrequested transitive manifest')")
            with mock.patch.object(fetch, 'fetch_git_dependency') as git_fetch:
                fetch.process_dir(None, root, ['third_party/native'])
            git_fetch.assert_called_once()


@unittest.skipUnless(CMAKE, 'CMake is required for configuration tests')
class NativeConfigurationTest(unittest.TestCase):

    def configure(self, *settings):
        return subprocess.run([
            CMAKE, *settings, '-P',
            str(ROOT / 'src/cmake/DawnNativeOnly.cmake')
        ], capture_output=True, text=True, check=False)

    def test_browser_configurations_fail_explicitly(self):
        for setting in ('-DEMSCRIPTEN=ON',
                        '-DCMAKE_SYSTEM_NAME=Emscripten',
                        '-DDAWN_BUILD_NODE_BINDINGS=ON'):
            with self.subTest(setting=setting):
                result = self.configure(setting)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('removed from this fork', result.stderr)

    def test_native_backends_and_legacy_disabled_options_remain_valid(self):
        for system in ('Linux', 'Windows', 'Darwin', 'Android', 'iOS'):
            with self.subTest(system=system):
                result = self.configure('-DCMAKE_SYSTEM_NAME=' + system,
                                        '-DEMSCRIPTEN=OFF',
                                        '-DDAWN_BUILD_NODE_BINDINGS=OFF',
                                        '-DDAWN_ENABLE_WEBGPU_ON_WEBGPU=ON')
                self.assertEqual(result.returncode, 0, result.stderr)


@unittest.skipUnless(shutil.which('bash'), 'Bash is required for setup-build')
class NativeSetupBuildTest(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'tools').mkdir()
        (self.root / 'bin').mkdir()
        shutil.copy2(ROOT / 'tools/setup-build', self.root / 'tools/setup-build')
        self.arguments = self.root / 'cmake-arguments.json'
        cmake = self.root / 'bin/cmake'
        cmake.write_text(
            '#!' + os.sys.executable + '\n'
            'import json, os, sys\n'
            'from pathlib import Path\n'
            'Path(os.environ["DAWN_TEST_CMAKE_ARGUMENTS"]).write_text('
            'json.dumps(sys.argv[1:]))\n')
        cmake.chmod(0o755)
        self.env = dict(os.environ,
                        PATH=str(self.root / 'bin') + os.pathsep + os.environ['PATH'],
                        DAWN_TEST_CMAKE_ARGUMENTS=str(self.arguments))

    def test_setup_build_produces_only_native_configuration(self):
        result = subprocess.run([
            'bash', str(self.root / 'tools/setup-build'),
            'cmake', 'debug', 'local'
        ], env=self.env, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = json.loads(self.arguments.read_text())
        self.assertIn('-DCMAKE_BUILD_TYPE=Debug', arguments)
        self.assertFalse(any('NODE_BINDINGS' in arg for arg in arguments))

    def test_removed_remote_toolchain_fails_before_configuring(self):
        result = subprocess.run([
            'bash', str(self.root / 'tools/setup-build'),
            'cmake', 'debug', 'remoteexec'
        ], env=self.env, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('removed Chromium build tooling', result.stdout)
        self.assertFalse(self.arguments.exists())


if __name__ == '__main__':
    unittest.main()
