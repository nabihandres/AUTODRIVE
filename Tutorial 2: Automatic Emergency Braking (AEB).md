# AEB F110 

Safety and autonomous driving stack for the F1TENTH platform on the AutoDRIVE simulator. The system provides Automatic Emergency Braking (AEB) via iTTC and supports both autonomous straight-line driving and manual teleoperation, with a keyboard-driven multiplexer to switch between sources at runtime.

---

## Prerequisites

Before running this package, make sure you have the following requirements installed and configured:

- **[Ubuntu 22.04](./Common%20Problems/Ubuntu%20with%20RTX%2050%20series.md)**
- **[ROS 2 Humble](https://docs.ros.org/en/humble/)** sourced (`/opt/ros/humble/setup.bash`)
- **AutoDRIVE DevKit** workspace (`~/autodrive_ws`) set up and built — see [AutoDRIVE_DevKit_Starter](https://github.com/hector-la/AutoDRIVE_DevKit_Starter/tree/main)
- Python virtual environment at `~/autodrive_ws/venv/`

It is also recommended to complete <a href="./Tutorial 1: AutoDrive Installation and Setup.md">Tutorial 1</a> before using this package, since it explains the basic setup and workspace configuration required to run the AutoDRIVE F1TENTH environment properly.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1: Installation](#step-1-installation)
- [Step 2: Usage](#step-2-usage)
- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Parameters](#parameters)
- [ROS 2 Interface](#ros-2-interface)
- [Contact](#contact)


---

## Step 1: Installation

Clone this package into the AutoDRIVE workspace source directory. The repository will be saved locally as `aeb_f110`:

```bash
cd ~/autodrive_ws/src
git clone https://github.com/Raulvillaes/AIROS-AutoDRIVE-F110-AEB aeb_f110

cd ~/autodrive_ws
source /opt/ros/humble/setup.bash
source venv/bin/activate
colcon build --packages-select aeb_f110
```

---

## Step 2: Usage

First, **open the AutoDRIVE Simulator** application. Then open the following terminals from `~/autodrive_ws`.

> **Important:** Run the terminals in the order shown below. The simulator must be running before launching the AEB system.

### Terminal 1: Simulator bridge

```bash
source /opt/ros/humble/setup.bash
source venv/bin/activate
export PYTHONPATH=~/autodrive_ws/venv/lib/python3.10/site-packages:$PYTHONPATH
source install/setup.bash
ros2 launch autodrive_f1tenth simulator_bringup_rviz.launch.py
```

> **Headless mode:** For a headless run, replace the last line with:
>
> ```bash
> ros2 launch autodrive_f1tenth simulator_bringup_headless.launch.py
> ```

### Terminal 2: AEB + multiplexer + linear driver

```bash
source /opt/ros/humble/setup.bash
source venv/bin/activate && source install/setup.bash
ros2 launch aeb_f110 auto.launch.py
```

The vehicle starts driving autonomously in a straight line. AEB is active from this point.

### Terminals 3 & 4: Mode switcher + teleop keyboard (optional)

Only needed if you want to switch between autonomous and manual mode at runtime. Run each command in a separate terminal.

The teleop commands are remapped to the aeb_f110 input topics, so manual driving still passes through the multiplexer and the AEB safety node.

To switch to manual mode, press [T] in the mode switcher terminal. To return to autonomous mode, press [A].

#### Terminal 3: Mode switcher

```bash
source /opt/ros/humble/setup.bash
source venv/bin/activate && source install/setup.bash
ros2 run aeb_f110 mode_switcher_node
```

```text
---------------------------------------
AEB F110 - Mode Switcher
---------------------------------------

A : Switch to AUTO  (linear driver)
T : Switch to TELEOP

Press CTRL+C to quit

NOTE: Press keys within this terminal
---------------------------------------
```

#### Terminal 4: Teleop keyboard

```bash
source /opt/ros/humble/setup.bash
source venv/bin/activate && source install/setup.bash
ros2 run autodrive_f1tenth teleop_keyboard --ros-args \
  -r /autodrive/f1tenth_1/throttle_command:=/aeb_f110/sources/teleop/throttle \
  -r /autodrive/f1tenth_1/steering_command:=/aeb_f110/sources/teleop/steering
```

VIDEO DE USO DE LOS NODOS MUX Y DE AEB

---

## How it works

### Architecture

```text
[linear_driver_node] → /aeb_f110/sources/auto/*   ───┐
                                                     │   [mux_node]  ←  [mode_switcher_node]
[teleop_keyboard]    → /aeb_f110/sources/teleop/* ───┘       │
                                                             ↓
                                              /aeb_f110/throttle_request
                                              /aeb_f110/steering_request
                                                             │
                                                       [aeb_node]
                                                             │
                                              /autodrive/f1tenth_1/throttle_command
                                              /autodrive/f1tenth_1/steering_command
                                                             │
                                                        [simulator]
```

The system is organized as a safety layer between the driving command sources and the AutoDRIVE simulator.

The **mux node** receives commands from different sources, such as the autonomous linear_driver_node and the manual teleop_keyboard. It selects which source is currently active and forwards only that source to the AEB input topics.

The **mode switcher node** allows changing the active source at runtime between autonomous mode and teleoperation mode.

The **AEB node** acts as the final safety gate before commands are sent to the simulator. All throttle and steering commands must pass through this node, so no driving source can bypass the emergency braking logic.

If the active source stops publishing commands, the multiplexer watchdog automatically sets the throttle to zero.

### Speed estimation

The AEB node subscribes to both wheel encoders:

- `left_encoder`
- `right_encoder`

For each wheel, the angular position is differentiated over time to estimate angular velocity. Then, using the wheel radius, the node converts angular velocity into linear wheel speed.

The longitudinal vehicle speed is estimated as the average of the left and right wheel speeds.

### iTTC computation

The AEB logic is based on **instantaneous Time-To-Collision (iTTC)**. This metric estimates how much time remains before the vehicle collides with an obstacle, assuming the current speed is maintained.

On every LiDAR scan, the AEB node:

1. **Filters invalid readings** — discards `inf`, `NaN`, and ranges outside `[range_min_cutoff, range_max]`.
2. **Applies an angular window** — keeps only the beams within ±`angular_window_deg` of the forward direction.
3. **Computes the instantaneous Time-To-Collision (iTTC)** for each remaining beam:

   ```text
   range_rate_i = v · cos(θᵢ)
   TTC_i        = rᵢ / range_rate_i   (only where range_rate_i > 0)
   ```
where:

- v is the estimated longitudinal vehicle speed.
- θᵢ is the angle of the LiDAR beam.
- range_rate_i represents how fast the vehicle is approaching the obstacle along that beam.
- rᵢ is the LiDAR range measurement for beam i.
- The TTC is computed only when range_rate_i > 0, meaning the vehicle is moving toward the obstacle.

4. **Triggers braking** if `min(TTC) < ttc_threshold`.
   
- If the minimum TTC is below the configured threshold, the AEB node overrides the throttle command and activates braking.

### State machine

| State | Behaviour |
|---|---|
| `NORMAL` | Throttle commands pass through unchanged |
| `BRAKING` | Throttle is overridden to `brake_command` (`0.0`) regardless of source input |

The brake latch is released **only** when the active source sends a negative throttle command. This requires deliberate reverse input before the vehicle can resume normal operation.

---

## Project structure

```text
aeb_f110/
├── aeb_f110/
│   ├── __init__.py
│   ├── aeb_node.py             # AEB safety node (iTTC + brake latch)
│   ├── mux_node.py             # Command multiplexer (source arbitration + watchdog)
│   ├── linear_driver_node.py   # Autonomous straight-line driver
│   └── mode_switcher_node.py   # Keyboard interface to switch active source
├── launch/
│   ├── auto.launch.py          # Launches AEB + mux + linear driver
│   └── manual.launch.py        # Launches AEB + mux (teleop active by default)
├── resource/
│   └── aeb_f110
├── demo.gif
├── package.xml
├── setup.cfg
└── setup.py
```

---


## Parameters

### `aeb_node`

All parameters can be tuned in [`launch/auto.launch.py`](launch/auto.launch.py).

| Parameter | Default | Description |
|---|---:|---|
| `wheel_radius` | `0.058` m | F1TENTH simulated wheel radius |
| `ttc_threshold` | `0.66` s | Minimum TTC before braking is triggered |
| `range_min_cutoff` | `0.13` m | Minimum valid LiDAR range (filters close-range noise) |
| `angular_window_deg` | `12.5` ° | Half-width of the forward sector used for TTC evaluation |
| `brake_command` | `0.0` | Throttle value applied while the brake latch is active |
| `min_speed` | `0.8` m/s | Minimum speed below which AEB does not engage |
| `encoder_timeout` | `0.5` s | Max age of encoder data — iTTC is skipped if exceeded |
| `max_wheel_speed` | `8.0` m/s | Speed ceiling for encoder spike rejection (wrap-around guard) |

### `linear_driver_node`

| Parameter | Default | Description |
|---|---:|---|
| `throttle` | `0.3` | Forward throttle value `[0.0, 1.0]` |
| `steering` | `0.0` | Steering angle (`0.0` = straight) |
| `publish_rate` | `20.0` Hz | Command publish frequency |

### `mux_node`

| Parameter | Default | Description |
|---|---:|---|
| `active_source` | `'auto'` | Source active at startup (`'auto'` or `'teleop'`) |
| `source_timeout` | `0.5` s | Time without messages before watchdog zeros throttle |

---

## ROS 2 Interface

### `aeb_node`

| Direction | Topic | Type | Description |
|---|---|---|---|
| Sub | `/autodrive/f1tenth_1/lidar` | `sensor_msgs/LaserScan` | LiDAR scan |
| Sub | `/autodrive/f1tenth_1/left_encoder` | `sensor_msgs/JointState` | Left wheel encoder |
| Sub | `/autodrive/f1tenth_1/right_encoder` | `sensor_msgs/JointState` | Right wheel encoder |
| Sub | `/aeb_f110/throttle_request` | `std_msgs/Float32` | Throttle request from mux |
| Sub | `/aeb_f110/steering_request` | `std_msgs/Float32` | Steering request from mux |
| Pub | `/autodrive/f1tenth_1/throttle_command` | `std_msgs/Float32` | Throttle sent to simulator (may be overridden) |
| Pub | `/autodrive/f1tenth_1/steering_command` | `std_msgs/Float32` | Steering sent to simulator (always passed through) |

### `mux_node`

| Direction | Topic | Type | Description |
|---|---|---|---|
| Sub | `/aeb_f110/sources/auto/throttle` | `std_msgs/Float32` | Throttle from linear driver |
| Sub | `/aeb_f110/sources/auto/steering` | `std_msgs/Float32` | Steering from linear driver |
| Sub | `/aeb_f110/sources/teleop/throttle` | `std_msgs/Float32` | Throttle from teleop |
| Sub | `/aeb_f110/sources/teleop/steering` | `std_msgs/Float32` | Steering from teleop |
| Sub | `/aeb_f110/mux/active_source` | `std_msgs/String` | Runtime source selection |
| Pub | `/aeb_f110/throttle_request` | `std_msgs/Float32` | Selected throttle forwarded to AEB |
| Pub | `/aeb_f110/steering_request` | `std_msgs/Float32` | Selected steering forwarded to AEB |

### `linear_driver_node`

| Direction | Topic | Type | Description |
|---|---|---|---|
| Pub | `/aeb_f110/sources/auto/throttle` | `std_msgs/Float32` | Constant forward throttle |
| Pub | `/aeb_f110/sources/auto/steering` | `std_msgs/Float32` | Constant steering (`0.0`) |

### `mode_switcher_node`

| Direction | Topic | Type | Description |
|---|---|---|---|
| Pub | `/aeb_f110/mux/active_source` | `std_msgs/String` | Source selection command (`'auto'` / `'teleop'`) |

---

## Contact

This project was developed as part of **AIROS – ESPOL**.

**Raúl Villavicencio**
GitHub: [https://github.com/Raulvillaes](https://github.com/Raulvillaes)

**Micaela Anamise**
GitHub: [https://github.com/carolinanamise13-hub](https://github.com/carolinanamise13-hub)

**Maykoll Vanegas**
GitHub: [https://github.com/VanegasMaykoll](https://github.com/VanegasMaykoll)
---

*AIROS – ESPOL*
