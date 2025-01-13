#!/usr/bin/env python3

import gzip
import argparse
import os
from os import path

parser = argparse.ArgumentParser(
                    prog = 'get_cif_info.py',
                    description = 'Get title and date from .cif file')

parser.add_argument('pdb_ids', nargs='*', help='CIF or PDB files')

args = parser.parse_args()
pdb_ids = args.pdb_ids

if len(pdb_ids)==0:
    parser.print_help()

for pdb_id in pdb_ids:
    if os.path.isfile( pdb_id ):
        cif_file = pdb_id
    elif os.path.isfile( pdb_id.lower() ): cif_file = pdb_id.lower()
    elif os.path.isfile( pdb_id + '.cif.gz' ): cif_file = pdb_id + '.cif.gz'
    elif os.path.isfile ( pdb_id.lower()+'.cif.gz'): cif_file = pdb_id.lower()+'.cif.gz'

    with gzip.open(cif_file,'rt') as f:
        title_in_next_line = False
        title = ''
        release_date_in_next_line = False
        release_date = ''
        for line in f:
            if title_in_next_line:
                title = line[1:].strip().replace("'",'').strip()
                title_in_next_line = False

            pos = line.find('_struct.title')
            if pos>=0:
                title = line[pos+len('_struct.title'):-1].strip().replace("'",'')
                if len(title)==0: title_in_next_line = True

            if release_date_in_next_line:
                release_date = line.split()[-1].strip()
                release_date_in_next_line = False

            pos = line.find('revision_date')
            if pos>=0:
                release_date = line[pos+len('revision_date'):-1].strip().replace("'",'')
                if len(release_date)==0: release_date_in_next_line = True

            if len(title)>0 and len(release_date)> 0:
                print( title,'\t%s' % cif_file,
                       '\t',release_date)
                break

        assert( len(title) > 0 )
        f.close()



