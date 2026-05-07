#!/usr/bin/env python3

import argparse
import os
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
            'Tip: add to ~/.bashrc:\n  %s() { target=$(%s "$@") || return 1; [ -d "$target" ] || { echo "No such directory: $target" >&2; echo "Re-run with -m / --make_dirs to create it." >&2; return 1; }; cd "$target" && pwd; }' % (alias_name, full_command))
    hint += '\nNOTE: c2c must be a shell function (not a plain alias) so it can change your directory.'
    return hint

parser = argparse.ArgumentParser(
    description='Print the equivalent of the current directory in another location.',
    epilog=_alias_hint('c2c', 'cd_to_cluster.py'),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('destination', help='destination name (e.g. local, dropbox, gdrive, sherlock)')
parser.add_argument('-m', '--make_dirs', action='store_true',
                    help='create the target directory (and parents) if it does not exist')
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
    if args.make_dirs:
        os.makedirs(target, exist_ok=True)
    print(target)
else:
    print('Different filesystem (%s). SSH there with:' % args.destination)
    print('  ssh %s' % cluster)
    print('Then cd to the equivalent directory:')
    print('  cd %s' % target)
    sys.exit(1)

