#!/usr/bin/env python3
from sys import argv,stdout,stderr
import shutil, json
from os import system,remove,path,makedirs,rmdir
from glob import glob
import argparse
import platform
import subprocess
import sys
import time

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

parser = argparse.ArgumentParser(description='Run USalign on a bunch of PDBs.')

parser.add_argument('refpdb', help='Reference PDB file')
parser.add_argument('pdb', type=str, nargs='+', help='PDB file to align')
parser.add_argument('--rna', action='store_true',  help='force residue number alignment')
parser.add_argument('--lddt_no_checks', action='store_true',  help='turn off stereochemical check in lddt')
parser.add_argument('-v', '--verbose', action='store_true', help='print docker/singularity command before running')

args = parser.parse_args()
if not path.exists( args.refpdb ):
    stderr.write( 'Could not find reference PDB file: '+args.refpdb+'\n' )
    exit(0)

# Copy reference to /tmp/
hashdir = hash(args.refpdb + ' '.join( args.pdb  ))
tmpdir = '/tmp/%s/' % hashdir
makedirs( tmpdir, exist_ok = True )

ref_tmp = tmpdir + path.basename(args.refpdb)
shutil.copyfile( args.refpdb, ref_tmp)
def fmt(filepath):
    return 'mmcif' if filepath.endswith(('.cif', '.mmcif')) else 'pdb'

ref_fmt = fmt(args.refpdb)
print( '%s,%s,%s,%s,%s,%s' % ( 'lddt', 'tm_score', 'ilddt', 'ics', 'ips', 'model' ) )
for infile in args.pdb:
    if not path.exists( infile ):
        stderr.write( 'Could not find model PDB file: '+infile+'\n' )
        continue
    infile_tmp =  tmpdir + path.basename(infile)
    shutil.copyfile( infile, infile_tmp)
    outfile_tmp = tmpdir + 'out.json'
    model_fmt = fmt(infile)
    if shutil.which('docker'):
        command = 'docker run --platform linux/amd64 --rm -v /tmp:/mnt registry.scicore.unibas.ch/schwede/openstructure:latest compare-structures -r %s  -m %s  -ft -rf %s -mf %s --lddt --ilddt --tm-score --ips --ics -o %s -v 0' % \
                  ( ref_tmp.replace('/tmp/','/mnt/'), infile_tmp.replace('/tmp/','/mnt/'), ref_fmt, model_fmt, outfile_tmp.replace('/tmp/','/mnt/') )
    else:
        command = 'singularity run --app OST /home/groups/rhiju/rkretsch/openstructure/singularity/ost.img  compare-structures -r %s  -m %s  -rf %s -mf %s --lddt --ilddt  --tm-score --ips --ics -o %s -v 0' % \
                  ( ref_tmp,infile_tmp,ref_fmt,model_fmt,outfile_tmp )
    if args.rna: command += ' -rna'
    if args.lddt_no_checks: command += ' --lddt-no-stereochecks'
    if args.verbose: print('Running: ' + command, file=stderr)
    errcode = system(command)
    lddt = 0
    tm_score = 0
    ilddt = float('nan')
    ics = 0
    ips = 0
    if errcode:
        print('ERROR: docker/singularity command failed with exit code %d' % errcode, file=stderr)
    if not errcode:
        assert( path.isfile(outfile_tmp) )
        result = json.load(open(outfile_tmp))
        lddt     = result.get('lddt', 0) or 0
        tm_score = result.get('tm_score', 0) or 0
        ilddt    = result.get('ilddt') or float('nan')
        ics      = result.get('ics', 0) or 0
        ips      = result.get('ips', 0) or 0
    print( '%f,%f,%f,%f,%f,%s' % ( lddt, tm_score, ilddt, ics, ips, infile ) )
    if path.isfile(outfile_tmp): remove( outfile_tmp )
    remove( infile_tmp )
    stdout.flush()
remove( ref_tmp )
rmdir( tmpdir )
