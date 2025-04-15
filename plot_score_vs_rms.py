#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import shutil

def extract_scores(file_name):
    # Read the file and filter lines for "SCORE"
    with open(file_name, 'r') as file:
        lines = [line for line in file if "SCORE" in line]

    if not lines:
        print(f"No SCORE lines found in {file_name}.")
        return None

    # Create a DataFrame from the SCORE lines
    data = [line.split() for line in lines]
    df = pd.DataFrame(data)

    # Assume header is in the first line
    header = df.iloc[0]
    df.columns = header
    df = df[1:]  # Skip the header row

    # Convert relevant columns to numeric
    df['score'] = pd.to_numeric(df['score'], errors='coerce')
    df['rms'] = pd.to_numeric(df['rms'], errors='coerce')

    # Drop any rows with NaN values in 'score' or 'rms'
    df = df.dropna(subset=['score', 'rms'])

    return df[['score', 'rms']]

def plot_scores(file_names):
    colors = ['black', 'red']
    plt.figure(figsize=(8, 6))

    all_scores = []

    for i, file_name in enumerate(file_names):
        scores_df = extract_scores(file_name)
        if scores_df is not None:
            plt.scatter(scores_df['rms'], scores_df['score'], color=colors[i], label=os.path.splitext(os.path.basename(file_name))[0])
            all_scores.append(scores_df['score'])

    # Combine all scores for y-axis limits
    if all_scores:
        combined_scores = pd.concat(all_scores)
        y_min = combined_scores.min() - 10
        y_max = combined_scores.quantile(0.9) + 50

        # Set y-limits
        plt.ylim(y_min, y_max)

    plt.title('Score vs RMS Scatterplot')
    plt.xlabel('RMS')
    plt.ylabel('Score')
    plt.legend()
    plt.grid()
    plt.tight_layout()

    # Save the figure
    output_file = 'score_vs_rms_plot.png'
    plt.savefig(output_file, dpi=300)
    print(f'Saved plot to {output_file}')
    plt.close()

    if shutil.which('open'): os.system(f'open {output_file}')

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python script.py <scorefile1> [<scorefile2>]")
        sys.exit(1)

    score_files = sys.argv[1:3]
    plot_scores(score_files)

