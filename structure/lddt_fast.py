#!/usr/bin/env python3
"""Fast all-atom lDDT scoring using OpenStructure's low-level lDDTScorer.

Loads the reference once, then scores all models in a single process.
Avoids the per-model overhead of `ost compare-structures` (chain mapping,
process startup, reference re-parsing).

Usage:
    python3 lddt_fast.py ref.pdb model1.pdb model2.pdb ...
    python3 lddt_fast.py -nc ref.pdb model1.pdb model2.pdb ...

Output: CSV lines: lddt,model_path
"""
import argparse
import sys
import os
import time

os.environ.setdefault("OST_ROOT", "/opt/miniconda3/envs/ost")
sys.path.insert(0, "/opt/miniconda3/envs/ost/lib/python3.12/site-packages")

from ost import io, conop, mol
from ost.mol.alg.lddt import lDDTScorer
from ost.mol.alg import stereochemistry
import math


def load_entity(path):
    fmt = "mmcif" if path.endswith((".cif", ".mmcif")) else "pdb"
    if fmt == "mmcif":
        ent = io.LoadMMCIF(path).GetDefaultEntity()
    else:
        ent = io.LoadPDB(path)
    return ent


def stereocheck(ent):
    """Run StereoCheck, return cleaned entity with clashing atoms removed."""
    checked_ent, clashes, bad_bonds, bad_angles = stereochemistry.StereoCheck(ent)
    return checked_ent, len(clashes), len(bad_bonds), len(bad_angles)


def main():
    parser = argparse.ArgumentParser(description="Fast all-atom lDDT scoring")
    parser.add_argument("ref", help="Reference PDB/CIF")
    parser.add_argument("models", nargs="+", help="Model PDB/CIF files")
    parser.add_argument("-nc", "--no-stereocheck", action="store_true",
                        help="Skip stereochemistry checks")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    compound_lib = conop.GetDefaultLib()

    t0 = time.time()
    ref_raw = load_entity(args.ref)
    if args.no_stereocheck:
        ref = ref_raw
    else:
        ref, n_clash, n_bond, n_angle = stereocheck(ref_raw)
        if args.verbose:
            print(f"# Ref stereo: {n_clash} clashes, {n_bond} bad bonds, "
                  f"{n_angle} bad angles", file=sys.stderr)
    scorer = lDDTScorer(ref, compound_lib=compound_lib)
    t_setup = time.time() - t0
    if args.verbose:
        n_atoms = sum(1 for a in ref_raw.atoms)
        print(f"# Setup: {t_setup:.3f}s (ref: {n_atoms} atoms)", file=sys.stderr)

    for model_path in args.models:
        if not os.path.exists(model_path):
            print(f"nan,nan,{model_path}")
            continue
        t1 = time.time()
        try:
            mdl_raw = load_entity(model_path)
            if args.no_stereocheck:
                mdl = mdl_raw
            else:
                mdl, n_clash, n_bond, n_angle = stereocheck(mdl_raw)
                if args.verbose:
                    print(f"#   stereo: {n_clash} clashes, {n_bond} bad bonds, "
                          f"{n_angle} bad angles", file=sys.stderr)
            chain_mapping = {mdl.chains[0].GetName(): ref.chains[0].GetName()}
            global_lddt, local_scores = scorer.lDDT(
                mdl, chain_mapping=chain_mapping, check_resnames=False
            )
            if global_lddt is None:
                global_lddt = math.nan
        except Exception as e:
            if args.verbose:
                print(f"# Error {model_path}: {e}", file=sys.stderr)
            global_lddt = math.nan
        t_model = time.time() - t1
        if args.verbose:
            print(f"# {os.path.basename(model_path)}: {t_model:.3f}s", file=sys.stderr)
        print(f"{global_lddt},nan,{model_path}")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
