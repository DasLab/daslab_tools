#!/usr/bin/env python3

import argparse
import sys
from os.path import abspath
from cluster_info import cluster_check, strip_home_dirname

parser = argparse.ArgumentParser(
    description='Print the equivalent of the current directory in another location.',
    epilog=(
        'Alias this to c2c in your ~/.bashrc:\n'
        '  alias c2c="cd_to_cluster.py"'
    ),
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
