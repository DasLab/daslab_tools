#!/usr/bin/env python3
import sys
import gzip
import os

def convert_sequence(seq):
    """Convert T->U in sequence"""
    return seq.translate(str.maketrans('Tt', 'Uu'))

def process_fasta(input_file, output_file):
    """Process FASTA file and convert sequences"""
    opener = gzip.open if input_file.endswith('.gz') else open
    out_opener = gzip.open if output_file.endswith('.gz') else open

    with opener(input_file, 'rt') as inf, out_opener(output_file, 'wt') as outf:
        for line in inf:
            if line.startswith('>'):
                outf.write(line.rstrip() + ' DNA2RNA\n')
            else:
                outf.write(convert_sequence(line))

def get_output_filename(input_file):
    """Generate output filename with .DNA2RNA suffix"""
    if input_file.endswith('.gz'):
        base = input_file[:-3]
        ext = os.path.splitext(base)[1]
        return base.replace(ext, f'.DNA2RNA{ext}.gz')
    else:
        base, ext = os.path.splitext(input_file)
        return f'{base}.DNA2RNA{ext}'

def is_fasta_file(filename):
    """Check if filename suggests it's a FASTA file"""
    fasta_extensions = ['.fa', '.fasta', '.fa.gz', '.fasta.gz']
    return any(filename.endswith(ext) for ext in fasta_extensions)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert DNA sequences or FASTA files to RNA (T→U).')
    parser.add_argument('inputs', nargs='+', help='DNA sequence string(s) or FASTA file(s)')
    args = parser.parse_args()

    for arg in args.inputs:
        if is_fasta_file(arg):
            output_file = get_output_filename(arg)
            process_fasta(arg, output_file)
            print(f"Processed {arg} -> {output_file}")
        else:
            print(convert_sequence(arg))

if __name__ == "__main__":
    main()
