#!/usr/bin/env python3

import argparse
from read_pdb import read_pdb
from make_tag import make_tag
from math import sqrt

parser = argparse.ArgumentParser(description='Check for cutpoints and C5\'-O5\' bond geometry issues in PDB file(s).')
parser.add_argument('pdbfiles', nargs='+', help='PDB file(s) to check')
args = parser.parse_args()

for pdb in args.pdbfiles:
    CUTOFF = 1.8

    ( coords, pdb_lines, sequence ) = read_pdb( pdb )

    print(pdb)

    cutpoints = []
    for chain in coords.keys():
        for rsd in coords[ chain ].keys():
            if ( rsd-1 not in coords[chain].keys() ): continue
            if ( " P  "  in  coords[ chain ][ rsd ].keys() ):
                x1 = coords[ chain ][ rsd   ][ " P  " ]
                x2 = coords[ chain ][ rsd-1 ][ " O3'" ]
                dist2 = 0
                for k in range(3):
                    d = x1[k] - x2[k]
                    dist2 += d*d
                dist = sqrt( dist2 )
                if ( dist > CUTOFF ): cutpoints.append( rsd-1 )

    print("Cutpoints: ", make_tag( cutpoints ))

    cutpoints = []
    for chain in coords.keys():
        for rsd in coords[ chain ].keys():
            if ( " O5'"  in  coords[ chain ][ rsd ].keys() ):
                x1 = coords[ chain ][ rsd   ][ " C5'" ]
                x2 = coords[ chain ][ rsd   ][ " O5'" ]
                dist2 = 0
                for k in range(3):
                    d = x1[k] - x2[k]
                    dist2 += d*d
                dist = sqrt( dist2 )
                if ( dist > CUTOFF ): cutpoints.append( rsd )

    print("C5'-O5' problem: ", make_tag( cutpoints ))
    print()
