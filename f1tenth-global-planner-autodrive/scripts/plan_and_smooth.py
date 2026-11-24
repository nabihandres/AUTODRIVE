#!/usr/bin/env python3
"""Plan and smooth a global path on YOUR saved SLAM map using the teacher's
base repository (https://github.com/widegonz/Global_Planner).

The planner and the smoother are chosen BY NAME, so every student can use the
algorithm that was assigned to them:

    python3 plan_and_smooth.py ~/autodrive_ws/maps/F1tenth_Map_walled.yaml \
        --repo ~/Global_Planner \
        --start 0.792 3.535 --goal 0.600 4.701 \
        --planner a_star --smoother pchip --factor 4 --inflate

Planners (grid based, `SearchFactory` names):
    a_star dijkstra gbfs jps d_star lpa_star d_star_lite theta_star
    lazy_theta_star s_theta_star
    (voronoi, aco and pso are also accepted, but on the F1TENTH map they
    returned no path or crashed in our tests; 'anya' is listed in the base
    factory but is not implemented in the repo.)
Smoothers:
    none        raw planner path (resampled)
    pchip       Douglas-Peucker + shape-preserving PCHIP, validated on the map
    cubic_spline  base repo CubicSpline (natural cubic spline, arc length)
    bspline     base repo BSpline (cubic interpolation)
    fem_pos     base repo FemPosSmoother (OSQP optimisation)

Outputs (in --out-dir): raw_path.csv, smoothed_path.csv (x, y, yaw) and
path_overlay.png. A summary is printed with the length, the minimum
clearance to the nearest obstacle and the number of samples that are closer
to an obstacle than the robot radius.

Not covered: the sample-based planners (rrt, rrt_connect, rrt_star,
informed_rrt) need a continuous `Map` environment instead of a grid.
"""
import argparse
import csv
import io
import contextlib
import math
import os
import sys

import numpy as np
import yaml
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import distance_transform_edt

GRID_PLANNERS = ['a_star', 'dijkstra', 'gbfs', 'jps', 'd_star', 'lpa_star',
                 'd_star_lite', 'voronoi', 'theta_star', 'lazy_theta_star',
                 's_theta_star', 'aco', 'pso']
SMOOTHERS = ['none', 'pchip', 'cubic_spline', 'bspline', 'fem_pos']


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def arc_length(pts):
    d = np.hypot(*np.diff(pts, axis=0).T)
    return np.concatenate([[0.0], np.cumsum(d)])


def dedupe(pts, tol=1e-9):
    keep = [0]
    for i in range(1, len(pts)):
        if np.hypot(*(pts[i] - pts[keep[-1]])) > tol:
            keep.append(i)
    return pts[keep]


def douglas_peucker_indices(pts, eps):
    n = len(pts)
    if n < 3:
        return list(range(n))
    keep = {0, n - 1}

    def dist(p, a, b):
        ab = b - a
        den = float(np.dot(ab, ab))
        if den == 0.0:
            return float(np.linalg.norm(p - a))
        t = min(max(float(np.dot(p - a, ab)) / den, 0.0), 1.0)
        return float(np.linalg.norm(p - (a + t * ab)))

    def rec(i, j):
        if j <= i + 1:
            return
        ds = [dist(pts[k], pts[i], pts[j]) for k in range(i + 1, j)]
        m = int(np.argmax(ds))
        if ds[m] > eps:
            k = i + 1 + m
            keep.add(k)
            rec(i, k)
            rec(k, j)

    rec(0, n - 1)
    return sorted(keep)


def resample(pts, step):
    """Uniform spacing along the curve, keeping the last point."""
    s = arc_length(pts)
    n = max(int(round(s[-1] / step)), 1)
    t = np.linspace(0.0, s[-1], n + 1)
    return np.column_stack([np.interp(t, s, pts[:, 0]),
                            np.interp(t, s, pts[:, 1])])


def yaw_of(pts):
    d = np.gradient(pts, axis=0)
    return np.arctan2(d[:, 1], d[:, 0])


