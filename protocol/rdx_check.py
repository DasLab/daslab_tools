#!/usr/bin/env python3
"""
Validate an RDX lab protocol sheet (Das Lab) exported from Google Sheets as .xlsx.

Checks the arithmetic and layout conventions these sheets follow, so a protocol is
verified before it reaches the bench:

  arithmetic   every reaction column sums to its stated Total; each premix cell is
               1x * multiplier; the aliquot side cell is premix_total / multiplier
  live cells   Totals, premix cells and aliquot cells are formulas, not stale literals
  typography   Arial throughout, bold-right row labels, bold-centred column headers
               over a rule, a rule under the last reagent row, plain left bullets
  text         purpose line <= 50 chars, rationale notes <= 105 chars and <= 3 of them
  artifacts    text eaten by Sheets' type parser ("1, 5" -> a date serial), percentages
               flattened to 0.4, doubled %% from a bad format string, stray blank
               rows and spacer columns

Export a sheet with File > Download > Microsoft Excel (.xlsx), then:

    rdx_check.py RDX129C.xlsx
    rdx_check.py *.xlsx --quiet          # errors only
"""

import argparse
import collections
import datetime
import re
import sys
import zipfile
from pathlib import Path

try:
    import openpyxl
except ImportError:
    sys.exit("rdx_check.py needs openpyxl:  pip3 install openpyxl")

MAX_PURPOSE = 50
MAX_NOTE = 105
MAX_NOTES = 3
FONT = "Arial"
TOL = 1e-6
# Sheets stores dates as days since 1899-12-30; anything a protocol would legitimately
# hold as a volume or concentration is far below this.
DATE_SERIAL_MIN, DATE_SERIAL_MAX = 20000, 80000

ERROR, WARN = "ERROR", "WARN"


class Finding:
    def __init__(self, level, cell, msg):
        self.level, self.cell, self.msg = level, cell, msg

    def __str__(self):
        return "  %-5s %-6s %s" % (self.level, self.cell or "", self.msg)


