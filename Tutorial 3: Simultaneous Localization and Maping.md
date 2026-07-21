# Generating a 2D Map of the F1TENTH in AutoDRIVE Using SLAM Toolbox

## Introduction

SLAM (*Simultaneous Localization and Mapping*) is a technique that allows a robot to build a map of an unknown environment while simultaneously estimating its position within that map. It combines sensor measurements, such as LiDAR scans, with the vehicle's position and orientation information.

In this tutorial, `slam_toolbox` will be configured in ROS 2 to generate a 2D occupancy map of the AutoDRIVE F1TENTH circuit. The required TF frames and topics will be verified, the SLAM parameters will be adapted to the simulator, the system will be launched in the correct order, and the final map will be visualized and saved from RViz2.

## Prerequisites

Before starting, make sure the following are available:

- Ubuntu 22.04.
- ROS 2 Humble.
- AutoDRIVE workspace located at `~/autodrive_ws`. (Tutorial 1)
- Compiled `autodrive_f1tenth` package. (Tutorial 1)
- AutoDRIVE Simulator for Linux. (Tutorial 1)
- Working bridge between Unity and ROS 2. (Tutorial 1)
- F1TENTH teleoperation node. (Tutorial 1)

The following commands will be used repeatedly to prepare a project terminal:

```bash
cd ~/autodrive_ws
source /opt/ros/humble/setup.bash
source venv/bin/activate
source install/setup.bash
```

## Table of Contents

