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

"""Exercise the native performance runner with an executable process fixture."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest


@unittest.skipUnless(os.name == 'posix',
                     'The executable fixture uses a POSIX shebang.')
class PerfTestRunnerTest(unittest.TestCase):

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.checkout = self.directory / 'native dawn checkout'
        (self.checkout / 'scripts').mkdir(parents=True)
        self.runner = self.checkout / 'scripts/perf_test_runner.py'
        shutil.copy2(Path(__file__).with_name('perf_test_runner.py'), self.runner)
        self.cwd = self.directory / 'unrelated working directory'
        self.cwd.mkdir()
        self.log = self.directory / 'calls.jsonl'
        self.env = dict(os.environ, DAWN_PERF_TEST_LOG=str(self.log))

    def install_binary(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!' + sys.executable + '\n' + textwrap.dedent('''\
            import json
            import os
            from pathlib import Path
            import sys

            with open(os.environ['DAWN_PERF_TEST_LOG'], 'a') as log:
                log.write(json.dumps({'binary': __file__, 'args': sys.argv[1:],
                                      'cwd': os.getcwd()}) + '\\n')
            mode = os.environ.get('DAWN_PERF_TEST_MODE', '')
            count = 1
            if '--gtest_filter=Missing.*' in sys.argv:
                count = 0
            elif '--gtest_filter=Multiple.*' in sys.argv:
                count = 2
            print('[==========] Running %d tests from 1 test suite.' % count)
            if '--calibration' in sys.argv:
                print('RESULT Native.steps: Case= %s count' %
                      os.environ.get('DAWN_PERF_TEST_STEPS', '42'))
                if mode == 'failed-calibration':
                    print('calibration failure', file=sys.stderr)
                    sys.exit(9)
            else:
                if '--override-steps=42' not in sys.argv:
                    print('wrong native override-steps argument', file=sys.stderr)
                    sys.exit(19)
                if mode != 'missing-metric':
                    print('*RESULT Native.wall_time: Case= 1.25 ms')
                    print('*RESULT Native.wall_time: Case= 2.75 ms')
                if mode == 'failed-measurement':
                    print('measurement failure', file=sys.stderr)
                    sys.exit(7)
            '''), encoding='utf-8')
        path.chmod(0o755)
        return path

    def run_runner(self, *args):
        return subprocess.run([sys.executable, str(self.runner), *args],
                              cwd=self.cwd, env=self.env, capture_output=True,
                              text=True, check=False)

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def assert_calibrated_experiments(self, result, binary):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = self.calls()
        self.assertEqual(len(calls), 11)
        self.assertEqual(calls[0]['args'],
                         ['--gtest_filter=Native.Case', '--calibration'])
        self.assertEqual([call['args'] for call in calls[1:]],
                         [['--gtest_filter=Native.Case', '--override-steps=42']] * 10)
        self.assertTrue(all(call['binary'] == str(binary) for call in calls))
        self.assertTrue(all(call['cwd'] == str(self.cwd) for call in calls))
        self.assertIn('running with 42 steps.', result.stdout)
        self.assertEqual(result.stdout.count('wall_time:'), 20)
        self.assertIn('mean: 2.00, variation: 37.50%', result.stdout)
        self.assertIn('truncated mean: 2.00, variation: 37.50%', result.stdout)

    def test_default_discovery_uses_newest_release_in_this_checkout(self):
        older = self.install_binary(self.checkout / 'out/Release/dawn_perf_tests')
        newer = self.install_binary(self.checkout / 'out/cmake-release/dawn_perf_tests')
        unrelated = self.install_binary(self.cwd / 'out/Release/dawn_perf_tests')
        os.utime(older, (1, 1))
        os.utime(newer, (2, 2))
        os.utime(unrelated, (3, 3))
        self.assert_calibrated_experiments(self.run_runner('Native.Case'), newer)

    def test_explicit_relative_binary_and_build_directory_support_spaces(self):
        binary = self.install_binary(self.directory / 'build with spaces/dawn_perf_tests')
        for option, path in (('--binary', binary), ('--build-dir', binary.parent)):
            with self.subTest(option=option):
                self.log.unlink(missing_ok=True)
                result = self.run_runner('Native.Case', option,
                                         os.path.relpath(path, self.cwd))
                self.assert_calibrated_experiments(result, binary)

    def test_filter_is_required_and_selection_options_are_exclusive(self):
        for args in ((), ('Native.Case', '--binary', 'a', '--build-dir', 'b')):
            with self.subTest(args=args):
                result = self.run_runner(*args)
                self.assertEqual(result.returncode, 2)
                self.assertIn('usage:', result.stderr)
                self.assertEqual(self.calls(), [])

    def test_missing_binary_is_reported_before_launch(self):
        for options in ((), ('--binary', 'missing executable'),
                        ('--build-dir', 'missing build directory')):
            with self.subTest(options=options):
                result = self.run_runner('Native.Case', *options)
                self.assertEqual(result.returncode, 1)
                self.assertIn('Cannot find native dawn_perf_tests', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(self.calls(), [])

    def test_unlaunchable_binary_is_reported(self):
        binary = self.install_binary(self.directory / 'not executable')
        binary.chmod(0o644)
        result = self.run_runner('Native.Case', '--binary', str(binary))
        self.assertEqual(result.returncode, 1)
        self.assertIn('Cannot run test executable', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(self.calls(), [])

    def test_failed_process_metrics_are_rejected_and_status_is_preserved(self):
        binary = self.install_binary(self.directory / 'dawn_perf_tests')
        for mode, status, call_count in (('failed-calibration', 9, 1),
                                        ('failed-measurement', 7, 2)):
            with self.subTest(mode=mode):
                self.log.unlink(missing_ok=True)
                self.env['DAWN_PERF_TEST_MODE'] = mode
                result = self.run_runner('Native.Case', '--binary', str(binary))
                self.assertEqual(result.returncode, status)
                self.assertIn('failed with status %d' % status, result.stderr)
                self.assertIn('failure', result.stderr)
                self.assertNotIn('wall_time:', result.stdout)
                self.assertEqual(len(self.calls()), call_count)

    def test_filter_must_select_exactly_one_test(self):
        binary = self.install_binary(self.directory / 'dawn_perf_tests')
        for name in ('Missing.*', 'Multiple.*'):
            with self.subTest(name=name):
                self.log.unlink(missing_ok=True)
                result = self.run_runner(name, '--binary', str(binary))
                self.assertEqual(result.returncode, 3)
                self.assertIn('exactly one test', result.stderr)
                self.assertEqual(len(self.calls()), 1)

    def test_missing_measurement_metric_is_rejected(self):
        binary = self.install_binary(self.directory / 'dawn_perf_tests')
        self.env['DAWN_PERF_TEST_MODE'] = 'missing-metric'
        result = self.run_runner('Native.Case', '--binary', str(binary))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Did not find the metric 'wall_time'", result.stderr)
        self.assertEqual(len(self.calls()), 2)

    def test_calibration_requires_a_positive_native_integer(self):
        binary = self.install_binary(self.directory / 'dawn_perf_tests')
        for steps in ('0', '42.5', '4294967296'):
            with self.subTest(steps=steps):
                self.log.unlink(missing_ok=True)
                self.env['DAWN_PERF_TEST_STEPS'] = steps
                result = self.run_runner('Native.Case', '--binary', str(binary))
                self.assertEqual(result.returncode, 1)
                self.assertIn('Calibration steps must be a positive 32-bit integer',
                              result.stderr)
                self.assertEqual(len(self.calls()), 1)


if __name__ == '__main__':
    unittest.main()
