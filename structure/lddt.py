#!/usr/bin/env python3
import argparse
import shutil, json, tempfile, math
from os import path, remove
import subprocess
import sys

ost_bin = shutil.which('ost')
if not ost_bin:
    print('ERROR: native ost binary not found on PATH. Install via: conda install -c openstructure openstructure', file=sys.stderr)
    sys.exit(1)

def fmt(filepath):
    return 'mmcif' if filepath.endswith(('.cif', '.mmcif')) else 'pdb'

parser = argparse.ArgumentParser(description='Compute lDDT scores between a reference and one or more model structures.')
parser.add_argument('-v', '--verbose', action='store_true', help='print ost command before running')
parser.add_argument('-nc', '--lddt_no_check', action='store_true', help='disable stereocheck in lDDT scoring')
parser.add_argument('ref', metavar='ref_pdb', help='reference structure (PDB or mmCIF)')
parser.add_argument('models', nargs='+', help='model structure(s) to score')
args = parser.parse_args()

if not path.isfile(args.ref):
    print('Could not find reference PDB file: ' + args.ref, file=sys.stderr)
    sys.exit(1)

ref_fmt = fmt(args.ref)
for infile in args.models:
    if not path.exists(infile):
        sys.stderr.write('Could not find model PDB file: ' + infile + '\n')
        continue
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tf:
        outfile = tf.name
    cmd = [ost_bin, 'compare-structures',
           '-r', args.ref, '-m', infile,
           '-rf', ref_fmt, '-mf', fmt(infile),
           '-ft', '--lddt', '--ilddt',
           '-o', outfile, '-v', '0']
    if args.lddt_no_check:
        cmd.append('--lddt-no-stereochecks')
    if args.verbose:
        print('Running: ' + ' '.join(cmd), file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True)
    lddt = math.nan
    ilddt = math.nan
    if result.returncode:
        print('ERROR: ost command failed with exit code %d' % result.returncode, file=sys.stderr)
        if result.stderr:
            sys.stderr.write(result.stderr.decode())
    elif path.isfile(outfile):
        data = json.load(open(outfile))
        lddt  = data.get('lddt')  or math.nan
        ilddt = data.get('ilddt') or math.nan
    print('%f,%f,%s' % (lddt, ilddt, infile))
    if path.isfile(outfile):
        remove(outfile)
    sys.stdout.flush()
