"""Count VehicleOdometry messages from PX4 over ROS 2 for N seconds. Usage: ros_hz.py TOPIC [SECONDS]"""
import sys
import time
import rclpy
from rclpy.qos import qos_profile_sensor_data
from px4_msgs.msg import VehicleOdometry

topic, dur = sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
rclpy.init()
node = rclpy.create_node('px4_hz_check')
got = []
node.create_subscription(VehicleOdometry, topic, lambda m: got.append(m), qos_profile_sensor_data)
t0 = time.time()
while time.time() - t0 < dur:
    rclpy.spin_once(node, timeout_sec=0.1)
print(f'{topic}: {len(got)} msgs in {dur:.0f} s = {len(got) / dur:.1f} Hz')
if got:
    m = got[-1]
    print(f'last position NED {[round(float(v), 2) for v in m.position]}, timestamp {m.timestamp}')
node.destroy_node()
rclpy.shutdown()
