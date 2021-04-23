# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import re
import sys
import math
import typing as typ
import pathlib as pl
import datetime as dt
import textwrap
from xml.sax.saxutils import escape as xml_escape

from . import vcs

Filename      = str
AuthorName    = str
Timeline      = typ.List[int]
Contributions = typ.Dict[AuthorName, Timeline]

FileStats = typ.Dict[Filename, Contributions]

AuthorFull    = typ.Tuple[str, str]
AuthorAliases = typ.Dict[typ.Pattern, AuthorFull]


class Stats(typ.NamedTuple):
    timeline_start: str
    timeline_end  : str
    filestats     : FileStats


StatsByAuthor = typ.Dict[AuthorFull, typ.List[typ.Tuple[dt.date, int, int]]]
StatsByFile   = typ.Dict[str       , StatsByAuthor]


def stats_by_file(commits: typ.List[vcs.Commit], author_aliases: AuthorAliases) -> StatsByFile:
    stats: StatsByFile = {}
    for commit in commits:
        name                = commit.author.strip()
        email               = commit.email.strip()
        author              = (name, email)
        _maybe_author_alias = f"{name} <{email}>"
        for alias_re, author_normalized in author_aliases.items():
            if alias_re.match(_maybe_author_alias):
                author = author_normalized

        for change in commit.changes:
            total_rel = change.added_rel + change.deleted_rel
            if total_rel > 0:
                added_ratio   = change.added_rel   / total_rel
                deleted_ratio = change.deleted_rel / total_rel
                added_lines   = round(change.changed_lines * added_ratio)
                deleted_lines = round(change.changed_lines * deleted_ratio)
            else:
                added_lines   = 0
                deleted_lines = 0

            if change.filename in stats:
                file_stats = stats[change.filename]
            else:
                file_stats = stats[change.filename] = {}

            date      = dt.date(*map(int, commit.date.split("-")))
            file_stat = (date, added_lines, deleted_lines)
            if author in file_stats:
                file_stats[author].append(file_stat)
            else:
                file_stats[author] = [file_stat]

    return stats


def calc_overall_stats(commits: typ.List[vcs.Commit], author_aliases: AuthorAliases) -> StatsByAuthor:
    stats        : StatsByFile   = stats_by_file(commits, author_aliases)
    overall_stats: StatsByAuthor = {}
    for file_stats_by_author in stats.values():
        for author, file_stats in file_stats_by_author.items():
            if author in overall_stats:
                overall_stats[author].extend(file_stats)
            else:
                overall_stats[author] = list(file_stats)
    return overall_stats


class Row(typ.NamedTuple):
    total : float
    author: str
    email : str
    scores: typ.List[float]


class Grid(typ.NamedTuple):
    min_date : dt.date
    max_date : dt.date
    day_width: float  # number of cells
    row_width: int
    rows     : typ.List[Row]


def calc_stats_grid(stats: StatsByAuthor, max_width: int) -> Grid:
    dates = {
        date for file_stats in stats.values() for date, added, removed in file_stats if added + removed > 0
    }

    min_date   = min(dates)
    max_date   = max(dates)
    total_days = (max_date - min_date).days + 1
    row_width  = min(max_width, total_days)
    day_width  = row_width / total_days

    rows = []
    for (author, email), file_stats in stats.items():
        row_scores = [0.0] * row_width

        total_score = 0.0
        for date, added, removed in file_stats:
            days    = (date - min_date).days
            changed = added + removed
            i       = int(row_width * days / total_days)
            score   = math.log2(changed + 1)
            row_scores[i] += score
            total_score += score

        row = Row(total_score, author, email, row_scores)
        rows.append(row)

    # sort desc by "most" contributions
    rows.sort(reverse=True)
    return Grid(min_date, max_date, day_width, row_width, rows)


Legend = typ.List[typ.Tuple[int, str]]


def quarter(month: int) -> int:
    return math.ceil(month / 3)


