# Racecar 阿克曼转向仿真
## 快速开始

```bash
# 编译
cd ~/racecar_ws4
colcon build

# 启动仿真
source install/setup.bash
ros2 launch racecar_description display.launch.py

# 控制小车（另一个终端）
source install/setup.bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 1.0}, angular: {z: 0.2}}" -r 10
```
>如果想要让点云更清晰的话，要在RVIZ的左边的LaserScan里把STyle改为Point

## 架构

### 小车结构

```
base_link
 ├─ left_rear_wheel_joint (continuous, Z轴) → left_rear_wheel_link   ← 驱动轮
 ├─ right_rear_wheel_joint (continuous, Z轴) → right_rear_wheel_link  ← 驱动轮
 ├─ left_front_steer_joint (revolute, Z轴) → left_front_steer_link
 │    └─ left_front_wheel_joint (continuous, Z轴) → left_front_wheel_link  ← 转向轮
 ├─ right_front_steer_joint (revolute, Z轴) → right_front_steer_link
 │    └─ right_front_wheel_joint (continuous, Z轴) → right_front_wheel_link ← 转向轮
 └─ 传感器 (LiDAR, 相机, IMU, GPS, 磁力计)
```

- 所有车轮绕 **Z 轴**旋转，通过 `rpy="-1.5708 0 0"` 使轮子水平
- 前转向节限位 ±0.6 rad（约 ±34°）

### 阿克曼转向

使用 Gazebo 内置的 `AckermannSteering` 插件（无需额外转换节点）：

- 插件：`gz-sim-ackermann-steering-system`
- 订阅：`/model/racecar/cmd_vel`（桥接自 ROS `/cmd_vel`）
- 里程计输出：`/model/racecar/odometry`（桥接至 ROS `/odom`）

| 参数 | 值 |
|------|-----|
| 轴距 | 0.30 m |
| 轮距 | 0.48 m |
| 轮径 | 0.06 m |
| 最大速度 | ±3.0 m/s |
| 最大转角 | 0.6 rad (~34°) |

### 参数

| 参数 | 值 |
|------|-----|
| 底盘尺寸 | 0.50 × 0.35 × 0.08 m |
| 质量 | 2.0 kg |
| 后轴位置 | x = -0.12 m |
| 前轴位置 | x = 0.18 m |

## 传感器

| 传感器 | ROS 话题 | 类型 | 参数 |
|--------|---------|------|------|
| **激光雷达** | `/scan` | `sensor_msgs/LaserScan` | VLP16, 360°×30°, 30m, 20Hz |
| **摄像头** | `/camera/image_raw` | `sensor_msgs/Image` | 640×480, 30Hz, FOV 60° |
| **IMU** | `/imu/data_raw` | `sensor_msgs/Imu` | 100Hz, 含噪声模型 |
| **GPS** | `/gps/fix` | `sensor_msgs/NavSatFix` | 5Hz, 22.5431°N 114.0579°E |
| **磁力计** | `/magnetometer` | `sensor_msgs/MagneticField` | — |
| **里程计** | `/odom` | `nav_msgs/Odometry` | 来自 AckermannSteering 插件 |


## ROS 话题

| 话题 | 方向 | 说明 |
|------|------|------|
| `/cmd_vel` | ROS → Gazebo | 速度控制 (Twist) |
| `/odom` | Gazebo → ROS | 里程计 |
| `/scan` | Gazebo → ROS | 激光雷达 |
| `/camera/image_raw` | Gazebo → ROS | 摄像头图像 |
| `/camera/camera_info` | Gazebo → ROS | 相机参数 |
| `/imu/data_raw` | Gazebo → ROS | IMU 数据 |
| `/gps/fix` | Gazebo → ROS | GPS 定位 |
| `/magnetometer` | Gazebo → ROS | 磁场数据 |
| `/tf` | Gazebo → ROS | 坐标变换 |
| `/joint_states` | Gazebo → ROS | 关节状态 |
| `/robot_description` | — | URDF 模型描述 |

## 赛道

赛道由蓝/黄色锥桶组成，分布在 x ∈ [-2, 27], y ∈ [-15, 14] 区域：

- 蓝色锥桶（赛道左侧）：沿路径排列，从起点 (-2, -15) 到终点 (27, 14)
- 黄色锥桶（赛道右侧）：与蓝色锥桶配合形成约 4m 宽赛道

小车起点：**(0, -15, 0.08)**，朝北（yaw = 1.5708 rad）

## 文件结构

```
src/racecar_description/
├── urdf/
│   ├── racecar.urdf.xacro    — 整车模型定义（底盘、车轮、转向、传感器、插件）
│   └── sensors.xacro         — 传感器宏定义（LiDAR、相机、IMU、GPS、磁力计）
├── launch/
│   └── display.launch.py     — 启动文件（Gazebo + Rviz2 + bridge + 感知节点）
├── config/
│   └── bridge.yaml           — ROS ↔ Gazebo 话题桥接配置
├── worlds/
│   └── track.sdf             — 赛道世界定义（锥桶、光照、物理引擎、系统插件）
├── rviz/
│   └── racecar.rviz          — RViz2 可视化配置
├── models/
│   ├── blue_cone/            — 蓝色锥桶模型
│   └── yellow_cone/          — 黄色锥桶模型
├── meshes/                   — 网格文件（预留）
├── CMakeLists.txt
└── package.xml
```

