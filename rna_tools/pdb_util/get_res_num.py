#!/usr/bin/env python3

import argparse
from read_pdb import read_pdb
from make_tag import make_tag_with_dashes, make_tag_with_dashes_and_commas, make_tag

parser = argparse.ArgumentParser(description='Print residue numbers from PDB file(s).')
parser.add_argument('pdbfiles', nargs='+', help='PDB file(s) to read')
parser.add_argument('-csv', action='store_true', help='output as comma-separated values')
parser.add_argument('-no_dashes', action='store_true', help='output without dash-compressed ranges')
args = parser.parse_args()

for main_pdb in args.pdbfiles:

    [ coords_main, lines_main, sequence_main, chains, residues ] = read_pdb( main_pdb )

    if args.csv:
        print(make_tag_with_dashes_and_commas( residues ))
    elif args.no_dashes:
        print(make_tag( residues ))
    else:
        print(make_tag_with_dashes( residues ))
