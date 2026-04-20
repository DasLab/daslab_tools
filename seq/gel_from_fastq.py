#!/usr/bin/env python3
"""
gel_from_fastq.py

Create a "gel" style heatmap PNG (gel.png) summarizing read-length histograms
for one or more FASTQ files.

Usage:
    python gel_from_fastq.py reads1.fastq reads2.fq.gz ... \
        [--max_len MAX] [--bin_width BIN] [--out OUTFILE]

Notes:
 - By default max length (y-axis top) = 1.2 * max(90th percentile length across files).
 - Default bin width = 1. Histograms are normalized per-file (sum to 1).
 - Default grayscale colormap: 0 -> white, max -> black.
 - If 'open' is available (macOS), the script will run `open gel.png`.
"""
import argparse
import os
import gzip
import sys
import shutil
import subprocess

import numpy as np
import matplotlib.pyplot as plt

def read_lengths_from_fastq(path):
    """Return a list of sequence lengths from a FASTQ (supports .gz)."""
    opener = gzip.open if path.endswith('.gz') else open
    lengths = []
    try:
        with opener(path, 'rt', encoding='utf-8', errors='replace') as fh:
            while True:
                header = fh.readline()
                if not header:
                    break
                seq = fh.readline()
                if not seq:
                    break
                fh.readline()  # plus line
                fh.readline()  # qual line
                lengths.append(len(seq.rstrip('\n').rstrip('\r')))
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
    return lengths

def nice_basename(path):
    """Return basename without directory and without .gz, .fastq, .fq (case-insensitive)."""
    name = os.path.basename(path)
    if name.lower().endswith('.gz'):
        name = name[:-3]
    for ext in ('.fastq', '.fq'):
        if name.lower().endswith(ext):
            name = name[: -len(ext)]
            break
    return name

def main():
    p = argparse.ArgumentParser(description="Create gel-like read-length heatmap from FASTQ files")
    p.add_argument('fastq', nargs='+', help='One or more FASTQ/FQ files (optionally gzipped)')
    p.add_argument('--max_len', type=float, default=None,
                   help='Maximum length shown on y-axis. Default = 1.2 * max(90th percentiles).')
    p.add_argument('--bin_width', type=float, default=5.0, help='Bin width for length histogram (default 5)')
    p.add_argument('--out', default='gel.png', help='Output PNG filename (default gel.png)')
    args = p.parse_args()

    files = args.fastq
    if len(files) < 1:
        p.error("Please supply at least one FASTQ file.")

    # Read lengths
    all_lengths = []
    p90s = []
    labels = []
    for f in files:
        lengths = read_lengths_from_fastq(f)
        all_lengths.append(lengths)
        if lengths:
            p90 = float(np.percentile(lengths, 90))
        else:
            p90 = 0.0
        p90s.append(p90)
        labels.append(nice_basename(f))

    # Determine max length L
    if args.max_len is None:
        computed_max = max(p90s) if p90s else 0.0
        L = int(np.ceil(1.2 * computed_max)) if computed_max > 0 else 0
        if L == 0:
            L = int(np.ceil(max((max(lengths) if lengths else 0) for lengths in all_lengths)))
    else:
        L = int(args.max_len)

    if L <= 0:
        L = 1

    bin_width = float(args.bin_width)
    if bin_width <= 0:
        raise ValueError("bin_width must be positive")

    # Build bins: from 0 to L inclusive
    bins = np.arange(0, L + bin_width, bin_width)
    num_bins = len(bins) - 1

    # Compute normalized histograms (per-file normalization so each column sums to 1)
    N = len(files)
    hist_matrix = np.zeros((num_bins, N), dtype=float)  # rows = length-bins, cols = files
    for i, lengths in enumerate(all_lengths):
        if not lengths:
            continue
        # Clip lengths > L to the last bin (or exclude them). We'll exclude > L (counts only up to L).
        filtered = [l for l in lengths if l <= L]
        if len(filtered) == 0:
            counts = np.zeros(num_bins, dtype=float)
        else:
            counts, _ = np.histogram(filtered, bins=bins)
            tot = counts.sum()
            if tot > 0:
                counts = counts.astype(float) / tot  # normalize so each column sums to 1
        hist_matrix[:, i] = counts

    # Plot heatmap: rows = bins (y), cols = files (x)
    fig, ax = plt.subplots(figsize=(max(6, N * 0.8), 6))
    # imshow expects shape (M,N) where first axis is vertical. We want row0=smallest lengths at bottom.
    vmax = hist_matrix.max() if hist_matrix.size > 0 else 1.0
    im = ax.imshow(hist_matrix, aspect='auto', origin='lower',
                   cmap='gray_r', vmin=0.0, vmax=vmax,
                   extent=[-0.5, N - 0.5, 0, L])
    ax.set_xlim(-0.5, N - 0.5)
    ax.set_ylim(0, L)
    ax.set_xticks(range(N))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_ylabel('Read length')
    ax.set_xlabel('Files')
    ax.set_title('Read-length distributions (normalized histograms)')
    plt.tight_layout()
    plt.savefig(args.out, dpi=750)
    plt.close(fig)

    # If 'open' exists (macOS), attempt to open the image
    if shutil.which('open') is not None:
        try:
            subprocess.run(['open', args.out], check=False)
        except Exception:
            pass

if __name__ == '__main__':
    main()

