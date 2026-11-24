"""Draw a saved map with a real-world coordinate grid.

Use it to choose start/goal coordinates in free (white) space.

Usage:
    python3 visualize_map.py <map.yaml> [-o map_with_grid.png]
"""
import argparse
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import yaml
from PIL import Image

matplotlib.use('Agg')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('map_yaml')
    parser.add_argument('-o', '--output', default='map_with_grid.png')
    args = parser.parse_args()

    with open(args.map_yaml, 'r') as f:
        meta = yaml.safe_load(f)
    image_path = os.path.join(
        os.path.dirname(os.path.abspath(args.map_yaml)), meta['image'])
    pgm = np.array(Image.open(image_path).convert('L'))

    # Row 0 of a PGM is the TOP of the picture (maximum Y). flipud makes
    # row 0 correspond to the map origin, exactly as map_server does.
    grid = np.flipud(pgm)
    height, width = grid.shape
    res = meta['resolution']
    x_min, y_min = meta['origin'][0], meta['origin'][1]
    x_max, y_max = x_min + width * res, y_min + height * res

    fig, ax = plt.subplots(figsize=(6, 16))
    ax.imshow(grid, cmap='gray', origin='lower',
              extent=[x_min, x_max, y_min, y_max])
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title('Pick start/goal in free space (white)')
    ax.grid(True, color='cyan', alpha=0.4, linewidth=0.5)
    ax.set_xticks(np.arange(np.floor(x_min), np.ceil(x_max) + 1, 1.0))
    ax.set_yticks(np.arange(np.floor(y_min), np.ceil(y_max) + 1, 1.0))
    ax.tick_params(axis='both', labelsize=7)
    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f'Image saved to: {args.output}')
    print(f'X range: [{x_min:.2f}, {x_max:.2f}]  Y range: [{y_min:.2f}, {y_max:.2f}]')


if __name__ == '__main__':
    main()
