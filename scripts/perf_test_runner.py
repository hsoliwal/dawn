#!/usr/bin/env python3
#
# Copyright 2019 The Dawn & Tint Authors
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

# Based on Angle's perf_test_runner.py

import argparse
import glob
import os
import re
import subprocess
import sys


class PerfTestError(Exception):

    def __init__(self, message, exit_code=1):
        super().__init__(message)
        self.exit_code = exit_code


def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        raise ValueError('mean requires at least one data point')
    return float(sum(data)) / float(n)  # in Python 2 use sum(data)/float(n)


def sum_of_square_deviations(data, c):
    """Return sum of square deviations of sequence data."""
    ss = sum((float(x) - c)**2 for x in data)
    return ss


def coefficient_of_variation(data):
    """Calculates the population coefficient of variation."""
    n = len(data)
    if n < 2:
        raise ValueError('variance requires at least two data points')
    c = mean(data)
    ss = sum_of_square_deviations(data, c)
    pvar = ss / n  # the population variance
    stddev = (pvar**0.5)  # population standard deviation
    return stddev / c


def truncated_list(data, n):
    """Compute a truncated list, n is truncation size"""
    if len(data) < n * 2:
        raise ValueError('list not large enough to truncate')
    return sorted(data)[n:-n]


def truncated_mean(data, n):
    """Compute a truncated mean, n is truncation size"""
    return mean(truncated_list(data, n))


def truncated_cov(data, n):
    """Compute a truncated coefficient of variation, n is truncation size"""
    return coefficient_of_variation(truncated_list(data, n))


def find_test_binary(args):
    binary_name = 'dawn_perf_tests'
    if sys.platform == 'win32':
        binary_name += '.exe'

    if args.binary:
        binary = os.path.abspath(args.binary)
    elif args.build_dir:
        binary = os.path.abspath(os.path.join(args.build_dir, binary_name))
    else:
        # Resolve release builds inside this Dawn checkout, regardless of cwd.
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = glob.glob(os.path.join(base_path, 'out', '*elease*',
                                            binary_name))
        candidates = sorted(path for path in candidates if os.path.isfile(path))
        binary = max(candidates, key=os.path.getmtime) if candidates else None

    if binary is None or not os.path.isfile(binary):
        raise PerfTestError(
            'Cannot find native %s%s. Select an existing executable with '
            '--binary or its directory with --build-dir.' %
            (binary_name, ': ' + binary if binary else ' in Dawn/out/*elease*'))
    return binary


def get_results(binary, test_name, metric, extra_args=()):
    try:
        process = subprocess.run(
            [binary, '--gtest_filter=' + test_name] + list(extra_args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            check=False)
    except OSError as error:
        raise PerfTestError('Cannot run test executable %s: %s' %
                            (binary, error)) from error

    output_string = process.stdout
    if process.returncode:
        # A failed test may print metrics before failing. Never accept them.
        exit_code = (process.returncode if process.returncode > 0 else
                     128 - process.returncode)
        raise PerfTestError(
            'Test executable failed with status %d:\n%s%s' %
            (process.returncode, output_string, process.stderr), exit_code)

    m = re.search(r'Running (\d+) tests?\b', output_string)
    if m and int(m.group(1)) != 1:
        raise PerfTestError('The filter must select exactly one test:\n' +
                            output_string, 3)

    # Native Dawn performance tests retain the RESULT metric output format.
    pattern = re.escape(metric) + r'.*= ([0-9.]+)'
    matches = re.findall(pattern, output_string)
    if not matches:
        raise PerfTestError("Did not find the metric '%s' in the test output:\n%s" %
                            (metric, output_string))
    try:
        return [float(value) for value in matches]
    except ValueError as error:
        raise PerfTestError("Invalid metric '%s' in the test output:\n%s" %
                            (metric, output_string)) from error


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Run a native Dawn performance test with calibration and '
        'ten measured experiments.')
    parser.add_argument('test_name', help='GTest filter selecting one test')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--binary', help='native performance test executable')
    selection.add_argument('--build-dir',
                           help='directory containing dawn_perf_tests')
    args = parser.parse_args(argv)

    try:
        binary = find_test_binary(args)
        print('Using test executable: ' + binary)
        print('Test name: ' + args.test_name)

        # Calibrate once, then pass the native executable's integer option.
        steps = get_results(binary, args.test_name, 'steps', ['--calibration'])[0]
        if not steps.is_integer() or not 0 < steps <= 0xffffffff:
            raise PerfTestError('Calibration steps must be a positive 32-bit integer.')
        steps = int(steps)
        print('running with %d steps.' % steps)

        metric = 'wall_time'
        max_experiments = 10
        scores = []
        for experiment in range(max_experiments):
            experiment_scores = get_results(
                binary, args.test_name, metric, ['--override-steps=%d' % steps])

            for score in experiment_scores:
                sys.stdout.write('%s: %.2f' % (metric, score))
                scores.append(score)

                if len(scores) > 1:
                    sys.stdout.write(', mean: %.2f' % mean(scores))
                    sys.stdout.write(', variation: %.2f%%' %
                                     (coefficient_of_variation(scores) * 100.0))

                if len(scores) > 7:
                    truncation_n = len(scores) >> 3
                    sys.stdout.write(', truncated mean: %.2f' %
                                     truncated_mean(scores, truncation_n))
                    sys.stdout.write(', variation: %.2f%%' %
                                     (truncated_cov(scores, truncation_n) * 100.0))

                print('')
    except PerfTestError as error:
        print(error, file=sys.stderr)
        return error.exit_code
    return 0


if __name__ == '__main__':
    sys.exit(main())
