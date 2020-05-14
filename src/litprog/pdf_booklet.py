import sys
import math
import time
import logging
import typing as typ
import pathlib2 as pl

import PyPDF2 as pdf

log = logging.getLogger(__name__)


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

# https://mbarkhau.keybase.pub/asciigrid/#vvO;EOAOA;AAAAADiBlApFBcgDLMCCCCCJLMgKVapFBhCAMAgSAhEAAkKVYiMBhCgMiRibrDBADAbizDAZiDgGVZjLVXgdMKizlAmAjCgdAKLiSkBqEhbAglhKjCqEh6VhGgFXiDkGgBVgWi6nJibAdnHBAAKhHAWkBYjLAVUkBWggAKAMICClAuAhfAKMCCCCCJKMhKqEibADkRlAnH

_booklet_page_numbering_illustration = r"""

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


def get_format_id(page_width_pt: int, page_height_pt: int) -> typ.Optional[str]:
    for format_id, (fmt_width_pt, fmt_height_pt) in PAPER_FORMATS_PT.items():
        delta = abs(fmt_width_pt - page_width_pt) + abs(fmt_height_pt - page_height_pt)
        if delta < 2:
            return format_id

    return None


def create(in_path: pl.Path, out_path: typ.Optional[pl.Path]) -> pl.Path:
    # TODO: option for page scale
    # rescale = 1.33
    rescale     = 1.00
    rescale_pct = 100 * (1 - rescale)

    max_sheets = MAX_BOOKLET_SHEETS

    if out_path is None:
        ext          = "".join(in_path.suffixes)
        out_filename = (in_path.name[: -len(ext)] + "_booklet") + ext
        _out_path    = in_path.parent / out_filename
    else:
        _out_path = out_path

    output = pdf.PdfFileWriter()

    with in_path.open(mode="rb") as in_fh:
        reader    = pdf.PdfFileReader(in_fh)
        media_box = reader.getPage(0).mediaBox

        in_page_width  = float(media_box.getWidth())
        in_page_height = float(media_box.getHeight())
        in_format_id   = get_format_id(in_page_width, in_page_height)
        if in_format_id is None:
            in_page_width_mm  = round(in_page_width  / PT_PER_MM)
            in_page_height_mm = round(in_page_height / PT_PER_MM)

            err_msg = f"Unknown page format: {in_page_width_mm}mm x {in_page_height_mm}mm"
            raise Exception(err_msg)

        (out_format_id, page_order, center_margin) = BOOKLET_FORMAT_MAPPING[in_format_id]
        log.info(f"Converting 2x{in_format_id} -> {out_format_id}")

        out_width, out_height = PAPER_FORMATS_PT[out_format_id]

        scale_w = round((out_width / 2) / in_page_width, 2)
        scale_h = round(out_height / in_page_height, 2)
        scale = min(scale_h, scale_w)
        log.info(f"{!scale} {!scale_w} {!scale_h}")
        scale = scale_h
        if scale < 1:
            log.info(f"scaling down by {1/scale:5.2f}x")
        elif scale > 1:
            log.info(f"scaling up by {scale}x")

        if rescale < 1:
            log.info(f"adding padding of {abs(rescale_pct):3.2f}%")
        elif rescale > 1:
            log.info(f"trimming by {abs(rescale_pct):5.2f}%")

        scale = scale * rescale

        trim_factor = (rescale - 1) / 2
        trim_x      = 0.5 * out_width  * trim_factor
        trim_y      = 0.6 * out_height * trim_factor
        # TODO: option for center spacing
        center_spacing = out_width * 0.005
        center_spacing = center_margin

        in_pages = list(reader.pages)

        if page_order == 'booklet':
            layout = booklet_page_layout(len(in_pages), max_sheets=max_sheets)
            booklet_page_indexes, booklet_index_by_page = layout
            half_page_to_in_page = list(enumerate(booklet_page_indexes))
        else:
            half_page_to_in_page = [
                (half_page_index, half_page_index) for half_page_index in range(len(in_pages))
            ]

        sheet_indexes = set(
            half_page_index // 2 for in_page_index, half_page_index in half_page_to_in_page
        )
        out_sheets = [
            output.addBlankPage(width=out_width, height=out_height) for _ in sheet_indexes
        ]

        for half_page_index, in_page_index in half_page_to_in_page:
            if len(in_pages) - 1 < in_page_index:
                continue

            in_page = in_pages[in_page_index]

            out_sheet = out_sheets[half_page_index // 2]
            if half_page_index % 2 == 0:
                x_offset = 0 - center_spacing
            else:
                x_offset = (out_width / 2) + center_spacing

            tx    = x_offset - trim_x
            ty    = 0        - trim_y
            tzero = time.time()
            if scale == 1:
                out_sheet.mergeTranslatedPage(in_page, tx=tx, ty=ty, expand=False)
            else:
                out_sheet.mergeScaledTranslatedPage(
                    in_page, scale=scale, tx=tx, ty=ty, expand=False
                )
            log.debug(
                f"booklet page {half_page_index:>2}", half_page_index % 2, time.time() - tzero
            )

        tzero = time.time()
        for out_sheet in out_sheets:
            out_sheet.compressContentStreams()
        compression_time = time.time() - tzero
        log.debug(f"compression time: {compression_time}")

        with _out_path.open(mode="wb") as out_fh:
            output.write(out_fh)

    return _out_path


def main() -> int:
    create(in_path=pl.Path(sys.argv[1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
