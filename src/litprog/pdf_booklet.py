# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import sys
import math
import time
import typing as typ
import logging
import pathlib as pl

import PyPDF2 as pdf

logger = logging.getLogger(__name__)


MAX_BOOKLET_SHEETS = 13
PAGES_PER_SHEET    = 4

PT_PER_INCH = 72
PT_PER_MM   = PT_PER_INCH / 25.4


BOOKLET_FORMAT_MAPPING = {
    # out_format, page_order, scale, margin
    'A6-Portrait'    : ('A5-Landscape'    , 'booklet', 0 * PT_PER_MM),
    'A5-Portrait'    : ('A4-Landscape'    , 'booklet', 0 * PT_PER_MM),
    'A4-Portrait'    : ('A4-Landscape'    , 'booklet', 0 * PT_PER_MM),
    'A3-Portrait'    : ('A4-Landscape'    , 'booklet', 0 * PT_PER_MM),
    'Half-Letter'    : ('Letter-Landscape', 'booklet', 0 * PT_PER_MM),
    '1of2col-A4'     : ('A4-Portrait'     , 'paper'  , 0 * PT_PER_MM),
    '1of2col-Letter' : ('Letter-Portrait' , 'paper'  , 0 * PT_PER_MM),
    'Letter-Portrait': ('A4-Landscape'    , 'booklet', -5 * PT_PER_MM),
}


PAPER_FORMATS_PT = {
    'A6-Portrait'     : (105  * PT_PER_MM  , 148 * PT_PER_MM),
    'A5-Landscape'    : (210  * PT_PER_MM  , 148 * PT_PER_MM),
    'A5-Portrait'     : (148  * PT_PER_MM  , 210 * PT_PER_MM),
    'A4-Landscape'    : (297  * PT_PER_MM  , 210 * PT_PER_MM),
    'A4-Portrait'     : (210  * PT_PER_MM  , 297 * PT_PER_MM),
    'A3-Portrait'     : (297  * PT_PER_MM  , 420 * PT_PER_MM),
    '1of2col-A4'      : (105  * PT_PER_MM  , 297 * PT_PER_MM),
    '1of2col-Letter'  : (4.25 * PT_PER_INCH, 11  * PT_PER_INCH),
    'Half-Letter'     : (5.5  * PT_PER_INCH, 8.5 * PT_PER_INCH),
    'Letter-Landscape': (11   * PT_PER_INCH, 8.5 * PT_PER_INCH),
    'Letter-Portrait' : (8.5  * PT_PER_INCH, 11  * PT_PER_INCH),
}


# https://helpx.adobe.com/acrobat/kb/print-booklets-acrobat-reader.html
# https://tex.stackexchange.com/questions/60934/


def calc_booklet_page_counts(
    total_pages: int, max_sheets: int = MAX_BOOKLET_SHEETS
) -> typ.List[int]:
    total_sheets = math.ceil(total_pages  / PAGES_PER_SHEET)
    num_booklets = math.ceil(total_sheets / max_sheets)

    # spb: sheets per booklet
    # ppb: pages per booklet

    target_ppb = total_pages / num_booklets
    spb        = math.floor(target_ppb / PAGES_PER_SHEET)
    ppb        = spb * PAGES_PER_SHEET

    if ppb * num_booklets < total_pages - PAGES_PER_SHEET:
        ppb += PAGES_PER_SHEET

    if ppb * num_booklets < total_pages:
        # Add extra pages to the last booklet
        last_ppb = ppb + PAGES_PER_SHEET
    else:
        last_ppb = ppb

    return [ppb] * (num_booklets - 1) + [last_ppb]


# Glossary
# Booklet: Multiple sheets that get bound together
# Sheet: Duplex printed piece of paper, with four pages
# Half-Sheet: One face of a sheet with two pages
# Page: One half of one side of a sheet

