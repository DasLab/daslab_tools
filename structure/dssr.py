#!env python3
from sys import argv
import shutil
from os import system, remove, path
from glob import glob

assert(shutil.which( 'x3dna-dssr' ))
files = argv[1:]
for infile in files:
    command = 'x3dna-dssr -i=%s > /dev/null 2> /dev/null'% infile
    system(command)
    ssfile = 'dssr-2ndstrs.dbn'
    if path.isfile(ssfile):
        lines = open('dssr-2ndstrs.dbn').readlines()
        print('%s,%s,%s' % ( lines[2].strip(), infile, lines[1].strip()))
    for outfile in glob('dssr-*'): remove(outfile)

