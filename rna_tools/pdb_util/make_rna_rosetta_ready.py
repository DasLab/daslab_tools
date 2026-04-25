#!/usr/bin/env python3

import argparse
import sys
from os.path import basename
from rna_server_conversions import make_rna_rosetta_ready

parser = argparse.ArgumentParser(
    description='Convert a PDB file to Rosetta-ready RNA format.',
)
parser.add_argument('pdbname', help='input PDB file (adds .pdb extension if missing)')
parser.add_argument('-remove_ions', action='store_true', help='remove ion HETATM records')
parser.add_argument('-old_rna', action='store_true', help='use old RNA residue naming')
parser.add_argument('-nochain', action='store_true', help='remove chain IDs from output')
parser.add_argument('-ignorechain', action='store_true', help='ignore chain IDs when reading')
parser.add_argument('-no_renumber', action='store_true', help='skip residue renumbering')
parser.add_argument('-reassign_chainids', metavar='CHAINIDS', default=None,
                    help='reassign chain IDs (e.g. AB)')
parser.add_argument('chainids', nargs='*',
                    help='chain(s) to extract (single-char); if absent, all chains are processed')
args = parser.parse_args()

pdbname = args.pdbname
if pdbname[-4:] != '.pdb' and pdbname[-7:] != '.pdb.gz':
    pdbname += '.pdb'

new_chainids = args.reassign_chainids or []

chainids = args.chainids
if len(chainids) > 0 and len(chainids[0]) == 1:
    pdbnames = [pdbname]
else:
    pdbnames = [pdbname] + chainids
    chainids = []
    args.ignorechain = True

for pdbname in pdbnames:
    pdblines = '\n'.join(open(pdbname, 'r').readlines())
    outputstring = make_rna_rosetta_ready(
        pdblines, args.nochain, args.ignorechain, chainids,
        new_chainids, args.no_renumber, args.remove_ions, args.old_rna
    )
    outfile = basename(pdbname).lower()
    outfile = outfile.replace('.pdb', '_RNA.pdb').replace('.gz', '')
    outid = open(outfile, 'w')
    outid.write(outputstring)
    print('Writing ... ' + outfile)
    outid.close()
