#!/usr/bin/env python3
"""
gdt.py — Wrapper around TMscore binary to compute GDT-TS scores.

Usage:
    gdt.py ref.pdb query1.pdb query2.pdb ...
    gdt.py -refpdb ref1.pdb ref2.pdb -pdb query1.pdb query2.pdb
    gdt.py -t ref.pdb query1.pdb          # tabular CSV output
"""
from __future__ import annotations

import argparse
import glob
import re
import shlex
import shutil
import subprocess
from os.path import exists
from sys import stderr, exit


def expand_patterns(patterns):
    out = []
    for p in patterns:
        if exists(p):
            out.append(p)
        else:
            matches = sorted(glob.glob(p))
            if matches:
                out.extend(matches)
            else:
                out.append(p)
    seen = set()
    uniq = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def parse_tmscore_output(lines):
    """Parse TMscore binary stdout for GDT-TS, TM-score, aligned length, RMSD."""
    gdt_ts = 0.0
    tmscore = 0.0
    nalign = 0
    rmsd = 0.0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('GDT-TS-score='):
            m = re.search(r'GDT-TS-score=\s*([\d.]+)', stripped)
            if m:
                gdt_ts = float(m.group(1))
        elif stripped.startswith('TM-score'):
            m = re.search(r'TM-score\s*=\s*([\d.]+)', stripped)
            if m:
                tmscore = float(m.group(1))
        elif stripped.startswith('RMSD'):
            m = re.search(r'([\d.]+)', stripped)
            if m:
                rmsd = float(m.group(1))
        elif stripped.startswith('Number of residues in common'):
            m = re.search(r'(\d+)\s*$', stripped)
            if m:
                nalign = int(m.group(1))
    return gdt_ts, tmscore, nalign, rmsd


def main():
    parser = argparse.ArgumentParser(description='Compute GDT-TS scores using the TMscore binary.')
    parser.add_argument('-refpdb', nargs='+',
                        help='Reference PDB file(s). If provided, -pdb must be used for queries.')
    parser.add_argument('-pdb', nargs='+',
                        help='PDB file(s) to align (use with -refpdb). Globs allowed.')
    parser.add_argument('inputs', nargs='*',
                        help='Legacy: first is ref PDB, rest are query PDBs (use when not using -refpdb).')
    parser.add_argument('-atom', default=" C1'", help='4-char atom name (default: " C1\'")')
    parser.add_argument('-t', '--tabular', action='store_true', help='output in csv format')
    parser.add_argument('-v', '--verbose', action='store_true', help='print command and full output')

    args = parser.parse_args()

    if shutil.which('TMscore') is None:
        stderr.write("Error: 'TMscore' not found in PATH.\n")
        exit(1)

    if args.refpdb:
        if not args.pdb:
            stderr.write("When using -refpdb you must provide query PDBs via -pdb\n")
            exit(1)
        ref_patterns = args.refpdb
        query_patterns = args.pdb
    else:
        if not args.inputs or len(args.inputs) < 2:
            stderr.write("Usage: gdt.py ref.pdb query1.pdb [query2.pdb ...]\n")
            parser.print_usage()
            exit(1)
        ref_patterns = [args.inputs[0]]
        query_patterns = args.inputs[1:]

    ref_files = expand_patterns(ref_patterns)
    query_files = expand_patterns(query_patterns)

    verified_refs = []
    for rf in ref_files:
        if not exists(rf):
            stderr.write(f'Could not find reference PDB file: {rf}\n')
            exit(1)
        verified_refs.append(rf)

    final_queries = []
    for q in query_files:
        if not exists(q):
            stderr.write(f'Could not find PDB file: {q}\n')
            continue
        final_queries.append(q)

    if not final_queries:
        stderr.write('No query PDB files found.\n')
        exit(1)

    if args.tabular:
        print('ref,query,GDT_TS')

    for refpdb in verified_refs:
        for pdb_path in final_queries:
            cmd = ['TMscore', pdb_path, refpdb, '-atom', args.atom]

            if args.verbose:
                print(shlex.join(cmd) if hasattr(shlex, 'join') else ' '.join(shlex.quote(a) for a in cmd))

            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            except FileNotFoundError:
                stderr.write('Executable not found: TMscore\n')
                exit(1)

            stdout_lines = res.stdout.splitlines()
            if args.verbose:
                for line in stdout_lines:
                    print(line.strip())

            gdt_ts, tmscore_val, nalign, rmsd_align = parse_tmscore_output(stdout_lines)

            if args.tabular:
                print('%s,%s,%f' % (refpdb, pdb_path, gdt_ts))
            else:
                print('%s -vs- %s: %9.5f over %d residues   GDT-TS: %f  TM-score: %f' %
                      (refpdb, pdb_path, rmsd_align, nalign, gdt_ts, tmscore_val))


if __name__ == '__main__':
    main()
