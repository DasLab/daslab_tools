#!/usr/bin/env python3

import argparse
import os
import shutil
import time
import glob

parser = argparse.ArgumentParser(
                    prog = 'archive_to_oak.py',
                    description = 'tar up a directory and copy to oak'
)

parser.add_argument('dir_name')

args = parser.parse_args()
dir_name =  args.dir_name
if dir_name[-1] == '/': dir_name = dir_name[:-1]

#if dir_name == '.' or not( os.path.isdir( os.path.basename(dir_name) ) ) :
#    print( 'Must specify a subdirectory of a current directory')
#    exit()

GROUP = os.getenv('GROUP')

abs_dir_name = os.path.abspath( dir_name )

def get_oak_dir( current_path, oak_path ):
    idx = abs_dir_name.find(current_path)
    if idx == -1:
        return ''
    else:
        return oak_path+os.path.dirname(abs_dir_name[idx+len(current_path):])

oak_dir = ''
if len(oak_dir) == 0:
    # 'scratch_group'
    oak_dir = get_oak_dir( '/scratch/groups/%s/' % (GROUP),
                           '/oak/stanford/groups/%s/sherlock/scratch/' % (GROUP) )
if len(oak_dir) == 0:
    # 'scratch'
    oak_dir = get_oak_dir( '/scratch/users/',
                           '/oak/stanford/groups/%s/sherlock/scratch/' % (GROUP) )
if len(oak_dir) == 0:
    # 'home'
    oak_dir = get_oak_dir( '/home/users/',
                           '/oak/stanford/groups/%s/sherlock/home/' % (GROUP) )
if len(oak_dir) == 0:
    # 'group'
    oak_dir = get_oak_dir( '/home/groups/%s/' % (GROUP),
                           '/oak/stanford/groups/%s/sherlock/home/' % (GROUP) )

if len(oak_dir) == 0:
    print( 'Could not figure out location' )
    exit()

basetag = os.path.basename( dir_name )
outfile = '%s/%s.tgz' % (oak_dir,basetag)

tag = 'archive_to_oak_%s' % basetag
sbatch_file = tag+'.sh'
fid = open( sbatch_file, 'w' )

fid.write('#!/bin/bash\n')
fid.write('#SBATCH --job-name=%s\n' % basetag )
fid.write('#SBATCH --output=%s.out\n' % tag)
fid.write('#SBATCH --error=%s.err\n' % tag )
fid.write('#SBATCH --partition=biochem,owners\n')
fid.write('#SBATCH --time=24:00:00\n')
fid.write('#SBATCH --cpus-per-task=1\n')
fid.write('#SBATCH --mem=8G\n')
fid.write('\n')
fid.write('tar cvfz %s.tgz %s\n' % (basetag,dir_name) )
fid.write('mkdir -p %s\n' % oak_dir )
fid.write('scp %s.tgz %s\n' % (basetag,outfile) )
fid.write('echo \n' )
fid.write('echo "Created: %s"\n' % outfile )
fid.write('echo "DONE"\n')
fid.close()


print( '\nCreated script to archive %s to %s. Type:\n\n sbatch %s\n' % (dir_name,outfile,sbatch_file) )
if os.path.isfile( outfile ):
    print( 'WARNING! %s already exists!\n' % (outfile))
