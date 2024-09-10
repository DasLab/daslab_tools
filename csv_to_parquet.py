#!env python3
import pandas as pd
from sys import argv
files = argv[1:]
for infile in files:
    assert( infile.find('.csv') > -1 )
    print('Reading: '+infile)
    df = pd.read_csv(infile)
    outfile = infile.replace('.csv','.csv.parquet')
    df.to_parquet(outfile)
    print('Created: '+outfile)
    print()
