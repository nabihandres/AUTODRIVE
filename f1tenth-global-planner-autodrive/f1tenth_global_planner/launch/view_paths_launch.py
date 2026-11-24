"""Show the CSV paths produced by plan_and_smooth.py in RViz.

Starts map_server + lifecycle manager (your SLAM map), the path viewer and RViz.

    ros2 launch f1tenth_global_planner view_paths_launch.py
    ros2 launch f1tenth_global_planner view_paths_launch.py \
        map_yaml:=$HOME/autodrive_ws/maps/F1tenth_Map_walled.yaml \
        waypoints_dir:=$HOME/autodrive_ws/waypoints
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    default_map = os.path.expanduser('~/autodrive_ws/maps/F1tenth_Map.yaml')
    default_dir = os.path.expanduser('~/autodrive_ws/waypoints')

    return LaunchDescription([
        DeclareLaunchArgument('map_yaml', default_value=default_map),
        DeclareLaunchArgument('waypoints_dir', default_value=default_dir),
        Node(package='nav2_map_server', executable='map_server',
             name='map_server', output='screen',
             parameters=[{'yaml_filename': LaunchConfiguration('map_yaml')}]),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
             name='lifecycle_manager_map', output='screen',
             parameters=[{'autostart': True,
                          'node_names': ['map_server']}]),
        Node(package='f1tenth_global_planner', executable='path_viewer_node',
             name='path_viewer_node', output='screen',
             parameters=[{'waypoints_dir': LaunchConfiguration('waypoints_dir'),
                          'frame_id': 'map'}]),
        Node(package='rviz2', executable='rviz2', name='rviz2',
             output='screen'),
    ])