1. [Installing and Understanding SLAM Toolbox Modes](#1-installing-and-understanding-slam-toolbox-modes)
2. [Copying and Configuring the SLAM Toolbox Parameters](#2-copying-and-configuring-the-slam-toolbox-parameters)
3. [Launching the System in the Correct Order](#3-launching-the-system-in-the-correct-order)
4. [Saving and Serializing the Map](#5-saving-and-serializing-the-map)

# 1. Installing and Understanding SLAM Toolbox Modes

## 1.1. Installing SLAM Toolbox on ROS 2 Humble

Update the package index and install `slam_toolbox`:

```bash
sudo apt update
sudo apt install ros-humble-slam-toolbox
```

Source ROS 2 and verify the installation:

```bash
source /opt/ros/humble/setup.bash
ros2 pkg prefix slam_toolbox
```

The expected output is similar to:

<img width="946" height="65" alt="Screenshot from 2026-07-20 20-07-09" src="https://github.com/user-attachments/assets/e6668779-5a3d-4f53-955c-6c0c4b93ab63" />

The available launch files can also be checked with:

```bash
ls $(ros2 pkg prefix slam_toolbox)/share/slam_toolbox/launch
```

## 1.2. Online and Offline Mapping

### Online mapping

In **online** mode, `slam_toolbox` processes data while the robot or simulator is running. The node continuously receives:

- LiDAR scans.
- TF transformations.
- Motion or odometry information.

The map is updated in real time as the vehicle moves. This is the mode used in this tutorial.

### Offline mapping

In **offline** mode, the sensors do not need to be connected in real time. Their data can be recorded beforehand, for example in a ROS bag, and processed later to build or refine the map.

This approach is useful for:

- Reprocessing data without driving the robot again.
- Testing different SLAM configurations on the same dataset.
- Playing recorded data at a different speed.
- Adjusting or continuing a previously serialized pose graph.

## 1.3. Synchronous and Asynchronous Modes

### Synchronous mode (`sync`)

Synchronous mode attempts to process all accepted scans in order. If the sensor rate or vehicle speed exceeds the available processing capacity, a queue of pending measurements may grow and the map may temporarily lag behind the actual robot motion.

It is normally launched with:

```bash
ros2 launch slam_toolbox online_sync_launch.py
```

This mode is useful when preserving as many scans as possible is important and sufficient computing resources are available.

### Asynchronous mode (`async`)

Asynchronous mode prioritizes real-time operation and avoids maintaining an increasingly large queue of delayed scans. It is therefore suitable when the robot is operating online and the SLAM process needs to remain close to the current simulation time.

It is normally launched with:

```bash
ros2 launch slam_toolbox online_async_launch.py
```

This tutorial uses **online asynchronous mapping** because the map is generated while the F1TENTH is moving inside the Unity simulator.

> Even in asynchronous mode, the vehicle should be driven slowly during mapping. Excessive speed can reduce scan overlap and produce thick walls, duplicated boundaries, deformations, or a *ghosting* effect.

# 2. Copying and Configuring the SLAM Toolbox Parameters

## 2.1. Create a Configuration Folder in the Project

Create a `config` directory inside the workspace source folder:

```bash
mkdir -p ~/autodrive_ws/src/config
```

## 2.2. Copy the Standard Configuration File

Obtain the installed location of `slam_toolbox`:

```bash
source /opt/ros/humble/setup.bash
SLAM_SHARE=$(ros2 pkg prefix slam_toolbox)/share/slam_toolbox
```

Copy the standard online asynchronous mapping configuration:

```bash
cp "$SLAM_SHARE/config/mapper_params_online_async.yaml" \
   ~/autodrive_ws/src/config/mapper_params_online_async.yaml
```

Confirm that the file was copied:

```bash
ls ~/autodrive_ws/src/config
```

The following file should be listed:

```text
mapper_params_online_async.yaml
```
video corto

## 2.3. Verify the Actual LiDAR Topic

AutoDRIVE may show a `/scan` topic, but in this configuration that topic does not have an active publisher. The topic containing the actual LiDAR measurements is:

```text
/autodrive/f1tenth_1/lidar
```

Check the message type:

```bash
ros2 topic type /autodrive/f1tenth_1/lidar
```

The expected result is:

```text
sensor_msgs/msg/LaserScan
```

Inspect one message:

```bash
ros2 topic echo /autodrive/f1tenth_1/lidar --once
```

The message should include a frame identifier similar to:

```yaml
header:
  frame_id: lidar
```

The publisher information for both topics can also be checked:

```bash
ros2 topic info /scan -v
ros2 topic info /autodrive/f1tenth_1/lidar -v
```

A topic can appear in `ros2 topic list` when a subscriber exists, even if no node is publishing data to it.

## 2.4. Verify the TF Tree

With Unity and the AutoDRIVE bridge running, generate the TF tree:

CAPTURA DE TFS DE AUTODRIVE

The relevant frames are:

- `map`: fixed global reference published by AutoDRIVE.
- `f1tenth_1`: moving base frame of the vehicle.
- `lidar`: LiDAR sensor frame.

The standard `base_footprint` frame is not mandatory. `slam_toolbox` can use any valid robot base frame as long as it is correctly connected through TF to the odometry reference and the LiDAR. In this project, `f1tenth_1` is used as the base frame.

## 2.5. Edit the Main ROS Parameters

Open the copied configuration file:

```bash
nano ~/autodrive_ws/src/config/mapper_params_online_async.yaml
```

Locate the ROS parameter section and configure it as follows:

```yaml
slam_toolbox:
  ros__parameters:

    # ROS Parameters
    odom_frame: map
    map_frame: slam_map
    base_frame: f1tenth_1
    scan_topic: /autodrive/f1tenth_1/lidar
    use_map_saver: true
    mode: mapping # localization
```
### Main parameter descriptions

#### `odom_frame: map`

Defines the frame that `slam_toolbox` will use as its odometric reference.

In a conventional ROS mobile robot architecture, this frame is usually called `odom`. In AutoDRIVE, however, the simulator already publishes the following transformation:

```text
map → f1tenth_1
```

Therefore, the simulator's `map` frame serves as the odometric reference for this project.

#### `map_frame: slam_map`

Defines the corrected global frame generated by `slam_toolbox`.

The name `slam_map` is used to avoid assigning the same frame name to both the SLAM-generated map and the `map` frame already published by AutoDRIVE. After launching SLAM, the expected TF chain is:

```text
slam_map → map → f1tenth_1 → lidar
```

#### `base_frame: f1tenth_1`

Defines the base frame of the vehicle. In the AutoDRIVE TF tree, the sensors, wheels, and encoders are children of `f1tenth_1`, so this frame fulfills the role commonly assigned to `base_link` or `base_footprint`.

#### `scan_topic: /autodrive/f1tenth_1/lidar`

Defines the actual LiDAR input topic. An absolute topic name beginning with `/` is used.

#### `use_map_saver: true`

Enables the service used to save the occupancy map in a format compatible with `map_server`, normally producing:

```text
map_name.pgm
map_name.yaml
```

#### `mode: mapping`

Configures the node to build and continuously update a map.

The `localization` value is used when a previously serialized pose graph already exists and the objective is only to localize the robot within that map.

Save and close the file in `nano`:

```text
Ctrl + O
Enter
Ctrl + X
```
Video corto de parametros

# 3. Launching the System in the Correct Order

The startup sequence is important because `/clock`, TF, and the LiDAR messages must begin with consistent timestamps.

## 3.1. Terminal 1: Start AutoDRIVE Simulator

Go to the simulator directory:

```bash
cd ~/Downloads/AutoDRIVE_Sim
```

The first time it is launched, grant execution permissions:

```bash
chmod +x "AutoDRIVE Simulator.x86_64"
```

Start the simulator:

```bash
./"AutoDRIVE Simulator.x86_64"
```

Select the F1TENTH scenario and start the simulation.

## 3.2. Terminal 2: Start the AutoDRIVE Bridge

```bash
cd ~/autodrive_ws
source /opt/ros/humble/setup.bash
source venv/bin/activate
source install/setup.bash

ros2 launch autodrive_f1tenth simulator_bringup_rviz.launch.py
```

This launch file starts the communication nodes between Unity and ROS 2. Depending on the package configuration, it may also open an RViz window prepared to display the vehicle and its sensors.

## 3.3. Wait for Time and Sensor Initialization

Before starting `slam_toolbox`, wait approximately 3 to 5 seconds so that the bridge can begin publishing:

- `/clock`.
- `/tf` and `/tf_static`.
- `/autodrive/f1tenth_1/lidar`.

> Do not restart Unity while `slam_toolbox` remains active. Restarting the simulator can cause simulation time to move backward and generate `TF_OLD_DATA` warnings.

## 3.4. Terminal 3: Start Teleoperation

```bash
cd ~/autodrive_ws
source /opt/ros/humble/setup.bash
source venv/bin/activate
source install/setup.bash

ros2 run autodrive_f1tenth teleop_keyboard
```

Do not move the vehicle yet. First start and verify `slam_toolbox`.

## 3.5. Terminal 4: Start SLAM Toolbox

Prepare the terminal:

```bash
cd ~/autodrive_ws
source /opt/ros/humble/setup.bash
source venv/bin/activate
source install/setup.bash
```

Obtain the absolute path of the parameter file:

```bash
CFG=$(realpath ./src/config/mapper_params_online_async.yaml)
```

Launch `slam_toolbox`:

```bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$CFG \
  use_sim_time:=true
```

### Why `use_sim_time:=true` is important

The simulator publishes its own clock on `/clock`. By enabling:

```bash
use_sim_time:=true
```

`slam_toolbox` uses the same time reference as Unity and the AutoDRIVE bridge. This allows every LiDAR scan to be associated with the TF transformations corresponding to the exact measurement time.

If `slam_toolbox` used the computer's real-time clock while the sensors used simulation time, transformations could fail, messages could be considered too old, and scans could be discarded.

# 3.6 Open a New RViz2 Window and configure the view

In a new terminal:

```bash
cd ~/autodrive_ws
source /opt/ros/humble/setup.bash
source venv/bin/activate
source install/setup.bash

rviz2
```

VIDEO DE RVIZ2 CON EL SLAM

# 4. Saving and Serializing the Map

## 4.1. Create a Folder for the Maps

Before saving, create a dedicated directory:

```bash
mkdir -p ~/autodrive_ws/maps
```

## 4.2. Save the Occupancy Map

In the `SlamToolboxPlugin` panel, locate the **Save Map** field.

Enter an absolute path without a file extension, for example:

```text
/home/maykoll_vanegas/autodrive_ws/maps/F1tenth_Map
```

Then press:

```text
Save Map
```

The following files should be generated:

```text
F1tenth_Map.pgm
F1tenth_Map.yaml
```

The `.pgm` file contains the occupancy map image, while the `.yaml` file stores metadata such as:

- Resolution.
- Origin.
- Occupancy thresholds.
- Image path.

Verify the generated files:

```bash
ls -lh ~/autodrive_ws/maps
```
Video de guardado del mapa

## 4.3. Summary of the Launch Order

The recommended sequence is:

```text
1. AutoDRIVE Simulator
2. ROS 2 bridge
3. Wait 3 to 5 seconds
4. Teleoperation node
5. SLAM Toolbox with use_sim_time:=true
6. RViz2
7. Drive slowly around the circuit
8. Save and serialize the map
```

---

## Technical References

- [SLAM Toolbox documentation for ROS 2 Humble](https://docs.ros.org/en/humble/p/slam_toolbox/)
- [Official SLAM Toolbox repository](https://github.com/SteveMacenski/slam_toolbox)
- [Official `online_async_launch.py` file](https://github.com/SteveMacenski/slam_toolbox/blob/ros2/launch/online_async_launch.py)
- [Standard `mapper_params_online_async.yaml` configuration](https://github.com/SteveMacenski/slam_toolbox/blob/ros2/config/mapper_params_online_async.yaml)
- [AutoDRIVE Ecosystem](https://autodrive-ecosystem.github.io/)

