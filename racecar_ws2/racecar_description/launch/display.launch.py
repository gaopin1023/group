import os
import tempfile
import subprocess
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_racecar = get_package_share_directory('racecar_description')
    xacro_path = os.path.join(pkg_racecar, 'urdf', 'racecar.urdf.xacro')
    rviz_config = os.path.join(pkg_racecar, 'rviz', 'racecar.rviz')
    world_template = os.path.join(pkg_racecar, 'worlds', 'track.sdf')
    bridge_yaml = os.path.join(pkg_racecar, 'config', 'bridge.yaml')
    points_bridge_yaml = os.path.join(pkg_racecar, 'config', 'points_bridge.yaml')
    models_path = os.path.join(pkg_racecar, 'models')

    with open(world_template, 'r') as f:
        world_content = f.read()
    world_content = world_content.replace(
        '<uri>model://blue_cone</uri>',
        f'<uri>file://{models_path}/blue_cone</uri>')
    world_content = world_content.replace(
        '<uri>model://yellow_cone</uri>',
        f'<uri>file://{models_path}/yellow_cone</uri>')
    world_file = os.path.join(tempfile.gettempdir(), 'racecar_track.sdf')

    physics_engine_path = '/usr/lib/x86_64-linux-gnu/gz-physics-8/engine-plugins'
    if 'GZ_SIM_PHYSICS_ENGINE_PATH' not in os.environ or not os.environ['GZ_SIM_PHYSICS_ENGINE_PATH']:
        os.environ['GZ_SIM_PHYSICS_ENGINE_PATH'] = physics_engine_path
    elif physics_engine_path not in os.environ['GZ_SIM_PHYSICS_ENGINE_PATH']:
        os.environ['GZ_SIM_PHYSICS_ENGINE_PATH'] = physics_engine_path + ':' + os.environ['GZ_SIM_PHYSICS_ENGINE_PATH']

    robot_desc = subprocess.check_output(['xacro', xacro_path]).decode('utf-8')

    urdf_path = os.path.join(tempfile.gettempdir(), 'racecar.urdf')
    with open(urdf_path, 'w') as f:
        f.write(robot_desc)
    sdf_path = os.path.join(tempfile.gettempdir(), 'racecar_model.sdf')
    subprocess.run(['gz', 'sdf', '-p', urdf_path], stdout=open(sdf_path, 'w'),
                   stderr=subprocess.DEVNULL)
    with open(sdf_path, 'r') as f:
        sdf_content = f.read()
    ms = sdf_content.find('<model')
    me = sdf_content.find('</model>') + len('</model>')
    model_sdf = sdf_content[ms:me] if ms >= 0 else sdf_content
    tag_end = model_sdf.find('>') + 1
    model_sdf = model_sdf[:tag_end] + '\n    <pose>0 -15 0.08 0 0 1.5708</pose>' + model_sdf[tag_end:]
    world_content = world_content.replace('</world>',
        f'  {model_sdf}\n</world>')
    with open(world_file, 'w') as f:
        f.write(world_content)

    return LaunchDescription([

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': world_file + ' -r'}.items()
        ),

        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': robot_desc,
                'frame_prefix': 'racecar/',
                'use_sim_time': True,
            }],
            output='screen'
        ),

        # 传感器静态 TF（imu/gps/magnetometer 保持静态）
        Node(package='tf2_ros', executable='static_transform_publisher',
            arguments=['0','0','0.02','0','0','0','racecar/base_link','racecar/base_link/imu']),
        Node(package='tf2_ros', executable='static_transform_publisher',
            arguments=['-0.18','0','0.04','0','0','0','racecar/base_link','racecar/base_link/gps']),
        Node(package='tf2_ros', executable='static_transform_publisher',
            arguments=['0.15','0.1','0.02','0','0','0','racecar/base_link','racecar/base_link/magnetometer']),

        # 统一动态 TF 发布节点（odom→base_link、base_link→racecar/base_link 及激光/相机别名）
        Node(package='racecar_description', executable='odom_to_tf.py',
            parameters=[{'use_sim_time': True}],
            output='screen'),

        Node(package='rviz2', executable='rviz2',
            arguments=['-d', rviz_config], output='screen'),

        # 主桥接（带 frame_prefix，不含 /scan/points）
        Node(package='ros_gz_bridge', executable='parameter_bridge',
            arguments=['--ros-args', '-p', f'config_file:={bridge_yaml}',
                       '-p', 'frame_prefix:=racecar/'],
            parameters=[{'use_sim_time': True}],
            output='screen'),

        # 点云桥接（不带 frame_prefix，frame_prefix 与 PointCloudPacked 不兼容）
        Node(package='ros_gz_bridge', executable='parameter_bridge',
            arguments=['--ros-args', '-p', f'config_file:={points_bridge_yaml}'],
            output='screen'),

        Node(package='sim_perception', executable='sim_node',
            parameters=[{'use_sim_time': True}],
            output='screen'),
    ])
