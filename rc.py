#!/usr/bin/env python3
"""
Reverse complement script for DNA/RNA sequences.
Handles both command line sequences and FASTA files.
"""

import argparse
import sys
import gzip
import os
from pathlib import Path

def reverse_complement(sequence, is_rna=False):
    """
    Generate reverse complement of a DNA or RNA sequence.

    Args:
        sequence (str): Input nucleotide sequence
        is_rna (bool): If True, use RNA complement (U instead of T)

    Returns:
        str: Reverse complement sequence
    """
    # Define complement mappings
    if is_rna:
        complement_map = {
            'A': 'U', 'U': 'A', 'G': 'C', 'C': 'G',
            'a': 'u', 'u': 'a', 'g': 'c', 'c': 'g',
            'N': 'N', 'n': 'n'
        }
    else:
        complement_map = {
            'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G',
            'a': 't', 't': 'a', 'g': 'c', 'c': 'g',
            'N': 'N', 'n': 'n'
        }

    # Generate complement and reverse
    complement = ''.join(complement_map.get(base, base) for base in sequence)
    return complement[::-1]

def is_fasta_file(filename):
    """Check if filename suggests it's a FASTA file."""
    extensions = ['.fa', '.fasta', '.fa.gz', '.fasta.gz']
    return any(filename.lower().endswith(ext) for ext in extensions)

def get_output_filename(input_filename):
    """Generate output filename for FASTA files."""
    input_path = Path(input_filename)

    if input_filename.lower().endswith('.gz'):
        # Handle gzipped files
        stem = input_path.stem  # removes .gz
        if stem.endswith('.fa'):
            return str(input_path.parent / (stem[:-3] + '.RC.fa.gz'))
        elif stem.endswith('.fasta'):
            return str(input_path.parent / (stem[:-6] + '.RC.fasta.gz'))
    else:
        # Handle non-gzipped files
        if input_filename.lower().endswith('.fa'):
            return input_filename[:-3] + '.RC.fa'
        elif input_filename.lower().endswith('.fasta'):
            return input_filename[:-6] + '.RC.fasta'

    return input_filename + '.RC'

def open_file(filename, mode='rt'):
    """Open file, handling both regular and gzipped files."""
    if filename.endswith('.gz'):
        return gzip.open(filename, mode)
    else:
        return open(filename, mode)

def process_fasta_file(input_filename, force_rna=False):
    """Process a FASTA file and create reverse complement output."""
    output_filename = get_output_filename(input_filename)

    try:
        with open_file(input_filename, 'rt') as infile:
            # Determine output file opening mode
            if output_filename.endswith('.gz'):
                outfile = gzip.open(output_filename, 'wt')
            else:
                outfile = open(output_filename, 'w')

            with outfile:
                sequence = ""
                header = ""

                for line in infile:
                    line = line.strip()
                    if line.startswith('>'):
                        # Process previous sequence if exists
                        if header and sequence:
                            is_rna = force_rna or 'U' in sequence.upper()
                            rc_seq = reverse_complement(sequence, is_rna)
                            outfile.write(f"{header} RC\n")
                            outfile.write(f"{rc_seq}\n")

                        # Start new sequence
                        header = line
                        sequence = ""
                    else:
                        sequence += line

                # Process last sequence
                if header and sequence:
                    is_rna = force_rna or 'U' in sequence.upper()
                    rc_seq = reverse_complement(sequence, is_rna)
                    outfile.write(f"{header} RC\n")
                    outfile.write(f"{rc_seq}\n")

        print(f"Reverse complement written to: {output_filename}")

    except Exception as e:
        print(f"Error processing {input_filename}: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Generate reverse complement of DNA/RNA sequences"
    )
    parser.add_argument(
        'sequences',
        nargs='+',
        help='Input sequences or FASTA files'
    )
    parser.add_argument(
        '-rna',
        action='store_true',
        help='Force RNA mode (use U instead of T)'
    )

    args = parser.parse_args()

    for seq_input in args.sequences:
        if is_fasta_file(seq_input):
            # Process as FASTA file
            if os.path.exists(seq_input):
                process_fasta_file(seq_input, args.rna)
            else:
                print(f"Error: File {seq_input} not found", file=sys.stderr)
        else:
            # Process as sequence string
            is_rna = args.rna or 'U' in seq_input.upper()
            rc_seq = reverse_complement(seq_input, is_rna)
            print(rc_seq)

if __name__ == "__main__":
    main()

