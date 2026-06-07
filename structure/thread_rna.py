#!/usr/bin/env python3
"""
thread_rna.py

Thread target sequence onto backbone atoms from a template PDB (6CHR), based on a hand-curated alignment.

Usage:
    python thread_rna.py -a target_denszok_handalign.fasta -p 6CHR.pdb -c A -o target_thread.pdb

Requirements:
    biopython
"""
import argparse
import math
import sys
import numpy as np
from Bio import SeqIO
from Bio.PDB import PDBParser, PDBIO, Structure, Model, Chain, Residue, Atom

# mapping common PDB resnames to single-letter nucleotide
RESMAP = {
    'A': 'A', 'G': 'G', 'C': 'C', 'U': 'U',
    'ADE': 'A', 'GUA': 'G', 'CYT': 'C', 'URA': 'U',
    'DA': 'A', 'DG': 'G', 'DC': 'C', 'DT': 'U',
}

def canonical_nt_from_resname(resname):
    if resname is None:
        return None
    rn = resname.strip().upper()
    if rn in RESMAP:
        return RESMAP[rn]
    if len(rn) >= 1 and rn[0] in ('A','C','G','U','T'):
        letter = rn[0]
        if letter == 'T':
            letter = 'U'
        return letter
    return None

def parse_alignment(aln_fasta):
    recs = list(SeqIO.parse(aln_fasta, "fasta"))
    if len(recs) < 2:
        raise ValueError("Expect at least two sequences in the alignment FASTA (target first, template PDB second).")
    ba_seq = str(recs[0].seq).upper()
    pdb_aln_seq = str(recs[1].seq).upper()
    if len(ba_seq) != len(pdb_aln_seq):
        raise ValueError("Alignment sequences have different lengths.")
    return ba_seq, pdb_aln_seq

def build_chain_residue_list(structure, chain_id):
    models = list(structure.get_models())
    if not models:
        raise ValueError("No models found in PDB.")
    model = models[0]
    if chain_id not in [c.get_id() for c in model.get_chains()]:
        raise ValueError(f"Chain {chain_id} not found in PDB.")
    chain = model[chain_id]
    residues = [res for res in chain.get_residues() if res.id[0] == ' ']
    return residues, chain

def is_backbone_atom_name(aname):
    n = aname.strip()
    if n == "P":
        return True
    if n in ("O1P", "O2P", "OP1", "OP2"):
        return True
    if "'" in n:
        return True
    return False

# ─── Ideal base geometry (NAKB Parkinson 1996) ──────────────────────────────

def compute_torsion(p1, p2, p3, p4):
    """Dihedral p1-p2-p3-p4 in degrees."""
    b1 = p2 - p1; b2 = p3 - p2; b3 = p4 - p3
    n1 = np.cross(b1, b2); n2 = np.cross(b2, b3)
    l1 = np.linalg.norm(n1); l2 = np.linalg.norm(n2)
    if l1 < 1e-8 or l2 < 1e-8:
        return 0.0
    n1 /= l1; n2 /= l2
    m = np.cross(n1, b2 / np.linalg.norm(b2))
    return float(np.degrees(np.arctan2(np.dot(m, n2), np.dot(n1, n2))))

def _nerf(a, b, c, bond, angle_deg, dihedral_deg):
    """Place atom d from a-b-c frame: d bonded to c at bond Å, angle b-c-d, dihedral a-b-c-d."""
    ang = math.radians(angle_deg); dih = math.radians(dihedral_deg)
    bc = c - b; bc /= np.linalg.norm(bc)
    n = np.cross(a - b, bc)
    if np.linalg.norm(n) < 1e-8:
        n = np.array([0., 0., 1.]) if abs(bc[2]) < 0.9 else np.array([1., 0., 0.])
    n /= np.linalg.norm(n)
    m = np.cross(bc, n)
    return c + bond * (-math.cos(ang) * bc + math.sin(ang) * (math.cos(dih) * m + math.sin(dih) * n))

