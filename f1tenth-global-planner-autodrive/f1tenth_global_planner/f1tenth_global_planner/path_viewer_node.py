"""Publish the CSV files written by plan_and_smooth.py as nav_msgs/Path.

Works with ANY planner/smoother: it only reads (x, y[, yaw]) rows.

    /raw_path       <- raw_path.csv
    /smoothed_path  <- smoothed_path.csv

Both topics use Transient Local QoS, so RViz receives them even if it is
opened after this node. Add two Path displays in RViz with
Durability Policy = Transient Local.
"""
import csv
import math
import os

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy


def read_csv(path):
    rows = []
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            yaw = float(r['yaw']) if 'yaw' in r and r['yaw'] != '' else None
            rows.append((float(r['x']), float(r['y']), yaw))
    # If the file has no yaw column, derive it from the neighbouring points
    for i, (x, y, yaw) in enumerate(rows):
        if yaw is None:
            a = rows[i]
            b = rows[min(i + 1, len(rows) - 1)]
            if b == a and i > 0:
                a, b = rows[i - 1], rows[i]
            rows[i] = (x, y, math.atan2(b[1] - a[1], b[0] - a[0]))
    return rows


class PathViewerNode(Node):
    def __init__(self):
        super().__init__('path_viewer_node')
        self.declare_parameter('waypoints_dir',
                               os.path.expanduser('~/autodrive_ws/waypoints'))
        self.declare_parameter('frame_id', 'map')

        qos = QoSProfile(depth=1,
                         reliability=QoSReliabilityPolicy.RELIABLE,
                         durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        self.pubs = {
            'raw_path.csv': self.create_publisher(Path, '/raw_path', qos),
            'smoothed_path.csv': self.create_publisher(
                Path, '/smoothed_path', qos),
        }
        folder = self.get_parameter('waypoints_dir').value
        for name, pub in self.pubs.items():
            file_path = os.path.join(folder, name)
            if not os.path.isfile(file_path):
                self.get_logger().warn(f'{file_path} not found, skipped')
                continue
            msg = self.to_path(read_csv(file_path))
            pub.publish(msg)
            self.get_logger().info(
                f'Published {len(msg.poses)} poses from {file_path}')

    def to_path(self, rows):
        frame = self.get_parameter('frame_id').value
        msg = Path()
        msg.header.frame_id = frame
        msg.header.stamp = self.get_clock().now().to_msg()
        for x, y, yaw in rows:
            p = PoseStamped()
            p.header = msg.header
            p.pose.position.x = x
            p.pose.position.y = y
            p.pose.orientation.z = math.sin(yaw / 2.0)
            p.pose.orientation.w = math.cos(yaw / 2.0)
            msg.poses.append(p)
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = PathViewerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
