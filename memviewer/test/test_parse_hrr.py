# Copyright 2026 Jetperch LLC
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

import unittest
import os
from memviewer.parse_hrr import parse_hrr


MYPATH = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(MYPATH, 'example_01.hrr')


class TestParseHrr(unittest.TestCase):

    def test_own_sizes_sum_to_top(self):
        # Parent counts include descendants; own sums should match top.
        syms = parse_hrr(FIXTURE, resource='LUT4')
        self.assertEqual(200.0, sum(s['size'] for s in syms))
        syms = parse_hrr(FIXTURE, resource='SLIC')
        self.assertEqual(100.0, sum(s['size'] for s in syms))

    def test_own_size_per_cell(self):
        by_name = {s['name']: s for s in parse_hrr(FIXTURE, resource='LUT4')}
        # top owns 200 - 60 (a) - 80 (b) = 60
        self.assertEqual(60.0, by_name['top']['size'])
        # a owns 60 - 25 (c) = 35
        self.assertEqual(35.0, by_name['a']['size'])
        self.assertEqual(25.0, by_name['c']['size'])
        self.assertEqual(80.0, by_name['b']['size'])

    def test_parent_linkage(self):
        by_name = {s['name']: s for s in parse_hrr(FIXTURE, resource='LUT4')}
        self.assertEqual('(top)', by_name['top']['source'])
        self.assertEqual('top', by_name['a']['source'])
        self.assertEqual('top', by_name['b']['source'])
        self.assertEqual('a', by_name['c']['source'])

    def test_missing_resource_drops_zero_entries(self):
        # Fixture has no EBR at all.
        syms = parse_hrr(FIXTURE, resource='EBR')
        self.assertEqual([], syms)

    def test_instance_path_in_addr(self):
        by_name = {s['name']: s for s in parse_hrr(FIXTURE, resource='LUT4')}
        self.assertEqual('top/a/c', by_name['c']['addr'])

    def test_subsystem_at_depth(self):
        # Fixture hierarchy: top (depth 0) / a (depth 1) / c (depth 2),
        # and top / b (depth 1).  At subsystem_depth=1, the deepest
        # block 'c' groups with its depth-1 ancestor 'a'; 'a' and 'b'
        # are their own subsystem; 'top' is shallower so it's its own.
        by_name = {s['name']: s
                   for s in parse_hrr(FIXTURE, resource='LUT4',
                                      subsystem_depth=1)}
        self.assertEqual('a', by_name['c']['subsystem'])
        self.assertEqual('a', by_name['a']['subsystem'])
        self.assertEqual('b', by_name['b']['subsystem'])
        self.assertEqual('top', by_name['top']['subsystem'])

    def test_subsystem_deeper_than_block(self):
        # At depth=2, blocks shallower than 2 get their own name,
        # 'c' at exactly depth 2 also gets its own name.
        by_name = {s['name']: s
                   for s in parse_hrr(FIXTURE, resource='LUT4',
                                      subsystem_depth=2)}
        self.assertEqual('c', by_name['c']['subsystem'])
        self.assertEqual('a', by_name['a']['subsystem'])
        self.assertEqual('b', by_name['b']['subsystem'])
        self.assertEqual('top', by_name['top']['subsystem'])
