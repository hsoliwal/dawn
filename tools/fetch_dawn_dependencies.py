# Copyright 2023 The Dawn & Tint Authors
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
"""
Helper script to download Dawn's source dependencies for a CMake build.

Each source dependency is pinned by its git submodule entry (the gitlink in this
checkout), and its URL comes from .gitmodules. Optional binary packages for the
D3D12 Agility SDK and Mesa are pinned below. No dependency manifest is executed,
and transitive submodules are not fetched.

This helps embedders, for example through CMake, get all the sources with
a single add_subdirectory call (or FetchContent) instead of more complex setups.
Run it from (or point -d at) a git checkout of Dawn: the pinned commits are read from git.
"""

import os
import shutil
import sys
import subprocess
import argparse
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser(
    prog='fetch_dawn_dependencies',
    description=__doc__,
)

parser.add_argument('-d',
                    '--directory',
                    type=str,
                    default="",
                    help="""
    Dawn checkout whose pinned dependencies are fetched. If not specified, the
    current working directory is used.
    """)

parser.add_argument('-g',
                    '--git',
                    type=str,
                    default="git",
                    help="""
    Path to the git command used to. By default, git is retrieved from the PATH.
    """)

parser.add_argument('-s',
                    '--shallow',
                    action='store_true',
                    default=True,
                    help="""
    Clone repositories without commit history (only getting data for the
    requested commit).
    NB: The git server hosting the dependencies must have turned on the
    `uploadpack.allowReachableSHA1InWant` option.
    """)
parser.add_argument('-ns',
                    '--no-shallow',
                    action='store_false',
                    dest='shallow',
                    help="Deactivate shallow cloning.")

parser.add_argument('-t',
                    '--use-test-deps',
                    action='store_true',
                    default=False,
                    help="""
    Deprecated: Test dependencies are now always included.
    """)

parser.add_argument('--fetch-agility-sdk',
                    action='store_true',
                    default=False,
                    help="Fetch the pinned D3D12 Agility SDK package.")
parser.add_argument('--fetch-swiftshader',
                    action='store_true',
                    default=False,
                    help="Fetch the native SwiftShader software GPU driver.")
parser.add_argument('--fetch-mesa',
                    action='store_true',
                    default=False,
                    help="Fetch Mesa and its pinned LLVM/Zstd fuzzing dependencies.")

parser.add_argument('--list',
                    action='store_true',
                    default=False,
                    help="Print path, URL and pinned commit of each dependency; fetch nothing.")

# The dependencies needed by the CMake build, as submodule paths.
REQUIRED_SUBMODULES = [
    'third_party/abseil-cpp',
    'third_party/directx-shader-compiler/src',
    'third_party/directx-headers/src',
    'third_party/glfw3/src',
    'third_party/jinja2',
    'third_party/EGL-Registry/src',
    'third_party/OpenGL-Registry/src',
    'third_party/libprotobuf-mutator/src',
    'third_party/protobuf',
    'third_party/markupsafe',
    'third_party/glslang/src',
    'third_party/google_benchmark/src',
    'third_party/googletest/src',
    'third_party/spirv-headers/src',
    'third_party/spirv-tools/src',
    'third_party/vulkan-headers/src',
    'third_party/vulkan-loader/src',
    'third_party/vulkan-utility-libraries/src',
    'third_party/webgpu-headers/src',
]

# The D3D12 Agility SDK is an archive, not a git repository.
AGILITY_SDK_PATH = 'third_party/agility-sdk/src'
AGILITY_SDK_PACKAGE = 'chromium/third_party/agility-sdk'
AGILITY_SDK_VERSION = 'version:2@1.722.0-preview'

# Mesa's Linux build uses these native binary packages rather than submodules.
MESA_PACKAGES = [
    ('third_party/llvm-dev', 'infra/3pp/tools/llvm-dev/linux-amd64',
     'version:3@22.1.0'),
    ('third_party/zstd', 'infra/3pp/static_libs/libzstd/linux-amd64',
     'Lf-seQJdussz81cZXnez5xIxEdkejDRxKumQpHbHMOUC'),
]


def main(args):
    root_dir = Path(args.directory).resolve()
    urls = submodule_urls(args, root_dir)
    required_submodules = list(REQUIRED_SUBMODULES)
    if args.fetch_swiftshader:
        required_submodules.append('third_party/swiftshader')
    if args.fetch_mesa:
        required_submodules.append('third_party/mesa/src')
    for submodule in required_submodules:
        if submodule not in urls:
            sys.exit(f"{submodule} has no entry in {root_dir / '.gitmodules'}")
        commit = pinned_commit(args, root_dir, submodule)
        if args.list:
            print(f"{submodule}\t{urls[submodule]}\t{commit}")
        else:
            fetch_git_dependency(args, urls[submodule], commit, root_dir / submodule)
    packages = []
    if args.fetch_agility_sdk:
        packages.append((AGILITY_SDK_PATH, AGILITY_SDK_PACKAGE, AGILITY_SDK_VERSION))
    if args.fetch_mesa:
        packages.extend(MESA_PACKAGES)
    for path, package, version in packages:
        if args.list:
            print(f"{path}\t{package}\t{version}")
        else:
            fetch_package(package, version, root_dir / path)