## 依赖说明（大家自己看着下载）

- ROS 2 Humble
- Gazebo Sim 8 (Harmonic)
- ros_gz_sim (Humble)
- ros_gz_bridge (Humble)
- xacro
- robot_state_publisher
- rviz2



## 遇到的问题解决

### 赛道的导入
最开始对锥桶赛道的导入一脸懵，我询问了AI该如何解决相关问题，最后使用model://绝对路径的方法把锥桶直接写入了世界文件中。

### 小车导入后阿克曼转向插件不工作
最开始用 ros_gz_sim create 把小车"发射"进仿真，车的阿克曼转向插件就像没通电一样，轮子不转
也是询问AI相关解决办法，一个个尝试，最后发现把小车模型直接写入世界文件里就可以解决。
具体解决办法：
1.用 xacro 把小车 URDF 展开
2.用 gz sdf -p 把 URDF 转成 SDF 格式
3.把转换后的 <model>...</model> 整个塞进世界文件的 </world> 前面
4.在模型里加一行 <pose>0 -15 0.08 0 0 1.5708</pose> 设定起点位置和朝向


### 雷达和相机不显示的问题

Gazebo 里能看到激光雷达的点云和摄像头画面，但 RViz2 里 LaserScan 和 Camera 面板一片空白。

Gazebo Sim 8 发布传感器数据时，frame_id 用的是 `racecar/base_link/laser` 和 `racecar/base_link/camera`。但 RViz2 只知道 `base_link`（来自 `robot_state_publisher`），不知道这些传感器 frame 在哪，所以无法把点云放到正确的位置，也无法渲染图像。

解决办法：手动告诉 RViz2 传感器 frame 的位置：

在 `display.launch.py` 里加了两个静态 TF 发布器：

```python
# 告诉 RViz2: 激光雷达 frame 在 base_link 正上方 12cm 处
Node(package='tf2_ros', executable='static_transform_publisher',
    arguments=['0','0','0.12','0','0','0','base_link','racecar/base_link/laser'])

# 告诉 RViz2: 摄像头 frame 也在 base_link 正上方 12cm 处
Node(package='tf2_ros', executable='static_transform_publisher',
    arguments=['0','0','0.12','0','0','0','base_link','racecar/base_link/camera'])
```

相当于给 RViz2 画了一张地图："传感器 frame 就在车底盘往上 12 厘米的位置"，这样它就知道把点云和图像渲染到哪了。

按理来说，Gazebo 会自动生成 TF 树，但不知为什么没生成，这里是用 Copilot 完成的修改。

### 物理引擎加载失败

Gazebo 启动后小车直接掉到地底下，或者轮子不转。

Gazebo Sim 8 的物理引擎插件路径没配置好，系统找不到 `libgz-physics8.so`。

解决办法：在启动脚本里手动指定物理引擎路径。

在 `display.launch.py` 顶部设置环境变量：

```python
physics_engine_path = '/usr/lib/x86_64-linux-gnu/gz-physics-8/engine-plugins'
if 'GZ_SIM_PHYSICS_ENGINE_PATH' not in os.environ or not os.environ['GZ_SIM_PHYSICS_ENGINE_PATH']:
    os.environ['GZ_SIM_PHYSICS_ENGINE_PATH'] = physics_engine_path
```

### GPS、IMU、磁力计没有数据

激光雷达和摄像头都有数据，但 `/gps/fix`、`/imu/data_raw`、`/magnetometer` 这三个话题收不到任何消息。

GPS、IMU、磁力计这些传感器在 Gazebo Sim 8 里需要额外的系统级插件才能工作，光在 URDF 里定义传感器是不够的。

解决办法：在世界文件 `track.sdf` 里添加对应的系统插件：

```xml
<plugin filename="gz-sim-navsat-system" name="gz::sim::systems::NavSat"></plugin>
<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu"></plugin>
<plugin filename="gz-sim-magnetometer-system" name="gz::sim::systems::Magnetometer"></plugin>
```

相当于给 Gazebo 装上"驱动"，告诉它：这些传感器类型需要额外的处理模块来生成数据。

### 小车位置和状态不重置

每次重启仿真，小车还在上次的位置，没有回到起点。

Gazebo 会把仿真状态缓存到 `~/.gz/sim/` 目录下，重启后自动恢复，不会从零开始。

解决办法：手动清理 Gazebo 缓存：

```bash
rm -rf ~/.gz/sim/log* ~/.gz/sim/8/tmp*
```

或者在启动脚本中自动清理临时文件：

```bash
rm -f /tmp/racecar_track.sdf /tmp/racecar*.sdf /tmp/racecar.urdf
```

