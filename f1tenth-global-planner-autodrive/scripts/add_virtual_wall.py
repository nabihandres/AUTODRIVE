"""Draw a virtual wall on a COPY of a saved map.

On a closed circuit, the start and the goal are close to each other, so the
shortest route between them is a short hop. A wall drawn between them forces
the planner to go all the way around the circuit.

The original map is never modified: a new .pgm/.yaml pair is written next to it.

Usage:
    python3 add_virtual_wall.py <map.yaml> --p1 X1 Y1 --p2 X2 Y2 \
        [--thickness 0.10] [-o <output.yaml>]

Example (wall across the track at y = 4.05 m):
    python3 add_virtual_wall.py ~/autodrive_ws/maps/F1tenth_Map.yaml \
        --p1 -0.2 4.05 --p2 1.6 4.05

Tip: use visualize_map.py first to read the coordinates of the two ends.
The wall must go from one border of the track to the other, so that it
completely closes the corridor.
"""
import argparse
import math
import os

import yaml
from PIL import Image, ImageDraw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('map_yaml')
    parser.add_argument('--p1', type=float, nargs=2, required=True,
                        metavar=('X', 'Y'), help='First end of the wall (m)')
    parser.add_argument('--p2', type=float, nargs=2, required=True,
                        metavar=('X', 'Y'), help='Second end of the wall (m)')
    parser.add_argument('--thickness', type=float, default=0.10,
                        help='Wall thickness in meters (default: 0.10)')
    parser.add_argument('-o', '--output', default=None,
                        help='Output .yaml (default: <name>_walled.yaml)')
    args = parser.parse_args()

    yaml_path = os.path.abspath(args.map_yaml)
    map_dir = os.path.dirname(yaml_path)
    with open(yaml_path, 'r') as f:
        meta = yaml.safe_load(f)

    pgm = Image.open(os.path.join(map_dir, meta['image'])).convert('L')
    width, height = pgm.size
    res = meta['resolution']
    origin_x, origin_y = meta['origin'][0], meta['origin'][1]

    def world_to_pixel(x, y):
        # Row 0 of a PGM is the TOP of the picture (maximum Y)
        col = (x - origin_x) / res
        row = (height - 1) - (y - origin_y) / res
        return col, row

    p1 = world_to_pixel(*args.p1)
    p2 = world_to_pixel(*args.p2)
    for name, (c, r) in (('p1', p1), ('p2', p2)):
        if not (0 <= c < width and 0 <= r < height):
            print(f'WARNING: {name} is outside the map '
                  f'(X range [{origin_x:.2f}, {origin_x + width * res:.2f}], '
                  f'Y range [{origin_y:.2f}, {origin_y + height * res:.2f}]).')

    line_width = max(1, int(math.ceil(args.thickness / res)))
    draw = ImageDraw.Draw(pgm)
    draw.line([p1, p2], fill=0, width=line_width)  # 0 = black = occupied

    if args.output:
        out_yaml = os.path.abspath(args.output)
    else:
        stem = os.path.splitext(os.path.basename(yaml_path))[0]
        out_yaml = os.path.join(map_dir, f'{stem}_walled.yaml')
    out_pgm = os.path.splitext(out_yaml)[0] + '.pgm'
    if out_yaml == yaml_path or out_pgm == os.path.join(map_dir, meta['image']):
        raise SystemExit('Refusing to overwrite the original map.')

    pgm.save(out_pgm)

    meta['image'] = os.path.basename(out_pgm)
    with open(out_yaml, 'w') as f:
        f.write(f"image: {meta['image']}\n")
        f.write(f"mode: {meta.get('mode', 'trinary')}\n")
        f.write(f"resolution: {meta['resolution']}\n")
        f.write(f"origin: {list(meta['origin'])}\n")
        f.write(f"negate: {meta.get('negate', 0)}\n")
        f.write(f"occupied_thresh: {meta['occupied_thresh']}\n")
        f.write(f"free_thresh: {meta['free_thresh']}\n")

    print(f'Wall drawn from {tuple(args.p1)} to {tuple(args.p2)} '
          f'({line_width} px thick).')
    print(f'Saved: {out_yaml}')
    print(f'Saved: {out_pgm}')


if __name__ == '__main__':
    main()
