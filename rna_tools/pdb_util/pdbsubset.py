#!/usr/bin/env python3

import argparse
import sys
from os.path import dirname, basename
from read_pdb import read_pdb
from parse_options import get_resnum_chain


def usage(parser):
    parser.print_help()
    sys.exit(1)


parser = argparse.ArgumentParser(
    description='Extract a subset of residues from one or more PDB files.',
    epilog=(
        'Residue specs: 5-9, C5-9, C:5-9, or C (whole chain).\n'
        'Positional args: pdbfile(s) residue-specs [prefix].\n'
        "Default prefix is 'subset_'."
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('args', nargs=argparse.REMAINDER,
                    help='PDB files, residue specs, and optional output prefix')
parsed = parser.parse_args()

resnums = []
chains  = []
segids  = []
pdbfiles = []
prefix = ''

for token in parsed.args:
    if token.endswith('.pdb'):
        pdbfiles.append(token)
        continue
    if get_resnum_chain(token, resnums, chains, segids):
        continue
    if len(prefix) > 0:
        print('Found two potential prefixes?', prefix, token)
        usage(parser)
    prefix = token

if len(pdbfiles) == 0:
    print('No PDB files specified.')
    usage(parser)
if len(resnums) == 0:
    print('No residue specs specified.')
    usage(parser)
if len(prefix) == 0:
    prefix = 'subset_'

print(resnums)
print(chains)
print(segids)


def get_pdb_line(lines_out, pdb_lines, resnum_desired, chain_desired, segid_desired):
    lines = []
    for chain in pdb_lines.keys():
        if chain_desired != chain and chain_desired != '': continue
        for segid in pdb_lines[chain].keys():
            if segid_desired != segid and segid_desired != '    ': continue
            if isinstance(resnum_desired, int) and (resnum_desired not in pdb_lines[chain][segid].keys()): continue

            if isinstance(resnum_desired, int):
                if len(lines) > 0:
                    print('WARNING! Found residue', resnum_desired, 'more than once: you may want to specify the chain.')
                for atom_name in pdb_lines[chain][segid][resnum_desired].keys():
                    lines.append(pdb_lines[chain][segid][resnum_desired][atom_name])
            else:
                assert resnum_desired == 'all'
                for resnum in pdb_lines[chain][segid]:
                    for atom_name in pdb_lines[chain][segid][resnum].keys():
                        lines.append(pdb_lines[chain][segid][resnum][atom_name])

    if len(lines) == 0:
        msg = 'WARNING! Did not find res num ' + str(resnum_desired)
        if chain_desired != '': msg += ' for chain ' + chain_desired
        print(msg)

    for line in lines:
        lines_out.append(line)


for pdbfile in pdbfiles:
    [coords, pdb_lines, sequence, _, __, ___] = read_pdb(pdbfile)

    lines_out = []
    for i in range(len(resnums)):
        get_pdb_line(lines_out, pdb_lines, resnums[i], chains[i], segids[i])

    pdbfile_out = '/'.join(filter(None, [
        dirname(pdbfile),
        prefix + basename(pdbfile)
    ]))
    print('Outputting: ', pdbfile_out)
    fid = open(pdbfile_out, 'w')
    for line in lines_out:
        fid.write(line + '\n')
    fid.close()
