#!/usr/bin/env python3

import argparse
from os import system

def stripchain(actualpdbname, out, startchain, newchain, chainspecified):
    lines = open(actualpdbname,'r').readlines()
    for line in lines:
        if (line.count('ATOM') or line.count('HETATM')) and (line[21:22] == startchain or not chainspecified):
            line = line[0:21]+newchain+line[22:]
        out.write(line)
    out.close()


parser = argparse.ArgumentParser(
    description='Replace chain ID in PDB file(s) in place.',
    epilog='The last argument is always the new chain ID; all preceding arguments are PDB files.',
)
parser.add_argument('pdbfiles_and_chain', nargs='+', metavar='pdbfile',
                    help='one or more PDB files followed by the new chain ID as the last argument')
args = parser.parse_args()

if len(args.pdbfiles_and_chain) < 2:
    parser.error('provide at least one PDB file and a new chain ID')

pdbfiles = args.pdbfiles_and_chain[:-1]
newchain = args.pdbfiles_and_chain[-1]

if newchain == '-' or newchain == '_':
    newchain = ' '

for actualpdbname in pdbfiles:
    out = open('tmp', 'w')
    stripchain(actualpdbname, out, ' ', newchain, 0)
    system('mv tmp ' + actualpdbname)
