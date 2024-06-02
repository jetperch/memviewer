#!/usr/bin/env python3
# Copyright 20212-24 Jetperch LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Update the project version.

Use the most recently CHANGELOG as the definitive version for:
- CHANGELOG.md
- memviewer/version.py
"""

import os
import re

MYPATH = os.path.dirname(os.path.abspath(__file__))


def _str(version):
    return '.'.join([str(x) for x in version])


def _changelog_version():
    path = os.path.join(MYPATH, 'CHANGELOG.md')
    with open(path, 'rt') as f:
        for line in f:
            if line.startswith('## '):
                version = line.split(' ')[1]
                return [int(x) for x in version.split('.')]


def _py_version(version):
    path = os.path.join(MYPATH, 'memviewer', 'version.py')
    path_tmp = path + '.tmp'
    with open(path, 'rt') as rd:
        with open(path_tmp, 'wt') as wr:
            for line in rd:
                if line.startswith('__version__'):
                    line = f'__version__ = "{_str(version)}"\n'
                wr.write(line)
    os.replace(path_tmp, path)


def run():
    version = _changelog_version()
    print(f'Version = {_str(version)}')
    _py_version(version)
    return 0


if __name__ == '__main__':
    run()
