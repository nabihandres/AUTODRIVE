"""Pick the start and goal by clicking on the INFLATED map.

The map is loaded and inflated exactly as the planner node does (same
map_server thresholds, same distance transform), so a point reported as
FREE here is also valid for global_planner_node.

Usage:
    python3 pick_start_goal.py <map.yaml> --radius 0.20

On screen:
    1. Click ONCE for the START (green)
    2. Click ONCE for the GOAL (red)
    3. The coordinates are printed in the terminal
"""
import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import yaml
from PIL import Image
from scipy.ndimage import distance_transform_edt


def load_map_as_occupancy(yaml_path):
    """Replicate nav2_map_server (trinary mode) -> grid with 0 / 100 / -1."""
    with open(yaml_path, 'r') as f:
        meta = yaml.safe_load(f)
    image_path = os.path.join(
        os.path.dirname(os.path.abspath(yaml_path)), meta['image'])
    pixels = np.array(Image.open(image_path).convert('L')).astype(float)

    occ = pixels / 255.0 if meta.get('negate', 0) else (255.0 - pixels) / 255.0
    grid = np.full(pixels.shape, -1, dtype=np.int8)
    grid[occ > meta['occupied_thresh']] = 100
    grid[occ < meta['free_thresh']] = 0

    # map_server flips the image so that row 0 is the minimum Y (origin)
    return np.flipud(grid), meta['resolution'], meta['origin']


def inflate(grid, resolution, robot_radius):
    occupied = (grid == 100) | (grid == -1)
    dist = distance_transform_edt(~occupied)
    inflated = grid.copy()
    inflated[dist <= robot_radius / resolution] = 100
    return inflated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_path')
    parser.add_argument('--radius', type=float, default=0.20)
    args = parser.parse_args()

    grid, resolution, origin = load_map_as_occupancy(args.yaml_path)
    inflated = inflate(grid, resolution, args.radius)

    height, width = grid.shape
    x_min, y_min = origin[0], origin[1]
    x_max = x_min + width * resolution
    y_max = y_min + height * resolution

    fig, ax = plt.subplots(figsize=(6, 16))
    ax.imshow(inflated, cmap='gray_r', origin='lower',
              extent=[x_min, x_max, y_min, y_max], vmin=-1, vmax=100)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title(f'Click 1 = START (green) | Click 2 = GOAL (red) | '
                 f'radius={args.radius} m')
    ax.grid(True, alpha=0.3)
    ax.set_xticks(np.arange(np.floor(x_min), np.ceil(x_max) + 1, 0.5))
    ax.set_yticks(np.arange(np.floor(y_min), np.ceil(y_max) + 1, 0.5))
    ax.tick_params(axis='both', labelsize=6)
    plt.tight_layout()

    print('Click on the figure: first START, then GOAL...')
    pts = plt.ginput(2, timeout=0)

    def is_free(x, y):
        gx = int((x - x_min) / resolution)
        gy = int((y - y_min) / resolution)
        if not (0 <= gx < width and 0 <= gy < height):
            return False, None
        return inflated[gy, gx] < 50, inflated[gy, gx]

    print('\n--- Result ---')
    for (x, y), label, color in zip(pts, ['START', 'GOAL'], ['green', 'red']):
        free, val = is_free(x, y)
        status = 'FREE' if free else f'OCCUPIED/INFLATED (value={val})'
        print(f'{label}: x={x:.3f}, y={y:.3f}  ->  {status}')
        ax.plot(x, y, 'o', color=color, markersize=10)

    plt.savefig('pick_result.png', dpi=150)
    print('\nImage saved as pick_result.png with the selected points.')
    plt.show()


if __name__ == '__main__':
    main()
