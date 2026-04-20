#!env python3
import pandas as pd
from sys import argv
files = argv[1:]
for infile in files:
    assert( infile.find('.parquet') > -1 )
    print('Reading: '+infile)
    df = pd.read_parquet(infile)
    outfile = infile.replace('.parquet','.csv')
    df.to_csv(outfile)
    print('Created: '+outfile)
    print()