def submodule_urls(args, root_dir):
    """Map each submodule path in .gitmodules to its URL."""
    proc = subprocess.run([args.git, 'config', '-f', str(root_dir / '.gitmodules'), '--get-regexp',
                           r'^submodule\..*\.(path|url)$'], capture_output=True, text=True, check=True)
    names, urls = {}, {}
    for line in proc.stdout.splitlines():
        key, value = line.split(' ', 1)
        name, field = key[len('submodule.'):].rsplit('.', 1)
        (names if field == 'path' else urls)[name] = value
    return {path: urls[name] for name, path in names.items() if name in urls}


def pinned_commit(args, root_dir, submodule):
    """The commit the checkout pins for a submodule (its gitlink)."""
    proc = subprocess.run([args.git, '-C', str(root_dir), 'ls-tree', 'HEAD', '--', submodule],
                          capture_output=True, text=True)
    fields = proc.stdout.split()
    if proc.returncode != 0 or len(fields) < 3 or fields[1] != 'commit':
        sys.exit(f"no pinned commit for {submodule}: run from a git checkout of Dawn")
    return fields[2]


def fetch_git_dependency(args, git_url, git_tag, submodule_path):

    # .git may be a directory (standalone clone) or a file (git submodule).
    # Every mutating Git command must succeed before CMake can build this pin.
    def git(*arguments, check=True):
        return subprocess.run([args.git, '-C', submodule_path, *arguments],
                              capture_output=True, check=check)

    log(f"Fetching dependency '{submodule_path}'")
    if (submodule_path / ".git").exists():
        # A previous interrupted shallow fetch can leave an initialized checkout
        # without HEAD. Treat that as an incomplete fetch and retry the pin.
        head = git('rev-parse', '--verify', 'HEAD', check=False)
        if head.returncode == 0 and head.stdout.decode().strip() == git_tag:
            return
        if git('cat-file', '-e', git_tag + '^{commit}', check=False).returncode:
            log(f"Updating '{submodule_path}' from '{git_url}'")
            fetch_arguments = ['fetch', git_url, git_tag]
            if args.shallow:
                fetch_arguments.extend(['--depth', '1'])
            git(*fetch_arguments)
    else:
        if args.shallow:
            log(f"Shallow cloning '{git_url}' at '{git_tag}' into '{submodule_path}'")
            submodule_path.mkdir(parents=True, exist_ok=True)
            shallow_clone(git, git_url, git_tag)
        else:
            log(f"Cloning '{git_url}' into '{submodule_path}'")
            subprocess.run([args.git, 'clone', git_url, submodule_path],
                           capture_output=True, check=True)

    log(f"Checking out tag '{git_tag}'")
    git('checkout', '--detach', git_tag)
    current = git('rev-parse', 'HEAD').stdout.decode().strip()
    expected = git('rev-parse', git_tag + '^{commit}').stdout.decode().strip()
    if current != expected:
        raise RuntimeError(f"Dependency '{submodule_path}' did not reach pinned commit {git_tag}")



def fetch_package(name, version, package_path):
    # Keep a local version stamp in the ignored dependency directory so repeated runs can skip
    # downloading the same version. The stamp is written only after extraction succeeds.
    stamp = package_path / ('.dawn-' + name.replace('/', '-') + '-version')
    if stamp.is_file() and stamp.read_text() == version:
        return

    log(f"Fetching package '{name}' at '{version}'")
    if package_path.exists():
        shutil.rmtree(package_path)
    package_path.mkdir(parents=True)
    url = ('https://chrome-infra-packages.appspot.com/dl/' + name + '/+/' +
           urllib.parse.quote(version, safe=''))
    with tempfile.TemporaryDirectory() as temp_dir:
        archive = Path(temp_dir) / 'package.zip'
        urllib.request.urlretrieve(url, archive)
        with zipfile.ZipFile(archive) as package_zip:
            package_zip.extractall(package_path)

    stamp.write_text(version)


def shallow_clone(git, git_url, git_tag):
    """
    Fetching only 1 commit is not exposed in the git clone API, so we decompose
    it manually in git init, git fetch, git checkout.
    """
    git('init')
    git('fetch', git_url, git_tag, '--depth', '1')


def log(msg):
    """Just makes it look good in the CMake log flow."""
    print(f"-- -- {msg}")


if __name__ == "__main__":
    main(parser.parse_args())
