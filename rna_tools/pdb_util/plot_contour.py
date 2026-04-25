#!/usr/bin/env python3

import argparse
import matplotlib
import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import sys
import math
import subprocess
from os.path import dirname, abspath

parser = argparse.ArgumentParser(
    description='Plot contour maps from nucleobase_sample_around tables.',
    epilog='See also Rosetta/demos/public/nucleobase_sample_around.',
)
parser.add_argument('table_files', nargs='+', metavar='in.table', help='table file(s) to plot')
parser.add_argument('--out', metavar='out.png', default=None, help='output PNG filename (single-file mode only)')
args = parser.parse_args()

for table_file in args.table_files:
    if table_file[-6:] != '.table': continue
    if table_file[:8] == 'score_z.': continue
    print('Making plot for: ', table_file)

    plt.clf()

    coords = []
    coords_ploted = []
    pdb_file = open(dirname(abspath(table_file)) + '/START.pdb')
    for line in pdb_file:
        if line[0:4] != 'ATOM':
            continue
        atom_type = line[13]
        x = -float(line.split()[6])
        y =  float(line.split()[7])
        z = -float(line.split()[8])
        coords.append([atom_type, x, y, z])
        if 'xz' in table_file:
            coords_ploted.append([x, z])
        elif 'yz' in table_file:
            coords_ploted.append([y, z])
        else:
            coords_ploted.append([x, y])
    pdb_file.close()

    for i, coord1 in enumerate(coords):
        color = ''
        markersize = 8
        atom_type = coord1[0]
        x = coords_ploted[i][0]
        y = coords_ploted[i][1]

        if atom_type == 'H':
            color = 'wo'
            markersize = 5
        elif atom_type == 'N':
            color = 'bo'
        elif atom_type == 'C':
            color = 'ko'
        elif atom_type == 'O':
            color = 'ro'
        scat = plt.plot(x, y, color)
        plt.setp(scat, 'markersize', markersize)

        for j, coord2 in enumerate(coords):
            if i == j:
                continue
            dist = ((coord1[1] - coord2[1]) ** 2 +
                    (coord1[2] - coord2[2]) ** 2 +
                    (coord1[3] - coord2[3]) ** 2)
            dist = math.sqrt(dist)
            if dist < 1.6:
                x_line = [x, coords_ploted[j][0]]
                y_line = [y, coords_ploted[j][1]]
                plt.plot(x_line, y_line, 'k-')

    scores_file = open(table_file)
    scores = []
    for line in scores_file:
        score_1d = []
        for elem in line.split():
            score = float(elem)
            if math.isnan(score):
                score = 1000
            score_1d.append(score)
        scores.append(score_1d)

    ns = len(scores)
    scores = np.array(scores)

    if ns == 0:
        print('Skipping ', table_file, ' ==> No data!')
        continue

    sum_bound = 0
    n_data = 0
    for i in range(ns):
        for j in range(ns):
            if i == 0 or i == ns - 1 or j == 0 or j == ns - 1:
                sum_bound += scores[i, j]
                n_data += 1

    baseline = sum_bound / n_data

    for i in range(ns):
        for j in range(ns):
            if math.isnan(scores[i, j]):
                print(i, ' ', j)
            scores[i, j] -= baseline

    min_score = scores.min()

    sample_grid = 0.2
    sample_max = (len(scores) - 1) * 0.5 * sample_grid
    X = np.arange(-sample_max, sample_max + sample_grid, sample_grid)
    Y = X

    grid_size = abs(min_score) / 100.0
    levels = np.arange(min_score, grid_size * 40, grid_size)

    CS = plt.contourf(X, Y, scores, levels)

    plt.axis([-10, 10, -10, 10])
    plt.colorbar()
    plt.title(table_file)

    if args.out:
        png_file = args.out
    elif len(args.table_files) == 1:
        png_file = table_file.replace('.table', '.png')
    else:
        png_file = table_file.replace('.table', '.png')

    if len(png_file) > 0:
        plt.savefig(png_file, dpi=200)
        print('Created: ', png_file)
        print()
        out = subprocess.run(['uname'], capture_output=True, text=True).stdout
        if 'Darwin' in out:
            subprocess.call(['open', png_file])
        if 'Linux' in out:
            subprocess.call(['xdg-open', png_file])
    else:
        plt.show()