# --------------------------------------------------------------------------
# Map (full resolution) used ONLY to validate the result
# --------------------------------------------------------------------------
class FullMap:
    """Full-resolution obstacle map with a distance-to-obstacle field.
    Uses the same threshold as the base repo (pixel < 0.45*255 is occupied)."""

    def __init__(self, yaml_path):
        import cv2
        with open(yaml_path) as f:
            meta = yaml.safe_load(f)
        img_path = meta['image']
        if not os.path.isabs(img_path):
            img_path = os.path.join(os.path.dirname(os.path.abspath(yaml_path)),
                                    img_path)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        self.res = float(meta['resolution'])
        self.origin = meta['origin']
        self.h, self.w = img.shape
        self.occ = np.flipud(img < int(0.45 * 255))     # row 0 = lowest y
        self.dist = distance_transform_edt(~self.occ) * self.res   # meters

    def clearance(self, pts):
        col = np.floor((pts[:, 0] - self.origin[0]) / self.res).astype(int)
        row = np.floor((pts[:, 1] - self.origin[1]) / self.res).astype(int)
        out = np.zeros(len(pts))
        ok = (col >= 0) & (col < self.w) & (row >= 0) & (row < self.h)
        out[ok] = self.dist[row[ok], col[ok]]
        return out                                       # 0 outside the map