_BOOKLET_PAGE_NUMBERING_ILLUSTRATION = r"""

         Booklet 1        Booklet 2

         +       +        +       +
    8   /|----->/|   16  /|----->/|
    -->/ | 6   / |   -->/ | 14  / |
      / 7| -->/ 5|     /15| -->/13|
     +   |   +   |    +   |   +   |
     |\  |   |\  |    |\  |   |\  |
     | \/    | \/     | \/    | \/
     |  \    |  \     |  \    |  \
     |   |   |   |    |   |   |   |
     |  1|   |  3|    |  9|   | 11|
      \  |  2 \  |  4  \  | 10 \  | 12
       \ |<--  \ |<--   \ |<--  \ |<--
        \|----->\|       \|----->\|
         +       +        +       +
"""


def booklet_page_layout(
    total_pages: int, max_sheets: int = MAX_BOOKLET_SHEETS
) -> typ.Tuple[typ.List[int], typ.List[int]]:
    booklet_page_counts = calc_booklet_page_counts(total_pages, max_sheets)

    booklet_index_by_page     : typ.List[int] = []
    booklet_page_index_by_page: typ.List[int] = []

    doc_page_offset = 0
    for booklet_index, booklet_page_count in enumerate(booklet_page_counts):
        left_doc_page_index  = doc_page_offset + booklet_page_count - 1
        right_doc_page_index = doc_page_offset
        while right_doc_page_index < left_doc_page_index:
            booklet_page_index_by_page.append(left_doc_page_index)
            booklet_page_index_by_page.append(right_doc_page_index)
            booklet_page_index_by_page.append(right_doc_page_index + 1)
            booklet_page_index_by_page.append(left_doc_page_index - 1)
            booklet_index_by_page += [booklet_index] * 4
            left_doc_page_index -= 2
            right_doc_page_index += 2

        doc_page_offset += booklet_page_count

    assert len(booklet_page_index_by_page) == len(booklet_index_by_page)
    assert len(booklet_page_index_by_page) == len(set(booklet_page_index_by_page))

    return booklet_page_index_by_page, booklet_index_by_page


def get_format_id(
    page_width_pt : float,
    page_height_pt: float,
    epsilon_pt    : float = 2.0,
) -> typ.Optional[str]:
    for format_id, (fmt_width_pt, fmt_height_pt) in PAPER_FORMATS_PT.items():
        delta = abs(fmt_width_pt - page_width_pt) + abs(fmt_height_pt - page_height_pt)
        if delta < epsilon_pt:
            return format_id

    return None


PDFPage = typ.Any

MediaBox = typ.Any

PageIndexMapping = typ.List[typ.Tuple[int, int]]


class OutputParameters(typ.NamedTuple):

    scale : float
    width : float
    height: float
    trim_x: float
    trim_y: float

    page_order    : str
    center_spacing: float


def _init_output_parameters(media_box: MediaBox, rescale: float) -> OutputParameters:
    in_page_width  = float(media_box.getWidth())
    in_page_height = float(media_box.getHeight())
    in_format_id   = get_format_id(in_page_width, in_page_height)
    if in_format_id is None:
        in_page_width_mm  = round(in_page_width  / PT_PER_MM)
        in_page_height_mm = round(in_page_height / PT_PER_MM)

        err_msg = f"Unknown page format: {in_page_width_mm}mm x {in_page_height_mm}mm"
        raise ValueError(err_msg)

    (out_format_id, page_order, center_margin) = BOOKLET_FORMAT_MAPPING[in_format_id]
    logger.info(f"Converting 2x{in_format_id} -> {out_format_id}")

    out_width, out_height = PAPER_FORMATS_PT[out_format_id]

    scale_w = round((out_width / 2) / in_page_width, 2)
    scale_h = round(out_height / in_page_height, 2)
    scale   = min(scale_h, scale_w)
    logger.info(f"scale={scale} scale_w={scale_w} scale_h={scale_h}")
    scale = scale_h
    if scale < 1:
        logger.info(f"scaling down by {1/scale:5.2f}x")
    elif scale > 1:
        logger.info(f"scaling up by {scale}x")

    rescale_pct = 100 * (1 - rescale)
    if rescale < 1:
        logger.info(f"adding padding of {abs(rescale_pct):3.2f}%")
    elif rescale > 1:
        logger.info(f"trimming by {abs(rescale_pct):5.2f}%")

    scale = scale * rescale

    trim_factor = (rescale - 1) / 2
    trim_x      = 0.5 * out_width  * trim_factor
    trim_y      = 0.6 * out_height * trim_factor
    # TODO: option for center spacing
    center_spacing = out_width * 0.005
    center_spacing = center_margin

    return OutputParameters(
        scale, out_width, out_height, trim_x, trim_y, page_order, center_spacing
    )


