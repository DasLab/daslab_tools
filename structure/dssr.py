#!/usr/bin/env python3
"""Run x3dna-dssr on structure files and print secondary structure.

Default (new) behaviour builds the secondary structure from DSSR's **base-pair list**
(the `List of N base pairs` block of the -o output) rather than from `dssr-2ndstrs.dbn`.

Why this matters, especially for DNA: the .dbn keeps only canonical Watson-Crick and
wobble pairs. A G-quadruplex is held together by Hoogsteen G+G pairs (Saenger 06-VI,
LW cWH), so its .dbn is all dots even though DSSR found every tetrad pair. Measured on
DNA structures: 1KF1 13 pairs -> empty dbn, 9MMF 18 -> empty, 148D 11 -> empty.
Any F1 scored off the .dbn is therefore 0/0 on the dominant DNA fold.

  --legacy      reproduce the old .dbn-based wrapper exactly
  --pairs       also print one line per base pair
  --all-pairs   build the dot-bracket from ALL pairs, not just canonical ones
  --dna         treat A-T and G-C as canonical and exclude G-T (not a stable DNA pair)

Output (CSV, one row per structure): dbn,file,sequence[,n_total,n_canon,n_noncanon]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from glob import glob

PAIR_HDR = re.compile(r"List of (\d+) base pairs?")
# e.g. "   1 A.DG2          A.DG8          G+G --          06-VI     cWH  cW+M"
PAIR_ROW = re.compile(
    r"^\s*(\d+)\s+(\S+)\s+(\S+)\s+(\S\S\S)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")
NT = re.compile(r"^(?:([\w']+)\.)?(.+?)(-?\d+)(?:\^(\w))?$")
# The per-nucleotide listing near the end of the -o output, e.g.
#   "   1  C . B.DC1     0.007  anti,~C2'-endo,non-canonical,...,i-motif"
# columns: serial, one-letter name, dbn char, chain-qualified id, base-ring rmsd,
# comma-separated features. Its serial IS the position in dssr-2ndstrs.dbn/.ct.
NT_ROW = re.compile(
    r"^\s*(\d+)\s+(\S)\s+(\S)\s+(\S+)\s+(-?\d+\.\d+)\s+(\S.*)$")

BRACKETS = [("(", ")"), ("[", "]"), ("{", "}"), ("<", ">")] + [
    (chr(ord("A") + i), chr(ord("a") + i)) for i in range(26)]


def canonical(name, bp, dna=False):
    """DSSR's intrinsic pair name column. WC and Wobble are the .dbn set."""
    if name in ("WC", "Wobble"):
        if dna and name == "Wobble":
            return False          # G-T wobble is not a stable DNA pair
        return True
    return False


def parse_dssr_output(text):
    """Return (pairs, order) where pairs is a list of dicts and order is the
    nucleotide order of appearance, which we use to lay out the sequence."""
    lines = text.splitlines()
    pairs, i = [], 0
    while i < len(lines):
        m = PAIR_HDR.search(lines[i])
        if not m:
            i += 1
            continue
        n_expected = int(m.group(1))
        i += 1
        while i < len(lines) and len(pairs) < n_expected:
            line = lines[i]
            # the block ends at a section delimiter; stop rather than drift into
            # the helix/stem listings, whose rows match the same shape
            if line.startswith("*") or line.startswith("List of"):
                break
            row = PAIR_ROW.match(line)
            if row:
                _, nt1, nt2, bp, name, saenger, lw, dssr = row.groups()
                pairs.append(dict(nt1=nt1, nt2=nt2, bp=bp, name=name,
                                  saenger=saenger, lw=lw, dssr=dssr))
            i += 1
        break
    return pairs


def parse_nt_list(text):
    """Ordered nt ids from the per-nucleotide listing of the -o output.

    This is the authoritative index: its serial numbers ARE the positions in
    dssr-2ndstrs.dbn and .ct, chain order included. Preferred over inferring chain
    order from the order chains first appear in the pair list, which is only a
    heuristic -- an entry can list its chains in the dbn in a different order than
    its pairs mention them, and then every pair of the later chain is placed in the
    wrong segment.

    Returns [] if the section is absent, so the caller can fall back.
    """
    order, want = [], 1
    for line in text.splitlines():
        m = NT_ROW.match(line)
        if not m:
            continue
        serial, _, dbn_ch, nt_id, _, _ = m.groups()
        if int(serial) != want:
            continue
        if len(dbn_ch) != 1 or not NT.match(nt_id):
            continue
        order.append(nt_id)
        want += 1
    return order


