#!/usr/bin/env python3

from Bio.PDB import PDBParser, PDBIO
import os

def split_models(input_pdb):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('input_structure', input_pdb)

    io = PDBIO()
    model_number = 1
    base_filename = os.path.splitext(input_pdb)[0]

    for model in structure:
        model_filename = f"{base_filename}_{model_number:04d}.pdb"
        io.set_structure(model)
        io.save(model_filename)
        print(f"Saved {model_filename}")
        model_number += 1

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python split_models.py <input_pdb_file>")
        sys.exit(1)

    input_pdb_file = sys.argv[1]
    split_models(input_pdb_file)
