import random
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Int32, Bool, String

class DataPublisherNode(Node):
    def __init__(self):
        super().__init__('data_publisher_node')
        
        # Opret publishers for de relevante topics
        self.distance_pub = self.create_publisher(Int32, '/robot/distance', 10)
        self.sensor_status_pub = self.create_publisher(String, '/robot/sensor_status', 10)
        self.robot_state_pub = self.create_publisher(String, '/robot/state', 10)
        self.robot_task_pub = self.create_publisher(String, '/robot/task', 10)
        self.robot_status_pub = self.create_publisher(String, '/robot/status', 10)
        self.battery_pub = self.create_publisher(Float32, '/robot/battery', 10)
        self.cpu_temp_pub = self.create_publisher(Float32, '/robot/cpu_temp', 10)
        self.brake_pub = self.create_publisher(Int32, '/robot/brake_count', 10)
        self.estop_pub = self.create_publisher(Bool, '/robot/e_stop', 10)
        self.lift_pub = self.create_publisher(Int32, '/robot/lift', 10)
        self.charge_time_pub = self.create_publisher(Int32, '/robot/charging_time', 10)
        
        self.timer = self.create_timer(5.0, self.publish_data)

        self.internal_brake_count = 0

        self.get_logger().info("Publisher Node er startet op.")

    # Logik til at generere og publicere data
    def publish_data(self):

        status_msg = String()
        status_msg.data = random.choice(["OK", "Advarsel", "Fejl"])
        self.robot_status_pub.publish(status_msg)

        state_msg = String()
        state_msg.data = random.choice(["Ledig", "Kører", "Oplader"])
        self.robot_state_pub.publish(state_msg)

        task_msg = String()
        task_msg.data = random.choice(["Ingen opgave", "Transporterer", "Lader"])
        self.robot_task_pub.publish(task_msg)

        distance_msg = Int32()
        distance_msg.data = random.randint(0, 1000)
        self.distance_pub.publish(distance_msg)

        bat_msg = Float32()
        bat_msg.data = random.uniform(20.0, 100.0)
        self.battery_pub.publish(bat_msg)

        cpu_msg = Float32()
        cpu_msg.data = random.uniform(30.0, 70.0)
        self.cpu_temp_pub.publish(cpu_msg)

        self.internal_brake_count += random.randint(0, 500)
        brake_msg = Int32()
        brake_msg.data = self.internal_brake_count
        self.brake_pub.publish(brake_msg)

        estop_msg = Bool()
        estop_msg.data = False
        self.estop_pub.publish(estop_msg)

        lift_msg = Int32()
        lift_msg.data = random.randint(0, 1)
        self.lift_pub.publish(lift_msg)

        charge_time_msg = Int32()
        charge_time_msg.data = random.randint(0, 120)
        self.charge_time_pub.publish(charge_time_msg)

def main(args=None):
    rclpy.init(args=args)
    node = DataPublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()