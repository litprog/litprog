#!/home/mbarkhau/miniconda3/envs/litprog_py38/bin/python
# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import sys
import typing as typ
import logging
import pathlib as pl

import pdfrw

logger = logging.getLogger("pdf_booklet")


MAX_SECTION_PAGES = 48
PAGES_PER_SHEET   = 4

assert MAX_SECTION_PAGES % PAGES_PER_SHEET == 0

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


# Glossary
# Section: Multiple sheets that get bound together
# Bifolio: Duplex printed piece of paper, with two sheets and four pages
# Sheet: One face of a bifolio with two pages
# Page: One half of one side of a sheet

_BOOKLET_PAGE_NUMBERING_ILLUSTRATION = r"""

       Section 1        Section 2

       +       +        +       +
  8   /|  6   /|   16  /|      /|
  -->/ |  -->/ |   -->/ | 14  / |
    / 7|    / 5|     /15| -->/13|
   +   |   +   |    +   |   +   |
   |\  |   |\  |    |\  |   |\  |
   | \/    | \/     | \/    | \/
   |  \    |  \     |  \    |  \
   |   |   |   |    |   |   |   |
   |  1|   |   |    |  9|   | 11|
    \  | 3  \  |     \  | 10 \  | 12
     \ | --->\ |      \ |<--  \ |<--
      \|<-- 2 \|<-- 4  \|      \|
       +       +        +       +
"""


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


class OutputParameters(typ.NamedTuple):

    width : float
    height: float

    scale     : float
    pad_x     : float
    pad_y     : float
    pad_center: float


def parse_output_parameters(
    in_page_width: float, in_page_height: float, out_sheet_format: str
) -> OutputParameters:
    # NOTE (mb 2021-03-04): Can we figure out the bounds of the inner content
    #   and scale + translate each page to be in a well defined content box
    #   in the output page?
    # NOTE (mb 2021-03-19): Nope, we can't, at least not easilly with PyPDF2.
    #   A possible alternative is PyMuPDF: https://pymupdf.readthedocs.io/

    # pylint: disable=too-many-locals

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
        out_sheet_width,
        out_sheet_height,
        scale,
        pad_x,
        pad_y,
        pad_center,
    )


PdfPage = typ.Any


def create(
    in_path         : pl.Path,
    out_path        : typ.Optional[pl.Path] = None,
    out_sheet_format: str = 'A4-Landscape',
    page_order      : str = 'booklet',
) -> pl.Path:
    assert out_sheet_format in PAPER_FORMATS_PT

    in_pdf    = pdfrw.PdfReader(in_path)
    in_pages  = in_pdf.pages
    firstpage = in_pages[0]

    _x0, _y0, in_page_width, in_page_height = map(float, firstpage["/MediaBox"])
    assert _x0 == 0
    assert _y0 == 0

    out_params = parse_output_parameters(in_page_width, in_page_height, out_sheet_format)
    if abs(out_params.scale - 1) > 0.02:
        # pylint: disable=import-outside-toplevel ; improves import time
        from litprog import pdf_booklet_old

        result_path = pdf_booklet_old.create(in_path, out_path, out_sheet_format, page_order)
        return result_path

    lx_offset = 0 - out_params.pad_center
    rx_offset = (out_params.width / 2) + out_params.pad_center

    in_sections: list[list[PdfPage]] = [[]]
    for in_page in in_pages:
        if len(in_sections[-1]) == MAX_SECTION_PAGES:
            in_sections.append([])
        in_sections[-1].append(in_page)

    class PageMerge(pdfrw.PageMerge):
        @property
        def xobj_box(self):
            return pdfrw.PdfArray((0, 0, out_params.width, out_params.height))

    def fixpage(l_page: pdfrw.PdfDict, r_page: pdfrw.PdfDict) -> pdfrw.PdfDict:
        result = PageMerge()
        if l_page:
            result.add(l_page)
            result[-1].x += lx_offset
        if r_page:
            result.add(r_page)
            result[-1].x += rx_offset

        return result.render()

    out_pages = []
    for in_section in in_sections:
        in_section += [None] * (-len(in_section) % 4)
        assert len(in_section) % 4 == 0

        while len(in_section) > 0:
            out_pages.append(fixpage(in_section.pop(), in_section.pop(0)))
            out_pages.append(fixpage(in_section.pop(0), in_section.pop()))

    if out_path is None:
        ext          = in_path.suffixes[-1]
        out_filename = (in_path.name[: -len(ext)] + "_booklet") + ext
        _out_path    = in_path.parent / out_filename
    else:
        _out_path = out_path

    out_pdf = pdfrw.PdfWriter(_out_path)
    out_pdf = out_pdf.addpages(out_pages)
    out_pdf.write()

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
