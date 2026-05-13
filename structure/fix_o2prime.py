#!/usr/bin/env python3
"""
fix_o2prime.py — Strip O2' atoms from RNA structure files and rebuild them
using Arena.

Bad O2' geometry (e.g. from early Protenix checkpoints) causes all-atom LDDT
to report 0.0; rebuilding from the remaining heavy atoms via Arena restores
meaningful LDDT while leaving backbone / base atoms untouched.

Usage:
    python3 fix_o2prime.py file1.cif file2.pdb ...
    python3 fix_o2prime.py *.cif --outdir /tmp/fixed/

Output files are named {stem}.fixO2prime.{ext} (same format as input).

Note: Arena requires RNA-only input. Use --strip-nonrna if the structure
contains protein or ligand chains. Those chains are removed before Arena and
are NOT restored in the output (the fixed file is suitable for LDDT scoring
but not for visualising the full complex).
"""

import argparse, shutil, subprocess, sys, tempfile
from pathlib import Path

from Bio.PDB import MMCIFParser, PDBParser, PDBIO, MMCIFIO

# Standard + common modified RNA residue names
RNA_RESIDUES = {
    'A', 'C', 'G', 'U',
    'PSU', '5MU', 'H2U', 'M2G', 'YG', 'OMG', 'OMC', 'OMU',
    '2MG', '7MG', 'A2M', 'G7M', 'MA6', 'I', 'INO',
}


def strip_o2prime(structure):
    removed = 0
    for model in structure:
        for chain in model:
            for residue in chain:
                if "O2'" in residue:
                    residue.detach_child("O2'")
                    removed += 1
    return removed


def strip_nonrna(structure):
    for model in structure:
        empty_chains = []
        for chain in model:
            non_rna = [r.id for r in chain if r.resname.strip() not in RNA_RESIDUES]
            for rid in non_rna:
                chain.detach_child(rid)
            if not list(chain.get_residues()):
                empty_chains.append(chain.id)
        for cid in empty_chains:
            model.detach_child(cid)


def _patch_cif_missing_atom_fields(filepath: Path) -> Path:
    """Return a path to a (possibly patched) CIF with B_iso_or_equiv and occupancy.

    Some Protenix CIF outputs omit these columns; BioPython's MMCIFParser requires
    them.  When absent, we inject dummy columns (value 1.00) into the _atom_site
    loop before parsing.  A temp file is written only when patching is needed;
    otherwise the original path is returned unchanged.
    """
    NEEDED = ('_atom_site.B_iso_or_equiv', '_atom_site.occupancy')
    text = filepath.read_text(errors='replace')
    missing = [f for f in NEEDED if f not in text]
    if not missing:
        return filepath

    lines = text.splitlines(keepends=True)
    out = []
    in_atom_header = False
    in_atom_data = False

    for line in lines:
        s = line.strip()
        if s == 'loop_':
            in_atom_header = False
            in_atom_data = False
        if s.startswith('_atom_site.'):
            in_atom_header = True
            in_atom_data = False
        elif in_atom_header and s and not s.startswith('#'):
            # First non-field line after the header → inject missing field names
            for f in missing:
                out.append(f + '\n')
            in_atom_header = False
            in_atom_data = True

        if in_atom_data and s and not s.startswith('_') and s not in ('#', 'loop_'):
            out.append(line.rstrip('\n') + (' 1.00' * len(missing)) + '\n')
        else:
            out.append(line)

    tmp = Path(tempfile.mktemp(suffix='.cif'))
    tmp.write_text(''.join(out))
    return tmp


def load_structure(filepath: Path):
    ext = filepath.suffix.lower()
    if ext in ('.cif', '.mmcif'):
        patched = _patch_cif_missing_atom_fields(filepath)
        try:
            return MMCIFParser(QUIET=True).get_structure(filepath.stem, str(patched)), True
        finally:
            if patched != filepath:
                patched.unlink(missing_ok=True)
    return PDBParser(QUIET=True).get_structure(filepath.stem, str(filepath)), False


def save_structure(structure, outpath: Path, is_cif: bool):
    if is_cif:
        io = MMCIFIO()
    else:
        io = PDBIO()
    io.set_structure(structure)
    io.save(str(outpath))


def run_arena(input_pdb: Path, output_pdb: Path, option: int = 5):
    result = subprocess.run(
        ['Arena', str(input_pdb), str(output_pdb), str(option)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Arena exited {result.returncode}: {result.stderr[:500]}")
    if not output_pdb.exists():
        raise RuntimeError("Arena ran but produced no output file")


def process_file(filepath: Path, outdir: Path | None, do_strip_nonrna: bool,
                 arena_option: int) -> Path:
    structure, is_cif = load_structure(filepath)

    if do_strip_nonrna:
        strip_nonrna(structure)

    n_removed = strip_o2prime(structure)
    print(f"  {filepath.name}: stripped {n_removed} O2' atoms")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_in  = Path(tmpdir) / "stripped.pdb"
        tmp_out = Path(tmpdir) / "arena_out.pdb"

        # Write RNA-only PDB for Arena
        pdbio = PDBIO()
        pdbio.set_structure(structure)
        pdbio.save(str(tmp_in))

        run_arena(tmp_in, tmp_out, option=arena_option)

        fixed = PDBParser(QUIET=True).get_structure("fixed", str(tmp_out))

    # Count how many O2' Arena added back
    n_added = sum(1 for m in fixed for ch in m for r in ch if "O2'" in r)
    print(f"  {filepath.name}: Arena rebuilt {n_added} O2' atoms")

    out_name = filepath.stem + ".fixO2prime" + filepath.suffix
    out_path = (outdir / out_name) if outdir else filepath.parent / out_name
    save_structure(fixed, out_path, is_cif)
    print(f"  → {out_path}")
    return out_path


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("files", nargs="+", help="CIF or PDB input files")
    ap.add_argument("--outdir", default=None,
                    help="Output directory (default: same directory as each input file)")
    ap.add_argument("--strip-nonrna", action="store_true",
                    help="Remove non-RNA chains before Arena (needed for RNA+protein targets)")
    ap.add_argument("--arena-option", type=int, default=5, choices=[1, 2, 3, 4, 5, 7],
                    help="Arena reconstruction option (default 5)")
    args = ap.parse_args()

    if not shutil.which('Arena'):
        sys.exit("Arena not found in PATH. Download and install from https://github.com/pylelab/Arena")

    outdir = Path(args.outdir) if args.outdir else None
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)

    errors = 0
    for f in args.files:
        try:
            process_file(Path(f).resolve(), outdir, args.strip_nonrna, args.arena_option)
        except Exception as e:
            print(f"  ERROR {f}: {e}", file=sys.stderr)
            errors += 1

    if errors:
        sys.exit(f"{errors} file(s) failed")


if __name__ == "__main__":
    main()
