#!/usr/bin/env python3
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


def parse_ld_map(f):
    """Parse a GCC LD map file.

    :param f: The path or file-like object.
    :return: A list of dictionaries, one for each symbol.

    Works on GCC 13 with "-ffunction-sections -fdata-sections"
    """
    if isinstance(f, str):
        with open(f, 'rt') as fin:
            return parse_ld_map(fin)
    state = 0
    symbols = []
    for line in f.readlines():
        add = None
        if state == 0 and line == 'Linker script and memory map\n':
            state = 1
        elif line.startswith('.debug_info'):
            break
        elif state == 1 and line.startswith(' .'):
            parts = line.strip().split(maxsplit=3)
            parts_len = len(parts)
            if parts_len == 1:
                name = parts[0]
                state = 2
            elif parts_len == 4:
                add = parts
            else:
                raise ValueError(f'unsupported parts: {parts_len}, {line}')
        elif state == 2:
            line = line.strip()
            addr, size, src = line.split()
            add = [name, addr, size, src]
            state = 1

        if add is not None:
            name, addr, size, src = add
            name_parts = name.split('.', 2)
            name_parts_len = len(name_parts)
            if name_parts[0] == '':
                name_parts = name_parts[1:]
                name_parts_len -= 1
            if name_parts_len == 2:
                section, name = name_parts
            elif name_parts_len == 1:
                section, name = '', name_parts[0]
            else:
                section, name = '', ''
            size = int(size, 16)
            if size > 0:
                if src.endswith('.obj'):
                    src = src[:-4]
                elif src.endswith('.o'):
                    src = src[:-2]
                symbols.append({
                    'section': section,
                    'name': name,
                    'addr': addr,
                    'size': size,
                    'source': src,
                })
    return symbols
