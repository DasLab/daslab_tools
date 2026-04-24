#!/usr/bin/env python3
from sys import stdout, stderr
import shutil, json, tempfile
from os import path
import argparse
import subprocess
import sys

ost_bin = shutil.which('ost')
if not ost_bin:
    print('ERROR: native ost binary not found on PATH. Install via: conda install -c openstructure openstructure', file=sys.stderr)
    sys.exit(1)

parser = argparse.ArgumentParser(description='Run OST compare-structures on a bunch of PDBs.')
parser.add_argument('refpdb', help='Reference PDB file')
parser.add_argument('pdb', type=str, nargs='+', help='PDB file(s) to evaluate')
parser.add_argument('--rna', action='store_true', help='force residue number alignment')
parser.add_argument('--lddt_no_checks', action='store_true', help='turn off stereochemical check in lddt')
parser.add_argument('-v', '--verbose', action='store_true', help='print ost command before running')

args = parser.parse_args()
if not path.exists(args.refpdb):
    stderr.write('Could not find reference PDB file: ' + args.refpdb + '\n')
    sys.exit(1)

def fmt(filepath):
    return 'mmcif' if filepath.endswith(('.cif', '.mmcif')) else 'pdb'

ref_fmt = fmt(args.refpdb)
print('%s,%s,%s,%s,%s,%s' % ('lddt', 'tm_score', 'ilddt', 'ics', 'ips', 'model'))
for infile in args.pdb:
    if not path.exists(infile):
        stderr.write('Could not find model PDB file: ' + infile + '\n')
        continue
    model_fmt = fmt(infile)
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tf:
        outfile = tf.name
    cmd = [ost_bin, 'compare-structures',
           '-r', args.refpdb, '-m', infile,
           '-rf', ref_fmt, '-mf', model_fmt,
           '-ft', '--lddt', '--ilddt', '--tm-score', '--ips', '--ics',
           '-o', outfile, '-v', '0']
    if args.rna:
        cmd.append('-rna')
    if args.lddt_no_checks:
        cmd.append('--lddt-no-stereochecks')
    if args.verbose:
        print('Running: ' + ' '.join(cmd), file=stderr)
    result = subprocess.run(cmd, capture_output=True)
    lddt = 0; tm_score = 0; ilddt = float('nan'); ics = 0; ips = 0
    if result.returncode:
        print('ERROR: ost command failed with exit code %d' % result.returncode, file=stderr)
        if result.stderr:
            stderr.write(result.stderr.decode())
    elif path.isfile(outfile):
        data = json.load(open(outfile))
        lddt     = data.get('lddt', 0) or 0
        tm_score = data.get('tm_score', 0) or 0
        ilddt    = data.get('ilddt') or float('nan')
        ics      = data.get('ics', 0) or 0
        ips      = data.get('ips', 0) or 0
    print('%f,%f,%f,%f,%f,%s' % (lddt, tm_score, ilddt, ics, ips, infile))
    if path.isfile(outfile):
        import os; os.remove(outfile)
    stdout.flush()
