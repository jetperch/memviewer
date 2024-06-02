# Copyright 2024 Jetperch LLC
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
Test the UI units module.
"""

import unittest
import os
from memviewer.parse_ld_map import parse_ld_map


MYPATH = os.path.dirname(os.path.abspath(__file__))


class TestParseLdMap(unittest.TestCase):

    def test_example_01(self):
        v = parse_ld_map(os.path.join(MYPATH, 'example_01.map'))
        self.assertEqual(158, len(v))
