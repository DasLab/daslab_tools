#!/usr/bin/env python3
import argparse
import pandas as pd

parser = argparse.ArgumentParser(description='Convert Parquet file(s) to CSV.')
parser.add_argument('files', nargs='+', help='Parquet file(s) to convert')
args = parser.parse_args()

for infile in args.files:
    assert infile.find('.parquet') > -1
    print('Reading: ' + infile)
    df = pd.read_parquet(infile)
    outfile = infile.replace('.parquet', '.csv')
    df.to_csv(outfile)
    print('Created: ' + outfile)
    print()
