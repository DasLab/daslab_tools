#!/usr/bin/env python3
from sys import argv,stdout
import shutil
from os import system, remove, path
from glob import glob

# currently have docker set up on Mac, and singularity set up on Sherlock
if not shutil.which( 'docker' ): assert(shutil.which('singularity'))
files = argv[1:]

if len(files) < 2:
    print( argv[0]+ " [ref] [model files]" )
    print( 'Note you might want to use ost.py in daslab_tools repo' )
    exit()

# Copy reference to /tmp/
assert( path.isfile( files[0] ))
ref_tmp = '/tmp/'+path.basename(files[0])
shutil.copyfile( files[0], ref_tmp)

for infile in files[1:]:
    infile_tmp =  '/tmp/'+path.basename(infile)
    shutil.copyfile( infile, infile_tmp)
    outfile_tmp = '/tmp/out.json'
    if shutil.which('docker'):
        command = 'docker run --platform linux/amd64 --rm -v /tmp:/mnt registry.scicore.unibas.ch/schwede/openstructure:latest compare-structures -r %s  -m %s  -ft -mf pdb --lddt --ilddt -o %s -v 0' % \
                  ( ref_tmp.replace('/tmp/','/mnt/'), infile_tmp.replace('/tmp/','/mnt/'), outfile_tmp.replace('/tmp/','/mnt/') )
    else:
        command = 'singularity run --app OST /home/groups/rhiju/rkretsch/openstructure/singularity/ost.img  compare-structures -r %s  -m %s  -mf pdb --lddt --ilddt -o %s -v 0' % \
                  ( ref_tmp,infile_tmp,outfile_tmp )
    errcode = system(command)
    lddt = 0
    ilddt = 0
    if not errcode:
        assert( path.isfile(outfile_tmp) )
        lines = open(outfile_tmp).readlines()
        for line in lines:
            pos = line.find('"lddt":')
            if (pos>-1): lddt = float( line[pos+8:].strip().replace(',','') )
            pos = line.find('"ilddt":')
            if (pos>-1): ilddt = float( line[pos+9:].strip().replace(',','').replace('null','nan') )
    print( '%f,%f,%s' % ( lddt, ilddt, infile ) )
    if path.isfile(outfile_tmp): remove( outfile_tmp )
    remove( infile_tmp )
    stdout.flush()
remove( ref_tmp )

