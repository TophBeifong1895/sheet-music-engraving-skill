# -*- coding: utf-8 -*-
"""abc_to_pdf.py -- render a single-staff ABC file to a printable A4 PDF.

Pipeline: verovio (ABC -> SVG per page) -> flatten_nested_svg fix ->
svglib -> reportlab (title block + uniform page fit).

Requires: verovio, svglib, reportlab; a CJK TTF/TTC font for CJK titles.

Usage:
    python abc_to_pdf.py tune.abc --title "敕勒歌" --subtitle "小提琴独奏谱" \
        --left "刘洲 曲" --right "四分音符= 64（约）　D 大调" --out tune.pdf

Notes / hard-won fixes encoded here:
- verovio emits a nested <svg class="definition-scale" viewBox>; svglib
  mis-scales it (systems then occupy only ~68% of page width) and drops the
  CSS stroke:currentColor (staff lines vanish). flatten_nested_svg() replaces
  the nested svg with <g color="black" transform="scale(..)>, fixing both.
- CJK glyphs need an external font: reportlab's built-ins lack CJK.
  msyh.ttc works; msyhl.ttc has NO musical glyphs (quarter-note etc.) --
  write tempo text as "四分音符= 64", never "♩=64".
- Starting layout for a song-length solo piece: pageWidth 1160,
  pageHeight 1770, scale 60, spacingSystem 10. Increase spacingSystem if
  the last page is nearly empty; decrease if bars look cramped.
"""
import argparse
import re

import verovio
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_W_PT, PAGE_H_PT = A4  # 595.27 x 841.89
MARGIN_LR = 36.0
CONTENT_W = PAGE_W_PT - 2 * MARGIN_LR


def flatten_nested_svg(svg):
    """Replace verovio's nested definition-scale <svg> with a scaled <g>."""
    m = re.search(r'<svg class="definition-scale"[^>]*?viewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>', svg)
    if not m:
        return svg
    vbw, vbh = float(m.group(1)), float(m.group(2))
    mo = re.search(r'<svg width="([\d.]+)px" height="([\d.]+)px"', svg)
    ow, oh = float(mo.group(1)), float(mo.group(2))
    sx, sy = ow / vbw, oh / vbh
    idx_outer = svg.rfind('</svg>')
    idx_inner = svg.rfind('</svg>', 0, idx_outer)
    svg = svg[:idx_inner] + '</g>' + svg[idx_inner + len('</svg>'):]
    return svg.replace(m.group(0), f'<g color="black" transform="scale({sx:.8f},{sy:.8f})">', 1)


def register_fonts(bold_path, light_path):
    pdfmetrics.registerFont(TTFont('cjk', bold_path, subfontIndex=0))
    light = light_path or bold_path
    pdfmetrics.registerFont(TTFont('cjkl', light, subfontIndex=0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('abc')
    ap.add_argument('--title', default='')
    ap.add_argument('--subtitle', default='')
    ap.add_argument('--left', default='', help='left header line (composer etc.)')
    ap.add_argument('--right', default='', help='right header line (tempo/key)')
    ap.add_argument('--out', default=None)
    ap.add_argument('--page-width', type=int, default=1160)
    ap.add_argument('--page-height', type=int, default=1770)
    ap.add_argument('--scale', type=int, default=60)
    ap.add_argument('--spacing-system', type=int, default=10)
    ap.add_argument('--spacing-staff', type=int, default=9)
    ap.add_argument('--font', default=r'C:\Windows\Fonts\msyh.ttc')
    ap.add_argument('--font-light', default=r'C:\Windows\Fonts\msyhl.ttc')
    a = ap.parse_args()

    out = a.out or re.sub(r'\.abc$', '.pdf', a.abc)

    tk = verovio.toolkit()
    tk.setOptions({
        'pageWidth': a.page_width, 'pageHeight': a.page_height,
        'scale': a.scale, 'header': 'none', 'footer': 'none',
        'breaks': 'auto',
        'pageMarginTop': 60, 'pageMarginBottom': 60,
        'pageMarginLeft': 40, 'pageMarginRight': 40,
        'spacingStaff': a.spacing_staff, 'spacingSystem': a.spacing_system,
    })
    assert tk.loadFile(a.abc), f'cannot load {a.abc}'
    drawings = []
    for i in range(1, tk.getPageCount() + 1):
        svg = flatten_nested_svg(tk.renderToSVG(i))
        tmp = f'._abc2pdf_p{i}.svg'
        open(tmp, 'w', encoding='utf-8').write(svg)
        drawings.append(svg2rlg(tmp))

    has_title = bool(a.title or a.subtitle or a.left or a.right)
    if has_title:
        register_fonts(a.font, a.font_light)

    c = rl_canvas.Canvas(out, pagesize=A4)
    scales = []
    for idx, d in enumerate(drawings):
        avail_h = (PAGE_H_PT - 110 - 30) if (idx == 0 and has_title) else (PAGE_H_PT - 50 - 30)
        s = CONTENT_W / d.width
        if d.height * s > avail_h:
            s *= avail_h / (d.height * s)
        scales.append(s)
    uniform = min(scales)

    import os
    for idx, d in enumerate(drawings):
        w_pt, h_pt = d.width * uniform, d.height * uniform
        x = (PAGE_W_PT - w_pt) / 2
        if idx == 0 and has_title:
            c.setFont('cjk', 22)
            c.drawCentredString(PAGE_W_PT / 2, PAGE_H_PT - 52, a.title)
            c.setFont('cjkl', 11)
            c.drawCentredString(PAGE_W_PT / 2, PAGE_H_PT - 74, a.subtitle)
            c.setFont('cjkl', 9)
            c.drawString(MARGIN_LR, PAGE_H_PT - 92, a.left)
            c.drawRightString(PAGE_W_PT - MARGIN_LR, PAGE_H_PT - 92, a.right)
        top = (PAGE_H_PT - 110) if (idx == 0 and has_title) else (PAGE_H_PT - 50)
        c.saveState()
        c.translate(x, top - h_pt)
        c.scale(uniform, uniform)
        renderPDF.draw(d, c, 0, 0)
        c.restoreState()
        c.showPage()

    c.save()
    for i in range(1, tk.getPageCount() + 1):
        os.remove(f'._abc2pdf_p{i}.svg')
    print('saved:', out, f'({tk.getPageCount()} pages)')


if __name__ == '__main__':
    main()
