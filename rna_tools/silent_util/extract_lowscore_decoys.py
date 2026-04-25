#!/usr/bin/env python3

import argparse
from sys import exit
from os import popen, system
from os.path import basename, exists, expanduser, expandvars
import subprocess
from glob import glob

parser = argparse.ArgumentParser(
    description='Extract N lowest-scoring decoys from Rosetta silent file(s).',
    epilog=(
        'The last positional args set the score column and count:\n'
        '  ex silent.out 10            — extract 10 lowest by score\n'
        '  ex silent.out -rms 5        — extract 5 lowest by rms\n'
        '  ex silent.out +rms 5        — extract 5 highest by rms\n'
        '  ex silent.out 3 10          — extract 10 lowest by column 3\n'
        '  ex silent.out rms=1.5       — extract all with rms==1.5\n'
    ),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('-no_replace_names',    action='store_true', help='keep original decoy tag names')
parser.add_argument('-extract_first_chain', action='store_true', help='extract only the first chain')
parser.add_argument('-start_at_zero',       action='store_true', help='start output numbering at 0')
parser.add_argument('-start_pdb',           metavar='FILE', default=None, help='starting PDB file')
parser.add_argument('-output_virtual',      action='store_true', help='output virtual residues')
parser.add_argument('-extra_res_fa',        nargs='+', metavar='FILE', default=[], help='extra residue params')
parser.add_argument('-rosetta_folder',      metavar='DIR', default='', help='path to Rosetta installation')
parser.add_argument('remainder',            nargs=argparse.REMAINDER,
                    metavar='args', help='<infile(s)> [±col|col=val] [N]')
args = parser.parse_args()

if not args.remainder:
    parser.print_help()
    exit()

replace_names       = not args.no_replace_names
extract_first_chain = args.extract_first_chain
start_at_zero       = args.start_at_zero
use_start_pdb       = args.start_pdb is not None
start_pdb_file      = args.start_pdb or ''
output_virtual      = args.output_virtual
extra_res_fa        = args.extra_res_fa
rosetta_folder      = args.rosetta_folder

# Tail-parse scorecol and N from the remainder (files come first, then optional col/N)
argv = list(args.remainder)

NSTRUCT_defined = 0
try:
    NSTRUCT = int(argv[-1])
    del(argv[-1])
    NSTRUCT_defined = 1
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
match_score_defined = 0
if not scorecol_defined:
    scorecol_name = argv[-1]
    if scorecol_name[0] == '-':
        scorecol_name_defined = 1
        scorecol_name = scorecol_name[1:]
        REVERSE = ''
    if scorecol_name[0] == '+':
        scorecol_name_defined = 1
        scorecol_name = scorecol_name[1:]
        REVERSE = '-r'
    if '=' in scorecol_name:
        scorecol_name_defined = 1
        scorecol_name_split = scorecol_name.split('=')
        scorecol_name = scorecol_name_split[0]
        try:
            match_score = float(scorecol_name_split[-1])
            match_score_defined = 1
            if not REVERSE:
                REVERSE = ''
            if not NSTRUCT_defined:
                NSTRUCT = None
        except:
            match_score_defined = 0
    if scorecol_name_defined:
        del(argv[-1])

infiles = argv

if rosetta_folder == '':
    rosetta_folder = expandvars('$ROSETTA')
MINI_DIR = rosetta_folder + '/main/source/bin/'
DB = rosetta_folder + '/main/database/'

HOMEDIR = expanduser('~')

for infile in infiles:
    tags = []

    scoretags = popen('head -n 2 ' + infile).readlines()[1].split()
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
        if match_score_defined:
            scoretag += '_%d' % int(match_score)
    else:
        scorecols = [scorecol]

    binary_silentfile = 0
    remark_lines = popen('head -n 7 ' + infile).readlines()
    for line in remark_lines:
        if len(line) > 6 and line[:6] == 'REMARK':
            remark_tags = line.split()
            if remark_tags.count('BINARY_SILENTFILE'):
                binary_silentfile = 1
            if remark_tags.count('BINARY'):
                binary_silentfile = 1

    coarse = 0
    if exists('remark_tags') and remark_tags.count('COARSE'):
        coarse = 1

    assert(infile[-3:] == 'out')

    terminiflag = ''
    fid = open(infile, 'r')
    line = 'ATOM'
    while (line.count('ATOM') or line.count('SCORE') or
           line.count('SEQU') or line.count('JUMP') or line.count('FOLD')):
        line = fid.readline()
    if line.count('AAV'):
        terminiflag = ' -termini '

    lines = popen('grep SCORE ' + infile + ' | grep -v NATIVE').readlines()

    score_plus_lines = []
    for line in lines:
        cols = line.split()
        score = 0.0
        try:
            for scorecol in scorecols:
                score += float(cols[abs(scorecol)])
        except:
            continue
        if REVERSE:
            score *= -1
        score_plus_lines.append((score, line))

    score_plus_lines.sort()
    if match_score_defined:
        score_plus_lines = list(filter(lambda x: float(x[0]) == match_score, score_plus_lines))
    lines = [x[-1] for x in score_plus_lines[:NSTRUCT]]

    templist_name = 'temp.%s.list' % basename(infile)

    fid = open(templist_name, 'w')
    count = 0
    for line in lines:
        cols = line.split()
        tag = cols[-1]
        if tag.find('desc') < 0:
            fid.write(tag + '\n')
            tags.append(tag)
            count = count + 1
        if NSTRUCT and count >= NSTRUCT:
            break
    outfilename = infile

    fid.close()

    startpdbflag = ''
    if use_start_pdb:
        startpdbflag = '-start_pdb ' + start_pdb_file

    extract_first_chain_tag = ''
    if extract_first_chain:
        extract_first_chain_tag = ' -extract_first_chain '

    softlink_bonds_file = 0
    wanted_bonds_file = infile + '.bonds'
    wanted_rot_templates_file = infile + '.rot_templates'
    bonds_files = glob('*.bonds')
    if len(bonds_files) > 0:
        if not exists(wanted_bonds_file):
            softlink_bonds_file = 1
            system('ln -fs ' + bonds_files[0] + ' ' + wanted_bonds_file)
            system('ln -fs ' + bonds_files[0].replace('.bonds', '.rot_templates')
                   + ' ' + wanted_rot_templates_file)

    MINI_EXE = MINI_DIR + 'extract_pdbs'
    if not exists(MINI_EXE):
        MINI_EXE = MINI_DIR + 'extract_pdbs.linuxgccrelease'
    if not exists(MINI_EXE):
        MINI_EXE = MINI_DIR + '/extract_pdbs.macosgccrelease'
        assert exists(MINI_EXE)

    command = ('%s -load_PDB_components -in:file:silent  %s   -in:file:tags %s -database %s'
               ' -out:file:residue_type_set centroid ' %
               (MINI_EXE, outfilename, ' '.join(tags), DB))

    old_rosetta = 0
    scorelabels = popen('head -n 2 ' + outfilename).readlines()[-1].split()
    if 'SCORE' in scorelabels:
        EXE = HOMEDIR + '/src/rosetta++/rosetta.gcc'
        if not exists(EXE):
            EXE = 'rm boinc* ros*txt; ' + HOMEDIR + '/src/rosetta++/rosetta.mactelboincgraphics '
        assert exists(EXE)
        command = ('%s -extract -l %s -paths %s/src/rosetta++/paths.txt -s %s %s %s ' %
                   (EXE, templist_name, HOMEDIR, outfilename, terminiflag,
                    startpdbflag + extract_first_chain_tag))
        old_rosetta = 1
        print('OLD_ROSETTA', old_rosetta)

    fid = open(infile, 'r')
    line = fid.readline()
    print(line)
    rna = 0
    sequence = line.split()[-1]
    rna = 1
    for c in sequence:
        if not (c == 'a' or c == 'c' or c == 'u' or c == 'g'):
            rna = 0
            break
    if rna:
        command += ' -enable_dna -enable_rna '

    lines = popen('head -n 8 ' + outfilename).readlines()
    if len(lines[6].split()) > 10:
        command += ' -fa_input'

    if rna and not old_rosetta:
        command = ('%s -load_PDB_components -database %s -in::file::silent %s -tags %s  -extract' %
                   (MINI_EXE, DB, outfilename, ' '.join(tags)))

        if binary_silentfile:
            silent_struct_type = 'binary_rna'
        else:
            silent_struct_type = 'rna'

        command = ('%s -load_PDB_components -database %s -in:file:silent %s -in:file:tags %s'
                   ' -in:file:silent_struct_type %s  ' %
                   (MINI_EXE, DB, outfilename, ' '.join(tags), silent_struct_type))

        if coarse:
            command += ' -out:file:residue_type_set coarse_rna '
        else:
            pass

        if output_virtual:
            command += ' -output_virtual '

    elif binary_silentfile:
        command = ('%s -load_PDB_components -in:file:silent  %s  -in:file:silent_struct_type binary'
                   ' -in:file:fullatom -in:file:tags %s -database %s  ' %
                   (MINI_EXE, outfilename, ' '.join(tags), DB))
        if output_virtual:
            command += ' -output_virtual '
        if len(extra_res_fa) > 0:
            command += ' -extra_res_fa '
            for m in extra_res_fa:
                command += ' ' + m

        if scoretags.count('vdw'):
            command += ' -out:file:residue_type_set centroid '

    print(command)
    system(command)

    if outfilename.find('t343') > 0:
        command = HOMEDIR + '/python/extract_t343.py %s %s' % (outfilename, ' '.join(tags))
        print(command)
        system(command)

    count = 1
    if start_at_zero:
        count = 0

    if replace_names:
        for tag in tags:
            if scorecol_defined or scorecol_name_defined:
                command = 'mv %s.pdb %s.%s.%d.pdb' % (tag, basename(infile), scoretag, count)
            else:
                command = 'mv %s.pdb %s.%d.pdb' % (tag, basename(infile), count)
            print(command)
            system(command)
            count += 1

    command = 'rm ' + templist_name
    print(command)
    system(command)

    if softlink_bonds_file:
        print(' WARNING! WARNING')
        print(' Found a .bonds and .rot_templates file and used it!')
