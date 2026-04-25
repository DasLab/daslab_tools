#!/usr/bin/env python3

import argparse
from sys import stdout
import glob

parser = argparse.ArgumentParser(
    description='Concatenate Rosetta silent/out files, deduplicating header lines.',
    epilog='Output goes to stdout unless -o is specified.',
)
parser.add_argument('outfiles', nargs='+', help='input .out / silent files (glob patterns accepted)')
parser.add_argument('-o', dest='final_outfile', metavar='OUTPUT', default=None,
                    help='write output to this file instead of stdout')
args = parser.parse_args()

if args.final_outfile is None:
    fid = stdout
else:
    fid = open(args.final_outfile, 'w')

sequence_line_found    = 0
description_line_found = 0
n_file = -1

for out_f in args.outfiles:
    all_files = glob.glob(out_f)
    for filename in all_files:
        data = open(filename)
        n_file += 1
        for line in data:
            line = line[:-1]
            if not line: break

            if line[:9] == 'SEQUENCE:':
                if sequence_line_found: continue
                else: sequence_line_found = 1

            if line.find('description') > -1:
                if description_line_found: continue
                else: description_line_found = 1

            description_index = line.find(' S_')
            if description_index < 0:
                description_index = line.find(' F_')

            if description_index >= 0:
                description_index -= 1
                tag = line[description_index:]
                newtag = tag + "_%03d" % n_file
                line = line[:description_index] + newtag

            if len(line) < 1: continue

            fid.write(line + '\n')

        data.close()

if args.final_outfile is not None:
    fid.close()
