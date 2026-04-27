#!/usr/bin/env python3

import argparse
import subprocess
import sys
from os import system
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
    description='rsync files from a remote cluster to the current directory.',
    epilog=_alias_hint('rfc', 'rsync_from_cluster.py'),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('cluster', help='cluster name (e.g. sherlock, oak)')
parser.add_argument('files_and_flags', nargs=argparse.REMAINDER,
                    help='files to fetch and/or rsync flags (e.g. --exclude --delete)')
if len(sys.argv) == 1:
    parser.print_help()
    print('\nRun  cluster_info.py  to see available destinations.')
    sys.exit(1)
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
    remote_spec = '"' + cluster_prefix + clusterdir + '/' + filename + '"'
    command = 'rsync -avL ' + remote_spec + ' . ' + ' '.join(extra_args)
    print(command)
    system(command)
    commands.append(command)

print()
print('Ran the following commands:')
for command in commands:
    print()
    print(command)