def nt_parts(nt_id):
    m = NT.match(nt_id)
    if not m:
        return None
    chain, resname, resseq, icode = m.groups()
    return chain or "A", resname, int(resseq), icode or ""


def layout_from_dbn_file(dbn_path):
    """The .dbn file gives the canonical residue order and sequence, including '&'
    between chains. We reuse it purely for ordering, not for the pairing."""
    if not os.path.isfile(dbn_path):
        return None, None
    lines = open(dbn_path).readlines()
    if len(lines) < 3:
        return None, None
    return lines[1].strip(), lines[2].strip()



def read_ct(path):
    """dssr-2ndstrs.ct: `index base prev next pair orig_resnum`. Returns the ordered
    list of original residue numbers, one per residue in the dbn layout."""
    if not os.path.isfile(path):
        return None
    out = []
    for line in open(path).readlines()[1:]:
        f = line.split()
        if len(f) >= 6:
            try:
                out.append(int(f[5]))
            except ValueError:
                return None
    return out or None


def map_pairs_to_indices(pairs, ct_resnums, chain_lens):
    """Map DSSR nt ids (e.g. 'A.DG2') onto 0-based positions in the concatenated dbn.

    The .ct gives the original residue number of every position in order. Residue
    numbers can repeat across chains, so resolve per chain segment: chains are taken
    in order of first appearance in the pair list, matching the dbn's chain order."""
    bounds, acc = [], 0
    for L in chain_lens:
        bounds.append((acc, acc + L))
        acc += L

    seen_chains = []
    for p in pairs:
        for key in ("nt1", "nt2"):
            parts = nt_parts(p[key])
            if parts and parts[0] not in seen_chains:
                seen_chains.append(parts[0])

    # position lookup per chain segment: {resnum: global index}
    seg_lookup = []
    for (lo, hi) in bounds:
        d = {}
        for gi in range(lo, min(hi, len(ct_resnums))):
            d.setdefault(ct_resnums[gi], gi)
        seg_lookup.append(d)

    chain_to_seg = {c: i for i, c in enumerate(seen_chains) if i < len(bounds)}

    idx = {}
    for p in pairs:
        for key in ("nt1", "nt2"):
            nid = p[key]
            if nid in idx:
                continue
            parts = nt_parts(nid)
            if not parts:
                continue
            chain, _, resseq, _ = parts
            seg = chain_to_seg.get(chain)
            if seg is not None and resseq in seg_lookup[seg]:
                idx[nid] = seg_lookup[seg][resseq]
                continue
            # fall back: unique match anywhere
            hits = [d[resseq] for d in seg_lookup if resseq in d]
            if len(hits) == 1:
                idx[nid] = hits[0]
    return idx


def group_helices(pairs_idx):
    """Group pairs into stacked helices: (i,j) and (i+1,j-1) belong together.
    DSSR builds its dot-bracket from helices/stems, so assigning a page per helix
    rather than per pair reproduces its bracket choices far more often."""
    remaining = set(pairs_idx)
    helices = []
    while remaining:
        i, j = min(remaining)
        helix = [(i, j)]
        remaining.discard((i, j))
        a, b = i + 1, j - 1
        while (a, b) in remaining:
            helix.append((a, b))
            remaining.discard((a, b))
            a, b = a + 1, b - 1
        helices.append(helix)
    return helices


def crosses(p, q):
    (a, b), (c, d) = p, q
    return a < c < b < d or c < a < d < b


def assign_brackets(pairs_idx, n, segments=None):
    """Greedy page assignment, one page per helix, largest helix first. The dominant
    stem therefore comes out as "()" and crossing helices fall to "[]", "{}", "<>",
    which is the convention DSSR's own dbn follows. Inter-chain pairs are kept, so
    `segments` is accepted for signature compatibility but not used to split."""
    out = ["."] * n
    helices = group_helices(pairs_idx)
    helices.sort(key=lambda h: (-len(h), min(h)))
    pages = []
    for helix in helices:
        placed = False
        for pi, page in enumerate(pages):
            if all(not crosses(x, y) for x in helix for y in page):
                page.extend(helix)
                placed = True
                break
        if not placed:
            pages.append(list(helix))
            pi = len(pages) - 1
        if pi < len(BRACKETS):
            o, c = BRACKETS[pi]
            for (i, j) in helix:
                if not (0 <= i < n and 0 <= j < n):
                    raise IndexError(
                        "base-pair index (%d, %d) is outside a structure of length %d. "
                        "The caller's pair indices are not positions in this bracket "
                        "array -- note DSSR's JSON `index_chain` is a GLOBAL index "
                        "across chains, not a position within one chain." % (i, j, n))
                out[i], out[j] = o, c
    return "".join(out), len(pages)


