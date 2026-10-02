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


import argparse
import sys
from memviewer import parse_elf, parse_hrr, parse_ld_map, treemap


_filter_operator_map = {
    'equals': str.__eq__,
    'contains': str.__contains__,
    'startswith': str.startswith,
    'endswith': str.endswith,
}


def validate_filter(s):
    parts = s.split(',')
    if len(parts) != 3:
        raise ValueError('Invalid filter specification')
    try:
        parts[1] = _filter_operator_map[parts[1]]
    except KeyError:
        raise ValueError('Invalid filter operator')
    return parts


def get_parser():
    p = argparse.ArgumentParser(
        description='Analyze a map file or compiled ELF.')
    p.add_argument('source',
                   help='The source map filename.')
    p.add_argument('--filename-prefix',
                   help='Strip a filename prefix.')
    p.add_argument('--address-prefix',
                   help='Filter by address prefix.')
    p.add_argument('--filter', '-f',
                   action='append',
                   type=validate_filter,
                   help='Add a filter specification in the format of "{field},{operator},{value}. ' +
                   'The operators are equals, startswith, contains, endswith.')
    p.add_argument('--groupby', '-g',
                   help='Group treemap by this field.')
    p.add_argument('--resource', '-r',
                   default='SLIC',
                   help='For .hrr files, the resource type to size by '
                        '(e.g. SLIC, LUT4, DISTRAM, PFUREG, RIPPLE, EBR). '
                        'Default: SLIC.')
    p.add_argument('--subsystem-depth',
                   type=int,
                   default=2,
                   help='For .hrr files, the instance path depth used to '
                        'tag each block with a "subsystem" field.  Use '
                        '--groupby subsystem to cluster by functional '
                        'block.  Default: 2.')
    return p


def run():
    args = get_parser().parse_args()
    if args.source.endswith('.map'):
        symbols = parse_ld_map(args.source)
    elif args.source.endswith('.hrr'):
        symbols = parse_hrr(args.source,
                            resource=args.resource,
                            subsystem_depth=args.subsystem_depth)
    else:
        symbols = parse_elf(args.source)

    if args.filter is not None:
        for field, operator, value in args.filter:
            symbols = [v for v in symbols if operator(v[field], value)]

    if args.address_prefix:
        symbols = [v for v in symbols if v['addr'].startswith(args.address_prefix)]

    for v in symbols:
        if 'libc.' in v['source']:
            v['source'] = 'libc'

    if args.filename_prefix:
        for v in symbols:
            v['source'] = v['source'].removeprefix(args.filename_prefix)

    if len(symbols) == 0:
        print('No matching symbols')
    else:
        treemap(symbols, args.groupby)

    return 0


if __name__ == '__main__':
    sys.exit(run())
