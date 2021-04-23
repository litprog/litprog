#!/home/mbarkhau/miniconda3/envs/litprog_py38/bin/python
# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import sys
import math
import time
import typing as typ
import logging
import pathlib as pl

import PyPDF2 as pypdf

logger = logging.getLogger("pdf_booklet")


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


def calc_booklet_page_counts(total_pages: int, max_sheets: int = MAX_BOOKLET_SHEETS) -> typ.List[int]:
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
    best_format_id: typ.Optional[str] = None
    best_delta = 999999

    for format_id, (fmt_width_pt, fmt_height_pt) in PAPER_FORMATS_PT.items():
        delta = abs(fmt_width_pt - page_width_pt) + abs(fmt_height_pt - page_height_pt)
        if delta < best_delta:
            best_format_id = format_id

        if delta < epsilon_pt:
            return format_id

    print(best_format_id, delta)
    return None


PDFReader = typ.Any

PDFPage = typ.Any

MediaBox = typ.Any

PageIndexMapping = typ.List[typ.Tuple[int, int]]


class OutputParameters(typ.NamedTuple):

    page_order: str
    width     : float
    height    : float

    scale     : float
    pad_x     : float
    pad_y     : float
    pad_center: float


def _init_output_parameters(reader: PDFReader, out_sheet_format: str) -> OutputParameters:
    # NOTE (mb 2021-03-04): Can we figure out the bounds of the inner content
    #   and scale + translate each page to be in a well defined content box
    #   in the output page?
    # NOTE (mb 2021-03-19): Nope, we can't, at least not easilly with PyPDF2.
    #   A possible alternative is PyMuPDF: https://pymupdf.readthedocs.io/

    # pylint: disable=too-many-locals

    media_box = reader.getPage(0).mediaBox

    in_page_width  = float(media_box.getWidth())
    in_page_height = float(media_box.getHeight())

    out_sheet_width, out_sheet_height = PAPER_FORMATS_PT[out_sheet_format]
    if out_sheet_width < out_sheet_height:
        errmsg = f"Invalid out_sheet_format={out_sheet_format}. Landscape format required."
        raise ValueError(errmsg)

    out_page_width  = out_sheet_width / 2
    out_page_height = out_sheet_height

    x_scale = out_page_width  / in_page_width
    y_scale = out_page_height / in_page_height

    scale = min(x_scale, y_scale)

    scaled_page_width  = in_page_width  * scale
    scaled_page_height = in_page_height * scale

    x_padding = out_page_width  - scaled_page_width
    y_padding = out_page_height - scaled_page_height

    pad_center = x_padding / 4
    pad_center = 0
    pad_x      = (x_padding - pad_center) / 2
    pad_y      = y_padding / 2

    _iw_mm = round(in_page_width      / PT_PER_MM)
    _ih_mm = round(in_page_height     / PT_PER_MM)
    _sw_mm = round(scaled_page_width  / PT_PER_MM)
    _sh_mm = round(scaled_page_height / PT_PER_MM)
    _ow_mm = round(out_sheet_width    / PT_PER_MM)
    _oh_mm = round(out_sheet_height   / PT_PER_MM)
    logger.info("OutputParameters")
    logger.info(f"    scale: {scale:5.2f}x")
    logger.info(f"    in : {_iw_mm}mm x {_ih_mm}mm -> {_sw_mm}mm x {_sh_mm}mm (2x)")
    logger.info(f"    out: {_ow_mm}mm x {_oh_mm}mm")

    return OutputParameters(
        'booklet',
        out_sheet_width,
        out_sheet_height,
        scale,
        pad_x,
        pad_y,
        pad_center,
    )


def _create_sheets(
    in_pages            : typ.List[PDFPage],
    output              : pypdf.PdfFileWriter,
    out_coords          : OutputParameters,
    half_page_to_in_page: PageIndexMapping,
) -> typ.List[PDFPage]:
    sheet_indexes = {half_page_index // 2 for in_page_index, half_page_index in half_page_to_in_page}
    out_sheets    = [
        output.addBlankPage(width=out_coords.width, height=out_coords.height) for _ in sheet_indexes
    ]

    for half_page_index, in_page_index in half_page_to_in_page:
        if len(in_pages) - 1 < in_page_index:
            continue

        in_page = in_pages[in_page_index]

        out_sheet = out_sheets[half_page_index // 2]
        if half_page_index % 2 == 0:
            x_offset = 0 - out_coords.pad_center
        else:
            x_offset = (out_coords.width / 2) + out_coords.pad_center

        translate_x = x_offset + out_coords.pad_x
        translate_y = 0        + out_coords.pad_y

        tzero = time.time()

        if abs(out_coords.scale - 1) < 0.01:
            out_sheet.mergeTranslatedPage(in_page, tx=translate_x, ty=translate_y, expand=False)
        else:
            out_sheet.mergeScaledTranslatedPage(
                in_page, scale=out_coords.scale, tx=translate_x, ty=translate_y, expand=False
            )

        duration = int((time.time() - tzero) * 1000)

        sheet_index = half_page_index % 2
        logger.debug(f"booklet page: {half_page_index:>2} sheet: {sheet_index:>2} {duration:>5}ms")

    return out_sheets


def create(
    in_path         : pl.Path,
    out_path        : typ.Optional[pl.Path] = None,
    out_sheet_format: str = 'A4-Landscape',
) -> pl.Path:
    assert out_sheet_format in PAPER_FORMATS_PT

    max_sheets = MAX_BOOKLET_SHEETS

    if out_path is None:
        ext          = in_path.suffixes[-1]
        out_filename = (in_path.name[: -len(ext)] + "_booklet") + ext
        _out_path    = in_path.parent / out_filename
    else:
        _out_path = out_path

    output = pypdf.PdfFileWriter()

    with in_path.open(mode="rb") as in_fobj:
        reader = pypdf.PdfFileReader(in_fobj)

        output_params = _init_output_parameters(reader, out_sheet_format)

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

    logger.info(f"Wrote to '{_out_path}'")

    return _out_path


def main() -> int:
    logging.basicConfig()
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    create(in_path=pl.Path(sys.argv[1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
