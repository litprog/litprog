#!/home/mbarkhau/miniconda3/envs/litprog_py39/bin/python
# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2022 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""Create a booklet from an existing pdf.

Usage: python pdf_booklet.py FILE [OPTIONS]

Options:
    --help
    --verbose
    --debug

    --in-path PATH
    --out-path PATH             default: <in_path>_booklet.pdf
    --out-format                default: A4-Landscape
    --max-section-sheets INT    default: 12
    --crop-width PT             default: 0
    --crop-height PT            default: 0
    --autofit/--no-autofit      default: true
"""

import sys
import math
import typing as typ
import logging
import pathlib as pl
import contextlib

import pdfrw

logger = logging.getLogger("pdf_booklet")


MAX_SECTION_SHEETS = 12
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
    'A6'              : (105  * PT_PER_MM  , 148 * PT_PER_MM),
    'A5-Landscape'    : (210  * PT_PER_MM  , 148 * PT_PER_MM),
    'A5-Portrait'     : (148  * PT_PER_MM  , 210 * PT_PER_MM),
    'A5'              : (148  * PT_PER_MM  , 210 * PT_PER_MM),
    'A4-Landscape'    : (297  * PT_PER_MM  , 210 * PT_PER_MM),
    'A4-Portrait'     : (210  * PT_PER_MM  , 297 * PT_PER_MM),
    'A4'              : (210  * PT_PER_MM  , 297 * PT_PER_MM),
    'A3-Portrait'     : (297  * PT_PER_MM  , 420 * PT_PER_MM),
    'A3'              : (297  * PT_PER_MM  , 420 * PT_PER_MM),
    '1of2col-A4'      : (105  * PT_PER_MM  , 297 * PT_PER_MM),
    '1of2col-Letter'  : (4.25 * PT_PER_INCH, 11  * PT_PER_INCH),
    'Half-Letter'     : (5.5  * PT_PER_INCH, 8.5 * PT_PER_INCH),
    'Letter-Landscape': (11   * PT_PER_INCH, 8.5 * PT_PER_INCH),
    'Letter-Portrait' : (8.5  * PT_PER_INCH, 11  * PT_PER_INCH),
    'Letter'          : (8.5  * PT_PER_INCH, 11  * PT_PER_INCH),
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
    pad_center: float
    lx_offset : float
    rx_offset : float


def parse_output_parameters(in_page_width: float, in_page_height: float, out_format: str) -> OutputParameters:
    # NOTE (mb 2021-03-04): Can we figure out the bounds of the inner content
    #   and scale + translate each page to be in a well defined content box
    #   in the output page?
    # NOTE (mb 2021-03-19): Nope, we can't, at least not easilly with PyPDF2.
    #   A possible alternative is PyMuPDF: https://pymupdf.readthedocs.io/

    # pylint: disable=too-many-locals

    out_sheet_width, out_sheet_height = PAPER_FORMATS_PT[out_format]
    if out_sheet_width < out_sheet_height:
        errmsg = f"Invalid out_format={out_format}. Landscape format required."
        raise ValueError(errmsg)

    out_page_width  = out_sheet_width / 2
    out_page_height = out_sheet_height

    x_scale = out_page_width  / in_page_width  * 0.98
    y_scale = out_page_height / in_page_height * 0.98

    scale = min(x_scale, y_scale)

    scaled_page_width  = in_page_width  * scale
    scaled_page_height = in_page_height * scale

    pad_center = (out_sheet_width / 2) - scaled_page_width
    lx_offset  = round(0 - pad_center)
    rx_offset  = round((out_sheet_width / 2) + pad_center)

    _iw_mm = round(in_page_width      / PT_PER_MM)
    _ih_mm = round(in_page_height     / PT_PER_MM)
    _sw_mm = round(scaled_page_width  / PT_PER_MM)
    _sh_mm = round(scaled_page_height / PT_PER_MM)
    _ow_mm = round(out_sheet_width    / PT_PER_MM)
    _oh_mm = round(out_sheet_height   / PT_PER_MM)

    logger.info("OutputParameters")
    logger.info(f"sheet scale: {scale:5.2f}x")
    logger.info(f"         in: {_iw_mm}mm x {_ih_mm}mm -> {_sw_mm}mm x {_sh_mm}mm (2x)")
    logger.info(f"        out: {_ow_mm}mm x {_oh_mm}mm")
    logger.info(f"    offsets: {lx_offset}mm {rx_offset}mm")

    return OutputParameters(
        out_sheet_width,
        out_sheet_height,
        scale,
        pad_center,
        lx_offset,
        rx_offset,
    )


PdfPage = typ.Any


@contextlib.contextmanager
def fit_pdf(in_path: pl.Path, crop_width: int, crop_height: int, out_format: str) -> typ.Iterator[pl.Path]:
    import PyPDF2 as pypdf

    tmp_path = in_path.parent / (in_path.name + ".crop_tmp")

    out_width, out_height = PAPER_FORMATS_PT[out_format]

    if out_width < out_height:
        out_height, out_width = (out_width, out_height)

    tgt_width  = round(out_width / 2)
    tgt_height = round(out_height)

    with in_path.open(mode="rb") as in_fobj:
        reader = pypdf.PdfFileReader(in_fobj)
        pages  = list(reader.pages)
        page0  = pages[0]

        media_box = page0.mediaBox

        in_page_width  = float(media_box.getWidth())
        in_page_height = float(media_box.getHeight())

        scale         = tgt_height / in_page_height
        scaled_width  = in_page_width  * scale
        scaled_height = in_page_height * scale

        logger.info(f"page scale={scale:.3f}x")

        translate_x = round((tgt_width  - (scaled_width  - crop_width )) / 2)
        translate_y = round((tgt_height - (scaled_height - crop_height)) / 2)

        logger.info(f"page padding: {translate_x} {translate_y}")

        output = pypdf.PdfFileWriter()

        for in_page in pages:
            out_page = output.addBlankPage(width=tgt_width, height=tgt_height)

            if abs(1 - scale) > 0.02:
                out_page.mergeScaledTranslatedPage(
                    in_page, scale=scale, tx=translate_x, ty=translate_y, expand=False
                )
            else:
                out_page.mergeTranslatedPage(in_page, tx=translate_x, ty=translate_y, expand=False)

            out_page.compressContentStreams()

        with tmp_path.open(mode='wb') as out_fobj:
            output.write(out_fobj)

    yield tmp_path

    tmp_path.unlink()


def _create(
    in_path          : pl.Path,
    out_path         : pl.Path,
    out_format       : str,
    max_section_pages: int,
) -> pl.Path:
    in_pdf = pdfrw.PdfReader(in_path)

    in_pages  = in_pdf.pages
    firstpage = in_pages[0]

    _x0, _y0, in_page_width, in_page_height = map(float, firstpage["/MediaBox"])
    assert _x0 == 0
    assert _y0 == 0

    out_params = parse_output_parameters(in_page_width, in_page_height, out_format)

    num_sections      = math.ceil(len(in_pages) / max_section_pages)
    max_section_pages = len(in_pages) // num_sections
    max_section_pages = max_section_pages + (4 - max_section_pages) % 4

    in_sections: list[list[PdfPage]] = [[]]
    for in_page in in_pages:
        if len(in_sections[-1]) == max_section_pages:
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
            result[-1].x += out_params.lx_offset
        if r_page:
            result.add(r_page)
            result[-1].x += out_params.rx_offset
        return result.render()

    blank_page = PageMerge().render()
    out_pages  = []
    for i, in_section in enumerate(in_sections):
        if i > 0:
            out_pages.append(blank_page)
            out_pages.append(blank_page)

        in_section += [None] * (-len(in_section) % 4)
        assert len(in_section) % 4 == 0

        while len(in_section) > 0:
            out_pages.append(fixpage(in_section.pop(), in_section.pop(0)))
            out_pages.append(fixpage(in_section.pop(0), in_section.pop()))

    out_pdf = pdfrw.PdfWriter(out_path)
    out_pdf = out_pdf.addpages(out_pages)
    out_pdf.write()

    logger.info(f"Wrote to '{out_path}'")

    return out_path


def create(
    in_path           : pl.Path,
    out_path          : typ.Optional[pl.Path] = None,
    out_format        : str  = 'A4-Landscape',
    max_section_sheets: int  = MAX_SECTION_SHEETS,
    crop_width        : int  = 0,
    crop_height       : int  = 0,
    autofit           : bool = True,
) -> pl.Path:
    assert in_path.exists(), f"No such file: {in_path}"

    if out_format not in PAPER_FORMATS_PT:
        valid_formats = list(PAPER_FORMATS_PT)
        errmsg        = f"Invalid out_format {out_format}. Valid formats: {valid_formats}"
        raise AssertionError(errmsg)

    max_section_pages = max_section_sheets * 4

    if out_path is None:
        ext          = in_path.suffixes[-1]
        out_filename = (in_path.name[: -len(ext)] + "_booklet") + ext
        _out_path    = in_path.parent / out_filename
    else:
        _out_path = out_path

    if autofit or crop_width or crop_height:
        with fit_pdf(in_path, crop_width, crop_height, out_format) as tmp_path:
            return _create(tmp_path, _out_path, out_format, max_section_pages)
    else:
        return _create(in_path, _out_path, out_format, max_section_pages)


def iter_kwargs(args: list[str]) -> typ.Iterator[tuple[str, typ.Any]]:
    idx = len(args) - 1
    key: typ.Optional[str] = None
    val: typ.Optional[str] = None
    while idx >= 0:
        arg = args[idx]

        if arg.startswith("--"):
            if arg.startswith("--no-"):
                key      = arg[5:]
                flag_val = False
            else:
                key      = arg[2:]
                flag_val = True

            key = key.replace("-", "_")

            if val is None:
                yield (key, flag_val)
            elif key.endswith("_path"):
                yield (key, pl.Path(val))
            else:
                try:
                    yield (key, int(val))
                except ValueError:
                    yield (key, val)
            val = None
        else:
            val = arg

        idx -= 1


def main(args: list[str]) -> int:
    if "-h" in args or "--help" in args:
        print(__doc__)
        return 0

    kwargs: typ.Dict[str, typ.Any] = {}

    if len(args) == 1:
        kwargs = {'in_path': args[0]}
    else:
        kwargs = dict(iter_kwargs(args))

    is_debug   = kwargs.pop("debug"  , False)
    is_verbose = kwargs.pop("verbose", False)

    logging.basicConfig()
    root_logger = logging.getLogger()
    if is_debug:
        root_logger.setLevel(logging.DEBUG)
    elif is_verbose:
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.WARNING)

    try:
        create(**kwargs)
        return 0
    except AssertionError as err:
        print(err)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
