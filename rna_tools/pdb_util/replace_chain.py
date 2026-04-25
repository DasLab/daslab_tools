#!/usr/bin/env python3

import argparse
from sys import stdout

def stripchain(actualpdbname, out, startchain, newchain, chainspecified):
    lines = open(actualpdbname,'r').readlines()
    for line in lines:
        if (line.count('ATOM') or line.count('HETATM')) and (line[21:22] == startchain or not chainspecified):
            line = line[0:21]+newchain+line[22:]
        out.write(line)
    out.close()


parser = argparse.ArgumentParser(
    description='Replace chain ID in a PDB file, writing result to stdout.',
    epilog='With one chain argument: replace all chains.\nWith two: replace startchain with newchain.',
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('pdbfile', help='PDB file to process')
parser.add_argument('chains', nargs='+', metavar='chain',
                    help='newchain, or startchain newchain')
args = parser.parse_args()

if len(args.chains) == 1:
    startchain = ' '
    newchain = args.chains[0]
    chainspecified = 0
elif len(args.chains) == 2:
    startchain = args.chains[0]
    newchain = args.chains[1]
    chainspecified = 1
else:
    parser.error('expected 1 or 2 chain arguments')

if startchain == '-' or startchain == '_':
    startchain = ' '
if newchain == '-' or newchain == '_':
    newchain = ' '

stripchain(args.pdbfile, stdout, startchain, newchain, chainspecified)
