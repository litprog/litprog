import math
import time
import typing as typ
import logging
import pathlib as pl

import PyPDF2 as pypdf

from . import pdf_booklet

logger = logging.getLogger("pdf_booklet")


PDFPage = typ.Any

PageIndexMapping = list[tuple[int, int]]

MAX_SECTION_PAGES = 48
PAGES_PER_SHEET   = 4

assert MAX_SECTION_PAGES % PAGES_PER_SHEET == 0


def _create_sheets(
    in_pages  : list[PDFPage],
    output    : pypdf.PdfFileWriter,
    out_params: pdf_booklet.OutputParameters,
    page_order: str,
) -> list[PDFPage]:
    half_page_to_in_page = _booklet_page_indexes(len(in_pages), page_order)
    sheet_indexes        = {in_page_index // 2 for _, in_page_index in half_page_to_in_page}
    out_sheets           = [
        output.addBlankPage(width=out_params.width, height=out_params.height) for _ in sheet_indexes
    ]
    for half_page_index, in_page_index in half_page_to_in_page:
        if in_page_index < len(in_pages):
            in_page = in_pages[in_page_index]

            out_sheet = out_sheets[half_page_index // 2]
            if half_page_index % 2 == 0:
                x_offset = 0 - out_params.pad_center
            else:
                x_offset = (out_params.width / 2) + out_params.pad_center

            translate_x = x_offset + out_params.pad_x
            translate_y = 0        + out_params.pad_y

            tzero = time.time()

            if abs(out_params.scale - 1) < 0.02:
                out_sheet.mergeTranslatedPage(in_page, tx=translate_x, ty=translate_y, expand=False)
            else:
                out_sheet.mergeScaledTranslatedPage(
                    in_page, scale=out_params.scale, tx=translate_x, ty=translate_y, expand=False
                )

            duration = int((time.time() - tzero) * 1000)

            sheet_index = half_page_index % 2
            logger.debug(f"booklet page: {half_page_index:>2} sheet: {sheet_index:>2} {duration:>5}ms")

    return out_sheets


def calc_section_page_counts(total_pages: int, max_pages: int = MAX_SECTION_PAGES) -> list[int]:
    total_sheets = math.ceil(total_pages  / PAGES_PER_SHEET)
    num_sections = math.ceil(total_sheets / (max_pages // 4))

    # sps: sheets per section
    # pps: pages per section

    target_ppb = total_pages / num_sections
    sps        = math.floor(target_ppb / PAGES_PER_SHEET)
    pps        = sps * PAGES_PER_SHEET

    if pps * num_sections < total_pages - PAGES_PER_SHEET:
        pps += PAGES_PER_SHEET

    if pps * num_sections < total_pages:
        # Add extra pages to the last section
        last_ppb = pps + PAGES_PER_SHEET
    else:
        last_ppb = pps

    return [pps] * (num_sections - 1) + [last_ppb]


def booklet_page_layout(total_pages: int, max_pages: int = MAX_SECTION_PAGES) -> list[int]:
    section_page_counts = calc_section_page_counts(total_pages, max_pages)

    section_page_index_by_page: list[int] = []

    doc_page_offset = 0
    for section_page_count in section_page_counts:
        left_doc_page_index  = doc_page_offset + section_page_count - 1
        right_doc_page_index = doc_page_offset
        while right_doc_page_index < left_doc_page_index:
            section_page_index_by_page.append(left_doc_page_index)
            section_page_index_by_page.append(right_doc_page_index)
            section_page_index_by_page.append(right_doc_page_index + 1)
            section_page_index_by_page.append(left_doc_page_index - 1)
            left_doc_page_index -= 2
            right_doc_page_index += 2

        doc_page_offset += section_page_count

    assert len(section_page_index_by_page) == len(set(section_page_index_by_page))

    return section_page_index_by_page


def _booklet_page_indexes(num_in_pages: int, page_order: str) -> PageIndexMapping:
    if page_order == 'booklet':
        booklet_page_indexes = booklet_page_layout(num_in_pages)
        return list(enumerate(booklet_page_indexes))
    else:
        return [(half_page_index, half_page_index) for half_page_index in range(num_in_pages)]


def create(
    in_path         : pl.Path,
    out_path        : typ.Optional[pl.Path] = None,
    out_sheet_format: str = 'A4-Landscape',
    page_order      : str = 'booklet',
) -> pl.Path:
    assert out_sheet_format in pdf_booklet.PAPER_FORMATS_PT

    if out_path is None:
        ext          = in_path.suffixes[-1]
        out_filename = (in_path.name[: -len(ext)] + "_booklet") + ext
        _out_path    = in_path.parent / out_filename
    else:
        _out_path = out_path

    output = pypdf.PdfFileWriter()

    with in_path.open(mode="rb") as in_fobj:
        reader   = pypdf.PdfFileReader(in_fobj)
        in_pages = list(reader.pages)

        media_box = reader.getPage(0).mediaBox

        in_page_width  = float(media_box.getWidth())
        in_page_height = float(media_box.getHeight())

        out_params = pdf_booklet.parse_output_parameters(in_page_width, in_page_height, out_sheet_format)
        out_sheets = _create_sheets(in_pages, output, out_params, page_order)
        tzero      = time.time()
        for out_sheet in out_sheets:
            out_sheet.compressContentStreams()
        compression_time = time.time() - tzero
        logger.debug(f"compression time: {compression_time}")

        with _out_path.open(mode="wb") as out_fobj:
            output.write(out_fobj)

    logger.info(f"Wrote to '{_out_path}'")

    return _out_path
