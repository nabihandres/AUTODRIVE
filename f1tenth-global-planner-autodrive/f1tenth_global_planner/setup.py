import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'f1tenth_global_planner'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Shirley Andrea',
    maintainer_email='shirley_andrea2004@outlook.es',
    description='Global path planning (Dijkstra + PCHIP) for F1TENTH in AutoDRIVE',
    license='MIT',
    entry_points={
        'console_scripts': [
            'global_planner_node = f1tenth_global_planner.global_planner_node:main',
            'path_smoother_node = f1tenth_global_planner.path_smoother_node:main',
            'path_viewer_node = f1tenth_global_planner.path_viewer_node:main',
        ],
    },
)
