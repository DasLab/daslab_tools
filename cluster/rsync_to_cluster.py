#!/usr/bin/env python3

import argparse
import subprocess
import sys
from shlex import quote
from os.path import abspath, expanduser, basename
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
    description='rsync files from the current directory to a remote cluster.',
    epilog=_alias_hint('r2c', 'rsync_to_cluster.py'),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('cluster', help='cluster name (e.g. sherlock, oak)')
parser.add_argument('files_and_flags', nargs=argparse.REMAINDER,
                    help='files/dirs to sync and/or rsync flags (e.g. --exclude --delete)')
if len(sys.argv) == 1:
    parser.print_help()
    print('\nRun  cluster_info.py  to see available destinations.')
    sys.exit(1)
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

clusterdir = remotedir + strip_home_dirname(abspath('.'))

# Paths under Google Drive contain spaces ("Shared drives", "Das Lab", ...).  The remote path
# is interpreted by a shell ON THE CLUSTER -- once by ssh for the mkdir, and again by rsync's
# own `ssh host rsync --server ...` -- so it has to be quoted FOR that shell.  Wrapping it in
# double quotes is not enough: the LOCAL shell consumes those first, and the remote mkdir then
# word-splits the path into several directories.  shlex.quote() produces quoting that survives
# to the remote side, and passing argv as a list keeps the local shell out of it entirely.
# (rsync's -s/--protect-args would also fix this, but macOS ships openrsync, which lacks it.)
remote_q = quote(clusterdir)


def run(cmd):
    print(' '.join(quote(c) for c in cmd))
    return subprocess.run(cmd).returncode


if cluster:
    run(['ssh', cluster, 'mkdir -p ' + remote_q])
    dest = cluster + ':' + remote_q
else:
    run(['mkdir', '-p', clusterdir])
    dest = clusterdir

rc = run(['rsync', '-avL'] + dirs + [dest] + extra_args)
if rc != 0:
    sys.exit(rc)