def num(v):
    """Numeric value of a cell, or None. Booleans and dates are not numbers here."""
    if isinstance(v, bool) or isinstance(v, (datetime.datetime, datetime.date)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def text(v):
    return v.strip() if isinstance(v, str) else ""


def blank(v):
    """True only for a genuinely empty cell. A numeric cell is not blank."""
    return v is None or (isinstance(v, str) and v.strip() == "")


def col_letter(i):
    return openpyxl.utils.get_column_letter(i)


def has_rule(cell):
    """True if the cell carries a bottom border. openpyxl leaves these as None."""
    b = cell.border
    return bool(b and b.bottom and b.bottom.style)


class Sheet:
    """Values and formulas for one worksheet, indexed 1-based as grid[row][col]."""

    def __init__(self, path):
        self.path = Path(path)
        vals = openpyxl.load_workbook(path, data_only=True)
        forms = openpyxl.load_workbook(path, data_only=False)
        self.ws, self.wf = vals.worksheets[0], forms.worksheets[0]
        self.name = self.ws.title
        self.nrow = min(self.ws.max_row, 300)
        self.ncol = min(self.ws.max_column, 26)

    def v(self, r, c):
        return self.ws.cell(row=r, column=c).value

    def f(self, r, c):
        return self.wf.cell(row=r, column=c).value

    def cell(self, r, c):
        return self.ws.cell(row=r, column=c)

    def ref(self, r, c):
        return "%s%d" % (col_letter(c), r)

    def is_formula(self, r, c):
        return isinstance(self.f(r, c), str) and self.f(r, c).startswith("=")

    def row_empty(self, r):
        return all(blank(self.v(r, c)) for c in range(1, self.ncol + 1))

    def col_empty(self, c, last_row):
        return all(blank(self.v(r, c)) for r in range(1, last_row + 1))

    def last_row(self):
        for r in range(self.nrow, 0, -1):
            if not self.row_empty(r):
                return r
        return 0


# --------------------------------------------------------------------------- grids

Grid = collections.namedtuple(
    "Grid", "hdr first last total lab v1 prem mult hdr_mult value_cols subtotal")


def find_grids(sh, last):
    """Locate every reaction grid, anchored on its Total row.

    Nothing about the geometry is assumed, because the layout drifted across the
    series: older sheets put reagent names in column B with values in C/D, newer
    ones put names in A with values in B/C, and some grids have one column per
    tube instead of a 1x/premix pair. So the label column is found from the Total
    row, the reagent block is walked upward from it, and every column the Total
    row carries a number in is treated as a value column.
    """
    grids = []
    for r in range(1, last + 1):
        lab = next((c for c in (1, 2)
                    if re.match(r"total\b", text(sh.v(r, c)), re.I)), None)
        if lab is None:
            continue

        def has_numbers(row):
            return any(num(sh.v(row, c)) is not None for c in range(lab + 1, sh.ncol + 1))

        first, subtotal = r, None
        # a label-less row carrying numbers directly above the Total is a subtotal row:
        # the house rule allows one total per table, not a subtotal and a total
        if r - 1 >= 1 and not text(sh.v(r - 1, lab)) and has_numbers(r - 1):
            subtotal = r - 1
            first = r - 1
        while first - 1 >= 1:
            u = first - 1
            label = text(sh.v(u, lab))
            if re.match(r"total\b", label, re.I):
                break
            if not label:
                # tolerate one annotation/spacer row inside the block, but stop at a
                # header row or at the top of the grid
                if has_numbers(u) or u - 1 < 1 or not text(sh.v(u - 1, lab)) \
                        or not has_numbers(u - 1):
                    break
                first = u - 1
                continue
            # a row whose first value cell holds text is the column-header row
            if num(sh.v(u, lab + 1)) is None and text(sh.v(u, lab + 1)):
                break
            first = u
        if first >= r or (subtotal is not None and first >= subtotal):
            continue
        hdr = first - 1 if first > 1 else None

        last_reag = subtotal - 1 if subtotal else r - 1
        # only the contiguous run of numeric columns beside the labels is part of the
        # reaction; anything past the first gap belongs to the right-hand index block.
        # A column carrying an "Aliquot" label is a side cell, not a reaction column --
        # it often sits flush against them and would otherwise look like a bad sum.
        side = {c for row in range(max(1, r - 40), r + 1) for c in range(lab + 1, sh.ncol + 1)
                if re.search(r"aliquot|split per tube", text(sh.v(row, c)), re.I)}
        value_cols = []
        for c in range(lab + 1, sh.ncol + 1):
            if num(sh.v(r, c)) is None:
                break
            if c not in side:
                value_cols.append(c)
        if not value_cols:
            continue

        prem = mult = hdr_mult = None
        if hdr:
            for c in range(lab + 1, sh.ncol + 1):
                m = re.search(r"premix", text(sh.v(hdr, c)), re.I)
                if m:
                    prem = c
                    mm = re.search(r"\(([\d.]+)\s*x\)", text(sh.v(hdr, c)))
                    hdr_mult = mm.group(1) if mm else None
                    mult = num(sh.v(hdr, c + 1))
                    if mult is None and hdr_mult:
                        mult = float(hdr_mult)
                    break
        grids.append(Grid(hdr, first, last_reag, r, lab, lab + 1, prem, mult,
                          hdr_mult, value_cols, subtotal))
    return grids


def check_grids(sh, last, out):
    grids = find_grids(sh, last)
    if not grids:
        out.append(Finding(WARN, "", "no reaction grid found - the arithmetic checks "
                                     "examined nothing on this sheet"))
        return
    for g in grids:
        tag = "grid at row %s" % (g.hdr if g.hdr else g.first)
        if g.subtotal:
            out.append(Finding(WARN, sh.ref(g.subtotal, g.v1),
                               "%s: subtotal row above the Total row - the house rule is one "
                               "total per table, with the aliquot in a labelled side cell" % tag))

        if g.hdr_mult is not None and g.mult is not None and abs(float(g.hdr_mult) - g.mult) > TOL:
            out.append(Finding(ERROR, sh.ref(g.hdr, g.prem + 1),
                               "%s: header says Premix (%sx) but the multiplier cell is %g"
                               % (tag, g.hdr_mult, g.mult)))

        # every column the Total row carries a number in must sum to it
        for c in g.value_cols:
            if c == g.prem:
                continue        # the premix column is checked against the multiplier below
            got = sum(x for x in (num(sh.v(r, c)) for r in range(g.first, g.last + 1))
                      if x is not None)
            want = num(sh.v(g.total, c))
            if abs(got - want) > 1e-4:
                out.append(Finding(ERROR, sh.ref(g.total, c),
                                   "%s: column %s sums to %g but Total says %g"
                                   % (tag, col_letter(c), got, want)))

        shared, prem_sum = [], 0.0
        if g.prem:
            for r in range(g.first, g.last + 1):
                c, b = sh.v(r, g.prem), num(sh.v(r, g.v1))
                if text(c) in ("-", "\u2013", "\u2014"):
                    continue
                cv = num(c)
                if cv is None:
                    continue
                shared.append(r)
                prem_sum += cv
                if g.mult is not None and b is not None and abs(cv - b * g.mult) > 1e-4:
                    out.append(Finding(ERROR, sh.ref(r, g.prem),
                                       "%s: premix is %g but 1x x %g = %g  (%s)"
                                       % (tag, cv, g.mult, b * g.mult,
                                          text(sh.v(r, g.lab)) or "unlabelled")))
        if shared:
            pt = num(sh.v(g.total, g.prem))
            if pt is None:
                out.append(Finding(WARN, sh.ref(g.total, g.prem),
                                   "%s: Total row carries the 1x column but not the premix column" % tag))
            elif abs(pt - prem_sum) > 1e-4:
                out.append(Finding(ERROR, sh.ref(g.total, g.prem),
                                   "%s: premix column sums to %g but Total says %g"
                                   % (tag, prem_sum, pt)))

            aliq = None
            for r in range(g.hdr, g.total + 1):
                for c in range(g.prem + 1, sh.ncol + 1):
                    if re.search(r"aliquot|split per tube", text(sh.v(r, c)), re.I):
                        for rr in (r + 1, r):
                            for cc in (c, c + 1):
                                if num(sh.v(rr, cc)) is not None and (rr, cc) != (r, c):
                                    aliq = (rr, cc, num(sh.v(rr, cc)))
                                    break
                            if aliq:
                                break
                    if aliq:
                        break
                if aliq:
                    break
            if aliq and g.mult:
                rr, cc, got = aliq
                want = prem_sum / g.mult
                if abs(got - want) > 1e-4:
                    out.append(Finding(ERROR, sh.ref(rr, cc),
                                       "%s: aliquot is %g but premix_total/%g = %g"
                                       % (tag, got, g.mult, want)))
                if not sh.is_formula(rr, cc):
                    out.append(Finding(WARN, sh.ref(rr, cc),
                                       "%s: aliquot is a literal, not a formula" % tag))
            elif g.mult:
                out.append(Finding(WARN, sh.ref(g.total, g.prem), "%s: no aliquot side cell found" % tag))

        # live cells
        for c in [g.v1] + ([g.prem] if g.prem else []):
            if num(sh.v(g.total, c)) is not None and not sh.is_formula(g.total, c):
                out.append(Finding(WARN, sh.ref(g.total, c), "%s: Total is a literal, not a formula" % tag))
        dead = [r for r in shared if not sh.is_formula(r, g.prem)]
        if dead:
            out.append(Finding(WARN, sh.ref(dead[0], g.prem),
                               "%s: %d premix cell(s) are literals, not formulas - rows %s "
                               "(a stale draft value hides here)"
                               % (tag, len(dead), ", ".join(str(r) for r in dead))))

        # typography
        for r in range(g.first, g.total + 1):
            fc = sh.cell(r, g.lab)
            if text(fc.value) and not (fc.font.bold and fc.alignment.horizontal == "right"):
                out.append(Finding(WARN, sh.ref(r, g.lab),
                                   "%s: row label should be bold and right-justified" % tag))
        if g.hdr is None:
            continue
        hc = sh.cell(g.hdr, g.v1)
        if not (hc.font.bold and hc.alignment.horizontal == "center"):
            out.append(Finding(WARN, sh.ref(g.hdr, g.v1),
                               "%s: column header should be bold and centred" % tag))
        if not (has_rule(sh.cell(g.hdr, g.v1)) or has_rule(sh.cell(g.hdr, g.prem or g.v1))):
            out.append(Finding(WARN, sh.ref(g.hdr, g.v1), "%s: no rule under the column-header row" % tag))
        if not (has_rule(sh.cell(g.last, g.v1)) or has_rule(sh.cell(g.last, g.prem or g.v1))):
            out.append(Finding(WARN, sh.ref(g.last, g.v1),
                               "%s: no rule under the last reagent row (row %d)" % (tag, g.last)))
        for r in range(g.first, g.total + 1):
            if r != g.last and (has_rule(sh.cell(r, g.v1)) or has_rule(sh.cell(r, g.prem or g.v1))):
                out.append(Finding(WARN, sh.ref(r, g.v1),
                                   "%s: stray rule under row %d - should sit under the last reagent row (%d)"
                                   % (tag, r, g.last)))


# ---------------------------------------------------------------------- text/layout

def check_text(sh, last, out):
    # title and purpose live in A or B depending on how old the sheet is
    tcol = next((c for c in (1, 2) if text(sh.v(1, c))), 1)
    pcol = next((c for c in (1, 2) if text(sh.v(2, c))), 1)
    title = text(sh.v(1, tcol))
    if not title:
        out.append(Finding(WARN, "A1", "no title"))
    else:
        f = sh.cell(1, tcol).font
        if not f.bold or (f.size or 0) < 12:
            out.append(Finding(WARN, sh.ref(1, tcol), "title should be bold and ~14 pt"))
    if not any(isinstance(sh.v(1, c), (datetime.datetime, datetime.date))
               for c in range(2, sh.ncol + 1)):
        out.append(Finding(WARN, "row 1", "no date in the top-right of the title row"))

    purpose = text(sh.v(2, pcol))
    if not purpose:
        out.append(Finding(WARN, sh.ref(2, pcol), "no purpose line"))
    elif len(purpose) > MAX_PURPOSE:
        out.append(Finding(WARN, sh.ref(2, pcol), "purpose line is %d chars (max %d): %r"
                           % (len(purpose), MAX_PURPOSE, purpose)))

    notes = [r for r in range(1, last + 1)
             if text(sh.v(r, 1)) and (sh.cell(r, 1).font.size or 10) <= 8]
    bullets = [r for r in notes if text(sh.v(r, 1)).startswith("•")]
    if not notes:
        out.append(Finding(WARN, "", "no 8 pt rationale notes found at the bottom"))
    if len(bullets) > MAX_NOTES:
        out.append(Finding(WARN, sh.ref(bullets[0], 1),
                           "%d rationale notes (max %d)" % (len(bullets), MAX_NOTES)))
    for r in notes:
        s = text(sh.v(r, 1))
        if len(s) > MAX_NOTE:
            out.append(Finding(WARN, sh.ref(r, 1),
                               "note is %d chars (max %d) - it will wrap when printed" % (len(s), MAX_NOTE)))

    for r in range(1, last + 1):
        s = text(sh.v(r, 1))
        if s.startswith("•"):
            a = sh.cell(r, 1)
            if a.font.bold or a.alignment.horizontal == "right":
                out.append(Finding(WARN, sh.ref(r, 1),
                                   "step bullet is bold/right-justified - stale formatting from the copied sheet"))


def check_layout(sh, last, out):
    r = 2
    while r <= last:
        if sh.row_empty(r):
            start = r
            while r <= last and sh.row_empty(r):
                r += 1
            n = r - start
            if n > 1:
                out.append(Finding(WARN, "row %d" % start,
                                   "%d blank rows in a row (only one separator belongs between blocks)" % n))
        else:
            r += 1
    for c in range(1, sh.ncol + 1):
        if sh.col_empty(c, last) and any(not sh.col_empty(cc, last) for cc in range(c + 1, sh.ncol + 1)):
            out.append(Finding(WARN, "col %s" % col_letter(c), "empty spacer column - wastes page width"))


def check_artifacts(sh, last, out):
    for r in range(1, last + 1):
        for c in range(1, sh.ncol + 1):
            cell = sh.cell(r, c)
            v = cell.value
            s = text(v)
            if "%%" in s:
                out.append(Finding(ERROR, sh.ref(r, c), "doubled %% - bad format string: %r" % s))
            if s and cell.font.name and cell.font.name != FONT:
                out.append(Finding(WARN, sh.ref(r, c), "font is %s, should be %s" % (cell.font.name, FONT)))
            n = num(v)
            if n is not None and DATE_SERIAL_MIN < n < DATE_SERIAL_MAX and float(n).is_integer():
                out.append(Finding(ERROR, sh.ref(r, c),
                                   "%g looks like a date serial - Sheets parsed text such as '1, 5' as a date; "
                                   "set the cell to plain text and re-enter" % n))
            fmt = cell.number_format or ""
            if n is not None and re.search(r"[ymd]{2}", fmt) and not (DATE_SERIAL_MIN < n < DATE_SERIAL_MAX):
                out.append(Finding(ERROR, sh.ref(r, c),
                                   "number %g carries a date format (%s) - it will render as a date" % (n, fmt)))
            if n is not None and 0 < n < 1 and "%" not in fmt and re.search(r"%", text(sh.v(r, 1))):
                out.append(Finding(WARN, sh.ref(r, c),
                                   "%g on a percentage row with no %% format - '40%%' was flattened to 0.4" % n))


def check(path):
    try:
        sh = Sheet(path)
    except zipfile.BadZipFile:
        return None, [Finding(ERROR, "", "not a readable .xlsx (Drive exports are sometimes "
                                         "truncated - re-download it)")]
    out = []
    last = sh.last_row()
    if last == 0:
        return sh, [Finding(ERROR, "", "sheet is empty")]
    check_grids(sh, last, out)
    check_text(sh, last, out)
    check_layout(sh, last, out)
    check_artifacts(sh, last, out)
    order = {ERROR: 0, WARN: 1}
    out.sort(key=lambda f: (order[f.level], f.cell))
    return sh, out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("xlsx", nargs="+", help="RDX protocol sheet(s) exported as .xlsx")
    p.add_argument("-q", "--quiet", action="store_true", help="show errors only")
    args = p.parse_args()

    n_err = n_warn = 0
    for path in args.xlsx:
        sh, findings = check(path)
        if args.quiet:
            findings = [f for f in findings if f.level == ERROR]
        errs = sum(f.level == ERROR for f in findings)
        n_err += errs
        n_warn += len(findings) - errs
        name = sh.name if sh else Path(path).stem
        print("%s  (%s)" % (Path(path).name, name))
        if findings:
            for f in findings:
                print(f)
        else:
            print("  clean")
        print()

    print("%d error(s), %d warning(s)" % (n_err, n_warn))
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
