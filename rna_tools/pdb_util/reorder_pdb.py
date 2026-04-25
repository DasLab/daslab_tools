#!/usr/bin/env python3

import argparse
from read_pdb import read_pdb
from make_tag import make_tag_with_dashes

parser = argparse.ArgumentParser(description='Reorder atoms in PDB file(s) by chain and residue, writing to *.REORDER.pdb.')
parser.add_argument('pdbfiles', nargs='+', help='PDB file(s) to reorder')
args = parser.parse_args()

for main_pdb in args.pdbfiles:

    assert( main_pdb[-4:] == '.pdb' )
    outfile = main_pdb.replace( '.pdb', '.REORDER.pdb' )
    fid = open( outfile, 'w' )
    [ coords_main, lines_main, sequence_main, chains_main, residues_main, segids_main ] = read_pdb( main_pdb )

    chains = list(lines_main.keys())
    chains.sort()
    for chain in chains:
        segids = list(lines_main[ chain ].keys())
        segids.sort()
        for segid in segids:
            residues = list(lines_main[ chain ][ segid ].keys())
            residues.sort()
            for residue in residues:
                for atom in list(lines_main[ chain ][ segid ][ residue ].keys()):
                    fid.write(  lines_main[ chain ][ segid ][ residue ][ atom ]+'\n' )
    fid.close()
    print('Created: ', outfile)
