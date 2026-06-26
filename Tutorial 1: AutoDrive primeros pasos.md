# AutoDRIVE - Installer & ROS 2 Bridge (AIROS) 🏎️



This repository provides a detailed guide to installing the AutoDRIVE simulator and configuring the communication bridge between the AutoDRIVE Simulator and ROS 2 Humble. The goal is to enable control and data acquisition for the F1TENTH vehicle for robotics and autonomous navigation projects.



---



## 📋 Prerequisites



Before starting, ensure your environment meets the following requirements:


* **Operating System:** ([Ubuntu 22.04](https://github.com/widegonz/Ubuntu-Installation))

* **Middleware:** ([ROS 2 Humble](https://docs.ros.org/en/humble/Installation.html))



---







## 🕹️ 1. Simulator Installation



Follow these steps to prepare the simulation environment:


1. **Download** the compressed file (.zip) of the simulator for Linux. 
* ⬇️ [Download AutoDRIVE Simulator Linux](https://github.com/Tinker-Twins/AutoDRIVE/releases/download/Simulator-0.3.0/AutoDRIVE_Simulator_Linux.zip)

2. **Save** the file in an accessible location and unzip it (e.g., ~/Downloads/AutoDRIVE_Sim).

3. **Open the terminal** and navigate to the folder where you extracted the simulator.

   ```bash

   cd ~/Downloads/AutoDRIVE_Sim

4. Grant execution permissions to the main binary:

      ```bash

   chmod +x "AutoDRIVE Simulator.x86_64"

5. Start the simulator by running the following command:

     ```bash

   ./"AutoDRIVE Simulator.x86_64"

---

## 2. ROS 2 BRIDGE (DEVKIT)

### 2.1 Workspace and Virtual Environment Setup

To avoid conflicts between the library versions required by the DevKit and the default Python packages installed in Ubuntu 22.04, we will use a Python Virtual Environment (`venv`). This isolates the required dependencies inside the workspace and prevents changes to the global system installation.

Run the following commands to create the workspace folder structure:

```bash
mkdir -p ~/autodrive_ws/src
cd ~/autodrive_ws
```

### 2.2 Configure the Virtual Environment and Instal Dependencies.

Create the virtual environment inside the workspace root:

```bash
python3 -m venv venv
```

Activate the environment:

```bash
source venv/bin/activate
```
---

> [!NOTE]
> The virtual environment must be activated every time a new terminal is opened before running the DevKit or installing Python dependencies.

With the virtual environment active, first update the basic Python installation tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Then install the required libraries using the verified versions for compatibility:

```bash
python -m pip install \
  PyYAML \
  eventlet==0.33.3 \
  Flask-SocketIO==4.1.0 \
  python-socketio==4.2.0 \
  python-engineio==3.13.0 \
  gevent-websocket==0.10.1 \
  transforms3d \
  attrdict \
  numpy==1.23.5 \
  opencv-contrib-python
```

> [!NOTE]
> `PyYAML` is included because ROS 2 commonly uses YAML files for node parameters, launch configurations, robot settings, and calibration files. Installing it inside the virtual environment avoids dependency warnings related to ROS 2 packages such as `launch-ros`.

> [!IMPORTANT]
> Do not leave empty lines after the backslash (`\`) when writing multiline commands in Bash.
> The backslash only continues the command on the next immediate line. If an empty line is inserted, the command will be interrupted and the remaining packages may be interpreted as separate terminal commands.

The `attrdict` library has compatibility issues with Python 3.10+, because it imports `Mapping`, `MutableMapping`, and `Sequence` from the old `collections` module. In Python 3.10, these classes must be imported from `collections.abc`.

To fix this issue without modifying the global system, apply the patch directly inside the virtual environment:

```bash
ATTRDICT_DIR="$(python -c 'import site, os; print(os.path.join(site.getsitepackages()[0], "attrdict"))')"

find "$ATTRDICT_DIR" -name "*.py" -exec sed -i \
  -e 's/from collections import Mapping, MutableMapping, Sequence/from collections.abc import Mapping, MutableMapping, Sequence/g' \
  -e 's/from collections import Mapping/from collections.abc import Mapping/g' \
  -e 's/from collections import MutableMapping/from collections.abc import MutableMapping/g' \
  -e 's/from collections import Sequence/from collections.abc import Sequence/g' \
  {} +
```

This method automatically detects the correct `attrdict` installation path inside the active virtual environment, instead of assuming a fixed Python version path such as `python3.10`.

#### Verify the Installation

After installing the dependencies and applying the patch, verify that the main libraries were installed correctly:

```bash
python -m pip show attrdict python-engineio transforms3d numpy
```

Then test the imports:

```bash
python - <<'PY'
from attrdict import AttrDict
import transforms3d
import numpy
import cv2
import socketio
import engineio

print("All dependencies were imported successfully.")
PY
```

If the message appears without errors, the virtual environment is correctly configured.

[Screencast from 06-26-2026 03:53:47 AM.webm](https://github.com/user-attachments/assets/df783665-119e-4cd0-a021-468c0ad4dc22)

### 2.4 Cloning and Organizing the Workspace

In this step, we will download the official AutoDRIVE repository and extract only the ROS 2 package required for this workspace.

AutoDRIVE includes several components, such as the Simulator, Testbed, DevKit, ADSS Toolkit, and SCSS Toolkit. However, for this ROS 2 bridge setup, we only need the `autodrive_ros2` package located inside the ADSS Toolkit.

The `src` folder is where ROS 2 source packages are placed before compilation. When `colcon build` is executed from the workspace root, it scans the `src` directory looking for valid ROS 2 packages. For this reason, we will move `autodrive_ros2` directly into `~/autodrive_ws/src`.

#### 2.4.1 Clone the AutoDRIVE DevKit Branch

Navigate to the workspace source folder:

```bash
cd ~/autodrive_ws/src
```

Clone only the `AutoDRIVE-Devkit` branch from the official repository:

```bash
git clone --single-branch --branch AutoDRIVE-Devkit https://github.com/Tinker-Twins/AutoDRIVE.git
```

The option `--branch AutoDRIVE-Devkit` selects the DevKit branch, while `--single-branch` avoids downloading unnecessary branch history from the repository.

#### 2.4.2 Extract the ROS 2 Package

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

#### 2.4.3 Remove the Original Repository Folder

After extracting the required ROS 2 package, the rest of the cloned repository is no longer needed inside this workspace.

Remove the original `AutoDRIVE` folder:

```bash
rm -rf ~/autodrive_ws/src/AutoDRIVE
```

This cleanup prevents `colcon` from scanning unnecessary files or unrelated packages during compilation.

> [!IMPORTANT]
> Only run this command after confirming that `autodrive_ros2` was successfully moved to `~/autodrive_ws/src`.

### 2.5 Compiling the Workspace

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

Activate the Python virtual environment:

```bash
source venv/bin/activate
```

Load the ROS 2 Humble environment:

```bash
source /opt/ros/humble/setup.bash
```

The virtual environment provides the Python libraries required by the AutoDRIVE DevKit, while the ROS 2 setup file provides access to ROS 2 commands, packages, environment variables, and build tools.

Build the workspace using:

```bash
colcon build --symlink-install
```

The `--symlink-install` option creates symbolic links instead of copying some files into the `install` folder. This is useful during development because changes in Python scripts and resource files can be reflected more easily without requiring a full rebuild every time.

After compilation, source the local workspace setup file:

```bash
source install/setup.bash
```

This command makes the newly compiled `autodrive_ros2` package available in the current terminal session.

> [!NOTE]
> This command must be executed in every new terminal before running the AutoDRIVE ROS 2 package, unless it is added permanently to the `.bashrc` file.

You can check if ROS 2 detects the package with:

```bash
ros2 pkg list | grep autodrive
```

If the package was correctly built and sourced, an AutoDRIVE-related package name should appear in the terminal.

Un detalle importante: `colcon` es el build tool estándar usado para compilar workspaces de ROS 2, y `--symlink-install` usa enlaces simbólicos en lugar de copiar archivos cuando es posible, lo cual es útil durante desarrollo.

VIDEO DE ESTE PROCESO

---

## 🚀 3. Execution and Teleoperation



To start the system, follow this order strictly. We recommend opening independent terminals for each process.


### Step 1: Start the Communication Bridge
You have two modes depending on whether you need sensor visualization or want to save system resources:


**Option A: Bridge with Visualization (RViz)**
Use this to see the LiDAR, camera feed, and the vehicle's 3D model while driving.
```bash

cd ~/autodrive_ws

source venv/bin/activate

source /opt/ros/humble/setup.bash

source install/setup.bash

export PYTHONUNBUFFERED=1

# Launches the bridge and opens RViz automatically
ros2 launch autodrive_f1tenth simulator_bringup_rviz.launch.py

```

**Option B: Simple Bridge (Headless)**
Use this if you only want to teleoperate the car without the graphical overhead of RViz.
```bash



cd ~/autodrive_ws

source venv/bin/activate

source /opt/ros/humble/setup.bash

source install/setup.bash

export PYTHONUNBUFFERED=1

# Launches only the communication bridge
ros2 launch autodrive_f1tenth simulator_bringup_headless.launch.py

```



### Step 2: Run the Simulator



Open a new terminal and launch the simulator:
```bash

cd ~/Downloads/AutoDRIVE_Sim  # Adjust path to your folder

./"AutoDRIVE Simulator.x86_64"

  ```

Actions in the simulator:


* Click the antenna button (Disconnected) until it changes to Connected.

* Verify that the driving mode is set to Autonomous.



### Step 3: Keyboard Control (Teleoperation)



In a new terminal, run the node to control the car using keys:
```bash

cd ~/autodrive_ws

source venv/bin/activate

source /opt/ros/humble/setup.bash

source install/setup.bash

ros2 run autodrive_f1tenth teleop_keyboard

```

Controls: W (Accelerate), S (Reverse), A (Left), D (Right), X (Brake).


Note: You must keep this terminal window selected/focused for the vehicle to respond to keystrokes.

# 🤝 Contributing
Contributions are welcome! If you have a suggestion that would make this better, please fork the repo and create a pull request.

✉️ Contact
Hector La Mota - [LinkedIn](https://www.linkedin.com/in/h%C3%A9ctor-la-mota-5a9b7a2a8/)
Carolina Sanchez
### SLIDES :https://docs.google.com/presentation/d/1Yl-QCOvlGdIBSREwMPxfj50a_lk7E9fm8FWiSNKZ6dg/edit?slide=id.p3#slide=id.p3
**AIROS - ESPOL**
