#!/usr/bin/env python3
"""
统一发布 racecar 相关动态 TF：
  {/odom.frame_id} → base_link            (来自 /odom 里程计，50Hz)
  base_link → {/odom.child_frame_id}        (恒等变换，frame 别名)
  base_link → racecar/base_link/laser       (激光 frame 别名，偏移 0 0 0.05)
  base_link → racecar/base_link/camera      (相机 frame 别名，偏移 0 0 0.12)
全部使用 /odom 的仿真时间戳。
frame_id 均从 /odom 消息中读取，兼容不同前缀配置。
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class OdomToTF(Node):
    def __init__(self):
        super().__init__('odom_to_tf')

        self.tf_broadcaster = TransformBroadcaster(self)
        self.sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10)
        self.get_logger().info('odom_to_tf node started, waiting for /odom...')

    def odom_callback(self, msg: Odometry):
        now = msg.header.stamp
        odom_frame = msg.header.frame_id       # e.g. "racecar/odom" or "odom"
        base_frame = msg.child_frame_id        # e.g. "racecar/base_link" or "base_link"

        # 定期打印 frame_id 方便调试（每 5 秒一次）
        self.get_logger().info(
            f'/odom frame_id="{odom_frame}" child_frame_id="{base_frame}"',
            throttle_duration_sec=5.0)

        # 1. {odom_frame} → base_link（里程计位姿）
        t1 = TransformStamped()
        t1.header.stamp = now
        t1.header.frame_id = odom_frame
        t1.child_frame_id = 'base_link'
        t1.transform.translation.x = msg.pose.pose.position.x
        t1.transform.translation.y = msg.pose.pose.position.y
        t1.transform.translation.z = msg.pose.pose.position.z
        t1.transform.rotation = msg.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t1)

        # 2. base_link → {base_frame}（恒等别名，仅当与 base_link 不同时）
        if base_frame != 'base_link':
            t2 = TransformStamped()
            t2.header.stamp = now
            t2.header.frame_id = 'base_link'
            t2.child_frame_id = base_frame
            t2.transform.translation.x = 0.0
            t2.transform.translation.y = 0.0
            t2.transform.translation.z = 0.0
            t2.transform.rotation.w = 1.0
            self.tf_broadcaster.sendTransform(t2)

        # 3. base_link → racecar/base_link/laser（偏移 0 0 0.05）
        t_laser = TransformStamped()
        t_laser.header.stamp = now
        t_laser.header.frame_id = 'base_link'
        t_laser.child_frame_id = 'racecar/base_link/laser'
        t_laser.transform.translation.x = 0.0
        t_laser.transform.translation.y = 0.0
        t_laser.transform.translation.z = 0.05
        t_laser.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t_laser)

        # 4. base_link → racecar/base_link/camera（偏移 0 0 0.12）
        t_camera = TransformStamped()
        t_camera.header.stamp = now
        t_camera.header.frame_id = 'base_link'
        t_camera.child_frame_id = 'racecar/base_link/camera'
        t_camera.transform.translation.x = 0.0
        t_camera.transform.translation.y = 0.0
        t_camera.transform.translation.z = 0.12
        t_camera.transform.rotation.w = 1.0
        self.tf_broadcaster.sendTransform(t_camera)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToTF()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
