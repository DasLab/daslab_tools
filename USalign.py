#!/usr/bin/env python3
import string
from glob import glob
from sys import argv,stderr,exit
from os import popen,system
from os.path import exists,basename
from operator import add
from math import sqrt
import argparse

parser = argparse.ArgumentParser(description='Run USalign on a bunch of PDBs.')
parser.add_argument('refpdb', help='Reference PDB file')
parser.add_argument('pdb', type=str, nargs='+', help='PDB file to align')
parser.add_argument('-dump', action='store_true', help='Prepare superposition PDB as .TMsup.pdb ')
parser.add_argument('-TMscore', type=int,default=0, help='integer setting for TMscore (0 by default means ignore sequence) ')
parser.add_argument('-RNA', action='store_true', help='only align RNA chains')
parser.add_argument('-force_mm', action='store_true', help='force align multimer (default auto-detect)')
parser.add_argument('-force_monomer', action='store_true', help='force align monomer (default auto-detect)')
parser.add_argument('-atom', default=" C3'", help='atom representative, 4 characters (default: " C3\'\") ')

args = parser.parse_args()

if not exists( args.refpdb ):
    stderr.write( 'Could not find reference PDB file: '+args.refpdb+'\n' )
    exit(0)

# autodetect whether to use multimer
lines = popen( 'grep TER %s ' % args.refpdb ).readlines()
mm = len(lines)>1
if args.force_mm: mm = True
if args.force_monomer: mm = False


EXEC = 'USalign'

for i in range(len(args.pdb)):
    if not exists( args.pdb[i] ):
        stderr.write( 'Could not find PDB file: '+args.pdb[i]+'\n' )
        exit(0)

    cmdline = '%s %s %s -TMscore %d -atom "%4s"' % (EXEC, args.pdb[i], args.refpdb, args.TMscore, args.atom)
    if args.RNA: cmdline += ' -mol RNA'
    if mm:  cmdline += ' -mm 1 -ter 1'
    if args.dump:
        sup_model_file = args.pdb[i].replace( '.pdb','' ) + '.TMsup.pdb'
        cmdline += ' -o %s' % sup_model_file
    lines = popen( cmdline ).readlines()

    TMscore = 0
    nalign = 0
    rmsd_align = 0
    for line in lines:
        if line.find('Structure_2') > -1 and line[:4] == 'TM-s':  # Go by reference score.
            TMscore = float( line.split(' ')[1] )
        if line.find('Aligned length') == 0:
            nalign = int( line.split()[2].replace(',','') )
            rmsd_align = float( line.split()[4].replace(',',''))

    print( '%s -vs- %s: %9.5f over %d residues   TM-score: %f' % (args.refpdb, args.pdb[i], rmsd_align, nalign, TMscore) )
    #print 'TM-score: %f' % (TMscore)