def _create_sheets(
    in_pages            : typ.List[PDFPage],
    output              : pdf.PdfFileWriter,
    out_coords          : OutputParameters,
    half_page_to_in_page: PageIndexMapping,
) -> typ.List[PDFPage]:
    sheet_indexes = {
        half_page_index // 2 for in_page_index, half_page_index in half_page_to_in_page
    }
    out_sheets = [
        output.addBlankPage(width=out_coords.width, height=out_coords.height) for _ in sheet_indexes
    ]

    for half_page_index, in_page_index in half_page_to_in_page:
        if len(in_pages) - 1 < in_page_index:
            continue

        in_page = in_pages[in_page_index]

        out_sheet = out_sheets[half_page_index // 2]
        if half_page_index % 2 == 0:
            x_offset = 0 - out_coords.center_spacing
        else:
            x_offset = (out_coords.width / 2) + out_coords.center_spacing

        translate_x = x_offset - out_coords.trim_x
        translate_y = 0        - out_coords.trim_y

        tzero = time.time()

        if out_coords.scale == 1:
            out_sheet.mergeTranslatedPage(in_page, tx=translate_x, ty=translate_y, expand=False)
        else:
            out_sheet.mergeScaledTranslatedPage(
                in_page, scale=out_coords.scale, tx=translate_x, ty=translate_y, expand=False
            )

        duration = int((time.time() - tzero) * 1000)

        sheet_index = half_page_index % 2
        logger.debug(f"booklet page: {half_page_index:>2} sheet: {sheet_index:>2} {duration:>5}ms")

    return out_sheets


def create(in_path: pl.Path, out_path: typ.Optional[pl.Path] = None) -> pl.Path:
    # TODO: option for page scale
    # rescale = 1.33
    rescale = 1.00

    max_sheets = MAX_BOOKLET_SHEETS

    if out_path is None:
        ext          = "".join(in_path.suffixes)
        out_filename = (in_path.name[: -len(ext)] + "_booklet") + ext
        _out_path    = in_path.parent / out_filename
    else:
        _out_path = out_path

    output = pdf.PdfFileWriter()

    with in_path.open(mode="rb") as in_fobj:
        reader    = pdf.PdfFileReader(in_fobj)
        media_box = reader.getPage(0).mediaBox

        output_params = _init_output_parameters(media_box, rescale)

        in_pages = list(reader.pages)

        if output_params.page_order == 'booklet':
            layout = booklet_page_layout(len(in_pages), max_sheets=max_sheets)
            booklet_page_indexes, _booklet_index_by_page = layout
            half_page_to_in_page = list(enumerate(booklet_page_indexes))
        else:
            half_page_to_in_page = [
                (half_page_index, half_page_index) for half_page_index in range(len(in_pages))
            ]

        out_sheets = _create_sheets(in_pages, output, output_params, half_page_to_in_page)
        tzero      = time.time()
        for out_sheet in out_sheets:
            out_sheet.compressContentStreams()
        compression_time = time.time() - tzero
        logger.debug(f"compression time: {compression_time}")

        with _out_path.open(mode="wb") as out_fobj:
            output.write(out_fobj)

    return _out_path


def main() -> int:
    create(in_path=pl.Path(sys.argv[1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
