# Copyright 2024-2025 Jetperch LLC
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


import bisect
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection


def _build_source_map(elf):
    """Build address-to-source-file mapping from DWARF compilation units.

    :param elf: An ELFFile instance.
    :return: A tuple of (sorted_low_pcs, ranges) for binary search lookup.
        Each entry in ranges is (low_pc, high_pc, source_file).
    """
    if not elf.has_dwarf_info():
        return [], []
    dwarf = elf.get_dwarf_info()
    ranges = []
    for cu in dwarf.iter_CUs():
        die = cu.get_top_DIE()
        attrs = die.attributes
        if 'DW_AT_low_pc' not in attrs:
            continue
        low_pc = attrs['DW_AT_low_pc'].value
        high_pc_attr = attrs.get('DW_AT_high_pc')
        if high_pc_attr is None:
            continue
        if high_pc_attr.form == 'DW_FORM_addr':
            high_pc = high_pc_attr.value
        else:
            high_pc = low_pc + high_pc_attr.value
        name = attrs.get('DW_AT_name')
        if name is None:
            continue
        source = name.value
        if isinstance(source, bytes):
            source = source.decode('utf-8', errors='replace')
        ranges.append((low_pc, high_pc, source))
    ranges.sort(key=lambda x: x[0])
    low_pcs = [r[0] for r in ranges]
    return low_pcs, ranges


def _lookup_source(addr, low_pcs, ranges):
    """Find the source file for a given address using the DWARF source map."""
    if not low_pcs:
        return ''
    idx = bisect.bisect_right(low_pcs, addr) - 1
    if idx < 0:
        return ''
    low_pc, high_pc, source = ranges[idx]
    if low_pc <= addr < high_pc:
        return source
    return ''


def parse_elf(f):
    """Parse an ELF file for symbol information.

    :param f: The ELF file path.
    :return: A list of dictionaries, one for each symbol.
        Each dictionary contains: section, name, addr, size, source.
    """
    with open(f, 'rb') as fh:
        elf = ELFFile(fh)
        low_pcs, ranges = _build_source_map(elf)
        symbols = []
        for section in elf.iter_sections():
            if not isinstance(section, SymbolTableSection):
                continue
            for sym in section.iter_symbols():
                if sym['st_info']['type'] not in ('STT_FUNC', 'STT_OBJECT'):
                    continue
                size = sym['st_size']
                if size <= 0:
                    continue
                name = sym.name
                if not name:
                    continue
                addr = sym['st_value']
                shndx = sym['st_shndx']
                if isinstance(shndx, str):
                    sec_name = shndx
                else:
                    try:
                        sec_name = elf.get_section(shndx).name
                    except Exception:
                        sec_name = ''
                sec_name = sec_name.lstrip('.')
                source = _lookup_source(addr, low_pcs, ranges)
                symbols.append({
                    'section': sec_name,
                    'name': name,
                    'addr': f'0x{addr:08x}',
                    'size': size,
                    'source': source,
                })
    return symbols