def _rot2d(v, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([v[0]*c - v[1]*s, v[0]*s + v[1]*c])

def _ring_step(pos, incoming_dir, bond, int_angle):
    """CCW ring traversal step; returns (new_pos, new_dir)."""
    nd = _rot2d(incoming_dir, 180.0 - int_angle)
    nd /= np.linalg.norm(nd)
    return pos + bond * nd, nd

def _build_ideal_base_3d(base_type):
    """Canonical frame: C1' at origin, glycosidic N along +z, chi-atom in xz (x>0)."""
    def to3d(c2d, d_C1N):
        return {name: np.array([x, 0.0, y + d_C1N]) for name, (x, y) in c2d.items()}

    c = {}
    if base_type == 'A':
        d = 1.462
        c4d = _rot2d(np.array([0., -1.]), 126.3)
        c8d = _rot2d(np.array([0., -1.]), -127.7)
        c.update({'N9': np.zeros(2), 'C4': 1.374 * c4d, 'C8': 1.373 * c8d})
        p, di = c['C4'].copy(), c4d
        p, di = _ring_step(p, di, 1.383, 105.8); c['C5'] = p.copy()
        p, di = _ring_step(p, di, 1.388, 110.7); c['N7'] = p.copy()
        n3d = _rot2d(-c4d, 127.4); c['N3'] = c['C4'] + 1.344 * n3d
        p, di = c['N3'].copy(), n3d
        p, di = _ring_step(p, di, 1.331, 110.6); c['C2'] = p.copy()
        p, di = _ring_step(p, di, 1.339, 129.3); c['N1'] = p.copy()
        p, di = _ring_step(p, di, 1.351, 118.6); c['C6'] = p.copy()
        u = c['N1'] - c['C6']; u /= np.linalg.norm(u)
        c['N6'] = c['C6'] + 1.335 * _rot2d(u, 118.6)
        return to3d(c, d)
    elif base_type == 'G':
        d = 1.459
        c4d = _rot2d(np.array([0., -1.]), 126.5)
        c8d = _rot2d(np.array([0., -1.]), -127.0)
        c.update({'N9': np.zeros(2), 'C4': 1.375 * c4d, 'C8': 1.374 * c8d})
        p, di = c['C4'].copy(), c4d
        p, di = _ring_step(p, di, 1.379, 105.4); c['C5'] = p.copy()
        p, di = _ring_step(p, di, 1.388, 110.8); c['N7'] = p.copy()
        n3d = _rot2d(-c4d, 126.0); c['N3'] = c['C4'] + 1.350 * n3d
        p, di = c['N3'].copy(), n3d
        p, di = _ring_step(p, di, 1.323, 111.9); c['C2'] = p.copy()
        p, di = _ring_step(p, di, 1.373, 123.9); c['N1'] = p.copy()
        p, di = _ring_step(p, di, 1.391, 125.1); c['C6'] = p.copy()
        u = c['N1'] - c['C6']; u /= np.linalg.norm(u)
        c['O6'] = c['C6'] + 1.240 * _rot2d(u, 119.9)
        u2 = c['N1'] - c['C2']; u2 /= np.linalg.norm(u2)
        c['N2'] = c['C2'] + 1.341 * _rot2d(u2, -116.2)
        return to3d(c, d)
    elif base_type == 'C':
        d = 1.470
        c2d = _rot2d(np.array([0., -1.]), 118.8)
        c6d = _rot2d(np.array([0., -1.]), -120.8)
        c.update({'N1': np.zeros(2), 'C2': 1.397 * c2d, 'C6': 1.367 * c6d})
        p, di = c['C2'].copy(), c2d
        p, di = _ring_step(p, di, 1.353, 119.2); c['N3'] = p.copy()
        p, di = _ring_step(p, di, 1.335, 119.9); c['C4'] = p.copy()
        p, di = _ring_step(p, di, 1.425, 121.9); c['C5'] = p.copy()
        u = c['N3'] - c['C2']; u /= np.linalg.norm(u)
        c['O2'] = c['C2'] + 1.240 * _rot2d(u, -121.9)
        u2 = c['N3'] - c['C4']; u2 /= np.linalg.norm(u2)
        c['N4'] = c['C4'] + 1.335 * _rot2d(u2, 118.0)
        return to3d(c, d)
    elif base_type == 'U':
        d = 1.469
        c2d = _rot2d(np.array([0., -1.]), 117.7)
        c6d = _rot2d(np.array([0., -1.]), -121.2)
        c.update({'N1': np.zeros(2), 'C2': 1.381 * c2d, 'C6': 1.375 * c6d})
        p, di = c['C2'].copy(), c2d
        p, di = _ring_step(p, di, 1.373, 114.9); c['N3'] = p.copy()
        p, di = _ring_step(p, di, 1.380, 127.0); c['C4'] = p.copy()
        p, di = _ring_step(p, di, 1.431, 114.6); c['C5'] = p.copy()
        u = c['N3'] - c['C2']; u /= np.linalg.norm(u)
        c['O2'] = c['C2'] + 1.219 * _rot2d(u, -122.2)
        u2 = c['N3'] - c['C4']; u2 /= np.linalg.norm(u2)
        c['O4'] = c['C4'] + 1.232 * _rot2d(u2, 119.4)
        return to3d(c, d)
    else:
        raise ValueError(f"Unknown base type: {base_type}")

IDEAL_BASE_COORDS = {b: _build_ideal_base_3d(b) for b in ('A', 'G', 'C', 'U')}
GLYCOSIDIC_N   = {'A': 'N9', 'G': 'N9', 'C': 'N1', 'U': 'N1'}
CHI_ATOM       = {'A': 'C4', 'G': 'C4', 'C': 'C2', 'U': 'C2'}
CHI_ANGLE_AT_N = {'A': 126.3, 'G': 126.5, 'C': 118.8, 'U': 117.7}
N_BOND         = {'A': 1.462, 'G': 1.459, 'C': 1.470, 'U': 1.469}
NCHI_BOND      = {'A': 1.374, 'G': 1.375, 'C': 1.397, 'U': 1.381}

def _get_atom(res, name):
    try:
        return np.array(res[name].get_coord(), dtype=float)
    except KeyError:
        return None

def get_chi_angle(res, base_type):
    o4p = _get_atom(res, "O4'"); c1p = _get_atom(res, "C1'")
    n   = _get_atom(res, GLYCOSIDIC_N[base_type])
    c   = _get_atom(res, CHI_ATOM[base_type])
    if any(x is None for x in (o4p, c1p, n, c)):
        return None
    return compute_torsion(o4p, c1p, n, c)

def build_base_atoms(c1p, o4p, c2p, base_type, chi_deg):
    """Return {atom_name: coord_3d} for ideal base at c1p with chi_deg (O4'-C1'-N-Cchi)."""
    n_pos     = _nerf(c2p, o4p, c1p, N_BOND[base_type], 108.0, 120.0)
    c_chi_pos = _nerf(o4p, c1p, n_pos, NCHI_BOND[base_type], CHI_ANGLE_AT_N[base_type], chi_deg)
    canon = IDEAL_BASE_COORDS[base_type]
    p2 = canon[GLYCOSIDIC_N[base_type]]
    p3 = canon[CHI_ATOM[base_type]]
    e1 = p2 / np.linalg.norm(p2)
    e2 = p3 - np.dot(p3, e1) * e1; e2 /= np.linalg.norm(e2)
    e3 = np.cross(e1, e2)
    q2 = n_pos - c1p; f1 = q2 / np.linalg.norm(q2)
    q3 = c_chi_pos - c1p; f2 = q3 - np.dot(q3, f1) * f1; f2 /= np.linalg.norm(f2)
    f3 = np.cross(f1, f2)
    R = np.column_stack([f1, f2, f3]) @ np.column_stack([e1, e2, e3]).T
    return {name: R @ pos + c1p for name, pos in canon.items()}

# ─── main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Thread target sequence onto template PDB backbone atoms.")
    parser.add_argument("-a", "--alignment", required=True, help="Alignment FASTA (target first, then 6CHR)")
    parser.add_argument("-p", "--pdb", required=True, help="PDB file. Residue numbering should correspond to 1,2,3,.. for FASTA")
    parser.add_argument("-c", "--chain", default="A", help="Chain ID in PDB to use (default A)")
    parser.add_argument("-o", "--out", default="target_thread.pdb", help="Output PDB filename")
    parser.add_argument("--zerofill", action="store_true", help="Add C1' at (0,0,0) for target residues missing from template")
    parser.add_argument("--no_bases", action="store_true", help="Omit base atoms (backbone only; legacy behavior)")
    args = parser.parse_args()

    ba_seq, pdb_aln_seq = parse_alignment(args.alignment)
    aln_len = len(ba_seq)
    full_pdb_seq = pdb_aln_seq.replace('-', '')

    parser_pdb = PDBParser(QUIET=True)
    structure = parser_pdb.get_structure("templ", args.pdb)
    residues_list, chain = build_chain_residue_list(structure, args.chain)

    pdb_chain_letters = []
    for res in residues_list:
        letter = canonical_nt_from_resname(res.get_resname())
        if letter is None:
            raise SystemExit(f"ERROR: Could not canonicalize PDB residue name '{res.get_resname()}' for residue {res.get_id()} in chain {args.chain}.")
        pdb_chain_letters.append(letter)

    seqpos_to_res = {}
    pos_in_full = 0
    for i, letter in enumerate(pdb_chain_letters):
        while pos_in_full < len(full_pdb_seq):
            if full_pdb_seq[pos_in_full] == letter:
                seqpos_to_res[pos_in_full + 1] = residues_list[i]
                pos_in_full += 1
                break
            pos_in_full += 1

    ba_pos = 0
    pdb_pos = 0
    to_write = []

    for col in range(aln_len):
        ba_ch = ba_seq[col]
        pdb_ch = pdb_aln_seq[col]
        if ba_ch != '-':
            ba_pos += 1
        if pdb_ch != '-':
            pdb_pos += 1
        if ba_ch != '-' and pdb_ch != '-':
            if pdb_pos in seqpos_to_res:
                res = seqpos_to_res[pdb_pos]
                res_letter = canonical_nt_from_resname(res.get_resname())
                if res_letter is None:
                    raise SystemExit(f"ERROR: Could not canonicalize PDB residue name '{res.get_resname()}' at {res.get_id()}.")
                if res_letter != pdb_ch:
                    raise SystemExit(
                        f"ERROR: PDB residue '{res_letter}' at chain {args.chain} residue {res.get_id()} "
                        f"does not match alignment letter '{pdb_ch}' at column {col+1}. Aborting."
                    )
                to_write.append((ba_pos, res, ba_ch))

    target_full_seq = ba_seq.replace('-', '')

    new_struct = Structure.Structure("target_thread")
    new_model = Model.Model(0)
    new_chain = Chain.Chain(args.chain)
    new_model.add(new_chain)
    new_struct.add(new_model)

    atom_serial = 1
    write_idx = 0
    for resnum_1based in range(1, len(target_full_seq) + 1):
        if write_idx < len(to_write) and to_write[write_idx][0] == resnum_1based:
            target_resnum, src_res, target_letter = to_write[write_idx]
            write_idx += 1
            src_base = canonical_nt_from_resname(src_res.get_resname())
            new_id = (' ', int(target_resnum), ' ')
            new_res = Residue.Residue(new_id, target_letter, '')

            def add_atom(aname, coord, bfactor=0.0, occupancy=1.0, altloc=" ", element=None):
                nonlocal atom_serial
                if element is None:
                    s = aname.strip()
                    element = s[0].upper() if s and s[0].isalpha() else "X"
                fullname = f"{aname:>4}"
                new_atom = Atom.Atom(aname, np.array(coord, dtype='f'), bfactor, occupancy,
                                     altloc, fullname, atom_serial, element)
                new_res.add(new_atom)
                atom_serial += 1

            # Backbone atoms from template
            for atom in src_res.get_atoms():
                aname = atom.get_name()
                if not is_backbone_atom_name(aname):
                    continue
                elem = atom.element.strip() if hasattr(atom, "element") and atom.element else None
                add_atom(aname, atom.get_coord(), atom.get_bfactor(),
                         atom.get_occupancy() if atom.get_occupancy() is not None else 1.0,
                         atom.get_altloc() if hasattr(atom, "get_altloc") else " ", elem)

            # Base atoms
            if not args.no_bases:
                if src_base == target_letter:
                    # Same base: copy directly from template
                    for atom in src_res.get_atoms():
                        aname = atom.get_name()
                        if is_backbone_atom_name(aname):
                            continue
                        elem = atom.element.strip() if hasattr(atom, "element") and atom.element else None
                        add_atom(aname, atom.get_coord(), atom.get_bfactor(),
                                 atom.get_occupancy() if atom.get_occupancy() is not None else 1.0,
                                 atom.get_altloc() if hasattr(atom, "get_altloc") else " ", elem)
                else:
                    # Different base: ideal geometry, preserve chi from source
                    c1p = _get_atom(src_res, "C1'")
                    o4p = _get_atom(src_res, "O4'")
                    c2p = _get_atom(src_res, "C2'")
                    if c1p is None or o4p is None or c2p is None:
                        print(f"Warning: missing ribose atoms at residue {target_resnum}, "
                              "skipping base placement.", file=sys.stderr)
                    else:
                        chi = get_chi_angle(src_res, src_base)
                        if chi is None:
                            chi = -160.0
                            print(f"Warning: could not read chi at residue {target_resnum}, "
                                  f"using default {chi}°.", file=sys.stderr)
                        for aname, coord in build_base_atoms(c1p, o4p, c2p, target_letter, chi).items():
                            add_atom(aname, coord, element=aname[0].upper())

            if len(list(new_res.get_atoms())) > 0:
                new_chain.add(new_res)

        elif args.zerofill:
            target_letter = target_full_seq[resnum_1based - 1]
            new_id = (' ', resnum_1based, ' ')
            new_res = Residue.Residue(new_id, target_letter, '')
            coord = np.array([0.0, 0.0, 0.0], dtype='f')
            new_atom = Atom.Atom("C1'", coord, 0.0, 1.0, " ", " C1'", atom_serial, "C")
            new_res.add(new_atom)
            atom_serial += 1
            new_chain.add(new_res)

    io = PDBIO()
    io.set_structure(new_struct)
    io.save(args.out)
    print(f"Wrote threaded backbone PDB to {args.out}")

if __name__ == "__main__":
    main()
