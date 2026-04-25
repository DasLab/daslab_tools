#!/usr/bin/env python3

import argparse
import subprocess
from os import system
from os.path import abspath
from cluster_info import cluster_check, strip_home_dirname

parser = argparse.ArgumentParser(
    description='rsync files from a remote cluster to the current directory.',
    epilog='Tip: alias this to rfc in your .bashrc:\n  alias rfc="rsync_from_cluster.py"',
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('cluster', help='cluster name (e.g. sherlock, oak)')
parser.add_argument('files_and_flags', nargs=argparse.REMAINDER,
                    help='files to fetch and/or rsync flags (e.g. --exclude --delete)')
args = parser.parse_args()

(cluster, remotedir) = cluster_check(args.cluster)
if cluster == 'unknown':
    parser.error('%s is not a known cluster' % args.cluster)

filenames = []
extra_args = []
for m in args.files_and_flags:
    if len(m) > 2 and '--' in m:
        extra_args.append(m)
    else:
        filenames.append(m)
if not filenames:
    filenames = ['.']

clusterdir = remotedir + strip_home_dirname(abspath('.'))
cluster_prefix = cluster + ':' if cluster else ''

commands = []
for filename in filenames:
    remote_filename = ' ' + cluster_prefix + clusterdir + '/' + filename
    command = 'rsync -avL' + remote_filename + ' . ' + ' '.join(extra_args)
    print(command)
    system(command)
    commands.append(command)

print()
print('Ran the following commands:')
for command in commands:
    print()
    print(command)
