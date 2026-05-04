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
import sys
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
    # fallback: first letter
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
    # keep only standard residues (het flag ' ')
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

def main():
    parser = argparse.ArgumentParser(description="Thread target sequence onto template PDB backbone atoms.")
    parser.add_argument("-a", "--alignment", required=True, help="Alignment FASTA (target first, then 6CHR)")
    parser.add_argument("-p", "--pdb", required=True, help="PDB file (e.g., 6CHR.pdb). Residue numbering should correspond to 1,2,3,.. for FASTA")
    parser.add_argument("-c", "--chain", default="A", help="Chain ID in PDB to use (default A)")
    parser.add_argument("-o", "--out", default="target_thread.pdb", help="Output PDB filename")
    parser.add_argument("--zerofill", action="store_true", help="Add C1' atom at (0,0,0) for target residues missing from template")
    args = parser.parse_args()

    ba_seq, pdb_aln_seq = parse_alignment(args.alignment)
    aln_len = len(ba_seq)
    full_pdb_seq = pdb_aln_seq.replace('-', '')  # full template sequence (no gaps), positions are 1..len

    parser_pdb = PDBParser(QUIET=True)
    structure = parser_pdb.get_structure("templ", args.pdb)
    residues_list, chain = build_chain_residue_list(structure, args.chain)

    # Build sequence from PDB chain residues (the residues actually present in PDB file)
    pdb_chain_letters = []
    for res in residues_list:
        letter = canonical_nt_from_resname(res.get_resname())
        if letter is None:
            raise SystemExit(f"ERROR: Could not canonicalize PDB residue name '{res.get_resname()}' for residue {res.get_id()} in chain {args.chain}.")
        pdb_chain_letters.append(letter)

    # Map the PDB-chain sequence as a subsequence into the alignment 6CHR full sequence
    # greedy scan: for each letter in pdb_chain_letters find next matching letter in full_pdb_seq
    seqpos_to_res = {}  # alignment-position (1-based in full_pdb_seq) -> residue object
    pos_in_full = 0
    for i, letter in enumerate(pdb_chain_letters):
        found = False
        while pos_in_full < len(full_pdb_seq):
            if full_pdb_seq[pos_in_full] == letter:
                # map this alignment full_seq position (1-based) to residues_list[i]
                seqpos_to_res[pos_in_full + 1] = residues_list[i]
                pos_in_full += 1
                found = True
                break
            pos_in_full += 1
        if not found:
            pass
            # couldn't find mapping -> PDB chain sequence is not a subsequence of the alignment 6CHR sequence
            #raise SystemExit(f"ERROR: PDB chain sequence (derived from chain {args.chain}) is not a subsequence of the 6CHR sequence in the alignment FASTA. Failed to map residue {i+1} (letter '{letter}'). Aborting.")

    # At this point, seqpos_to_res maps alignment 6CHR positions (1-based in full_pdb_seq) that are present in the PDB
    # Iterate the alignment columns; for columns where both target and 6CHR have residues, check PDB residue identity matches the alignment's 6CHR letter, error if not.
    ba_pos = 0
    pdb_pos = 0  # position in full_pdb_seq (counts non-gaps)
    to_write = []

    for col in range(aln_len):
        ba_ch = ba_seq[col]
        pdb_ch = pdb_aln_seq[col]
        if ba_ch != '-':
            ba_pos += 1
        if pdb_ch != '-':
            pdb_pos += 1
        if ba_ch != '-' and pdb_ch != '-':
            # check that this pdb_pos maps to a resolved residue in PDB (seqpos_to_res)
            if pdb_pos in seqpos_to_res:
                res = seqpos_to_res[pdb_pos]
                res_letter = canonical_nt_from_resname(res.get_resname())
                if res_letter is None:
                    raise SystemExit(f"ERROR: Could not canonicalize PDB residue name '{res.get_resname()}' at {res.get_id()} while checking alignment correspondence.")
                # Now enforce that the PDB residue identity matches the alignment 6CHR letter
                # Treat T in PDB as U for comparison
                if res_letter != pdb_ch:
                    # if res_letter is T treated as U, we already converted T->U in canonicalization
                    raise SystemExit(f"ERROR: PDB residue identity '{res_letter}' (from PDB resname '{res.get_resname()}') at chain {args.chain} residue {res.get_id()} does not match the 6CHR letter '{pdb_ch}' in the alignment at alignment column {col+1}. Aborting.")
                # Record mapping: write residue for this target position using this PDB residue as template
                to_write.append((ba_pos, res, ba_ch))
            else:
                # template residue not resolved in PDB -> skip (silent)
                continue

    import numpy as np

    target_full_seq = ba_seq.replace('-', '')
    covered_resnums = set(r[0] for r in to_write)

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
            new_id = (' ', int(target_resnum), ' ')
            new_res = Residue.Residue(new_id, target_letter, '')
            for atom in src_res.get_atoms():
                aname = atom.get_name()
                if not is_backbone_atom_name(aname):
                    continue
                coord = atom.get_coord()
                bfactor = atom.get_bfactor()
                occupancy = atom.get_occupancy() if atom.get_occupancy() is not None else 1.00
                altloc = atom.get_altloc() if hasattr(atom, "get_altloc") else " "
                fullname = f"{aname:>4}"
                element = None
                if hasattr(atom, "element") and atom.element is not None:
                    element = atom.element.strip()
                else:
                    s = aname.strip()
                    element = s[0].upper() if s and s[0].isalpha() else "X"
                new_atom = Atom.Atom(aname, coord, bfactor, occupancy, altloc, fullname, atom_serial, element)
                new_res.add(new_atom)
                atom_serial += 1
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
