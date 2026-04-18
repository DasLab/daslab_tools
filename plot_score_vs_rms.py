#!/usr/bin/env python3
"""Plot score vs. rms_fill (or rms) from Rosetta .out files."""

import sys
import os
import subprocess
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def parse_out_file(filepath):
    header = None
    rows = []
    with open(filepath) as f:
        for line in f:
            if not line.startswith('SCORE:'):
                continue
            fields = line.split()
            if fields[1] == 'score':  # header row
                header = fields[1:]
            else:
                rows.append(fields[1:])
    if header is None or not rows:
        raise ValueError(f"No SCORE lines found in {filepath}")
    min_len = min(len(header), min(len(r) for r in rows))
    df = pd.DataFrame([r[:min_len] for r in rows], columns=header[:min_len])
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col])
    return df


def get_rms_col(df, filepath):
    if 'rms_fill' in df.columns:
        return 'rms_fill'
    if 'rms' in df.columns:
        return 'rms'
    raise ValueError(f"Neither 'rms_fill' nor 'rms' found in {filepath}. Columns: {list(df.columns)}")


def make_plot(filepaths):
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    if len(filepaths) == 1:
        # Single file: save PNG next to the .out file
        filepath = filepaths[0]
        df = parse_out_file(filepath)
        rms_col = get_rms_col(df, filepath)
        title = os.path.basename(filepath)
        out_png = os.path.splitext(filepath)[0] + '.png'

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(df[rms_col], df['score'], s=30, alpha=0.5, linewidths=0,
                   color=colors[0])
        ax.set_xlabel(rms_col)
        ax.set_ylabel('score')
        ax.set_title(title)
    else:
        # Multiple files: overlay on one plot, save in the directory of the first file
        fig, ax = plt.subplots(figsize=(9, 6))
        rms_col_used = None
        for i, filepath in enumerate(filepaths):
            df = parse_out_file(filepath)
            rms_col = get_rms_col(df, filepath)
            rms_col_used = rms_col
            label = os.path.basename(filepath)
            ax.scatter(df[rms_col], df['score'], s=30, alpha=0.5, linewidths=0,
                       color=colors[i % len(colors)], label=label)

        ax.set_xlabel(rms_col_used)
        ax.set_ylabel('score')
        ax.set_title('Score vs. RMS')
        ax.legend(fontsize=8, markerscale=2)

        first_dir = os.path.dirname(os.path.abspath(filepaths[0]))
        out_png = os.path.join(first_dir, 'score_rms_combined.png')

    plt.tight_layout()
    fig.savefig(out_png, dpi=300)
    plt.close(fig)
    print(f"Saved: {out_png}")

    if subprocess.run(['which', 'open'], capture_output=True).returncode == 0:
        subprocess.run(['open', out_png])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} file1.out [file2.out ...]")
        sys.exit(1)
    make_plot(sys.argv[1:])
