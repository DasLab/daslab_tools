#!/usr/bin/env python3

import argparse
import subprocess
import sys
from os.path import abspath
from cluster_info import cluster_check, strip_home_dirname

def _alias_hint(alias_name, full_command):
    if '-h' not in sys.argv and '--help' not in sys.argv:
        return ''
    ok = subprocess.run(['/bin/bash', '-i', '-c', 'alias ' + alias_name],
                        capture_output=True).returncode == 0
    return ('Alias active: use  %s  instead of the full script name.' % alias_name
            if ok else
            'Tip: add to ~/.bashrc:\n  alias %s="%s"' % (alias_name, full_command))

parser = argparse.ArgumentParser(
    description='Print the equivalent of the current directory in another location.',
    epilog=_alias_hint('c2c', 'cd_to_cluster.py'),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('destination', help='destination name (e.g. local, dropbox, gdrive, sherlock)')
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
