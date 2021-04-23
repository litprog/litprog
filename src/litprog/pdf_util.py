#!/home/mbarkhau/miniconda3/envs/litprog_py37/bin/python
# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import io
import sys
import typing as typ
import pathlib as pl

import PyPDF2 as pdf

PT_PER_INCH = 72
PT_PER_MM   = PT_PER_INCH / 25.4


PAPER_FORMATS_PT = {
    'A6'    : (105 * PT_PER_MM  , 148 * PT_PER_MM),
    'A5'    : (148 * PT_PER_MM  , 210 * PT_PER_MM),
    'A4'    : (210 * PT_PER_MM  , 297 * PT_PER_MM),
    'A3'    : (297 * PT_PER_MM  , 420 * PT_PER_MM),
    'Letter': (8.5 * PT_PER_INCH,  11 * PT_PER_INCH),
}

Points = float


def parse_to_pt(size: str, w_pt: Points, h_pt: Points) -> typ.Tuple[Points, Points]:
    if size.endswith("%"):
        x_pt = (float(size[:-1]) / 100) * w_pt
        y_pt = (float(size[:-1]) / 100) * h_pt
        return (x_pt, y_pt)
    elif size.endswith("pt"):
        size_pt = float(size[:-2])
        return (size_pt, size_pt)
    elif size.endswith("mm"):
        size_pt = float(size[:-2]) * PT_PER_MM
        return (size_pt, size_pt)
    elif size.endswith("inch"):
        size_pt = float(size[:-4]) * PT_PER_INCH
        return (size_pt, size_pt)
    else:
        raise Exception(f"Invalid unit {size}. Valid units are pt, mm, %")


class OpCoordinantes(typ.NamedTuple):
    next_w_pt   : float
    next_h_pt   : float
    scale_factor: float
    translate_x : float
    translate_y : float


PDFDocument = typ.Any


def _calc_op_coords(pdf_doc: PDFDocument, op: str, raw_ops: typ.Iterator[str]) -> OpCoordinantes:
    curr_media_box = pdf_doc.getPage(0).mediaBox

    cur_w_pt = float(curr_media_box.getWidth())
    cur_h_pt = float(curr_media_box.getHeight())

    # initial defaults are modified/updated by ops
    next_w_pt    = cur_w_pt
    next_h_pt    = cur_h_pt
    translate_x  = translate_y = 0.0
    scale_factor = 1.0

    if op == 'crop':
        crop_side = next(raw_ops).lower()
        crop_arg  = next(raw_ops)

        crop_l = crop_r = crop_t = crop_b = 0.0

        crop_x_pt, crop_y_pt = parse_to_pt(crop_arg, cur_w_pt, cur_h_pt)
        if crop_side in ('l', 'left'):
            crop_l = crop_x_pt
        elif crop_side in ('r', 'right'):
            crop_r = crop_x_pt
        elif crop_side in ('t', 'top'):
            crop_t = crop_y_pt
        elif crop_side in ('b', 'bottom'):
            crop_b = crop_y_pt
        else:
            errmsg = f"Invalid side {crop_side}. Valid sides are left, right, top, bottom"
            raise Exception(errmsg)

        translate_x -= crop_l
        translate_y -= crop_b
        next_w_pt = cur_w_pt - crop_l - crop_r
        next_h_pt = cur_h_pt - crop_t - crop_b
    elif op == 'scale':
        scale_type = next(raw_ops)
        scale_arg  = next(raw_ops)
        if scale_type == 'by':
            scale_factor = float(scale_arg)
        elif scale_type == 'to':
            next_w_pt, next_h_pt = PAPER_FORMATS_PT[scale_arg]
            scale_w      = next_w_pt / cur_w_pt
            scale_h      = next_h_pt / cur_h_pt
            scale_factor = min(scale_w, scale_h)
        else:
            raise Exception(f"Invalid scale arg: {scale_type}")
    else:
        # TODO: resize, translate
        raise Exception(f"Invalid operation: {op}")

    next_w_pt = round(next_w_pt)
    next_h_pt = round(next_h_pt)

    print(f"{op} w:{next_w_pt} h:{next_h_pt} s:{scale_factor} x:{translate_x} y:{translate_y}")
    return OpCoordinantes(
        next_w_pt,
        next_h_pt,
        scale_factor,
        translate_x,
        translate_y,
    )


def main(args: typ.Sequence[str] = sys.argv[1:]) -> int:
    # pylint: disable=dangerous-default-value

    in_path  = pl.Path(args[0])
    out_path = pl.Path(args[1])
    raw_ops  = iter(args[2:])

    curr_fobj = in_path.open(mode="rb")

    for op in raw_ops:
        curr_pdf  = pdf.PdfFileReader(curr_fobj)
        op_coords = _calc_op_coords(curr_pdf, op, raw_ops)

        next_pdf = pdf.PdfFileWriter()
        for cur_page in curr_pdf.pages:
            next_page = next_pdf.addBlankPage(width=op_coords.next_w_pt, height=op_coords.next_h_pt)
            next_page.mergeScaledTranslatedPage(
                cur_page,
                op_coords.scale_factor,
                op_coords.translate_x,
                op_coords.translate_y,
                expand=False,
            )
            # next_page.compressContentStreams()

        next_fobj = io.BytesIO()
        next_pdf.write(next_fobj)
        next_fobj.seek(0)

        curr_fobj.close()
        curr_fobj = next_fobj

    with out_path.open(mode="wb") as out_fobj:
        out_fobj.write(curr_fobj.read())

    return 0


if __name__ == '__main__':
    sys.exit(main())