def run_one(infile, args, dssr_bin):
    with tempfile.TemporaryDirectory() as td:
        outp = os.path.join(td, "out.txt")
        try:
            subprocess.run([dssr_bin, f"-i={os.path.abspath(infile)}", f"-o={outp}"],
                           cwd=td, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=600, check=False)
        except subprocess.TimeoutExpired:
            sys.stderr.write(f"{infile}: DSSR timed out\n")
            return None
        seq, dbn = layout_from_dbn_file(os.path.join(td, "dssr-2ndstrs.dbn"))
        if args.legacy:
            if seq is None:
                return None
            return dict(dbn=dbn, seq=seq, n_total=None, n_canon=None, n_non=None, pairs=[])
        if not os.path.isfile(outp) or seq is None:
            return None
        pairs = parse_dssr_output(open(outp, errors="replace").read())

        # Index map from dssr-2ndstrs.ct, whose final column is the ORIGINAL residue
        # number for every residue, paired or not. Using only paired residues (as an
        # earlier version did) compresses the coordinates and shifts the whole string.
        ct = read_ct(os.path.join(td, "dssr-2ndstrs.ct"))
        if ct is None:
            return None
        chain_lens = [len(c) for c in seq.split("&")]
        # Prefer the -o nucleotide listing: its serials are the dbn positions outright,
        # so no chain-order inference is needed. Fall back to resnum matching only if
        # that section is missing or disagrees with the dbn length.
        text = open(outp, errors="replace").read()
        order = parse_nt_list(text)
        if order and len(order) == sum(chain_lens):
            idx_of = {nid: k for k, nid in enumerate(order)}
        else:
            idx_of = map_pairs_to_indices(pairs, ct, chain_lens)

        use = []
        for p in pairs:
            is_can = canonical(p["name"], p["bp"], dna=args.dna)
            if args.all_pairs or is_can:
                a, b = idx_of.get(p["nt1"]), idx_of.get(p["nt2"])
                if a is not None and b is not None and a != b:
                    use.append((min(a, b), max(a, b)))
        linear_len = sum(chain_lens)
        segments, acc = [], 0
        for L in chain_lens:
            segments.append((acc, acc + L))
            acc += L
        db_flat, npages = assign_brackets(use, linear_len, segments)
        parts, c0 = [], 0
        for L in chain_lens:
            parts.append(db_flat[c0:c0 + L])
            c0 += L
        newdbn = "&".join(parts)
        ncan = sum(1 for p in pairs if canonical(p["name"], p["bp"], dna=args.dna))
        return dict(dbn=newdbn, seq=seq, n_total=len(pairs), n_canon=ncan,
                    n_non=len(pairs) - ncan, pairs=pairs, npages=npages)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdbfiles", nargs="+")
    ap.add_argument("--legacy", action="store_true",
                    help="use the old dssr-2ndstrs.dbn output verbatim")
    ap.add_argument("--pairs", action="store_true", help="also print every base pair")
    ap.add_argument("--all-pairs", action="store_true",
                    help="build the dot-bracket from all pairs, not just canonical")
    ap.add_argument("--dna", action="store_true",
                    help="DNA conventions: exclude G-T wobble from the canonical set")
    ap.add_argument("--counts", action="store_true", help="append pair counts")
    if len(sys.argv) == 1:
        ap.print_help()
        sys.exit(1)
    a = ap.parse_args()

    dssr_bin = shutil.which("x3dna-dssr") or os.path.expanduser(
        "~/src/x3dna-v2.4/bin/x3dna-dssr")
    if not os.path.isfile(dssr_bin):
        sys.exit("x3dna-dssr not found on PATH or at ~/src/x3dna-v2.4/bin/")

    for infile in a.pdbfiles:
        r = run_one(infile, a, dssr_bin)
        if r is None:
            sys.stderr.write(f"{infile}: no DSSR output\n")
            continue
        row = f'{r["dbn"]},{infile},{r["seq"]}'
        if a.counts and r["n_total"] is not None:
            row += f',{r["n_total"]},{r["n_canon"]},{r["n_non"]}'
        print(row)
        if a.pairs:
            for p in r["pairs"]:
                print(f'  {p["nt1"]}\t{p["nt2"]}\t{p["bp"]}\t{p["name"]}\t'
                      f'{p["saenger"]}\t{p["lw"]}')


if __name__ == "__main__":
    main()
