import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 获取 EKF 配置文件路径
    ekf_config = os.path.join(
        get_package_share_directory('racecar_localization'),
        'config',
        'ekf.yaml'
    )

    return LaunchDescription([
        # 1. GPS 坐标转换节点 (navsat_transform_node)
        Node(
            package='robot_localization',
            executable='navsat_transform_node',
            name='navsat_transform',
            output='screen',
            # 关键修改：强行注入仿真时间，并确保核心参数与 YAML 一致
            parameters=[{
                'use_sim_time': True,                  # 必须开启仿真时间
                'magnetic_declination_radians': 0.0,
                'yaw_offset': 1.5707963,
                'zero_altitude': True,
                'use_odometry_yaw': True,
                'wait_for_datum': False,
                'publish_odometry_gps': True,
                'broadcast_cartesian_transform': True,   # 建议开启，方便直接在 TF 树里看 map->utm
                'datum':"39.9,116.4,0.0,map,racecar/base_link"  
            }],
            remappings=[
                ('imu', '/imu/data_raw'),
                ('gps/fix', '/gps/fix'),
                ('odometry/gps', '/odometry/gps'),
                ('odometry/filtered', '/odometry/filtered')
            ]
        ),

        # 2. EKF 滤波主节点
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node', # 已与你的 yaml 里的 ekf_filter_node 严格对齐
            output='screen',
            parameters=[
                ekf_config,
                {'use_sim_time': True} # 核心保险：强制覆盖 YAML 里的 use_sim_time，杜绝时间戳报错
            ]
        ),

            # 3. GPS 协方差中继节点
        Node(
            package='racecar_description',
            executable='gps_odom_relay.py',
            name='gps_odom_relay',
            output='screen',
            parameters=[
                {'use_sim_time': True}
            ]
        )

    ])

