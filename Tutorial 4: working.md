# F1TENTH Autonomous Navigation & Multimodal Anomaly Detection (AutoDRIVE)

## Project Description
This project implements a reactive autonomous navigation system for an F1TENTH vehicle using the AutoDRIVE ecosystem and ROS 2 Humble. The core of the system is based on the Follow the Gap algorithm, which allows the vehicle to avoid obstacles at high speeds by searching for the deepest space within the LiDAR horizon. Additionally, it integrates a multimodal anomaly detection layer that cross-references laser perception data with the vehicle's dynamic telemetry.

### Reactive Planning – Follow the Gap
A control node is implemented to process LiDAR point clouds to identify safe "gaps". The algorithm applies a Safety Bubble around detected obstacles to prevent collisions and selects the center of the deepest gap as the steering target.

## 1. Installation

### 1.0 Install ROS-based dependencies:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-rosdep python3-colcon-common-extensions git
sudo apt install ros-humble-ackermann-msgs
sudo apt install ros-humble-nav2-msgs
```
### 1.1 Clone and install all dependencies:
```bash
sudo apt install -y python3-rosdep
sudo rosdep init
rosdep update

mkdir -p ~/autodrive_ws/src
cd ~/autodrive_ws/src
# Clone the AutoDRIVE Bridge
git clone [https://github.com/Triton-AI/autodrive_ros2.git](https://github.com/Triton-AI/autodrive_ros2.git)
# Clone this repository
git clone [https://github.com/Marcos-6783/f1tenth-gap-follow-autodrive.git](https://github.com/Marcos-6783/f1tenth-gap-follow-autodrive.git)

cd ~/autodrive_ws
rosdep install --from-paths src --ignore-src -r -y
```
### 1.2 Build your workspace:
```bash
cd ~/autodrive_ws
colcon build --packages-select gap_follow
source install/setup.bash
```
### ROS 2 package structure
```bash
autodrive_ws/
└── src/
    ├── f1tenth-gap-follow-autodrive/
    │   ├── gap_follow/
    │   │   ├── src/
    │   │   │   └── reactive_node.cpp
    │   │   ├── launch/
    │   │   └── CMakeLists.txt
    └── autodrive_ros2/
        └── autodrive_bridge/
```
### ROS Node Graph
    1. Reactive Node: Processes LiDAR data and calculates steering/throttle.

    2. AutoDRIVE Bridge: Connects ROS 2 with the Unity simulator.

    3. Simulator: Virtual testing environment.

    4. RViz2: Visualization of LaserScan data and Safety Bubbles.
    
### Launch files & Execution
Running the Project
Bridge:
```bash
source ~/autodrive_ws/install/setup.bash
ros2 launch autodrive_ros2 autodrive_bridge.launch.py
Reactive Node: Procesa LiDAR y calcula steering/throttle.
```
Reactive Navigation:
```bash
source ~/autodrive_ws/install/setup.bash
ros2 run gap_follow reactive_node
```

### ⚠️ Multimodal Anomaly Detection
The system integrates advanced safety logic:

Spatial Anomaly (LiDAR): Identifies unmapped obstacles or sudden changes in the environment.

State Anomaly (Perception-based): The system monitors the correlation between control commands and environment changes. If a throttle command is active but the LiDAR scan remains static for a prolonged period, the system infers a collision or stall and triggers an emergency stop protocol.

### Project Execution
Results:https://drive.google.com/file/d/1-0ueHXua01EAlZdTATlNUiUPNk7Jf6PK/view?usp=sharing

### 📊 Visual Results

<img width="1276" height="711" alt="image" src="https://github.com/user-attachments/assets/3ed9340b-c423-4427-925c-d80858181082" />
<img width="1366" height="768" alt="image" src="https://github.com/user-attachments/assets/5de64e89-5c16-4a77-8a65-5f121de7eb67" />

Note: Tests were conducted in the AutoDRIVE testbed, achieving stable navigation without collisions by mitigating noise in the LiDAR sensor.

### Code Explanation
reactive_node.cpp (Follow the Gap Implementation)
The node subscribes to:

/autodrive/f1tenth_1/lidar (sensor_msgs/msg/LaserScan)

And publishes:

/autodrive/f1tenth_1/steering_command (std_msgs/msg/Float32)

/autodrive/f1tenth_1/throttle_command (std_msgs/msg/Float32)

Processing Logic:

Preprocessing: LiDAR data is filtered to remove infinite values and noise.

Find Closest Point: Locates the obstacle nearest to the vehicle.

Eliminate Bubble: "Draws" a safety radius (zeros) around that point to prevent the car from attempting to pass too closely.

Find Best Gap: Searches for the longest sequence of points with maximum distances.

Steering Calculation: Targets the center of the selected gap.

## Technical Code Walkthrough (reactive_node.cpp)
### 1. Perception Filtering (The "Focus" Phase)
```bash
float view_angle = 70.0 * M_PI / 180.0;
// ... (indexing logic)
if (ranges[i] > 4.5) ranges[i] = 4.5;
```
Explanation: We narrow the LiDAR's field of view to a 70° frontal arc. This prevents the car from being distracted by walls behind it or in its blind spots. We also cap the distance at 4.5 meters to focus on immediate obstacles rather than distant track features.

### 2. The Safety Bubble (Collision Mitigation)
```bash
int bubble_radius = 40; 
for (int i = -bubble_radius; i <= bubble_radius; i++) {
    ranges[closest_index + i] = 0.0;
}
```
Explanation: After locating the closest obstacle point, the algorithm "draws" a virtual circular mask of zeros around it. This Safety Bubble accounts for the physical width of the F1TENTH chassis, ensuring the path planning logic treats the entire area near an obstacle as impassable.

### 3. Gap Identification (Path Selection)
```bash
if (ranges[i] > 2.0) { // Deep space threshold
    // ... logic to find the largest contiguous sequence
}
```
Explanation: The algorithm scans the filtered array for the "Deepest Gap"—the longest sequence of consecutive LiDAR beams that report a clear path of at least 2.0 meters. By targeting the center of this gap, the car naturally gravitates toward the most open area of the track.

### 4. Adaptive Control & Perception-Based Anomaly Detection
```bash
if (std::abs(angle) < 0.1) {
    throttle_msg.data = 0.15; // Straightaway speed
} else {
    throttle_msg.data = 0.10; // Cornering speed
}
```
Explanation: * Dynamic Throttle: The node implements a basic speed-to-steering mapping. It reduces speed during sharp turns to prevent understeer and increases it on straight sections.

Stall Detection: Since external telemetry was decoupled for standalone stability, the system uses a Spatial Anomaly counter. If the car commands movement but the LiDAR environment remains static for more than 20 frames, it triggers an emergency stop to prevent motor burnout.




## 🎓 Author
**Marcos Emmanuel Balón García**
*Mechatronics Engineering Student*
Escuela Superior Politécnica del Litoral (ESPOL)
Guayaquil, Ecuador

Developed as part of the Mechatronics Engineering curriculum at ESPOL.