def calc_legend(grid: Grid) -> Legend:
    num_days  = (grid.max_date - grid.min_date).days
    num_years = num_days / 365.25

    if num_years <= 4:
        year_step  = 0
        month_step = 3
    elif num_years <= 8:
        year_step  = 1
        month_step = 0
    else:
        year_step  = int(num_years / 5)
        month_step = 0

    cur_year  = grid.min_date.year
    cur_month = quarter(grid.min_date.month) * 3 - 2

    while dt.date(cur_year, cur_month, 1) <= grid.min_date:
        cur_year  += year_step
        cur_month += month_step
        if cur_month > 12:
            cur_year += 1
            cur_month = 1

    prev_date = grid.min_date

    max_date = (grid.max_date.year + 1, grid.max_date.month + 3)
    widths   = []
    yyyy_qtr = []
    while (cur_year, cur_month) < max_date:
        cur_date = dt.date(cur_year, cur_month, 1)
        width    = (cur_date - prev_date).days
        widths.append(width)
        qtr = quarter(prev_date.month)
        yyyy_qtr.append((prev_date.year, qtr))

        prev_date = cur_date
        cur_year  += year_step
        cur_month += month_step
        if cur_month > 12:
            cur_year += 1
            cur_month = 1

    legend = []
    for i, ((year, qtr), width) in enumerate(zip(yyyy_qtr, widths)):
        cell_width = round(width * grid.day_width)
        if i == 0:
            legend.append((cell_width, ""))
        elif qtr == 1:
            legend.append((cell_width, "|" + str(year)))
        else:
            legend.append((cell_width, "╷Q" + str(qtr)))

    return legend


def max_score(rows: typ.List[Row]) -> float:
    return max(sum((row.scores for row in rows), []))


def grid_to_text(grid: Grid):
    # legend
    legend = calc_legend(grid)

    timescale_parts = [part_str.ljust(part_width) for part_width, part_str in legend]

    legend_str = "".join(timescale_parts)
    legend_str = legend_str[: grid.row_width]
    if len(legend_str) > 6:
        legend_str = legend_str[:-6] + (legend_str[-6:].rstrip("Q0123456789 "))
    legend_str = legend_str.ljust(grid.row_width)

    min_date_str = grid.min_date.isoformat()
    max_date_str = grid.max_date.isoformat()

    header_line = f" {min_date_str:>55} |" + legend_str + "| " + max_date_str

    # timelines
    chars = " .:!#"
    chars = " ▁▃▄▅▆▇█"
    chars = " ⡀⣀⣄⣤⣦⣶⣷⣿"

    scale = (len(chars) - 1) / max_score(grid.rows)

    lines = [header_line]
    for total_score, author, email, row_scores in grid.rows:
        timeline = "".join(chars[round(s * scale)] for s in row_scores)
        lines.append(f"{author:<25} {email:<30} |{timeline}| {total_score:7.2f}")

    return "\n".join(lines)


def _iter_marker_elems(grid: Grid, text_width: int) -> typ.Iterable[str]:
    legend = calc_legend(grid)

    max_date_x_offset = text_width + grid.row_width
    x_offset          = text_width
    for part_width, part_str in legend:
        legend_elem_str = f"""
        <text x="0" y="0" width="{part_width}">
            <tspan x="{x_offset}" dy="16">{xml_escape(part_str)}</tspan>
        </text>
        """
        x_offset += part_width
        yield legend_elem_str
        if x_offset + 20 > max_date_x_offset:
            return


def _iter_legend_elems(grid: Grid, text_width: int) -> typ.Iterable[str]:
    max_date_x_offset = text_width + grid.row_width
    min_date_x_offset = text_width - 80

    yield f"""
    <text x="0" y="0" width="80">
        <tspan x="{min_date_x_offset}" dy="16">{grid.min_date.isoformat()}|</tspan>
    </text>
    """

    yield from _iter_marker_elems(grid, text_width)

    yield f"""
    <text x="0" y="0" width="80">
        <tspan x="{max_date_x_offset}" dy="16">|{grid.max_date.isoformat()}</tspan>
    </text>
    """


class TextRow(typ.NamedTuple):
    author  : str
    email   : str
    y_offset: int
    scores  : typ.List[float]


