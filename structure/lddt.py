#!/usr/bin/env python3
from sys import argv,stdout,stderr
import shutil
from os import system, remove, path
from glob import glob
import math
import platform
import subprocess
import sys
import time

def fmt(filepath):
    return 'mmcif' if filepath.endswith(('.cif', '.mmcif')) else 'pdb'

def ensure_docker_running():
    """On macOS, start Docker Desktop if the daemon isn't responding."""
    if subprocess.run(['docker', 'info'], capture_output=True).returncode == 0:
        return
    if platform.system() != 'Darwin':
        print('Docker is installed but not running. Please start it.', file=sys.stderr)
        sys.exit(1)
    print('Docker daemon not running — starting Docker Desktop...', file=sys.stderr)
    subprocess.run(['open', '-a', 'Docker'])
    for _ in range(30):
        time.sleep(2)
        if subprocess.run(['docker', 'info'], capture_output=True).returncode == 0:
            print('Docker is ready.', file=sys.stderr)
            return
    print('Timed out waiting for Docker to start.', file=sys.stderr)
    sys.exit(1)

# currently have docker set up on Mac, and singularity set up on Sherlock
if not shutil.which( 'docker' ): assert(shutil.which('singularity'))
if shutil.which('docker'): ensure_docker_running()
args = argv[1:]
verbose = '-v' in args or '--verbose' in args
files = [a for a in args if a not in ('-v', '--verbose')]

if len(files) < 2:
    print( argv[0]+ " [-v/--verbose] [ref] [model files]" )
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
    ref_fmt = fmt(files[0])
    model_fmt = fmt(infile)
    if shutil.which('docker'):
        command = 'docker run --platform linux/amd64 --rm -v /tmp:/mnt registry.scicore.unibas.ch/schwede/openstructure:latest compare-structures -r %s  -m %s  -ft -rf %s -mf %s --lddt --ilddt -o %s -v 0' % \
                  ( ref_tmp.replace('/tmp/','/mnt/'), infile_tmp.replace('/tmp/','/mnt/'), ref_fmt, model_fmt, outfile_tmp.replace('/tmp/','/mnt/') )
    else:
        command = 'singularity run --app OST /home/groups/rhiju/rkretsch/openstructure/singularity/ost.img  compare-structures -r %s  -m %s  -rf %s -mf %s --lddt --ilddt -o %s -v 0' % \
                  ( ref_tmp,infile_tmp,ref_fmt,model_fmt,outfile_tmp )
    if verbose: print('Running: ' + command, file=stderr)
    errcode = system(command)
    lddt = -1
    ilddt = -1
    if errcode:
        print('ERROR: docker/singularity command failed with exit code %d' % errcode, file=sys.stderr)
    if not errcode:
        assert( path.isfile(outfile_tmp) )
        lines = open(outfile_tmp).readlines()
        for line in lines:
            pos = line.find('"lddt":')
            if (pos>-1 and lddt == -1): lddt = float( line[pos+8:].strip().replace(',','') )
            pos = line.find('"ilddt":')
            if (pos>-1 and ilddt == -1): ilddt = float( line[pos+9:].strip().replace(',','').replace('null','nan') )
    if lddt == -1: lddt = math.nan
    if ilddt == -1: ilddt = math.nan
    print( '%f,%f,%s' % ( lddt, ilddt, infile ) )
    if path.isfile(outfile_tmp): remove( outfile_tmp )
    remove( infile_tmp )
    stdout.flush()
remove( ref_tmp )

