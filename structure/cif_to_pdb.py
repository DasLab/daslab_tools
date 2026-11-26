#!/usr/bin/env python3

import argparse
import os
from Bio.PDB import MMCIFParser, PDBIO

parser = argparse.ArgumentParser(
                    prog = 'cif_to_pdb.py',
                    description = 'Convert mmCIF file(s) to PDB format')

parser.add_argument('cif_files', nargs='+', help='Input .cif file(s)')
parser.add_argument('-o', '--outdir', default=None, help='Output directory (default: same as input)')

args = parser.parse_args()

mmcif_parser = MMCIFParser(QUIET=True)

for cif_file in args.cif_files:
    if not os.path.isfile(cif_file):
        print(f'File not found: {cif_file}')
        continue

    base = os.path.splitext(os.path.basename(cif_file))[0]
    outdir = args.outdir if args.outdir else os.path.dirname(os.path.abspath(cif_file))
    pdb_file = os.path.join(outdir, base + '.pdb')

    structure = mmcif_parser.get_structure(base, cif_file)

    io = PDBIO()
    io.set_structure(structure)
    io.save(pdb_file)

    print(f'{cif_file} -> {pdb_file}')
