"""Batch lDDT scoring script run inside the OST container.

Invoked by lddt.py as a single Docker call:
    ost -v 0 /mnt/lddt_batch_ost.py /mnt/lddt_manifest.tsv

manifest.tsv has one row per comparison (tab-separated):
    ref_path  ref_fmt  model_path  model_fmt

Writes one output line per row to stdout:
    lddt_value<TAB>ilddt_value
"""
import sys
import math
from ost.mol.alg import scoring_base, scoring
import ost

ost.PushVerbosityLevel(0)


def load_struct(p, fmt):
    if fmt in ('cif', 'mmcif'):
        return scoring_base.MMCIFPrep(p, fault_tolerant=True)
    return scoring_base.PDBPrep(p, fault_tolerant=True)


with open(sys.argv[1]) as fh:
    rows = [ln.strip().split('\t') for ln in fh if ln.strip()]

for ref_path, ref_fmt, mdl_path, mdl_fmt in rows:
    try:
        ref = load_struct(ref_path, ref_fmt)
        mdl = load_struct(mdl_path, mdl_fmt)
        sc = scoring.Scorer(mdl, ref)
        lddt_v = sc.lddt if sc.lddt is not None else math.nan
        ilddt_v = sc.ilddt if sc.ilddt is not None else math.nan
    except Exception:
        lddt_v = ilddt_v = math.nan
    sys.stdout.write(f'{lddt_v}\t{ilddt_v}\n')
    sys.stdout.flush()