# --------------------------------------------------------------------------
# Smoothers
# --------------------------------------------------------------------------
def smooth_pchip(raw, fm, radius, eps, step):
    """Douglas-Peucker control points + PCHIP; if a sample ends up closer to
    an obstacle than `radius`, raw points are added around it (refinement)."""
    idx = douglas_peucker_indices(raw, eps)
    for _ in range(40):
        ctrl = dedupe(raw[idx])
        s = arc_length(ctrl)
        t = np.arange(0.0, s[-1], step / 4.0)
        t = np.append(t, s[-1])
        curve = np.column_stack([PchipInterpolator(s, ctrl[:, 0])(t),
                                 PchipInterpolator(s, ctrl[:, 1])(t)])
        bad = np.where(fm.clearance(curve) < radius)[0]
        if len(bad) == 0:
            break
        # raw index of the nearest control point on each side of the worst
        # sample, then insert the raw point in the middle of that gap
        worst = curve[bad[0]]
        k = int(np.argmin(np.hypot(*(raw - worst).T)))
        left = max([i for i in idx if i <= k], default=0)
        right = min([i for i in idx if i >= k], default=len(raw) - 1)
        if right - left < 2:
            break
        idx = sorted(set(idx) | {(left + right) // 2})
    return curve


def smooth_cubic(raw, eps, step, repo_curve):
    ctrl = dedupe(raw[douglas_peucker_indices(raw, eps)])
    s = arc_length(ctrl)
    gen = repo_curve.CubicSpline(step)
    t = np.arange(0.0, s[-1], step)
    px, _ = gen.spline(list(s), list(ctrl[:, 0]), t)
    py, _ = gen.spline(list(s), list(ctrl[:, 1]), t)
    out = np.column_stack([px, py])
    return np.vstack([out, ctrl[-1]])


def smooth_bspline(raw, eps, repo_curve):
    ctrl = dedupe(raw[douglas_peucker_indices(raw, eps)])
    gen = repo_curve.BSpline(step=0.005, k=3, param_mode='centripetal',
                             spline_mode='interpolation')
    pts = gen.run([tuple(p) for p in ctrl], display=False)
    return np.array(pts)


def smooth_fem(raw, step, w_smooth, w_length, w_ref, bound, repo_curve):
    dense = resample(raw, step)
    gen = repo_curve.FemPosSmoother(w_smooth, w_length, w_ref,
                                    bound, bound, bound, bound)
    pts = gen.run([tuple(p) for p in dense], display=False)
    return np.array(pts)


# --------------------------------------------------------------------------
def write_csv(path, pts, with_yaw=True):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        if with_yaw:
            w.writerow(['x', 'y', 'yaw'])
            for (x, y), yaw in zip(pts, yaw_of(pts)):
                w.writerow([f'{x:.4f}', f'{y:.4f}', f'{yaw:.4f}'])
        else:
            w.writerow(['x', 'y'])
            for x, y in pts:
                w.writerow([f'{x:.4f}', f'{y:.4f}'])


def report(name, pts, fm, radius):
    c = fm.clearance(pts)
    length = float(arc_length(pts)[-1])
    inv = int(np.sum(c < radius))
    print(f'{name:<9} points={len(pts):4d}  length={length:6.2f} m  '
          f'min clearance={c.min():5.3f} m  samples < {radius:.2f} m: '
          f'{inv}/{len(pts)}')
    return inv


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('map_yaml')
    ap.add_argument('--repo', required=True,
                    help='Path of the cloned widegonz/Global_Planner repo')
    ap.add_argument('--start', type=float, nargs=2, required=True,
                    metavar=('X', 'Y'))
    ap.add_argument('--goal', type=float, nargs=2, required=True,
                    metavar=('X', 'Y'))
    ap.add_argument('--planner', default='a_star', choices=GRID_PLANNERS)
    ap.add_argument('--smoother', default='pchip', choices=SMOOTHERS)
    ap.add_argument('--factor', type=int, default=4,
                    help='Downsampling factor of the base load_map (default 4)')
    ap.add_argument('--inflate', action='store_true',
                    help='Inflate obstacles by --robot-radius before planning '
                         '(the base repo does not do it)')
    ap.add_argument('--robot-radius', type=float, default=0.20)
    ap.add_argument('--simplify-epsilon', type=float, default=0.15)
    ap.add_argument('--step', type=float, default=0.10,
                    help='Spacing of the exported waypoints in m (default 0.10)')
    ap.add_argument('--fem-weights', type=float, nargs=3, default=[100, 1, 1],
                    metavar=('SMOOTH', 'LENGTH', 'REF'))
    ap.add_argument('--fem-bound', type=float, default=0.10)
    ap.add_argument('--out-dir', default='waypoints')
    ap.add_argument('--no-plot', action='store_true')
    a = ap.parse_args()

    repo = os.path.abspath(os.path.expanduser(a.repo))
    sys.path.insert(0, repo)
    sys.path.insert(0, os.path.join(repo, 'f1tenth'))
    import matplotlib
    matplotlib.use('Agg')
    from f1tenth_map import load_map, grid_from_map, world_to_map
    from python_motion_planning.utils import SearchFactory
    import python_motion_planning.curve_generation as repo_curve

    yaml_path = os.path.abspath(os.path.expanduser(a.map_yaml))
    out_dir = os.path.abspath(os.path.expanduser(a.out_dir))
    os.makedirs(out_dir, exist_ok=True)

    # 1) Map -> grid, exactly as the base repo does it
    map_bin, res, origin = load_map(yaml_path, a.factor)
    h, w = map_bin.shape
    if a.inflate:
        r_cells = a.robot_radius / res
        d = distance_transform_edt(map_bin == 0)
        map_bin = np.where(d <= r_cells, 1, 0).astype(np.uint8) | map_bin
        # keep start and goal usable if they fall inside the inflated band
    env_cells = {}
    for name, p in (('start', a.start), ('goal', a.goal)):
        i, j = world_to_map(p[0], p[1], res, origin)
        if not (0 <= i < w and 0 <= j < h):
            sys.exit(f'{name} is outside the map')
        if map_bin[h - 1 - j, i] == 1:
            if a.inflate:
                map_bin[h - 1 - j, i] = 0      # force the cell open
                print(f'WARNING: {name} was inside the inflated band; '
                      'its cell was opened')
            else:
                sys.exit(f'{name} {p} falls on an obstacle after downsampling '
                         f'(factor {a.factor}). Move it or lower --factor.')
        env_cells[name] = (i, j)
    env = grid_from_map(map_bin)
    print(f'Grid {w}x{h}, cell = {res:.3f} m, start cell {env_cells["start"]}, '
          f'goal cell {env_cells["goal"]}')

    # 2) Planner by name
    planner = SearchFactory()(a.planner, start=env_cells['start'],
                              goal=env_cells['goal'], env=env)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cost, cells, _ = planner.plan()
    if not cells:
        sys.exit(f'{a.planner} did not find a path. Check the virtual wall, '
                 'the --factor and the start/goal cells.')
    cells = [tuple(c[:2]) for c in cells]
    world = np.array([[origin[0] + (i + 0.5) * res, origin[1] + (j + 0.5) * res]
                      for i, j in cells])
    # Planners return goal->start or start->goal: orient it
    if np.hypot(*(world[0] - a.start)) > np.hypot(*(world[-1] - a.start)):
        world = world[::-1]
    world[0], world[-1] = a.start, a.goal          # exact end points
    raw = dedupe(world)
    print(f'{a.planner}: cost {cost:.1f} cells, {len(raw)} raw points')

    # 3) Smoother by name
    if a.smoother == 'none':
        smooth = raw
    elif a.smoother == 'pchip':
        smooth = None
    elif a.smoother == 'cubic_spline':
        smooth = smooth_cubic(raw, a.simplify_epsilon, a.step, repo_curve)
    elif a.smoother == 'bspline':
        smooth = smooth_bspline(raw, a.simplify_epsilon, repo_curve)
    else:
        smooth = smooth_fem(raw, a.step, *a.fem_weights, a.fem_bound,
                            repo_curve)

    fm = FullMap(yaml_path)
    if a.smoother == 'pchip':
        smooth = smooth_pchip(raw, fm, a.robot_radius, a.simplify_epsilon,
                              a.step)
    smooth = resample(dedupe(np.asarray(smooth, dtype=float)), a.step)
    raw_out = np.round(resample(raw, a.step), 4)   # same values as the CSV
    smooth = np.round(smooth, 4)

    # 4) Validate and export
    print('--- validation on the full-resolution map ---')
    report('raw', raw_out, fm, a.robot_radius)
    report('smoothed', smooth, fm, a.robot_radius)
    write_csv(os.path.join(out_dir, 'raw_path.csv'), raw_out)
    write_csv(os.path.join(out_dir, 'smoothed_path.csv'), smooth)
    print(f'CSV files written to {out_dir}')

    if not a.no_plot:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 8))
        ext = [origin[0], origin[0] + fm.w * fm.res,
               origin[1], origin[1] + fm.h * fm.res]
        ax.imshow(np.where(fm.occ, 0.0, 1.0), cmap='gray', origin='lower',
                  extent=ext, vmin=0, vmax=1)
        ax.plot(raw_out[:, 0], raw_out[:, 1], '-', c='tab:orange', lw=1.5,
                label=f'raw ({a.planner})')
        ax.plot(smooth[:, 0], smooth[:, 1], '-', c='tab:blue', lw=2,
                label=f'smoothed ({a.smoother})')
        ax.plot(*a.start, 'go', ms=9, label='start')
        ax.plot(*a.goal, 'r*', ms=13, label='goal')
        px = np.concatenate([raw_out[:, 0], smooth[:, 0]])
        py = np.concatenate([raw_out[:, 1], smooth[:, 1]])
        m = 0.8
        ax.set_xlim(px.min() - m, px.max() + m)
        ax.set_ylim(py.min() - m, py.max() + m)
        ax.set_aspect('equal')
        ax.set_xlabel('x [m]')
        ax.set_ylabel('y [m]')
        ax.legend(loc='best')
        ax.set_title(f'{a.planner} + {a.smoother}')
        fig.savefig(os.path.join(out_dir, 'path_overlay.png'), dpi=120,
                    bbox_inches='tight')
        print(f'Overlay saved to {os.path.join(out_dir, "path_overlay.png")}')


if __name__ == '__main__':
    main()
