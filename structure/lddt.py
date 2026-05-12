#!/opt/miniconda3/envs/ost/bin/python3
"""Fast all-atom lDDT scoring using OpenStructure's low-level lDDTScorer.

Loads the reference once, then scores all models in a single process.
Avoids the per-model overhead of `ost compare-structures` (process startup,
reference re-parsing).

Usage:
    lddt.py ref.pdb model1.pdb model2.pdb ...
    lddt.py -nc ref.pdb model1.pdb ...          # skip stereocheck
    lddt.py --ilddt ref.pdb model1.pdb ...      # also compute ilddt
    lddt.py --chain-mapper ref.pdb model1.pdb   # sequence-based chain mapping

Output (CSV): lddt,ilddt,model_path
  ilddt is nan unless --ilddt is given.
  ilddt is nan for single-chain targets regardless.
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
    # Resolve symlinks so format detection works even when the link name has wrong extension
    real = os.path.realpath(path)
    if real.endswith((".cif", ".mmcif")):
        return io.LoadMMCIF(path)
    else:
        return io.LoadPDB(path)


def stereocheck(ent):
    checked_ent, clashes, bad_bonds, bad_angles = stereochemistry.StereoCheck(ent)
    return checked_ent, len(clashes), len(bad_bonds), len(bad_angles)


def name_based_chain_mapping(mdl, ref):
    """Map model chains onto reference chains by name, with positional fallback."""
    ref_names = {c.GetName() for c in ref.chains}
    mdl_names = [c.GetName() for c in mdl.chains]
    mapping = {mc: mc for mc in mdl_names if mc in ref_names}
    if not mapping:
        ref_list = [c.GetName() for c in ref.chains]
        mapping = {mc: rc for mc, rc in zip(mdl_names, ref_list)}
    return mapping, None  # (chain_mapping, residue_mapping)


def sequence_based_chain_mapping(chain_mapper, mdl):
    """Map model chains using ChainMapper (sequence alignment).
    Returns (chain_mapping, residue_mapping) matching lDDTScorer.lDDT() params.
    """
    from ost.mol.alg import chain_mapping as cm_mod
    result = chain_mapper.GetMapping(mdl)
    flat = result.GetFlatMapping(mdl_as_key=True)   # {mdl_ch: ref_ch}
    alns = {aln.GetSequence(1).GetName(): aln for aln in result.alns}
    # only keep chains that have an alignment (some very short chains may be skipped)
    chain_map = {mc: tc for mc, tc in flat.items() if mc in alns}
    res_map = alns if chain_map else None
    if not chain_map:
        # nothing mapped — fall back to name-based
        return name_based_chain_mapping(mdl, chain_mapper.target)
    return chain_map, res_map


def score_model(scorer, mdl, chain_map, res_map, do_ilddt):
    """Compute global lDDT and (optionally) ilddt. Returns (lddt, ilddt)."""
    kwargs = dict(chain_mapping=chain_map, check_resnames=False)
    if res_map is not None:
        kwargs["residue_mapping"] = res_map

    global_lddt, _ = scorer.lDDT(mdl, **kwargs)
    if global_lddt is None:
        global_lddt = math.nan

    ilddt = math.nan
    if do_ilddt and sum(1 for _ in scorer.chain_names) > 1 and len(chain_map) > 1:
        try:
            ilddt, _ = scorer.lDDT(mdl, no_intrachain=True, **kwargs)
            if ilddt is None:
                ilddt = math.nan
        except Exception:
            ilddt = math.nan

    return global_lddt, ilddt


def main():
    parser = argparse.ArgumentParser(description="Fast all-atom lDDT scoring")
    parser.add_argument("ref", help="Reference PDB/CIF")
    parser.add_argument("models", nargs="+", help="Model PDB/CIF files")
    parser.add_argument("-nc", "--no-stereocheck", action="store_true",
                        help="Skip stereochemistry checks")
    parser.add_argument("--ilddt", action="store_true",
                        help="Also compute interface lDDT (no_intrachain=True); "
                             "nan for single-chain targets")
    parser.add_argument("--chain-mapper", action="store_true",
                        help="Use ChainMapper for sequence-based chain mapping "
                             "(slower but robust when chain IDs differ)")
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

    chain_mapper = None
    if args.chain_mapper:
        from ost.mol.alg import chain_mapping as cm_mod
        chain_mapper = cm_mod.ChainMapper(ref)

    t_setup = time.time() - t0
    if args.verbose:
        n_atoms = sum(1 for _ in ref_raw.atoms)
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

            if chain_mapper is not None:
                chain_map, res_map = sequence_based_chain_mapping(chain_mapper, mdl)
            else:
                chain_map, res_map = name_based_chain_mapping(mdl, ref)

            global_lddt, ilddt = score_model(scorer, mdl, chain_map, res_map,
                                             do_ilddt=args.ilddt)
        except Exception as e:
            if args.verbose:
                print(f"# Error {model_path}: {e}", file=sys.stderr)
            global_lddt, ilddt = math.nan, math.nan

        t_model = time.time() - t1
        if args.verbose:
            print(f"# {os.path.basename(model_path)}: {t_model:.3f}s", file=sys.stderr)
        print(f"{global_lddt},{ilddt},{model_path}")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
