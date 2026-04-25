#!/usr/bin/env python3

import argparse
import subprocess
from parse_options import get_ints

parser = argparse.ArgumentParser(
    description='Fix chain breaks in RNA PDB files using ERRASER.',
)
parser.add_argument('pdbs', nargs='+', help='PDB file(s) to fix')
args = parser.parse_args()

for pdb in args.pdbs:
    resnum_line = subprocess.run('get_res_num.py ' + pdb, shell=True,
                                 capture_output=True, text=True).stdout.splitlines()[0]
    cols = resnum_line.split()
    resnum = []
    print(resnum_line)
    for col in cols:
        get_ints(col, resnum)
    print('Residue numbers: ', resnum)

    # find existing cutpoint
    command = 'rna_rosetta_ready_set.py -pdb %s' % pdb
    lines = subprocess.run(command, shell=True, capture_output=True, text=True).stdout.splitlines(keepends=True)
    cutpoint_num = []
    for line in lines:
        if line.find('cutpoint in Rosetta pdb file') > -1:
            cols = line[:-1].split(':')[-1].split()
            for col in cols:
                cutpoint_num.append(int(col))

    print('Cutpoint number in renumbered PDB according to rna_rosetta_ready_set:', cutpoint_num)

    # actually use my new script 'check_cutpoint.py' to figure out stuff.
    command = 'check_cutpoints.py ' + pdb
    lines = subprocess.run(command, shell=True, capture_output=True, text=True).stdout.splitlines(keepends=True)
    cutpoints_num        = [int(x) for x in lines[1][:-1].split(':')[1].split()]
    distort_geometry_num = [int(x) for x in lines[2][:-1].split(':')[1].split()]

    print('Cutpoint number in renumbered PDB according to check_cutpoint.py:', cutpoint_num)
    print('Distorted C5*-O5* geometry in renumbered PDB according to check_cutpoint.py:', distort_geometry_num)

    rebuild_num = distort_geometry_num
    for n in cutpoint_num:
        if resnum[n] > resnum[n - 1] + 1:
            print(n, ' is meant to be a cutpoint, so no rebuild there.')
            continue
        if n not in rebuild_num:
            rebuild_num.append(n)
        if n + 1 not in rebuild_num:
            rebuild_num.append(n + 1)

    print(rebuild_num)

    tag = pdb.replace('.pdb', '')

    if len(rebuild_num) > 0:
        print(rebuild_num)
        rebuild_num_list = ''
        for m in rebuild_num:
            rebuild_num_list += ' %d' % m

        readysetpdb = tag + '_ready_set.pdb'

        command = ('seq_rebuild.py -pdb  %s -scoring_file rna/rna_hires_07232011_with_intra_base_phosphate'
                   '  -rebuild_res_list  %s  -native_screen_RMSD 2.0' % (readysetpdb, rebuild_num_list))
        print(command)
        subprocess.run(command, shell=True)

        command = 'cp  %s_ready_set_erraser.pdb   %s_fixcutpoint.pdb' % (tag, tag)
        print(command)
        subprocess.run(command, shell=True)

        command = 'renumber_pdb_in_place.py %s_fixcutpoint.pdb  %s' % (tag, resnum_line)
        print(command)
        subprocess.run(command, shell=True)
    else:
        print('No cutpoints identified!!!!')
        command = 'cp %s.pdb  %s_fixcutpoint.pdb' % (tag, tag)
        print(command)
        subprocess.run(command, shell=True)
