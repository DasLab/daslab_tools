#!/usr/bin/env python3

import argparse
import gzip

def extractchain(actualpdbname, out, chains_to_extract):
    if actualpdbname.endswith('.gz'):
        with gzip.open(actualpdbname, 'rt') as f:
            lines = f.readlines()
    else:
        lines = open(actualpdbname, 'r').readlines()

    for line in lines:
        if (line.count('ATOM') or line.count('HETATM')) and (line[21:22] in chains_to_extract):
            out.write(line)
    out.close()

parser = argparse.ArgumentParser(description='Extract chain(s) from a PDB file into a new file.')
parser.add_argument('pdbfile', help='PDB file to extract from')
parser.add_argument('chains', nargs='+', help='chain ID(s) to extract')
args = parser.parse_args()

newpdbfile = args.pdbfile.replace('.pdb', ''.join(args.chains) + '.pdb')
out = open(newpdbfile, 'w')

print('Extracting to', newpdbfile, '...')

extractchain(args.pdbfile, out, args.chains)
