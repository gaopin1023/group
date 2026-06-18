cat > src/racecar_description/scripts/gps_odom_relay.py << 'EOF'
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry

class GpsOdomRelay(Node):
    def __init__(self):
        super().__init__('gps_odom_relay')
        self.pub = self.create_publisher(Odometry, '/odometry/gps_fixed', 10)
        self.sub = self.create_subscription(Odometry, '/odometry/gps', self.cb, 10)

    def cb(self, msg: Odometry):
        cov = list(msg.pose.covariance)
        cov[0] = 0.5    # x
        cov[7] = 0.5    # y
        cov[14] = 99999.0  # z 不用,设大
        cov[21] = 99999.0
        cov[28] = 99999.0
        cov[35] = 99999.0
        msg.pose.covariance = cov
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = GpsOdomRelay()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
EOF
chmod +x src/racecar_description/scripts/gps_odom_relay.py
