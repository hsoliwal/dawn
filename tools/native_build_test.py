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
import io
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
        self.args = fetch.parser.parse_args(['--directory', str(ROOT)])
        self.urls = fetch.submodule_urls(self.args, ROOT)

    def test_gitlinks_keep_native_pins_without_browser_tooling(self):
        modules = configparser.ConfigParser()
        modules.read(ROOT / '.gitmodules')
        native_sources = {modules[s]['path'] for s in modules.sections()}
        self.assertFalse((ROOT / 'DEPS').exists())
        self.assertEqual(set(self.urls), native_sources)
        self.assertEqual(set(fetch.REQUIRED_SUBMODULES) |
                         {'third_party/swiftshader', 'third_party/mesa/src'},
                         native_sources)
        self.assertFalse(any('gclient-condition' in modules[s]
                             for s in modules.sections()))
        removed = ('build', 'buildtools', 'testing', 'tools/clang', 'tools/mb',
                   'third_party/catapult', 'third_party/depot_tools',
                   'third_party/partition_alloc', 'third_party/perfetto',
                   'third_party/placeholder_chromium', 'third_party/v8',
                   'third_party/node', 'third_party/emscripten',
                   'third_party/emdawnwebgpu')
        for path in self.urls:
            self.assertFalse(any(path == prefix or path.startswith(prefix + '/')
                                 for prefix in removed), path)
            with self.subTest(path=path):
                self.assertRegex(fetch.pinned_commit(self.args, ROOT, path),
                                 r'^[0-9a-f]{40}$')

    def test_default_fetch_selects_only_native_dependencies(self):
        args = fetch.parser.parse_args(['--directory', str(ROOT)])
        with mock.patch.object(fetch, 'fetch_git_dependency') as git_fetch:
            with mock.patch.object(fetch, 'fetch_package') as package_fetch:
                fetch.main(args)
        selected = {
            call.args[3].relative_to(ROOT).as_posix()
            for call in git_fetch.call_args_list
        }
        self.assertEqual(selected, set(fetch.REQUIRED_SUBMODULES))
        self.assertTrue({
            'third_party/abseil-cpp',
            'third_party/jinja2',
            'third_party/spirv-tools/src',
            'third_party/vulkan-headers/src',
            'third_party/webgpu-headers/src',
        } <= selected)
        package_fetch.assert_not_called()

    def test_optional_native_drivers_fetch_their_pinned_dependencies(self):
        args = fetch.parser.parse_args([
            '--directory', str(ROOT), '--fetch-swiftshader', '--fetch-mesa',
            '--fetch-agility-sdk'
        ])
        with mock.patch.object(fetch, 'fetch_git_dependency') as git_fetch:
            with mock.patch.object(fetch, 'fetch_package') as package_fetch:
                fetch.main(args)
        source_paths = {call.args[3].relative_to(ROOT).as_posix()
                        for call in git_fetch.call_args_list}
        sdk_paths = {call.args[2].relative_to(ROOT).as_posix()
                     for call in package_fetch.call_args_list}
        self.assertTrue({'third_party/swiftshader', 'third_party/mesa/src'} <= source_paths)
        self.assertEqual(sdk_paths, {'third_party/agility-sdk/src',
                                    'third_party/llvm-dev', 'third_party/zstd'})

    def test_list_reports_selected_source_and_package_pins_without_fetching(self):
        args = fetch.parser.parse_args([
            '--directory', str(ROOT), '--list', '--fetch-swiftshader',
            '--fetch-mesa', '--fetch-agility-sdk'
        ])
        with mock.patch.object(fetch, 'fetch_git_dependency') as git_fetch:
            with mock.patch.object(fetch, 'fetch_package') as package_fetch:
                with mock.patch('sys.stdout', new_callable=io.StringIO) as output:
                    fetch.main(args)
        git_fetch.assert_not_called()
        package_fetch.assert_not_called()
        rows = [line.split('\t') for line in output.getvalue().splitlines()]
        pins = {path: (url, pin) for path, url, pin in rows}
        self.assertEqual(len(rows), len(pins))
        self.assertEqual(set(pins), set(self.urls) | {
            'third_party/agility-sdk/src', 'third_party/llvm-dev', 'third_party/zstd'
        })
        for path, url in self.urls.items():
            self.assertEqual(pins[path], (url, fetch.pinned_commit(args, ROOT, path)))
        self.assertEqual(pins['third_party/llvm-dev'],
                         ('infra/3pp/tools/llvm-dev/linux-amd64', 'version:3@22.1.0'))
        self.assertEqual(pins['third_party/zstd'],
                         ('infra/3pp/static_libs/libzstd/linux-amd64',
                          'Lf-seQJdussz81cZXnez5xIxEdkejDRxKumQpHbHMOUC'))

    def test_regular_file_cannot_supply_a_dependency_pin(self):
        with self.assertRaisesRegex(SystemExit, 'no pinned commit'):
            fetch.pinned_commit(self.args, ROOT, 'go.mod')

    def test_full_clone_does_not_reintroduce_transitive_submodules(self):
        args = argparse.Namespace(git='git', shallow=False)
        url, pin = 'https://example.invalid/native.git', 'a' * 40
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'native'
            completed = subprocess.CompletedProcess([], 0, stdout=('a' * 40).encode())
            with mock.patch.object(fetch.subprocess, 'run', return_value=completed) as run:
                fetch.fetch_git_dependency(args, url, pin, target)
        self.assertEqual(run.call_args_list[0].args[0], [
            'git', 'clone', 'https://example.invalid/native.git', target
        ])
        self.assertEqual(run.call_args_list[1].args[0],
                         ['git', '-C', target, 'checkout', '--detach', 'a' * 40])

    def test_native_fetch_failures_stop_before_success(self):
        args = argparse.Namespace(git='git', shallow=True)
        url, pin = 'https://example.invalid/native.git', 'a' * 40
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
                            fetch.fetch_git_dependency(args, url, pin, target)
                    self.assertEqual(commands[-1][3], failing_command)

    def test_full_clone_failure_propagates(self):
        args = argparse.Namespace(git='git', shallow=False)
        url, pin = 'https://example.invalid/native.git', 'a' * 40
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'native'

            def clone(command, **kwargs):
                self.assertTrue(kwargs['check'])
                raise subprocess.CalledProcessError(1, command)

            with mock.patch.object(fetch.subprocess, 'run', side_effect=clone) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    fetch.fetch_git_dependency(args, url, pin, target)
            run.assert_called_once()

    def test_existing_git_submodule_updates_to_pin_without_recloning(self):
        args = argparse.Namespace(git='git', shallow=True)
        url, pin = 'https://example.invalid/native.git', 'a' * 40
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / '.git').write_text('gitdir: ../modules/native')
            before = subprocess.CompletedProcess([], 0, stdout=('b' * 40).encode())
            after = subprocess.CompletedProcess([], 0, stdout=('a' * 40).encode())
            with mock.patch.object(fetch.subprocess, 'run',
                                   side_effect=[before, after, after, after, after]) as run:
                fetch.fetch_git_dependency(args, url, pin, target)
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
            url = str(source)
            args = argparse.Namespace(git='git', shallow=True)
            real_run = subprocess.run

            def interrupted_fetch(command, **kwargs):
                if command[3] == 'fetch':
                    raise subprocess.CalledProcessError(1, command)
                return real_run(command, **kwargs)

            with mock.patch.object(fetch.subprocess, 'run', side_effect=interrupted_fetch):
                with self.assertRaises(subprocess.CalledProcessError):
                    fetch.fetch_git_dependency(args, url, pin, target)
            self.assertTrue((target / '.git').exists())
            fetch.fetch_git_dependency(args, url, pin, target)
            actual = subprocess.check_output(['git', '-C', target, 'rev-parse', 'HEAD'],
                                             text=True).strip()
            self.assertEqual(actual, pin)

    def test_unrequested_dependency_manifests_are_not_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / 'third_party/native'
            nested.mkdir(parents=True)
            (root / 'DEPS').write_text(
                "raise RuntimeError('retired root manifest')")
            (nested / 'DEPS').write_text(
                "raise RuntimeError('unrequested transitive manifest')")
            (root / '.gitmodules').write_text(
                '[submodule "third_party/native"]\n'
                '\tpath = third_party/native\n'
                '\turl = https://example.invalid/native.git\n')
            subprocess.run(['git', '-C', root, 'init'], check=True, capture_output=True)
            pin = 'a' * 40
            subprocess.run(['git', '-C', root, 'update-index', '--add', '--cacheinfo',
                            '160000,' + pin + ',third_party/native'],
                           check=True, capture_output=True)
            subprocess.run(['git', '-C', root, '-c', 'user.name=Native build test',
                            '-c', 'user.email=native-build-test@example.invalid',
                            'commit', '-m', 'Native gitlink fixture'],
                           check=True, capture_output=True)
            args = fetch.parser.parse_args(['--directory', str(root)])
            with mock.patch.object(fetch, 'REQUIRED_SUBMODULES', ['third_party/native']):
                with mock.patch.object(fetch, 'fetch_git_dependency') as git_fetch:
                    fetch.main(args)
            git_fetch.assert_called_once()
            self.assertEqual(git_fetch.call_args.args,
                             (args, 'https://example.invalid/native.git', pin, nested))


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


