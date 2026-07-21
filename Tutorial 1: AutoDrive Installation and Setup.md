# AutoDRIVE - Installer & ROS 2 Bridge (AIROS) 🏎️

This repository provides a detailed guide to installing the AutoDRIVE simulator and configuring the communication bridge between the AutoDRIVE Simulator and ROS 2 Humble. The goal is to enable control and data acquisition for the F1TENTH vehicle for robotics and autonomous navigation projects.

## [Ver diapositivas de la presentación](https://docs.google.com/presentation/d/1Yl-QCOvlGdIBSREwMPxfj50a_lk7E9fm8FWiSNKZ6dg/edit?slide=id.g3ccc816dfd6_0_11#slide=id.g3ccc816dfd6_0_11)

---

## 📋 Prerequisites
Before starting, ensure your environment meets the following requirements:

* **Operating System:** ([Ubuntu 22.04](https://github.com/widegonz/Ubuntu-Installation))

* **Middleware:** ([ROS 2 Humble](https://docs.ros.org/en/humble/Installation.html))

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [1. Simulator Installation](#1-simulator-installation)
  - [1.1 Download AutoDRIVE Simulator](#11-download-autodrive-simulator)
  - [1.2 Extract the Simulator](#12-extract-the-simulator)
  - [1.3 Open the Simulator Folder](#13-open-the-simulator-folder)
  - [1.4 Grant Execution Permissions](#14-grant-execution-permissions)
  - [1.5 Start AutoDRIVE Simulator](#15-start-autodrive-simulator)
- [2. ROS 2 Bridge](#2-ros-2-bridge)
  - [2.1 Workspace and Virtual Environment Setup](#21-workspace-and-virtual-environment-setup)
  - [2.2 Configure the Virtual Environment and Install Dependencies](#22-configure-the-virtual-environment-and-install-dependencies)
    - [2.2.1 Install ROS 2 System Dependencies](#221-install-ros-2-system-dependencies)
    - [2.2.2 Create and Activate the Virtual Environment](#222-create-and-activate-the-virtual-environment)
    - [2.2.3 Install Python Dependencies](#223-install-python-dependencies)
    - [2.2.4 Critical Compatibility Patch for attrdict](#224-critical-compatibility-patch-for-attrdict)
    - [2.2.5 Verify the Installation](#225-verify-the-installation)
  - [2.3 Cloning and Organizing the Workspace](#23-cloning-and-organizing-the-workspace)
    - [2.3.1 Clone the AutoDRIVE DevKit Branch](#231-clone-the-autodrive-devkit-branch)
    - [2.3.2 Extract the ROS 2 Package](#232-extract-the-ros-2-package)
    - [2.3.3 Remove the Original Repository Folder](#233-remove-the-original-repository-folder)
  - [2.4 Compiling the Workspace](#24-compiling-the-workspace)
- [3. Execution and Teleoperation](#3-execution-and-teleoperation)
  - [3.1 Start the Communication Bridge](#31-start-the-communication-bridge)
    - [Option A: Bridge with RViz Visualization](#option-a-bridge-with-rviz-visualization)
    - [Option B: Headless Bridge](#option-b-headless-bridge)
  - [3.2 Run AutoDRIVE Simulator](#32-run-autodrive-simulator)
  - [3.3 Keyboard Control: Teleoperation](#33-keyboard-control-teleoperation)
  - [3.4 Recommended Execution Order](#34-recommended-execution-order)

---

## 1. Simulator Installation

In this section, we will download and prepare AutoDRIVE Simulator for Linux.

AutoDRIVE Simulator is the graphical simulation environment where the F1TENTH vehicle will run. Later, this simulator will be connected to ROS 2 through the AutoDRIVE DevKit bridge.

### 1.1 Download AutoDRIVE Simulator

Download the compressed Linux version of AutoDRIVE Simulator from the official release:

[Download AutoDRIVE Simulator Linux](https://github.com/Tinker-Twins/AutoDRIVE/releases/download/Simulator-0.3.0/AutoDRIVE_Simulator_Linux.zip)

Save the `.zip` file in an accessible location, for example:

```text
~/Downloads
```

### 1.2 Extract the Simulator

Extract the downloaded file and rename the extracted folder as:

```text
AutoDRIVE_Sim
```

For this tutorial, we assume the simulator is located at:

```text
~/Downloads/AutoDRIVE_Sim
```

> [!NOTE]
> If you extracted the simulator in a different folder, replace the path in the following commands with your actual location.

### 1.3 Open the Simulator Folder

Open a terminal and navigate to the simulator folder:

```bash
cd ~/Downloads/AutoDRIVE_Sim
```

This folder should contain the main simulator executable:

```text
AutoDRIVE Simulator.x86_64
```

### 1.4 Grant Execution Permissions

Before running the simulator, the main binary must have execution permissions.

Run:

```bash
chmod +x "AutoDRIVE Simulator.x86_64"
```

This command allows Ubuntu to execute the simulator as a program.

> [!NOTE]
> This step is usually required only once after extracting the simulator.

---

### 1.5 Start AutoDRIVE Simulator

Run the simulator with:

```bash
./"AutoDRIVE Simulator.x86_64"
```

The `./` indicates that the executable is located in the current directory.

If the simulator starts correctly, the AutoDRIVE graphical interface should open.

> [!IMPORTANT]
> At this stage, the simulator may show its communication status as `Disconnected`. This is expected because the ROS 2 bridge has not been started yet. The connection will be established later in the execution section.

https://github.com/user-attachments/assets/255f35c9-1cc0-4e90-990a-4d0f33764d0f

---

## 2. ROS 2 BRIDGE

### 2.1 Workspace and Virtual Environment Setup

To avoid conflicts between the library versions required by the DevKit and the default Python packages installed in Ubuntu 22.04, we will use a Python Virtual Environment (`venv`). This isolates the required dependencies inside the workspace and prevents changes to the global system installation.

Run the following commands to create the workspace folder structure:

```bash
mkdir -p ~/autodrive_ws/src
cd ~/autodrive_ws
```

### 2.2 Configure the Virtual Environment and Install Dependencies

In this step, we will install the basic dependencies required by the AutoDRIVE ROS 2 bridge and create a Python virtual environment inside the workspace.

The dependency setup is divided into two parts:

```text id="hk9qoa"
System dependencies  → Installed with apt
Python dependencies  → Installed inside the virtual environment with pip
```

This separation is important because some libraries are part of ROS 2 and should be installed through the Ubuntu package manager, while others are specific Python packages required by the AutoDRIVE DevKit.

#### 2.2.1 Install ROS 2 System Dependencies

Some Python modules used by the AutoDRIVE ROS 2 bridge are provided by ROS 2 packages instead of `pip`.

Install the ROS 2 transformation library:

```bash id="dy8eyh"
sudo apt update
sudo apt install -y \
  ros-humble-tf-transformations \
  ros-humble-imu-tools
```

The package `ros-humble-tf-transformations` provides the `tf_transformations` Python module, which is used by the bridge to convert orientations between Euler angles and quaternions.

The package `ros-humble-imu-tools` provides additional IMU-related tools and RViz plugins used to visualize IMU data. This helps avoid RViz errors related to the `rviz_imu_plugin/Imu` display.

This is required because the AutoDRIVE bridge imports functions such as:

```python id="pu5p52"
from tf_transformations import quaternion_from_euler
```

Without this package, the bridge may fail with an error similar to:

```text id="o5kuy3"
ModuleNotFoundError: No module named 'tf_transformations'
```

#### 2.2.2 Create and Activate the Virtual Environment

Create the virtual environment inside the workspace root:

```bash id="a3k9oe"
python3 -m venv venv
```

Activate the environment:

```bash id="yzmcdv"
source venv/bin/activate
```

When the environment is active, the terminal prompt should show `(venv)` at the beginning.

> [!NOTE]
> The virtual environment must be activated every time a new terminal is opened before running the DevKit or installing Python dependencies.


#### 2.2.3 Install Python Dependencies

With the virtual environment active, first update the basic Python installation tools:

```bash id="mnsjjq"
python -m pip install --upgrade pip setuptools wheel
python -m pip install colcon-common-extensions
```
Installing `colcon` inside the virtual environment helps ensure that the workspace is built using the same Python environment where the AutoDRIVE dependencies were installed.

Then install the required libraries using fixed versions for compatibility:

```bash id="9ln6qj"
python -m pip install \
  PyYAML \
  eventlet==0.33.3 \
  Flask==1.1.4 \
  Flask-SocketIO==4.1.0 \
  python-socketio==4.2.0 \
  python-engineio==3.13.0 \
  Werkzeug==1.0.1 \
  Jinja2==2.11.3 \
  itsdangerous==1.1.0 \
  MarkupSafe==2.0.1 \
  gevent \
  gevent-websocket==0.10.1 \
  transforms3d \
  attrdict \
  Pillow \
  numpy==1.23.5 \
  opencv-contrib-python
```

> [!NOTE]
> `PyYAML` is included because ROS 2 commonly uses YAML files for node parameters, launch configurations, robot settings, and calibration files.
> 
> `Pillow` provides the `PIL` module, which is used by the AutoDRIVE bridge for image handling. Without it, the bridge may fail with:
>
> ```text
> ModuleNotFoundError: No module named 'PIL'
> ```

> [!IMPORTANT]
> The versions of `Flask`, `Flask-SocketIO`, `python-socketio`, `python-engineio`, `Werkzeug`, `Jinja2`, `itsdangerous`, and `MarkupSafe` are fixed to avoid compatibility issues with the AutoDRIVE communication bridge.
>
> Do not leave empty lines after the backslash (`\`) when writing multiline commands in Bash. The backslash only continues the command on the next immediate line. If an empty line is inserted, the command will be interrupted and the remaining packages may be interpreted as separate terminal commands.

#### 2.2.4 Critical Compatibility Patch for `attrdict`

The `attrdict` library has compatibility issues with Python 3.10+, because it imports `Mapping`, `MutableMapping`, and `Sequence` from the old `collections` module.

In Python 3.10, these classes must be imported from:

```text id="fjlb6g"
collections.abc
```

To fix this issue without modifying the global system, apply the patch directly inside the virtual environment:

```bash id="t5l1m3"
ATTRDICT_DIR="$(python -c 'import site, os; print(os.path.join(site.getsitepackages()[0], "attrdict"))')"

find "$ATTRDICT_DIR" -name "*.py" -exec sed -i \
  -e 's/from collections import Mapping, MutableMapping, Sequence/from collections.abc import Mapping, MutableMapping, Sequence/g' \
  -e 's/from collections import Mapping/from collections.abc import Mapping/g' \
  -e 's/from collections import MutableMapping/from collections.abc import MutableMapping/g' \
  -e 's/from collections import Sequence/from collections.abc import Sequence/g' \
  {} +
```

This method automatically detects the correct `attrdict` installation path inside the active virtual environment, instead of assuming a fixed Python version path such as:

```text id="f3okh0"
python3.10
```

#### 2.2.5 Verify the Installation

After installing the dependencies and applying the patch, verify that the main Python libraries were installed correctly:

```bash id="6uvmaa"
python -m pip show \
  PyYAML \
  attrdict \
  transforms3d \
  Pillow \
  gevent \
  gevent-websocket \
  numpy \
  opencv-contrib-python \
  Flask \
  Flask-SocketIO \
  python-socketio \
  python-engineio
```

You can also check the exact installed versions with:

```bash id="ufkym8"
python -m pip freeze | grep -E "Flask|Werkzeug|Jinja2|MarkupSafe|itsdangerous|socketio|engineio|eventlet|gevent|PyYAML|attrdict|transforms3d|Pillow|numpy|opencv"
```
The communication-related dependencies should include versions similar to:

```text id="btqwgd"
Flask==1.1.4
Flask-SocketIO==4.1.0
python-socketio==4.2.0
python-engineio==3.13.0
Werkzeug==1.0.1
Jinja2==2.11.3
itsdangerous==1.1.0
MarkupSafe==2.0.1
```

Then test the Python virtual environment imports:

```bash id="k742lx"
python - <<'PY'
from attrdict import AttrDict
from PIL import Image
from gevent import pywsgi
import geventwebsocket
import transforms3d
import numpy
import cv2
import socketio
import engineio
import flask
import yaml

print("All virtual environment dependencies were imported successfully.")
PY
```

Finally, verify that the ROS 2 transformation module is available:

```bash id="d45k94"
source /opt/ros/humble/setup.bash

python - <<'PY'
from tf_transformations import quaternion_from_euler

print("ROS 2 tf_transformations imported successfully.")
PY
```

If both messages appear without errors, the system and virtual environment dependencies are correctly configured.


https://github.com/user-attachments/assets/4a939ea6-87d3-4630-8bc7-48050aa04e3d


### 2.3 Cloning and Organizing the Workspace

In this step, we will download the official AutoDRIVE repository and extract only the ROS 2 package required for this workspace.

AutoDRIVE includes several components, such as the Simulator, Testbed, DevKit, ADSS Toolkit, and SCSS Toolkit. However, for this ROS 2 bridge setup, we only need the `autodrive_ros2` package located inside the ADSS Toolkit.

The `src` folder is where ROS 2 source packages are placed before compilation. When `colcon build` is executed from the workspace root, it scans the `src` directory looking for valid ROS 2 packages. For this reason, we will move `autodrive_ros2` directly into `~/autodrive_ws/src`.

#### 2.3.1 Clone the AutoDRIVE DevKit Branch

Navigate to the workspace source folder:

```bash
cd ~/autodrive_ws/src
```

Clone only the `AutoDRIVE-Devkit` branch from the official repository:

```bash
git clone --single-branch --branch AutoDRIVE-Devkit https://github.com/Tinker-Twins/AutoDRIVE.git
```

The option `--branch AutoDRIVE-Devkit` selects the DevKit branch, while `--single-branch` avoids downloading unnecessary branch history from the repository.

#### 2.3.2 Extract the ROS 2 Package

The ROS 2 package is located inside the following path:

```text
AutoDRIVE/ADSS Toolkit/autodrive_ros2
```

Since the folder name `ADSS Toolkit` contains a space, the path must be written using quotation marks.

Move the ROS 2 package to the root of the `src` folder:

```bash
mv "$HOME/autodrive_ws/src/AutoDRIVE/ADSS Toolkit/autodrive_ros2" "$HOME/autodrive_ws/src/"
```

After moving the package, the workspace should have this structure:

```text
autodrive_ws/
├── src/
│   └── autodrive_ros2/
├── venv/
```

You can verify it with:

```bash
ls ~/autodrive_ws/src
```

The output should include:

```text
autodrive_ros2
```

#### 2.3.3 Remove the Original Repository Folder

After extracting the required ROS 2 package, the rest of the cloned repository is no longer needed inside this workspace.

Remove the original `AutoDRIVE` folder:

```bash
rm -rf Autodrive
```

Remove the previous log file to ensure a clean build:

```bash
rm -rf build install log
```

This cleanup prevents `colcon` from scanning unnecessary files or unrelated packages during compilation.

> [!IMPORTANT]
> Only run this command after confirming that `autodrive_ros2` was successfully moved to `~/autodrive_ws/src`.

### 2.4 Compiling the Workspace

Once the `src` folder is organized, the workspace can be compiled using `colcon`, the standard build tool used in ROS 2 workspaces.

A ROS 2 workspace usually contains three main parts after compilation:

```text
autodrive_ws/
├── src/        # Source code of the ROS 2 packages
├── build/      # Temporary build files generated by colcon
├── install/    # Installed workspace files used when sourcing the workspace
├── log/        # Build logs
└── venv/       # Python virtual environment
```

The `src` folder contains the original package source code. The `build`, `install`, and `log` folders are generated automatically when `colcon build` is executed.

Return to the workspace root:

```bash
cd ~/autodrive_ws
```

Load the ROS 2 Humble environment:

```bash
source /opt/ros/humble/setup.bash
```

Activate the Python virtual environment:

```bash
source venv/bin/activate
```

The virtual environment provides the Python libraries required by the AutoDRIVE DevKit, while the ROS 2 setup file provides access to ROS 2 commands, packages, environment variables, and build tools.

Build the workspace using:

```bash
python -m colcon build --symlink-install
```

The `--symlink-install` option creates symbolic links instead of copying some files into the `install` folder. This is useful during development because changes in Python scripts and resource files can be reflected more easily without requiring a full rebuild every time.

Using `python -m colcon` helps ensure that the build process uses the Python environment where the AutoDRIVE dependencies were installed.

After compilation, source the local workspace setup file:

```bash
source install/setup.bash
```

This command makes the newly compiled `autodrive_ros2` package available in the current terminal session.

> [!NOTE]
> This command must be executed in every new terminal before running the AutoDRIVE ROS 2 package.

You can check if ROS 2 detects the package with:

```bash
ros2 pkg list | grep autodrive
```

If the package was correctly built and sourced, an AutoDRIVE-related package name should appear in the terminal.

https://github.com/user-attachments/assets/57a2bed2-dc34-469a-8b7b-8336618073cb

---

## 3. Execution and Teleoperation

In this section, we will run the complete AutoDRIVE system. The execution requires three independent processes:

```text
Terminal 1 → ROS 2 communication bridge
Terminal 2 → AutoDRIVE Simulator
Terminal 3 → Keyboard teleoperation node
```

Each process must remain running in its own terminal. Closing one of them may interrupt the connection between the simulator, the ROS 2 bridge, and the teleoperation node.

### 3.1 Start the Communication Bridge

The communication bridge connects AutoDRIVE Simulator with ROS 2.

Its role is to exchange data between both sides:

```text
Simulator → ROS 2 topics
ROS 2 commands → Simulator
```

For example, sensor data such as LiDAR, camera, vehicle state, and other simulation information are published as ROS 2 topics. At the same time, control commands generated in ROS 2 are sent back to the simulator.

Before running the bridge, open a terminal and load the required environments:

```bash
cd ~/autodrive_ws

source /opt/ros/humble/setup.bash
source venv/bin/activate
source install/setup.bash

export PYTHONUNBUFFERED=1
```

The command `source venv/bin/activate` activates the Python virtual environment where the required AutoDRIVE Python dependencies were installed.

The command `source /opt/ros/humble/setup.bash` loads the ROS 2 Humble environment.

The command `source venv/bin/activate` activates the Python virtual environment where the required AutoDRIVE Python dependencies were installed.

The command `source install/setup.bash` loads the compiled packages from the current workspace.

### Option A: Bridge with RViz Visualization

Use this option if you want to visualize the vehicle, LiDAR, camera data, and other ROS 2 information in RViz while the simulator is running.

```bash
ros2 launch autodrive_f1tenth simulator_bringup_rviz.launch.py
```

This launch file starts the AutoDRIVE ROS 2 bridge and opens RViz automatically.

This option is useful for debugging and visualization, but it uses more system resources.

### Option B: Headless Bridge

Use this option if you only want to run the communication bridge without opening RViz.

```bash
ros2 launch autodrive_f1tenth simulator_bringup_headless.launch.py
```

This launch file starts only the communication bridge.

This option is recommended when you want to save system resources or when you only need to teleoperate the vehicle.

> [!TIP]
> If this is your first test, it is recommended to start with the headless bridge. Once the simulator connects correctly, you can try the RViz version.

### 3.2 Run AutoDRIVE Simulator

Open a new terminal and launch the simulator.

Go to the folder where AutoDRIVE Simulator was extracted:

```bash
cd ~/Downloads/AutoDRIVE_Sim
```

Run the simulator:

```bash
./"AutoDRIVE Simulator.x86_64"
```

> [!NOTE]
> If your simulator is stored in a different folder, replace the path with the correct location.

Once the simulator opens:

1. Click the antenna button labeled `Disconnected`.
2. Wait until it changes to `Connected`.
3. Verify that the driving mode is set to `Autonomous`.

The `Connected` status means that the simulator successfully established communication with the ROS 2 bridge.

If the button does not change to `Connected`, return to the bridge terminal and check for Python errors, missing dependencies, or failed ROS 2 nodes.

### 3.3 Keyboard Control: Teleoperation

Open a third terminal to run the keyboard teleoperation node.

Load the same workspace environment:

```bash
cd ~/autodrive_ws

source /opt/ros/humble/setup.bash
source venv/bin/activate
source install/setup.bash
```

Run the keyboard teleoperation node:

```bash
ros2 run autodrive_f1tenth teleop_keyboard
```

Use the following keys to control the vehicle:

```text
W → Accelerate
S → Reverse
A → Turn left
D → Turn right
X → Brake
```

> [!IMPORTANT]
> The teleoperation terminal must remain selected and focused. If another window is active, the keyboard inputs will not be captured by the teleoperation node.

https://github.com/user-attachments/assets/e91b4b6d-f625-48be-8c49-94108f4ffb49

### 3.4 Recommended Execution Order

The recommended order is:

```text
1. Start the ROS 2 bridge.
2. Start AutoDRIVE Simulator.
3. Connect the simulator using the antenna button.
4. Verify that the simulator status changes to Connected.
5. Run the keyboard teleoperation node.
6. Keep the teleoperation terminal focused while driving.
```

Following this order ensures that the simulator can find the bridge when the connection button is pressed.

---

# 🤝 Contributing
Contributions are welcome! If you have a suggestion that would make this better, please fork the repo and create a pull request.

✉️ Contact
1. Hector La Mota - [LinkedIn](https://www.linkedin.com/in/h%C3%A9ctor-la-mota-5a9b7a2a8/)
2. Carolina Sanchez - [LinkedIn](https://www.linkedin.com/in/carolinas%C3%A1nchezcevallos/)
3. Maykoll Vanegas - - [LinkedIn](https://www.linkedin.com/in/maykoll-steven-vanegas-silva-baa225219/)

**AIROS - ESPOL**
