#!/usr/bin/env python3

import argparse
import subprocess
import sys
from os.path import abspath
from cluster_info import cluster_check, strip_home_dirname

def _alias_hint(alias_name, full_command):
    if '-h' not in sys.argv and '--help' not in sys.argv:
        return ''
    ok = subprocess.run(['/bin/bash', '-i', '-c', 'type ' + alias_name],
                        capture_output=True).returncode == 0
    hint = ('Shell function active: use  %s  instead of the full script name.' % alias_name
            if ok else
            'Tip: add to ~/.bashrc:\n  %s() { target=$(%s "$@") && cd "$target"; }' % (alias_name, full_command))
    hint += '\nNOTE: c2c must be a shell function (not a plain alias) so it can change your directory.'
    return hint

parser = argparse.ArgumentParser(
    description='Print the equivalent of the current directory in another location.',
    epilog=_alias_hint('c2c', 'cd_to_cluster.py'),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('destination', help='destination name (e.g. local, dropbox, gdrive, sherlock)')
if len(sys.argv) == 1:
    parser.print_help()
    print('\nRun  cluster_info.py  to see available destinations.')
    sys.exit(1)
args = parser.parse_args()

(cluster, remotedir) = cluster_check(args.destination)
if cluster == 'unknown':
    parser.error('%s is not a known destination' % args.destination)

target = remotedir + strip_home_dirname(abspath('.'))
if cluster == '':
    print(target)
else:
    print('Different filesystem (%s). SSH there with:' % args.destination)
    print('  ssh %s' % cluster)
    print('Then cd to the equivalent directory:')
    print('  cd %s' % target)
    sys.exit(1)

