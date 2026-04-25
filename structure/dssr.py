#!/usr/bin/env python3
import argparse
import shutil
from os import system, remove, path
from glob import glob

assert(shutil.which('x3dna-dssr'))

parser = argparse.ArgumentParser(description='Run x3dna-dssr on PDB files and print secondary structure.')
parser.add_argument('pdbfiles', nargs='+', help='PDB files to analyze')
args = parser.parse_args()

for infile in args.pdbfiles:
    command = 'x3dna-dssr -i=%s > /dev/null 2> /dev/null' % infile
    system(command)
    ssfile = 'dssr-2ndstrs.dbn'
    if path.isfile(ssfile):
        lines = open('dssr-2ndstrs.dbn').readlines()
        print('%s,%s,%s' % (lines[2].strip(), infile, lines[1].strip()))
    for outfile in glob('dssr-*'): remove(outfile)
