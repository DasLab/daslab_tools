#!/usr/bin/env python3

import argparse
import subprocess
from os import system
from os.path import abspath, expanduser, basename
from cluster_info import cluster_check, strip_home_dirname

parser = argparse.ArgumentParser(
    description='rsync files from the current directory to a remote cluster.',
    epilog='Tip: alias this to r2c in your .bashrc:\n  alias r2c="rsync_to_cluster.py"',
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('cluster', help='cluster name (e.g. sherlock, oak)')
parser.add_argument('files_and_flags', nargs=argparse.REMAINDER,
                    help='files/dirs to sync and/or rsync flags (e.g. --exclude --delete)')
args = parser.parse_args()

(cluster, remotedir) = cluster_check(args.cluster)
if cluster == 'unknown':
    parser.error('%s is not a known cluster' % args.cluster)

dirs = []
extra_args = []
for m in args.files_and_flags:
    if len(m) > 2 and '--' in m:
        extra_args.append(m)
    else:
        dirs.append(m)
if not dirs:
    dirs = ['.']

clusterdir = '"' + remotedir + strip_home_dirname(abspath('.')) + '"'

command = 'mkdir -p ' + clusterdir
if cluster:
    command = 'ssh ' + cluster + ' ' + command
print(command)
system(command)

cluster_prefix = cluster + ':' if cluster else ''
command = 'rsync -avL ' + ' '.join(dirs) + ' ' + cluster_prefix + clusterdir + ' ' + ' '.join(extra_args)
print(command)
system(command)

print()
print('Ran the following command:')
print(command)
