#!/usr/bin/env python3

import argparse
from sys import stdout
from os.path import basename
from get_sequence import get_sequences
from make_tag import make_tag_with_dashes

parser = argparse.ArgumentParser(
    description='Extract sequence(s) from PDB file(s) in FASTA format.',
)
parser.add_argument('pdbfiles', nargs='+', help='PDB file(s) to extract sequence from')
parser.add_argument('-nochain', action='store_true',
                    help='omit chain identifiers from FASTA headers')
args = parser.parse_args()

for pdbname in args.pdbfiles:
    (sequences, chains, resnums, segids) = get_sequences(pdbname, args.nochain)
    for i in range(len(sequences)):
        if len(sequences[i]) == 0: continue
        stdout.write('>%s %s\n' % (basename(pdbname), make_tag_with_dashes(resnums[i], chains[i], segids[i])))
        stdout.write(sequences[i])
        stdout.write('\n')
        stdout.write('\n')
