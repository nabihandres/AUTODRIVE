"""Global path planner (Dijkstra) for the F1TENTH vehicle in AutoDRIVE.

The node receives the occupancy map, inflates the obstacles by the robot
radius, runs Dijkstra on the inflated grid (with a lane-centering penalty)
and publishes the resulting waypoints on /raw_path.
"""
import csv
import heapq
import math
import os

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid, Path
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from scipy.ndimage import distance_transform_edt


class GlobalPlannerNode(Node):
    def __init__(self):
        super().__init__('global_planner_node')

        # ---- Parameters ----
        self.declare_parameter('start_x', 0.0)
        self.declare_parameter('start_y', 0.0)
        self.declare_parameter('goal_x', 0.0)
        self.declare_parameter('goal_y', 5.0)
        self.declare_parameter('robot_radius', 0.30)  # meters
        self.declare_parameter('use_rviz_goals', True)

        # Weight of the penalty that keeps the path away from the walls
        self.declare_parameter('centering_weight', 5.0)

        self.declare_parameter(
            'waypoints_csv_path',
            os.path.expanduser('~/autodrive_ws/waypoints/raw_path.csv'))

        self.robot_radius = self.get_parameter('robot_radius').value
        self.use_rviz_goals = self.get_parameter('use_rviz_goals').value
        self.centering_weight = self.get_parameter('centering_weight').value

        self.map_data = None
        self.map_info = None
        self.inflated_grid = None
        self.dist_map_cells = None  # Distance (in cells) to the nearest obstacle

        self.start_world = (
            self.get_parameter('start_x').value,
            self.get_parameter('start_y').value,
        )
        self.goal_world = (
            self.get_parameter('goal_x').value,
            self.get_parameter('goal_y').value,
        )
        self.start_set_by_rviz = False
        self.goal_set_by_rviz = False

        # QoS: map_server publishes the map as "latched" (transient local)
        map_qos = QoSProfile(depth=1)
        map_qos.reliability = QoSReliabilityPolicy.RELIABLE
        map_qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL

        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, map_qos)

        if self.use_rviz_goals:
            self.initialpose_sub = self.create_subscription(
                PoseWithCovarianceStamped, '/initialpose',
                self.initialpose_callback, 10)
            self.goal_sub = self.create_subscription(
                PoseStamped, '/goal_pose', self.goal_callback, 10)

        path_qos = QoSProfile(depth=1)
        path_qos.reliability = QoSReliabilityPolicy.RELIABLE
        path_qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        self.path_pub = self.create_publisher(Path, '/raw_path', path_qos)

        self.get_logger().info(
            f'GlobalPlannerNode ready. start(default)={self.start_world}, '
            f'goal(default)={self.goal_world}, robot_radius={self.robot_radius}, '
            f'centering_weight={self.centering_weight}')

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def map_callback(self, msg: OccupancyGrid):
        self.map_info = msg.info
        grid = np.array(msg.data, dtype=np.int8).reshape(
            (msg.info.height, msg.info.width))
        self.map_data = grid
        self.inflated_grid = self.inflate_obstacles(grid, msg.info.resolution)
        self.get_logger().info(
            f'Map received: {msg.info.width}x{msg.info.height} '
            f'@ {msg.info.resolution} m/cell. Obstacles inflated '
            f'with radius {self.robot_radius} m.')
        self.save_debug_image()
        self.try_plan()

    def save_debug_image(self):
        """Save the REAL grid used by Dijkstra (already inflated) with the
        start and goal marked, to choose coordinates without ambiguity."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(6, 16))
            ax.imshow(self.inflated_grid, cmap='gray_r', origin='lower',
                      extent=[self.map_info.origin.position.x,
                              self.map_info.origin.position.x +
                              self.map_info.width * self.map_info.resolution,
                              self.map_info.origin.position.y,
                              self.map_info.origin.position.y +
                              self.map_info.height * self.map_info.resolution])
            ax.plot(*self.start_world, 'go', markersize=10, label='start')
            ax.plot(*self.goal_world, 'ro', markersize=10, label='goal')
            ax.legend()
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.grid(True, alpha=0.3)
            out_path = '/tmp/f1tenth_planner_debug.png'
            plt.tight_layout()
            plt.savefig(out_path, dpi=150)
            plt.close(fig)
            self.get_logger().info(
                f'Debug image (inflated grid + start/goal) saved to: '
                f'{out_path}')
        except Exception as e:
            self.get_logger().warn(f'Could not save the debug image: {e}')

    def initialpose_callback(self, msg: PoseWithCovarianceStamped):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        self.start_world = (x, y)
        self.start_set_by_rviz = True
        self.get_logger().info(f'New start from RViz: ({x:.2f}, {y:.2f})')
        self.try_plan()

    def goal_callback(self, msg: PoseStamped):
        x = msg.pose.position.x
        y = msg.pose.position.y
        self.goal_world = (x, y)
        self.goal_set_by_rviz = True
        self.get_logger().info(f'New goal from RViz: ({x:.2f}, {y:.2f})')
        self.try_plan()

    # ------------------------------------------------------------------
    # Map preprocessing
    # ------------------------------------------------------------------
    def inflate_obstacles(self, grid: np.ndarray, resolution: float) -> np.ndarray:
        """Inflate the obstacles by the robot radius using a distance transform."""
        occupied = (grid == 100) | (grid == -1)  # occupied or unknown = obstacle
        free_mask = ~occupied

        # Keep the continuous distance map: it is reused by the centering cost
        self.dist_map_cells = distance_transform_edt(free_mask)

        radius_cells = self.robot_radius / resolution
        inflated = grid.copy()
        inflated[self.dist_map_cells <= radius_cells] = 100
        return inflated

    # ------------------------------------------------------------------
    # World <-> grid conversion
    # ------------------------------------------------------------------
    def world_to_grid(self, x, y):
        info = self.map_info
        gx = int((x - info.origin.position.x) / info.resolution)
        gy = int((y - info.origin.position.y) / info.resolution)
        return gx, gy

    def grid_to_world(self, gx, gy):
        info = self.map_info
        x = gx * info.resolution + info.origin.position.x + info.resolution / 2.0
        y = gy * info.resolution + info.origin.position.y + info.resolution / 2.0
        return x, y

    # ------------------------------------------------------------------
    # Dijkstra
    # ------------------------------------------------------------------
    def dijkstra(self, grid: np.ndarray, start, goal):
        height, width = grid.shape
        sx, sy = start
        gx, gy = goal

        def in_bounds(x, y):
            return 0 <= x < width and 0 <= y < height

        def is_free(x, y):
            return grid[y, x] < 50  # <50 = free (0 = free, 100 = occupied)

        if not in_bounds(sx, sy) or not in_bounds(gx, gy):
            self.get_logger().error('Start or goal is outside the map.')
            return None
        if not is_free(sx, sy):
            self.get_logger().error('Start is inside an occupied/inflated zone.')
            return None
        if not is_free(gx, gy):
            self.get_logger().error('Goal is inside an occupied/inflated zone.')
            return None

        # 8-connectivity: (dx, dy, base cost of the move)
        neighbors = [
            (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
            (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)),
            (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2)),
        ]

        dist = {(sx, sy): 0.0}
        prev = {}
        visited = set()
        pq = [(0.0, (sx, sy))]

        while pq:
            d, (cx, cy) = heapq.heappop(pq)
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))

            if (cx, cy) == (gx, gy):
                break

            for dx, dy, move_cost in neighbors:
                nx, ny = cx + dx, cy + dy

                if not in_bounds(nx, ny) or not is_free(nx, ny):
                    continue

                # Modified cost: penalty for being close to obstacles
                dist_to_wall_cells = self.dist_map_cells[ny, nx]
                penalty = self.centering_weight / (dist_to_wall_cells + 0.1)

                nd = d + move_cost + penalty

                if nd < dist.get((nx, ny), float('inf')):
                    dist[(nx, ny)] = nd
                    prev[(nx, ny)] = (cx, cy)
                    heapq.heappush(pq, (nd, (nx, ny)))

        if (gx, gy) not in prev and (sx, sy) != (gx, gy):
            self.get_logger().error('Dijkstra did not find a path.')
            return None

        # Rebuild the path from goal to start
        path = [(gx, gy)]
        node = (gx, gy)
        while node != (sx, sy):
            node = prev[node]
            path.append(node)
        path.reverse()
        return path

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    def try_plan(self):
        if self.inflated_grid is None:
            return

        start_cell = self.world_to_grid(*self.start_world)
        goal_cell = self.world_to_grid(*self.goal_world)

        self.get_logger().info(
            f'Planning with Dijkstra: start_cell={start_cell}, '
            f'goal_cell={goal_cell}')

        cell_path = self.dijkstra(self.inflated_grid, start_cell, goal_cell)
        if cell_path is None:
            return

        self.publish_path(cell_path)

    def publish_path(self, cell_path):
        path_msg = Path()
        path_msg.header.frame_id = 'map'
        path_msg.header.stamp = self.get_clock().now().to_msg()

        for gx, gy in cell_path:
            wx, wy = self.grid_to_world(gx, gy)
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.pose.position.x = wx
            pose.pose.position.y = wy
            pose.pose.orientation.w = 1.0
            path_msg.poses.append(pose)

        self.path_pub.publish(path_msg)
        self.get_logger().info(
            f'Path published on /raw_path with {len(path_msg.poses)} points.')
        self.export_waypoints_csv(path_msg)

    def export_waypoints_csv(self, path_msg: Path):
        csv_path = self.get_parameter('waypoints_csv_path').value
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'x', 'y'])
            for i, pose in enumerate(path_msg.poses):
                writer.writerow(
                    [i, pose.pose.position.x, pose.pose.position.y])
        self.get_logger().info(f'Raw waypoints exported to: {csv_path}')


def main(args=None):
    rclpy.init(args=args)
    node = GlobalPlannerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
