#!/usr/bin/env python3
import argparse
import pandas as pd

parser = argparse.ArgumentParser(description='Re-encode Parquet file(s) using PyArrow engine.')
parser.add_argument('files', nargs='+', help='Parquet file(s) to re-encode')
args = parser.parse_args()

for infile in args.files:
    assert infile.find('.parquet') > -1
    print('Reading: ' + infile)
    df = pd.read_parquet(infile)
    outfile = infile.replace('.parquet', '.PYARROW.parquet')
    df.to_parquet(outfile)
    print('Created: ' + outfile)
    print()
