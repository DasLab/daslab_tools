#!/usr/bin/env python3
import sys
import gzip
import os

def convert_sequence(seq):
    """Convert U->T in sequence"""
    return seq.translate(str.maketrans('Uu', 'Tt'))

def process_fasta(input_file, output_file):
    """Process FASTA file and convert sequences"""
    opener = gzip.open if input_file.endswith('.gz') else open
    out_opener = gzip.open if output_file.endswith('.gz') else open

    with opener(input_file, 'rt') as inf, out_opener(output_file, 'wt') as outf:
        for line in inf:
            if line.startswith('>'):
                # Add RNA2DNA tag to header
                outf.write(line.rstrip() + ' RNA2DNA\n')
            else:
                # Convert sequence
                outf.write(convert_sequence(line))

def get_output_filename(input_file):
    """Generate output filename with .RNA2DNA suffix"""
    if input_file.endswith('.gz'):
        base = input_file[:-3]  # Remove .gz
        ext = os.path.splitext(base)[1]  # Get .fa/.fasta
        return base.replace(ext, f'.RNA2DNA{ext}.gz')
    else:
        base, ext = os.path.splitext(input_file)
        return f'{base}.RNA2DNA{ext}'

def is_fasta_file(filename):
    """Check if filename suggests it's a FASTA file"""
    fasta_extensions = ['.fa', '.fasta', '.fa.gz', '.fasta.gz']
    return any(filename.endswith(ext) for ext in fasta_extensions)

def main():
    if len(sys.argv) < 2:
        print("Usage: python rna2dna.py <string_or_file> [string_or_file ...]")
        sys.exit(1)

    for arg in sys.argv[1:]:
        if is_fasta_file(arg):
            # Process as FASTA file
            output_file = get_output_filename(arg)
            process_fasta(arg, output_file)
            print(f"Processed {arg} -> {output_file}")
        else:
            # Process as string
            converted = convert_sequence(arg)
            print(converted)

if __name__ == "__main__":
    main()

