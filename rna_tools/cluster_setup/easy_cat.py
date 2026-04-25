#!/usr/bin/env python3
import argparse
import subprocess
from os import system, getcwd, chdir, listdir
from os.path import basename, abspath, dirname, exists, join, isdir
from glob import glob

parser = argparse.ArgumentParser(
    description='Collect and merge Rosetta silent files from job output directories into per-tag .out files.'
)
parser.add_argument('outfiles', nargs='+',
                    help='output directories or .out files to merge')
if len(__import__('sys').argv) == 1:
    parser.print_help()
    __import__('sys').exit(1)
args = parser.parse_args()

outfiles = args.outfiles
scripts_path = dirname( abspath( __file__ ) )

which_files_to_cat = {}

for outfile in outfiles:
    if not exists( outfile ): # look inside subdirectories
        d = '.'
        CWD = getcwd()
        subdirs = [o for o in listdir(d) if isdir(join(d,o))]
        for subdir in subdirs:
            chdir( subdir )
            print(subdir)
            system( 'easy_cat.py %s' % outfile )
            print()
            chdir( CWD )
        continue
    if (outfile[-4:] == '.out' ):
        #Old style, user specified a bunch of outfiles.
        tag = "_".join(outfile.split('_')[:-2])
        if tag not in which_files_to_cat.keys():
            which_files_to_cat[tag] = []
        which_files_to_cat[tag].append( outfile )

    else: #New style -- look inside a directory!

        globfiles = glob( outfile+'/*/*out' )

        if len( globfiles ) == 0: globfiles = glob( outfile + '/*out'  )

        # Remove any "checkpoint" files from stepwise checkpointing
        globfiles = [x for x in globfiles if "S_" not in x and "_checkpoint" not in x]

        # make sure to order 0,1,2,... 10, 11, 12, ... 100, 101, ...
        globfiles_with_length = [[len(x), x] for x in globfiles]
        globfiles_with_length.sort()
        globfiles = [x[-1] for x in globfiles_with_length]

        for file in globfiles:
            tag = basename( file ).replace('.out','')
            if tag not in which_files_to_cat.keys():
                which_files_to_cat[tag] = []
            which_files_to_cat[tag].append( file )


for tag in which_files_to_cat.keys():
    cat_file = tag+".out"
    print("Catting into: ", cat_file, end='')
    command = 'python3 %s/cat_outfiles.py %s >  %s ' % \
              (scripts_path, " ".join( which_files_to_cat[tag] ),
               cat_file )
    system( command )

    cat_file_contributors = cat_file + '.txt'
    fid_txt = open( cat_file_contributors, 'w' )
    for m in range( len( which_files_to_cat[tag] ) ):
        fid_txt.write( '%03d %s\n' % (m, which_files_to_cat[tag][m]) )
    fid_txt.close()

    lines = subprocess.run(['grep', 'SCORE', cat_file],
                           capture_output=True, text=True).stdout.splitlines(keepends=True)
    print('... from %d primary files. Found %d  decoys.' % (len( which_files_to_cat[tag] ), len(lines)-1))

    fid_sc = open( cat_file.replace('.out','.sc'), 'w' )
    for line in lines:
        fid_sc.write( line )
    fid_sc.close()
