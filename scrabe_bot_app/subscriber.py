import time
import rclpy
from rclpy.node import Node
import requests

from std_msgs.msg import Float32, Int32, Bool

class DataSubscriberNode(Node):
    def __init__(self):
        super().__init__('robot_sub_node')
        
        # 1. Konfiguration af API
        self.api_url = "http://172.31.32.1:5280/api/robotdata"
        #self.robot_id = 4 # Eller hent dynamisk
        #self.hospital = "Herlev Hospital"
        #self.afdeling = "Kardiologisk"

        # retry variabel
        self.next_api_attempt_time = 0.0

        # Intern state, gemmer de nyeste værdier
        self.state = {
            'batteri_niveau': 0.0,
            'cpu_temperatur': 0.0,
            'bremse_aktiveringer': 0,
            'ladetid': 0,
            'e_stop': False,
            'løft': 0
        }

        # Opret subscriptions til de relevante topics
        self.create_subscription(Float32, '/robot/battery', self.battery_callback, 10)
        self.create_subscription(Float32, '/robot/cpu_temp', self.cpu_temp_callback, 10)
        self.create_subscription(Int32, '/robot/brake_count', self.brake_callback, 10)
        self.create_subscription(Bool, '/robot/e_stop', self.estop_callback, 10)
        self.create_subscription(Int32, '/robot/charging_time', self.charging_time_callback, 10)
        self.create_subscription(Int32, '/robot/lift', self.lift_callback, 10)        

        # 4. Timer til at udregne tilstand og sende data (f.eks. hvert 2. sekund)
        self.timer = self.create_timer(2.0, self.process_and_send_data)
        self.get_logger().info("Robot Sub Node er startet op.")

    # --- Callbacks til at opdatere intern state ---
    def battery_callback(self, msg):
        self.state['batteri_niveau'] = msg.data

    def cpu_temp_callback(self, msg):
        self.state['cpu_temperatur'] = msg.data

    def brake_callback(self, msg):
        self.state['bremse_aktiveringer'] = msg.data

    def estop_callback(self, msg):
        self.state['e_stop'] = msg.data

    def charging_time_callback(self, msg):
        self.state['ladetid'] = msg.data
    
    def lift_callback(self, msg):
        self.state['løft'] = msg.data

    def process_and_send_data(self):

        test_robotter = [
            {"id": 4, "hospital": "Herlev Hospital", "afdeling": "Kardiologisk"},
            {"id": 5, "hospital": "Herlev Hospital", "afdeling": "Onkologisk"},
            {"id": 6, "hospital": "Rigshospitalet", "afdeling": "Kardiologisk"},
            {"id": 7, "hospital": "OUH", "afdeling": "Pædiatrisk"},
            {"id": 8, "hospital": "OUH", "afdeling": "Kardiologisk"}
        ]

        # Udregn "Sensor" status
        sensor_status = "OK"
        if self.state['cpu_temperatur'] > 60:
            sensor_status = "Fejl"
        elif self.state['cpu_temperatur'] > 50:
            sensor_status = "Advarsel"

        # Udregn "Status" og "Tilstand"
        robot_status = "Online"
        tilstand = "Kører"
        
        if self.state['e_stop']:
            tilstand = "Nødstop"
            sensor_status = "Fejl"
        elif self.state['batteri_niveau'] < 15 and self.state['ladetid'] > 0:
            robot_status = "Oplader"
            tilstand = "Oplader"

        # Dummy logik for opgave (dette kommer måske fra et andet topic som /robot/current_goal?)
        opgave = "Ingen" 

        for robot in test_robotter:

            payload = {
                "RobotId": robot["id"],
                "RobotStatus": robot_status,           
                "BatteryLevel": int(self.state['batteri_niveau']),  
                "CPUTemperature": int(self.state['cpu_temperatur']), 
                "SensorStatus": sensor_status,         
                "RobotTask": opgave,
                "RobotState": tilstand,
                "BreakCount": self.state['bremse_aktiveringer'],
                "ChargingTime": self.state['ladetid'],
                "EStop": self.state['e_stop'],         
                "Lift": self.state['løft'],
                "Hospital": robot["hospital"],
                "Department": robot["afdeling"],
                "Distance": 0 
            }

        # Send data til C# API'en
        try:
            response = requests.post(self.api_url, json=payload, timeout=2.0)
            if response.status_code != 200:
                self.get_logger().warning(f"Fejl ved afsendelse til API: {response.status_code}")
            else:
                self.get_logger().info("Data sendt succesfuldt til C# API!")

        except requests.exceptions.RequestException as e:
            self.get_logger().error(f"Kunne ikke forbinde til C# API: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = DataSubscriberNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()