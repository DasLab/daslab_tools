#!/usr/bin/env python3

import argparse
from os import system, remove
from os.path import exists
import renumber_pdb_in_place
import parse_tag

parser = argparse.ArgumentParser(
    description='Prepare RNA Puzzle submission PDB from a ranked list of models.',
    epilog='PDB file names should be listed in order in submit_order.list.',
)
parser.add_argument('puzzle_number', help='RNA Puzzle problem number (e.g. 34)')
parser.add_argument('-renumber', metavar='RES', default=None,
                    help='residue renumbering spec (e.g. A:1-50)')
parser.add_argument('-unvirt', metavar='RES', default=None,
                    help='additional residues to unvirtualize (residue 1 always included)')
args = parser.parse_args()

lines = open('submit_order.list').readlines()
pdbs = [x.replace('\n', '') for x in lines]

problem_number = args.puzzle_number

new_numbers, chains = [], []
if args.renumber is not None:
    new_numbers, chains = parse_tag.parse_tag(args.renumber)
    print(new_numbers, chains)

unvirt_res = [1]
if args.unvirt is not None:
    unvirt_res += parse_tag.parse_tag(args.unvirt)[0]
unvirt_res = ' '.join(list(set(map(str, unvirt_res))))

final_submit_pdb = 'DASLAB_Problem%s.pdb' % problem_number
if exists(final_submit_pdb):
    remove(final_submit_pdb)

count = 0
for pdb in pdbs:
    if len(pdb) == 0:
        continue

    count = count + 1

    if len(new_numbers) and not pdb.startswith('default'):
        new_pdb = pdb.replace('.pdb', '.renumbered.pdb')
        cmd = ' '.join(['cp', pdb, new_pdb])
        print(cmd)
        system(cmd)
        pdb = new_pdb

        renumber_pdb_in_place.renumber_pdb([pdb], new_numbers, chains=chains)

        new_pdb = pdb.replace('.pdb', '.REORDER.pdb')
        cmd = 'reorder_pdb.py ' + pdb
        print(cmd)
        system(cmd)
        pdb = new_pdb

    new_pdb = pdb.replace('.pdb', '.unvirtualized.pdb')
    command = 'rna_graft -s %s %s -o %s -unvirtualize_phosphate_res %s -graft_backbone_only' % (
        pdb, pdb, new_pdb, unvirt_res
    )
    print(command)
    print(system(command))
    pdb = new_pdb

    new_pdb = 'DASLAB_Problem%s_Rank%d.pdb' % (problem_number, count)
    command = 'reorder_to_standard_pdb.py %s > %s' % (pdb, new_pdb)
    print(command)
    system(command)

    command = 'echo MODEL %d >> %s' % (count, final_submit_pdb)
    print(command)
    system(command)

    command = 'cat %s >> %s' % (new_pdb, final_submit_pdb)
    print(command)
    system(command)

    command = 'echo TER >> %s' % final_submit_pdb
    print(command)
    system(command)

    command = 'echo ENDMDL >> %s' % final_submit_pdb
    print(command)
    system(command)

print('\nSubmit this combined pdb: ', final_submit_pdb)
