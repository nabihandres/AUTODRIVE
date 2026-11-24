"""Serve the saved map only (map_server + lifecycle manager).

Use it to check that the map loads before running the planner.

    ros2 launch f1tenth_global_planner map_launch.py
    ros2 launch f1tenth_global_planner map_launch.py map_yaml:=/path/to/map.yaml
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Map saved with SLAM Toolbox in Tutorial 3
    default_map = os.path.expanduser('~/autodrive_ws/maps/F1tenth_Map.yaml')

    map_arg = DeclareLaunchArgument(
        'map_yaml',
        default_value=default_map,
        description='Absolute path to the map .yaml file')

    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'yaml_filename': LaunchConfiguration('map_yaml')}]
    )

    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[{
            'autostart': True,
            'node_names': ['map_server']
        }]
    )

    return LaunchDescription([
        map_arg,
        map_server_node,
        lifecycle_manager_node,
    ])
