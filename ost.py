#!/usr/bin/env python3
from sys import argv,stdout,stderr
import shutil
from os import system,remove,path,makedirs,rmdir
from glob import glob
import argparse
# currently have docker set up on Mac, and singularity set up on Sherlock
if not shutil.which( 'docker' ): assert(shutil.which('singularity'))

parser = argparse.ArgumentParser(description='Run USalign on a bunch of PDBs.')

parser.add_argument('refpdb', help='Reference PDB file')
parser.add_argument('pdb', type=str, nargs='+', help='PDB file to align')
parser.add_argument('--rna', action='store_true',  help='force residue number alignment')
parser.add_argument('--lddt_no_checks', action='store_true',  help='turn off stereochemical check in lddt')

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
print( '%s,%s,%s,%s,%s,%s' % ( 'lddt', 'tm_score', 'ilddt', 'ics', 'ips', 'model' ) )
for infile in args.pdb:
    if not path.exists( infile ):
        stderr.write( 'Could not find model PDB file: '+infile+'\n' )
        continue
    infile_tmp =  tmpdir + path.basename(infile)
    shutil.copyfile( infile, infile_tmp)
    outfile_tmp = tmpdir + 'out.json'
    if shutil.which('docker'):
        command = 'docker run --platform linux/amd64 --rm -v /tmp:/mnt registry.scicore.unibas.ch/schwede/openstructure:latest compare-structures -r %s  -m %s  -ft -mf pdb --lddt --ilddt --tm-score --ips --ics -o %s -v 0' % \
                  ( ref_tmp.replace('/tmp/','/mnt/'), infile_tmp.replace('/tmp/','/mnt/'), outfile_tmp.replace('/tmp/','/mnt/') )
    else:
        command = 'singularity run --app OST /home/groups/rhiju/rkretsch/openstructure/singularity/ost.img  compare-structures -r %s  -m %s  -mf pdb --lddt --ilddt  --tm-score --ips --ics -o %s -v 0' % \
                  ( ref_tmp,infile_tmp,outfile_tmp )
    if args.rna: command += ' -rna'
    if args.lddt_no_checks: command += ' --lddt-no-stereochecks'
    errcode = system(command)
    lddt = 0
    tm_score = 0
    ilddt = 0
    ics = 0
    ips = 0
    if not errcode:
        assert( path.isfile(outfile_tmp) )
        lines = open(outfile_tmp).readlines()
        for line in lines:
            pos = line.find('"lddt":')
            if (pos>-1): lddt = float( line[pos+8:].strip().replace(',','') )
            pos = line.find('"ilddt":')
            if (pos>-1): ilddt = float( line[pos+9:].strip().replace(',','').replace('null','nan') )
            pos = line.find('"tm_score":')
            if (pos>-1): tm_score = float( line[pos+11:].strip().replace(',','') )
            pos = line.find('"ics":')
            if (pos>-1): ics = float( line[pos+7:].strip().replace(',','').replace('null','nan') )
            pos = line.find('"ips":')
            if (pos>-1): ips = float( line[pos+7:].strip().replace(',','').replace('null','nan') )
    print( '%f,%f,%f,%f,%f,%s' % ( lddt, tm_score, ilddt, ics, ips, infile ) )
    if path.isfile(outfile_tmp): remove( outfile_tmp )
    remove( infile_tmp )
    stdout.flush()
remove( ref_tmp )
rmdir( tmpdir )
