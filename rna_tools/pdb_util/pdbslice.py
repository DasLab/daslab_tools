#!/usr/bin/env python3

import argparse
import gzip
import sys
from os.path import basename, exists
from parse_options import get_resnum_chain, get_ints

parser = argparse.ArgumentParser(
    description='Extract a slice of residues from PDB file(s).',
    epilog=(
        'Modes:\n'
        '  -subset RES...      keep listed residues (e.g. A:1-10 B:5)\n'
        '  -segments N N...    keep residue ranges given as start/end pairs\n'
        '  -excise RES...      remove listed residues\n'
        '  (none)              range mode: last two args are startseq endseq\n'
        '\n'
        'Examples:\n'
        '  pdbslice.py file.pdb prefix -subset A:1-10\n'
        '  pdbslice.py file.pdb 100 200\n'
        '  pdbslice.py file.pdb 100 200 myprefix_\n'
        '  pdbslice.py file.pdb prefix -excise B:5'
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('all_args', nargs=argparse.REMAINDER,
                    help='pdbfile(s), flags, and positional prefix/range args')
args = parser.parse_args()

# Manually extract -subset, -segments, -excise flags from all_args,
# leaving pdbfiles and prefix/range in pdbargs.
all_args = list(args.all_args)

subset_residues, subset_chains, subset_segids = [], [], []
excise_residues, excise_chains, excise_segids = [], [], []
segment_integers = []
pdbargs = []

i = 0
while i < len(all_args):
    arg = all_args[i]
    if arg == '-subset':
        i += 1
        while i < len(all_args) and not all_args[i].startswith('-'):
            get_resnum_chain(all_args[i], subset_residues, subset_chains, subset_segids)
            i += 1
    elif arg == '-excise':
        i += 1
        while i < len(all_args) and not all_args[i].startswith('-'):
            get_resnum_chain(all_args[i], excise_residues, excise_chains, excise_segids)
            i += 1
    elif arg == '-segments':
        i += 1
        while i < len(all_args) and not all_args[i].startswith('-'):
            get_ints(all_args[i], segment_integers)
            i += 1
    else:
        pdbargs.append(arg)
        i += 1

# Expand -segments into subset residues
if segment_integers:
    assert len(segment_integers) % 2 == 0, '-segments requires an even number of integers'
    for k in range(len(segment_integers) // 2):
        for j in range(segment_integers[2 * k], segment_integers[2 * k + 1] + 1):
            subset_residues.append(j)
            subset_chains.append('')
            subset_segids.append('    ')

use_subset = len(subset_residues) > 0
use_excise = len(excise_residues) > 0

if not pdbargs:
    parser.print_help()
    sys.exit(1)

if use_excise or use_subset:
    pdbfiles = pdbargs[:-1]
    prefix = pdbargs[-1]
    use_range = False
    startseq = endseq = 0
else:
    use_range = True
    try:
        pdbfiles = pdbargs[:-2]
        startseq = int(pdbargs[-2])
        endseq = int(pdbargs[-1])
        prefix = 'region_%d_%d_' % (startseq, endseq)
    except (ValueError, IndexError):
        pdbfiles = pdbargs[:-3]
        startseq = int(pdbargs[-3])
        endseq = int(pdbargs[-2])
        prefix = pdbargs[-1]

if not pdbfiles:
    parser.print_help()
    sys.exit(1)

atomnums = []


def matches(res, chain, segid, match_res, match_chain, match_segid):
    for n in range(len(match_res)):
        if (res == match_res[n] and
                (match_chain[n] == '' or match_chain[n] == chain) and
                (match_segid[n] == '    ' or match_segid[n] == segid)):
            return True
    return False


for pdbfile in pdbfiles:
    if not exists(pdbfile):
        print('Problem: ', pdbfile, ' does not exist!')
        continue

    try:
        outid = open(prefix + basename(pdbfile), 'w')
    except Exception:
        print('failed to open outfile')
        continue

    if pdbfile.endswith('.gz'):
        lines = gzip.open(pdbfile, 'rt').readlines()
    else:
        lines = open(pdbfile).readlines()

    for line in lines:
        if len(line) > 4 and (line[:6] == 'ATOM  ' or line[:6] == 'HETATM'):
            currentchain = line[21]
            currentresidue = line[22:26]
            currentsegid = line[72:76].strip()
            if len(currentsegid) == 0:
                currentsegid = '    '
            atomnum = int(line[6:11])
            try:
                currentresidue_val = int(currentresidue)
                if use_subset and not matches(currentresidue_val, currentchain, currentsegid,
                                              subset_residues, subset_chains, subset_segids):
                    continue
                if use_excise and matches(currentresidue_val, currentchain, currentsegid,
                                          excise_residues, excise_chains, excise_segids):
                    continue
                if use_range and (int(currentresidue) < startseq or int(currentresidue) > endseq):
                    continue
            except Exception:
                continue

            atomnums.append(atomnum)
            outid.write(line)

        elif len(line) > 6 and line[:6] == 'CONECT':
            atomnum1 = int(line[6:11])
            atomnum2 = int(line[11:16])
            if atomnum1 in atomnums and atomnum2 in atomnums:
                outid.write(line)

    outid.close()
