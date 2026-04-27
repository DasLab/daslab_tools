#!/usr/bin/env python3

from os.path import expanduser, expandvars, basename
import subprocess

user_name = basename(expanduser('~'))
biox3_user_name = expandvars('$BIOX3_USER_NAME')
if biox3_user_name == '$BIOX3_USER_NAME': biox3_user_name = user_name
sherlock_user_name = expandvars('$SHERLOCK_USER_NAME')
if sherlock_user_name == '$SHERLOCK_USER_NAME': sherlock_user_name = user_name

def cluster_check(cluster_in):
    clusterlist = [
        'biox3', 'biox3_scratch',
        'sherlock', 'sherlock_scratch', 'sherlock_group', 'sherlock_scratch_group',
        'scratch', 'scratch_group', 'group', 'sg', 'ss', 'sherlock_oak', 'oak',
        'local', 'dropbox', 'gdrive',
    ]

    cluster = cluster_in
    if cluster not in clusterlist:
        print('Hey, ' + cluster + ' is not a known cluster.')
        cluster = 'unknown'

    cluster_dir = ''

    if cluster == 'scratch':        cluster = 'sherlock_scratch'
    if cluster == 'ss':             cluster = 'sherlock_scratch'
    if cluster == 'scratch_group':  cluster = 'sherlock_scratch_group'
    if cluster == 'sg':             cluster = 'sherlock_scratch_group'
    if cluster == 'group':          cluster = 'sherlock_group'
    if cluster == 'oak':            cluster = 'sherlock_oak'

    if cluster == 'biox3':
        cluster = '%s@biox3.stanford.edu' % biox3_user_name
        cluster_dir = '/home/%s/' % biox3_user_name

    if cluster == 'biox3_scratch':
        cluster = '%s@biox3.stanford.edu' % biox3_user_name
        cluster_dir = '/scratch/users/%s/' % biox3_user_name

    if cluster == 'sherlock':
        cluster = '%s@login.sherlock.stanford.edu' % sherlock_user_name
        cluster_dir = '/home/users/%s/' % sherlock_user_name

    if cluster == 'sherlock_group':
        cluster = '%s@login.sherlock.stanford.edu' % sherlock_user_name
        cluster_dir = '/home/groups/rhiju/%s/' % sherlock_user_name

    if cluster == 'sherlock_scratch':
        cluster = '%s@login.sherlock.stanford.edu' % sherlock_user_name
        cluster_dir = '/scratch/users/%s/' % sherlock_user_name

    if cluster == 'sherlock_scratch_group':
        cluster = '%s@login.sherlock.stanford.edu' % sherlock_user_name
        cluster_dir = '/scratch/groups/rhiju/%s/' % sherlock_user_name

    if cluster == 'sherlock_oak':
        cluster = '%s@login.sherlock.stanford.edu' % sherlock_user_name
        cluster_dir = '/oak/stanford/groups/rhiju/sherlock/home/%s/' % sherlock_user_name

    if cluster == 'local':
        cluster = ''
        cluster_dir = '/Users/%s/LocalDataAnalysis/' % user_name

    if cluster == 'dropbox':
        cluster = ''
        cluster_dir = '/Users/%s/Dropbox/' % user_name

    if cluster == 'gdrive':
        cluster = ''
        cluster_dir = '/Users/%s/Google Drive/My Drive/' % (user_name)

    hostname = subprocess.run(['hostname'], capture_output=True, text=True).stdout
    if 'sherlock' in cluster and hostname[:3] == 'sh0':  # local transfer on Sherlock
        cluster = ''

    return (cluster, cluster_dir)


def strip_home_dirname(clusterdir):
    clusterdir = clusterdir.replace('/Users/%s/' % user_name, '')
    clusterdir = clusterdir.replace('Dropbox/', '')
    clusterdir = clusterdir.replace('LocalDataAnalysis/', '')
    clusterdir = clusterdir.replace('Library/CloudStorage/GoogleDrive-%s@stanford.edu/My Drive/' % user_name, '')
    clusterdir = clusterdir.replace('Google Drive/My Drive/','')
    clusterdir = clusterdir.replace('Library/CloudStorage/', '')
    clusterdir = clusterdir.replace('/scratch/users/%s/' % user_name, '')
    clusterdir = clusterdir.replace('/scratch/groups/rhiju/%s/' % user_name, '')
    clusterdir = clusterdir.replace('/home/users/%s/' % user_name, '')
    clusterdir = clusterdir.replace('/home/%s/' % user_name, '')
    return clusterdir


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='List available cluster/destination names.')
    parser.add_argument('-a', '--all', action='store_true', help='show resolved host and path for each destination')
    args = parser.parse_args()

    entries = [
        ('local',                  []),
        ('dropbox',                []),
        ('gdrive',                 []),
        ('sherlock',               []),
        ('sherlock_scratch',       ['scratch', 'ss']),
        ('sherlock_group',         ['group']),
        ('sherlock_scratch_group', ['scratch_group', 'sg']),
        ('sherlock_oak',           ['oak']),
        ('biox3',                  []),
        ('biox3_scratch',          []),
    ]

    print('Available destinations:\n')
    if args.all:
        print(f'  {"name":<26}  {"aliases":<18}  host / path')
        print('  ' + '-' * 74)
    for name, aliases in entries:
        alias_str = ' (' + ', '.join(aliases) + ')' if aliases else ''
        if args.all:
            cluster, cluster_dir = cluster_check(name)
            host = '(local)' if cluster == '' else cluster
            print(f'  {name:<26}  {", ".join(aliases):<18}  {host}  {cluster_dir}')
        else:
            print(f'  {name}{alias_str}')
    if not args.all:
        print('\n  (run with -a/--all to see resolved host and path for each)')
