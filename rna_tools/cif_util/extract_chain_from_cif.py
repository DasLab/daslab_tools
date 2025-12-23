#!/usr/bin/env python
import sys
import gzip
import argparse
from Bio import PDB

def extract_chain_from_cif(cif_file, chain_id, output_file, C1prime_only = False):
    # Create a parser to read CIF files
    parser = PDB.MMCIFParser(QUIET=True)

    # Check if the file is gzipped and read it accordingly
    if cif_file.endswith('.gz'):
        with gzip.open(cif_file, 'rt') as gz_file:
            structure = parser.get_structure('structure', gz_file)
    else:
        structure = parser.get_structure('structure', cif_file)

    num_lines = 0
    # Open a new PDB file to write the specified chain
    with open(output_file, 'w') as pdb_file:
        # Iterate through the model and chains to fetch the desired chain
        found_chain = False
        for model in structure: # just do first model!
            for chain in model:
                #print(chain.id)
                if chain.id == chain_id:
                    found_chain = True
                    # Write the atoms of the specified chain to the PDB file
                    for residue in chain:
                        for atom in residue:
                            if C1prime_only and not atom.name=="C1'": continue
                            # Format and write atom in PDB format
                            pdb_file.write(
                                f'ATOM  {str(atom.serial_number)[-5:]:>5s}  {atom.name:4s}{residue.resname:>3s}{chain.id[-2:]:>2s}{residue.id[1]:>4d}{residue.id[2]:1s}   {atom.coord[0]:>8.3f}{atom.coord[1]:>8.3f}{atom.coord[2]:>8.3f}{atom.occupancy:>6.2f}{atom.bfactor:>6.2f}           {atom.element}\n'
                            )
                            num_lines += 1
            if found_chain: break

    print(f"Successfully extracted {num_lines} lines from chain {chain_id} to {output_file}")

def main():
    # Command line argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('cif_file', help='Input CIF file (PDB.cif or PDB.cif.gz)')
    parser.add_argument('chain_id', help='Chain ID to extract')
    parser.add_argument('-o', '--output', default='', help='Output PDB file name (default: {PDB}_{chain}.pdb)')
    parser.add_argument('--C1prime_only', action='store_true', help='Only output C1'' atoms')

    args = parser.parse_args()

    # Determine output file name if not provided
    if not args.output:
        args.output = f"{args.cif_file.split('.')[0]}_{args.chain_id}.pdb"

    extract_chain_from_cif(args.cif_file, args.chain_id, args.output, args.C1prime_only )

if __name__ == '__main__':
    main()
