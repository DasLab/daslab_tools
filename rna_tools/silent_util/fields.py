#!/usr/bin/env python3
## look at fa scores

import argparse
import subprocess
import sys

def _alias_hint(alias_name, full_command):
    if '-h' not in sys.argv and '--help' not in sys.argv:
        return ''
    ok = subprocess.run(['/bin/bash', '-i', '-c', 'alias ' + alias_name],
                        capture_output=True).returncode == 0
    return ('Alias active: use  %s  instead of the full script name.' % alias_name
            if ok else
            'Tip: add to ~/.bashrc:\n  alias %s="%s"' % (alias_name, full_command))

parser = argparse.ArgumentParser(
    description='Show which column numbers correspond to which score terms in a Rosetta silent or score file.',
    epilog=_alias_hint('fp', 'fields.py'),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('scorefile', help='Rosetta silent file or score file')
args = parser.parse_args()

file1 = args.scorefile

inputfile = open(file1, 'r')

firstline = inputfile.readline()
if firstline.find('desc') < 0:
    firstline = inputfile.readline()

if firstline.find('desc') >= 0:
    labels = firstline.split()
    for i, label in enumerate(labels):
        print('%4d %s' % (i + 1, label))
else:
    lines = subprocess.run(['grep', 'SCORE', file1], capture_output=True, text=True).stdout.splitlines()[:50]
    if len(lines) > 0:
        cols = lines[-1].split()
        for i in range(len(cols) // 2):
            print('%4d %s' % (2 * i + 2, cols[2 * i]))
    else:
        firstline = open(file1).readline()
        cols = firstline.split()
        for i in range(len(cols)):
            print('%4d %s' % (i + 1, cols[i]))

print()
print('Score tags for: ', file1)
