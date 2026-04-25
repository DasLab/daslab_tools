#!/usr/bin/env python3
import argparse
import pandas as pd

parser = argparse.ArgumentParser(description='Convert CSV file(s) to Parquet.')
parser.add_argument('files', nargs='+', help='CSV file(s) to convert')
args = parser.parse_args()

for infile in args.files:
    assert infile.find('.csv') > -1
    print('Reading: ' + infile)
    df = pd.read_csv(infile)
    outfile = infile.replace('.csv', '.csv.parquet')
    df.to_parquet(outfile)
    print('Created: ' + outfile)
    print()
