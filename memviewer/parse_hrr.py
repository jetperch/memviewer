#!/usr/bin/env python3
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

"""Parse a Lattice Diamond hierarchical resource report (.hrr) file.

Each "Report for cell" block reports total cell usage including all
descendants.  This parser converts that cumulative view into per-cell
"own" usage (this cell minus direct children) so the values sum
correctly when rendered as a treemap.
"""

import re


_SEPARATOR_RE = re.compile(r'^-{3,}\s*$', re.MULTILINE)
_HEADER_RE = re.compile(r'Report for cell\s+(\S+)')
_PATH_RE = re.compile(r'Instance path:\s*(\S+)')
_CELL_USAGE_RE = re.compile(r'Cell usage:(.*?)(?:SUB MODULES|\Z)', re.DOTALL)


# Lattice ECP5 resource types that appear in .hrr files.
RESOURCE_TYPES = (
    'SLIC', 'LUT4', 'DISTRAM', 'PFUREG', 'RIPPLE',
    'EBR', 'IOLGC', 'IOREG', 'IOBUF', 'DSP', 'PLL',
)


def _parse_block(chunk):
    """Parse a single separator-delimited chunk.

    :param chunk: The text between two separator lines.
    :return: dict with name, path, resources -- or None if chunk is not
        a cell report.
    """
    m_header = _HEADER_RE.search(chunk)
    m_path = _PATH_RE.search(chunk)
    if m_header is None or m_path is None:
        return None
    m_usage = _CELL_USAGE_RE.search(chunk)
    resources = {}
    if m_usage is not None:
        for line in m_usage.group(1).splitlines():
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            if parts[0] == 'cell':
                continue  # column header
            try:
                count = float(parts[1])
            except ValueError:
                continue
            resources[parts[0]] = count
    return {
        'name': m_header.group(1),
        'path': m_path.group(1),
        'resources': resources,
    }


def _compute_own_sizes(blocks):
    """Subtract direct children from each block to get its own usage."""
    path_to_block = {b['path']: b for b in blocks}
    children = {b['path']: [] for b in blocks}
    for path in path_to_block:
        idx = path.rfind('/')
        if idx < 0:
            continue
        parent = path[:idx]
        if parent in children:
            children[parent].append(path)

    for block in blocks:
        own = dict(block['resources'])
        for child_path in children[block['path']]:
            for res, val in path_to_block[child_path]['resources'].items():
                own[res] = own.get(res, 0.0) - val
        # Tiny negatives from float rounding -> clamp to zero.
        block['own'] = {k: v if v > 0.0 else 0.0 for k, v in own.items()}
        block['parent'] = path_to_block[
            block['path'][:block['path'].rfind('/')]
        ]['name'] if '/' in block['path'] and block['path'][:block['path'].rfind('/')] in path_to_block else ''


def _compute_subsystems(blocks, depth):
    """Tag each block with its subsystem: the cell name of its ancestor
    at the given path depth.  Blocks at or above the target depth become
    their own subsystem.
    """
    path_to_block = {b['path']: b for b in blocks}
    for block in blocks:
        segments = block['path'].split('/')
        ancestor_path = '/'.join(segments[:depth + 1])
        ancestor = path_to_block.get(ancestor_path)
        block['subsystem'] = ancestor['name'] if ancestor else block['name']


def parse_hrr(f, resource='SLIC', subsystem_depth=2):
    """Parse a Lattice Diamond .hrr hierarchical resource report.

    :param f: The .hrr file path.
    :param resource: The resource type to report as ``size``.  Common
        values: SLIC, LUT4, DISTRAM, PFUREG, RIPPLE, EBR.
    :param subsystem_depth: The instance path depth used to compute each
        block's ``subsystem`` field (default 2, which maps to the
        functional-block level in most designs).  Use the ``subsystem``
        field with ``--groupby subsystem`` to cluster each top-level
        block with all of its descendants.
    :return: A list of dicts, one per cell instance, with fields:
        section (the resource type), name (cell name), addr (instance
        path), size (own count for this resource), source (parent cell
        name), subsystem (ancestor cell name at ``subsystem_depth``).
    """
    with open(f, 'rt') as fin:
        text = fin.read()
    blocks = []
    for chunk in _SEPARATOR_RE.split(text):
        block = _parse_block(chunk)
        if block is not None:
            blocks.append(block)
    _compute_own_sizes(blocks)
    _compute_subsystems(blocks, subsystem_depth)

    symbols = []
    for b in blocks:
        size = b['own'].get(resource, 0.0)
        if size <= 0.0:
            continue
        symbols.append({
            'section': resource,
            'name': b['name'],
            'addr': b['path'],
            'size': size,
            'source': b['parent'] or '(top)',
            'subsystem': b['subsystem'],
        })
    return symbols
