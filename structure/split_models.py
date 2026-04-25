#!/usr/bin/env python3

import argparse
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
    parser = argparse.ArgumentParser(description='Split a multi-model PDB file into individual model files.')
    parser.add_argument('pdbfile', help='input PDB file containing multiple models')
    args = parser.parse_args()
    split_models(args.pdbfile)
