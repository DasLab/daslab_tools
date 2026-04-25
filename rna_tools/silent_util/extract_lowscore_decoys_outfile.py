#!/usr/bin/env python3

import argparse
from sys import exit, stderr, stdout
from os import popen
from os.path import basename
import subprocess

parser = argparse.ArgumentParser(
    description='Extract N lowest-scoring models from Rosetta silent file(s) into a new silent file.',
    epilog=(
        'The last positional args set the score column and count:\n'
        '  exo silent.out 10       — extract 10 lowest by score\n'
        '  exo silent.out -rms 5   — extract 5 lowest by rms\n'
        '  exo silent.out +rms 5   — extract 5 highest by rms\n'
        '  exo silent.out 2.5      — extract all with score < 2.5 (float = cutoff)\n'
        '\n'
        'Alias suggestion for ~/.bashrc:\n'
        '  alias exo="extract_lowscore_decoys_outfile.py -out"'
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('-out', action='store_true',
                    help='write output to a .topN.out file instead of stdout')
parser.add_argument('remainder', nargs=argparse.REMAINDER,
                    metavar='args', help='<infile(s)> [±col] [N|score_cutoff]')
args = parser.parse_args()

if not args.remainder:
    parser.print_help()
    exit()

output_to_file = args.out

# Tail-parse scorecol and N from the remainder
argv = list(args.remainder)

SCORE_CUTOFF = 0

try:
    NSTRUCT = float(argv[-1])
    if argv[-1].count('.') > 0:
        SCORE_CUTOFF = NSTRUCT
        NSTRUCT = 0
    else:
        NSTRUCT = int(NSTRUCT)
    del(argv[-1])
except:
    NSTRUCT = 2

scorecol_defined = 0
try:
    scorecol = int(argv[-1])
    del(argv[-1])
    scorecol_defined = 1
except:
    scorecol = -1

REVERSE = ''
if scorecol > 0:
    REVERSE = ' --reverse '

scorecol_name_defined = 0
if not scorecol_defined:
    scorecol_name = argv[-1]
    if scorecol_name[0] == '-':
        scorecol_name_defined = 1
        scorecol_name = scorecol_name[1:]
        del(argv[-1])
        REVERSE = ''
    if scorecol_name[0] == '+':
        scorecol_name_defined = 1
        scorecol_name = scorecol_name[1:]
        REVERSE = '-r'
        del(argv[-1])

infiles = argv
score_plus_lines = []
firstlines = []
IS_OUTFILE = 1

if output_to_file:
    assert len(infiles) == 1

for infile in infiles:

    if len(firstlines) == 0:
        firstlines = popen('head -n 5 ' + infile).readlines()
        scoretags = firstlines[1].split()
        if firstlines[0].find('SEQUENCE') < 0 and firstlines[0].find('SCORE:') >= 0:
            IS_OUTFILE = 0
            scoretags = firstlines[0].split()

    scoretag = ''
    if scorecol_defined:
        scoretag = scoretags[abs(scorecol)]

    if scorecol_name_defined:
        scorecol_names = scorecol_name.split(',')
        scorecols = []
        for s in scorecol_names:
            assert scoretags.count(s)
            scorecol = scoretags.index(s)
            scorecols.append(scorecol)
        scoretag = scorecol_name
    else:
        scorecols = [scorecol]

    command = 'grep SCORE ' + infile + ' | grep -v NATIVE'
    lines = popen(command).readlines()

    for line in lines:
        cols = line.split()
        score = 0.0
        try:
            for scorecol in scorecols:
                score += float(cols[abs(scorecol)])
        except:
            continue

        if NSTRUCT == 0:
            if REVERSE:
                if score < SCORE_CUTOFF:
                    continue
            else:
                if score > SCORE_CUTOFF:
                    continue

        if REVERSE:
            score *= -1
        score_plus_lines.append((score, line, infile))

score_plus_lines.sort()

tags_for_infile = {}
for infile in infiles:
    tags_for_infile[infile] = []

count = 0
for score_plus_line in score_plus_lines:
    line = score_plus_line[1]
    cols = line.split()
    tag = cols[-1]

    infile = score_plus_line[2]
    tags_for_infile[infile].append(tag)

    count += 1
    if NSTRUCT > 0 and count >= NSTRUCT:
        break

stderr.write('Extracting %d models from %s\n' % (count, ' '.join(infiles)))

fid = stdout
if output_to_file:
    newfile = infile
    if scorecol_name_defined:
        newfile = newfile.replace('.out', '.%s.out' % scorecol_name)
    newfile = newfile.replace('.out', '.top%d.out' % NSTRUCT)
    fid = open(newfile, 'w')

if not IS_OUTFILE:
    command = 'head -n 1 ' + infile
    lines = popen(command).readlines()
elif firstlines[2][:6] == 'REMARK':
    command = 'head -n 3 ' + infile
    lines = popen(command).readlines()
elif len(firstlines) > 4 and firstlines[4][:6] == 'REMARK':
    command = 'head -n 5 ' + infile
    lines = popen(command).readlines()
    del(lines[2])
    del(lines[2])
else:
    command = 'head -n 2 ' + infile
    lines = popen(command).readlines()

for line in lines:
    fid.write(line)

n = -1
for infile in infiles:

    n += 1

    ok_tags = tags_for_infile[infile]
    if len(ok_tags) == 0:
        continue

    data = open(infile, 'r')
    line = data.readline()
    line = data.readline()

    writeout = 0
    while line:
        line = data.readline()[:-1]
        if len(line) < 2:
            continue
        if line[:9] == 'SEQUENCE:':
            continue
        cols = line.split()
        tag = cols[-1]

        if cols[0][:5] == 'SCORE':
            if ok_tags.count(tag) > 0:
                writeout = 1
            else:
                writeout = 0

        if not writeout:
            continue

        if n > 0:
            tagcols = tag.split('_')
            try:
                tagnum = int(tagcols[-1])
                tagcols[-1] = '%04d_%06d' % (n, tagnum)
                newtag = '_'.join(tagcols)
                description_index = line.find(tag)
                line = line[:description_index] + newtag
            except:
                continue

        fid.write(line + '\n')

    data.close()

if output_to_file:
    fid.close()
    stderr.write('Outputted models to: %s\n' % newfile)
