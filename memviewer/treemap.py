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

import numpy as np
import pandas as pd
import squarify
import itertools
from bokeh.palettes import Category20c
from bokeh.models import HoverTool
from bokeh.plotting import figure, show
from bokeh.transform import factor_cmap


def groupby(field, symbols: list) -> dict:
    """Return the grouping by field.

    :param field: The field or list of fields in each symbol used for grouping.
    :param symbols: The list of symbols, which is each a map.
    :return: A dictionary mapping field name to the list of symbols.
    """
    if isinstance(field, str):
        field = [field]
    f, field = field[0], field[1:]
    grouped = {}
    for symbol in symbols:
        key = symbol[f]
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(symbol)
    if len(field):
        for key, value in grouped.items():
            grouped[key] = groupby(field, value)
    return grouped


def _colors(length, palette=None):
    idx = max(palette.keys())
    palette = itertools.cycle(palette[idx])
    return [next(palette) for i in range(length)]


def _treemap(df, x, y, dx, dy):
    normed = squarify.normalize_sizes(df['size'], dx, dy)
    blocks = squarify.squarify(normed, x, y, dx, dy)
    blocks_df = pd.DataFrame(blocks).set_index(df.index)
    return df.join(blocks_df, how='left').reset_index()


def treemap_grouped(symbols: list, groupby):
    df = pd.DataFrame(symbols)
    size_by_group = df.groupby([groupby]).sum('size').sort_values(by='size', ascending=False)

    x, y = 0, 0
    w, h = 1000, 800

    blocks_by_group = _treemap(size_by_group, x, y, w, h)
    groups = blocks_by_group[groupby].unique()

    dfs = []
    for index, d in blocks_by_group.iterrows():
        df_group = df[df[groupby] == d[groupby]]
        dfs.append(_treemap(df_group, d['x'], d['y'], d['dx'], d['dy']))
    blocks = pd.concat(dfs)

    hover = HoverTool(tooltips=[
        ('name', '@name'),
        ('file', '@source'),
        ('size', '@size'),
    ])

    p = figure(width=w, height=h, title='Memory Map',
               tools=[hover, 'pan', 'wheel_zoom', 'box_zoom', 'reset'],
               x_range=(0, w), y_range=(0, h))
    p.block('x', 'y', 'dx', 'dy',
            line_color='white', line_width=1,
            fill_color=factor_cmap(groupby, _colors(len(groups), Category20c), groups),
            source=blocks)
    p.text('x', 'y', x_offset=2, text=groupby, source=blocks_by_group,
           text_font_size="10pt", text_color="white")
    blocks['ytop'] = blocks.y + blocks.dy
    p.text('x', 'ytop', x_offset=2, y_offset=2, text='name', source=blocks,
           text_font_size="6pt", text_baseline="top",
           text_color='white')

    p.axis.axis_label = None
    p.axis.visible = False
    show(p)


def treemap_flat(symbols: list):
    x, y = 0, 0
    width, height = 1000, 800
    data = [(v['size'], f"{v['source']}|{v['name']}") for v in symbols]
    data = sorted(data, reverse=True)
    values = [v[0] for v in data]
    sizes = np.array(values, dtype=float)

    values = squarify.normalize_sizes(values, width, height)
    rects = squarify.squarify(values, x, y, width, height)

    source = pd.DataFrame(data={
        'name': [v[1].split('|')[1] for v in data],
        'file': [v[1].split('|')[0] for v in data],
        'legend': [v[1] for v in data],
        'size': sizes,
        'color': _colors(len(sizes), Category20c),
    })
    source = source.join(pd.DataFrame(rects), how='left').reset_index()

    hover = HoverTool(tooltips=[
        ('name', '@name'),
        ('file', '@file'),
        ('size', '@size'),
    ])

    p = figure(width=width, height=height, title='Memory Map',
               tools=[hover, 'pan', 'wheel_zoom', 'box_zoom', 'reset'],
               x_range=(0, width), y_range=(0, height))
    p.block('x', 'y', 'dx', 'dy',
            line_color='white', fill_color='color',
            source=source)

    p.axis.axis_label = None
    p.axis.visible = False
    show(p)


def treemap(symbols: list, groupby=None):
    """Generate and display a treemap.

    :param symbols: The list of dictionaries, one for each symbol.
        Each symbol must contain the fields section, name, addr, size, source.
    :param groupby: The optional field used to group the treemap.
    """
    if groupby is None:
        treemap_flat(symbols)
    else:
        treemap_grouped(symbols, groupby)