@unittest.skipUnless(shutil.which('bash') and shutil.which('find') and shutil.which('dirname'),
                     'Bash and file discovery tools are required for native tooling')
class NativeToolsTest(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'tools/src/cmd/gen').mkdir(parents=True)
        (self.root / 'tools/src/cmd/run-parallel').mkdir()
        (self.root / 'bin').mkdir()
        for tool in ('format', 'run', 'run.py'):
            shutil.copy2(ROOT / 'tools' / tool, self.root / 'tools' / tool)
        for command in ('bash', 'find', 'dirname'):
            (self.root / 'bin' / command).symlink_to(shutil.which(command))
        (self.root / 'bin/python3').symlink_to(os.sys.executable)
        self.arguments = self.root / 'arguments.json'
        self.env = dict(os.environ, PATH=str(self.root / 'bin'),
                        DAWN_TEST_TOOL_ARGUMENTS=str(self.arguments))

    def install_tool(self, name):
        tool = self.root / 'bin' / name
        tool.write_text(
            '#!' + os.sys.executable + '\n'
            'import json, os, sys\n'
            'from pathlib import Path\n'
            'Path(os.environ["DAWN_TEST_TOOL_ARGUMENTS"]).write_text(json.dumps({'
            '"args": sys.argv[1:], "cwd": os.getcwd(), '
            '"cgo": os.environ.get("CGO_ENABLED"), '
            '"modules": os.environ.get("GO111MODULE")}))\n'
            'sys.exit(int(os.environ.get("DAWN_TEST_TOOL_EXIT", "0")))\n')
        tool.chmod(0o755)

    def test_format_uses_native_tools_without_gn_or_depot_tools(self):
        sources = ['src/sample.h', 'src/sample.cc', 'src/sample.cpp',
                   'src/sample.m', 'src/sample.mm', 'include/public.h']
        for source in sources:
            path = self.root / source
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('// native formatter input\n')
        self.install_tool('clang-format')
        for parallel in (False, True):
            with self.subTest(parallel=parallel):
                if parallel:
                    self.install_tool('go')
                # Neither branch has GN or a depot_tools formatter wrapper.
                result = subprocess.run([
                    shutil.which('bash'), str(self.root / 'tools/format')
                ], cwd=self.root, env=self.env, capture_output=True,
                   text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                actual = json.loads(self.arguments.read_text())
                if parallel:
                    prefix = ['run', './tools/src/cmd/run-parallel',
                              'clang-format', '-i', '$', '--']
                    self.assertEqual(actual['args'][:len(prefix)], prefix)
                    self.assertCountEqual(actual['args'][len(prefix):], sources)
                    self.assertEqual(actual['cgo'], '0')
                    self.assertEqual(actual['modules'], 'on')
                else:
                    self.assertEqual(actual['args'][0], '-i')
                    self.assertCountEqual(actual['args'][1:], sources)
                self.assertEqual(actual['cwd'], str(self.root))

    def test_launcher_preserves_native_go_arguments_environment_and_failure(self):
        self.install_tool('go')
        self.env['DAWN_TEST_TOOL_EXIT'] = '7'
        for relative_path in (False, True):
            with self.subTest(relative_path=relative_path):
                self.arguments.unlink(missing_ok=True)
                self.env['PATH'] = (os.path.relpath(self.root / 'bin', self.root.parent)
                                    if relative_path else str(self.root / 'bin'))
                result = subprocess.run([
                    os.sys.executable, str(self.root / 'tools/run.py'),
                    'gen', 'build', '-check-stale'
                ], cwd=self.root.parent, env=self.env, capture_output=True,
                   text=True, check=False)
                self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
                actual = json.loads(self.arguments.read_text())
                self.assertEqual(actual, {
                    'args': ['run', './tools/src/cmd/gen', 'build', '-check-stale'],
                    'cwd': str(self.root), 'cgo': '0', 'modules': 'on'
                })

    def test_launcher_reports_missing_go_before_starting_a_tool(self):
        result = subprocess.run([
            os.sys.executable, str(self.root / 'tools/run.py'), 'gen', 'build'
        ], env=self.env, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Go is not installed or not in PATH', result.stderr)
        self.assertFalse(self.arguments.exists())


if __name__ == '__main__':
    unittest.main()
