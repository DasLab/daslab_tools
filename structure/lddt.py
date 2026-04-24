#!/usr/bin/env python3
from sys import argv, stdout, stderr
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

args = argv[1:]
verbose        = '-v' in args or '--verbose' in args
no_stereocheck = '--lddt_no_check' in args or '-nc' in args
files = [a for a in args if a not in ('-v', '--verbose', '--lddt_no_check', '-nc')]

if len(files) < 2:
    print(argv[0] + ' [-v/--verbose] [-nc/--lddt_no_check] <ref> <model files...>')
    sys.exit(0)

if not path.isfile(files[0]):
    print('Could not find reference PDB file: ' + files[0], file=stderr)
    sys.exit(1)

ref_fmt = fmt(files[0])
for infile in files[1:]:
    if not path.exists(infile):
        stderr.write('Could not find model PDB file: ' + infile + '\n')
        continue
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tf:
        outfile = tf.name
    cmd = [ost_bin, 'compare-structures',
           '-r', files[0], '-m', infile,
           '-rf', ref_fmt, '-mf', fmt(infile),
           '-ft', '--lddt', '--ilddt',
           '-o', outfile, '-v', '0']
    if no_stereocheck:
        cmd.append('--lddt-no-stereochecks')
    if verbose:
        print('Running: ' + ' '.join(cmd), file=stderr)
    result = subprocess.run(cmd, capture_output=True)
    lddt = math.nan
    ilddt = math.nan
    if result.returncode:
        print('ERROR: ost command failed with exit code %d' % result.returncode, file=stderr)
        if result.stderr:
            stderr.write(result.stderr.decode())
    elif path.isfile(outfile):
        data = json.load(open(outfile))
        lddt  = data.get('lddt')  or math.nan
        ilddt = data.get('ilddt') or math.nan
    print('%f,%f,%s' % (lddt, ilddt, infile))
    if path.isfile(outfile):
        remove(outfile)
    stdout.flush()