def _iter_image_elems(
    grid      : Grid,
    rows      : typ.List[TextRow],
    text_width: int,
    img_width : int,
    max_height: int,
    padding   : int,
) -> typ.Iterable[str]:
    scale = max_height / max_score(grid.rows)

    for i, row in enumerate(rows):
        text_elem_str = f"""
        <text x="0" y="{row.y_offset}" width="{text_width}" height="{max_height}">
            <tspan x="4" dy="14">{xml_escape(row.author)}</tspan>
            <tspan x="4" dy="16">{xml_escape(row.email)}</tspan>
        </text>
        <rect class="bg" x="{text_width}" y="{row.y_offset}" width="{grid.row_width}" height="{max_height}"/>
        """

        x_offset   = text_width
        base_width = max(1, int((grid.row_width - 5) / len(row.scores)))

        timeline_elems = []
        for score in row.scores:
            width = base_width * 5
            if score:
                height = max(3, round(scale * score))
                elem_y = row.y_offset + max_height - height
                elem_x = x_offset - width
                elem   = f'<rect x="{elem_x}" y="{elem_y}" width="{width}" height="{height}" fill="#0009"/>'
                timeline_elems.append(elem.strip())
            x_offset += base_width

        timeline_elems_str = "\n".join(timeline_elems)

        row_str = textwrap.dedent(text_elem_str) + textwrap.dedent(timeline_elems_str)
        yield row_str.strip()

        if i + 1 < len(rows):
            line_y = round(row.y_offset + max_height + padding / 2)
            line   = f'<line x1="4" x2="{img_width - 8}" y1="{line_y}" y2="{line_y}" stroke="#888"></line>'
            yield line


SVG_IMG_TMPL = """
<svg xmlns="http://www.w3.org/2000/svg" width="{img_width}" height="{img_height}" version="1.1">
  <defs>
    <style type='text/css'><![CDATA[
      text, tspan {{
        font-size: 14px;
        font-family: lp-iosevka, 'Iosevka Term SS05', monospace;
        font-weight: normal;
      }}
      rect.bg {{
        fill: #F00B;
        display: none;
      }}
    ]]></style>
  </defs>
  {img_content}
</svg>
"""


def grid_to_svg(grid: Grid):
    padding       = 5
    max_height    = 35
    row_height    = max_height + padding
    legend_height = row_height // 2
    img_height    = legend_height + row_height * len(grid.rows)

    textwidth_chars = 19
    text_rows: typ.List[TextRow] = []
    for i, (_, author, email, row_scores) in enumerate(grid.rows):
        y_offset = i * row_height + 4 + legend_height
        email    = ("<" + email + ">").lower()

        textwidth_chars = max(textwidth_chars, len(author), len(email))
        text_rows.append(TextRow(author, email, y_offset, row_scores))

    text_width = int(textwidth_chars * 8 + padding)
    img_width  = text_width + grid.row_width + 80

    legend_elems = list(_iter_legend_elems(grid, text_width))
    image_elems  = list(_iter_image_elems(grid, text_rows, text_width, img_width, max_height, padding))

    svg_img = SVG_IMG_TMPL.format(
        img_width=img_width,
        img_height=img_height,
        img_content="\n".join(legend_elems + image_elems),
    )
    return textwrap.dedent(svg_img).strip()


def write_stats_svg(stats: StatsByAuthor, svg_path: pl.Path) -> None:
    grid = calc_stats_grid(stats, max_width=120)
    # print()
    # print(grid_to_text(grid))

    grid    = calc_stats_grid(stats, max_width=400)
    svg_img = grid_to_svg(grid)
    with svg_path.open(mode="w", encoding="utf-8") as fobj:
        fobj.write(svg_img)


PROJECT_NAMES = [
    # "pycalver",
    # "bootstrapit",
    "markdown-katex",
    # "markdown-svgbob",
    "markdown-aafigure",
    "lib3to6",
    "litprog",
    # "lexid",
    "imeig",
    "sbk",
]


def main() -> int:
    cwd            = os.getcwd()
    mb_author      = ("Manuel Barkhau", "mbarkhau@gmail.com")
    author_aliases = {
        re.compile(r".*barkhau.*"     , re.IGNORECASE): mb_author,
        re.compile(r".*root@vserver.*", re.IGNORECASE): mb_author,
    }
    for project_name in PROJECT_NAMES:
        project_path = f"../{project_name}/"
        os.chdir(project_path)

        vcs_api = vcs.get_vcs_api()
        assert vcs_api is not None
        commits       = vcs_api.commits()
        overall_stats = calc_overall_stats(commits, author_aliases)

        commits       = vcs_api.commits()
        overall_stats = calc_overall_stats(commits, author_aliases)
        os.chdir(cwd)

        stats_img_path = pl.Path("scratch", project_name + ".svg")
        write_stats_svg(overall_stats, stats_img_path)
    return 0


if __name__ == '__main__':
    import pretty_traceback

    pretty_traceback.install(envvar='ENABLE_PRETTY_TRACEBACK')
    sys.exit(main())
