"""Draw the map with the raw (Dijkstra) and smoothed (PCHIP) waypoints.

Usage:
    python3 plot_waypoints.py <map.yaml> <raw_path.csv> <smoothed_path.csv> \
        -o trajectory_overlay.png
"""
import argparse
import csv
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import yaml
from PIL import Image

matplotlib.use('Agg')


def load_map(yaml_path):
    with open(yaml_path, 'r') as f:
        meta = yaml.safe_load(f)
    image_path = os.path.join(
        os.path.dirname(os.path.abspath(yaml_path)), meta['image'])
    img = np.array(Image.open(image_path).convert('L'))
    return img, meta['resolution'], meta['origin']


def load_waypoints(csv_path):
    xs, ys = [], []
    with open(csv_path, 'r') as f:
        for row in csv.DictReader(f):
            xs.append(float(row['x']))
            ys.append(float(row['y']))
    return np.array(xs), np.array(ys)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('map_yaml')
    parser.add_argument('raw_csv')
    parser.add_argument('smoothed_csv')
    parser.add_argument('-o', '--output', default='trajectory_overlay.png')
    args = parser.parse_args()

    pgm, resolution, origin = load_map(args.map_yaml)
    ros_array = np.flipud(pgm)  # row 0 = minimum Y, ROS convention

    height, width = ros_array.shape
    x_min, y_min = origin[0], origin[1]
    x_max = x_min + width * resolution
    y_max = y_min + height * resolution

    xs_raw, ys_raw = load_waypoints(args.raw_csv)
    xs_s, ys_s = load_waypoints(args.smoothed_csv)

    fig, ax = plt.subplots(figsize=(6, 16))
    ax.imshow(ros_array, cmap='gray', origin='lower',
              extent=[x_min, x_max, y_min, y_max])
    ax.plot(xs_raw, ys_raw, '-', color='red', linewidth=1.2,
            label=f'Raw path - Dijkstra ({len(xs_raw)} pts)')
    ax.plot(xs_s, ys_s, '-', color='limegreen', linewidth=1.8,
            label=f'Smoothed path - PCHIP ({len(xs_s)} pts)')
    ax.plot(xs_raw[0], ys_raw[0], 'o', color='blue', markersize=8, label='Start')
    ax.plot(xs_raw[-1], ys_raw[-1], 'o', color='gold', markersize=8, label='Goal')

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title('Global path: Dijkstra + PCHIP smoothing')
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f'Image saved to: {args.output}')


if __name__ == '__main__':
    main()
