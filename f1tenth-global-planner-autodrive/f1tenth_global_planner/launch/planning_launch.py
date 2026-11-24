"""Full global planning pipeline: map + Dijkstra + smoothing + RViz.

Examples:

    ros2 launch f1tenth_global_planner planning_launch.py
    ros2 launch f1tenth_global_planner planning_launch.py centering_weight:=0.0
    ros2 launch f1tenth_global_planner planning_launch.py \
        start_x:=0.792 start_y:=3.535 goal_x:=0.6 goal_y:=4.701
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Copy of the Tutorial 3 map with the virtual wall (see add_virtual_wall.py)
    default_map = os.path.expanduser(
        '~/autodrive_ws/maps/F1tenth_Map_walled.yaml')
    default_waypoints_dir = os.path.expanduser('~/autodrive_ws/waypoints')

    # ---- Launch arguments ----
    args = [
        DeclareLaunchArgument('map_yaml', default_value=default_map,
                              description='Absolute path to the map .yaml'),
        DeclareLaunchArgument('waypoints_dir',
                              default_value=default_waypoints_dir,
                              description='Folder where the CSV files are saved'),
        DeclareLaunchArgument('start_x', default_value='0.792'),
        DeclareLaunchArgument('start_y', default_value='3.535'),
        DeclareLaunchArgument('goal_x', default_value='0.600'),
        DeclareLaunchArgument('goal_y', default_value='4.701'),
        DeclareLaunchArgument('robot_radius', default_value='0.20'),
        DeclareLaunchArgument('centering_weight', default_value='5.0'),
        DeclareLaunchArgument('simplify_epsilon', default_value='0.15'),
        DeclareLaunchArgument('safety_radius', default_value='0.08'),
        DeclareLaunchArgument('points_per_meter', default_value='10.0'),
    ]

    def as_float(name):
        # Force the type: "5" would otherwise be parsed as an integer
        return ParameterValue(LaunchConfiguration(name), value_type=float)

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

    global_planner_node = Node(
        package='f1tenth_global_planner',
        executable='global_planner_node',
        name='global_planner_node',
        output='screen',
        parameters=[{
            'start_x': as_float('start_x'),
            'start_y': as_float('start_y'),
            'goal_x': as_float('goal_x'),
            'goal_y': as_float('goal_y'),
            'robot_radius': as_float('robot_radius'),
            'centering_weight': as_float('centering_weight'),
            'use_rviz_goals': True,
            'waypoints_csv_path': PathJoinSubstitution(
                [LaunchConfiguration('waypoints_dir'), 'raw_path.csv']),
        }]
    )

    path_smoother_node = Node(
        package='f1tenth_global_planner',
        executable='path_smoother_node',
        name='path_smoother_node',
        output='screen',
        parameters=[{
            'points_per_meter': as_float('points_per_meter'),
            'simplify_epsilon': as_float('simplify_epsilon'),
            'safety_radius': as_float('safety_radius'),
            'waypoints_csv_path': PathJoinSubstitution(
                [LaunchConfiguration('waypoints_dir'), 'smoothed_path.csv']),
        }]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
    )

    return LaunchDescription(args + [
        map_server_node,
        lifecycle_manager_node,
        global_planner_node,
        path_smoother_node,
        rviz_node,
    ])
