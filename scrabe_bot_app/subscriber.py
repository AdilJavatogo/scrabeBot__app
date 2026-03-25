import os
import time
import rclpy
from rclpy.node import Node
import requests

from std_msgs.msg import Float32, Int32, Bool, String

class DataSubscriberNode(Node):
    def __init__(self):
        super().__init__('robot_sub_node')
        
        # 1. Konfiguration af API
                                                    #self.api_url = "http://172.31.32.1:5280/api/robotdata"
        #self.robot_id = 4 # Eller hent dynamisk
        #self.hospital = "Herlev Hospital"
        #self.afdeling = "Kardiologisk"
        
        # Konfiguration af API, læser fra docker-compose miljøvariabler, med fallback til localhost
        api_base_url = os.environ.get("ROBOMONITOR_API_URL", "http://host.docker.internal:5280") # skal nok laves om det tailscale ip senere
        self.api_url = f"{api_base_url}/api/robotdata"

        self.has_received_data = False

        self.request_count = 0
        self.max_requests = 300

        # retry variabel
        self.next_api_attempt_time = 0.0 # muligvis slet, da det virker allerede

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
        self.create_subscription(Float32, '/robot/distance', self.distance_callback, 10)
        self.create_subscription(String, '/robot/sensor_status', self.sensor_status_callback, 10)
        self.create_subscription(String, '/robot/state', self.robot_state_callback, 10)
        self.create_subscription(String, '/robot/task', self.robot_task_callback, 10)
        self.create_subscription(String, '/robot/status', self.robot_status_callback, 10)
        self.create_subscription(Float32, '/robot/battery', self.battery_callback, 10)
        self.create_subscription(Float32, '/robot/cpu_temp', self.cpu_temp_callback, 10)
        self.create_subscription(Int32, '/robot/brake_count', self.brake_callback, 10)
        self.create_subscription(Bool, '/robot/e_stop', self.estop_callback, 10)
        self.create_subscription(Int32, '/robot/charging_time', self.charging_time_callback, 10)
        self.create_subscription(Int32, '/robot/lift', self.lift_callback, 10)        

        # Timer til at udregne tilstand og sende data (f.eks. hvert 2. sekund)
        self.timer = self.create_timer(2.0, self.process_and_send_data)
        self.get_logger().info("Robot Sub Node er startet op.")

    # --- Callbacks til at opdatere intern state ---

    def distance_callback(self, msg):
        self.state['distance'] = msg.data
        self.has_received_data = True

    def sensor_status_callback(self, msg):
        self.state['sensor_status'] = msg.data
        self.has_received_data = True

    def robot_state_callback(self, msg):
        self.state['robot_state'] = msg.data
        self.has_received_data = True

    def robot_task_callback(self, msg):
        self.state['robot_task'] = msg.data
        self.has_received_data = True

    def robot_status_callback(self, msg):
        self.state['robot_status'] = msg.data
        self.has_received_data = True

    def battery_callback(self, msg):
        self.state['batteri_niveau'] = msg.data
        self.has_received_data = True

    def cpu_temp_callback(self, msg):
        self.state['cpu_temperatur'] = msg.data
        self.has_received_data = True

    def brake_callback(self, msg):
        self.state['bremse_aktiveringer'] = msg.data
        self.has_received_data = True

    def estop_callback(self, msg):
        self.state['e_stop'] = msg.data
        self.has_received_data = True

    def charging_time_callback(self, msg):
        self.state['ladetid'] = msg.data
        self.has_received_data = True
    
    def lift_callback(self, msg):
        self.state['løft'] = msg.data
        self.has_received_data = True

    def process_and_send_data(self):

        if self.request_count >= self.max_requests:
            self.get_logger().info(f"Grænsen på {self.max_requests} requests er nået. Stopper dataafsendelse.")
            self.timer.cancel()
            return

        # Send kun, hvis vi har modtaget data fra ROS-topics mindst én gang
        if not self.has_received_data:
            return
        
        # API-nøgle, læser fra docker compose miljøvariabel, med fallback til en dummy værdi
        # self.api_key = os.environ.get("ROBOT_API_KEY", "MANGLER_NØGLE")

        test_robotter = [
            {"id": 4, "hospital": "Herlev Hospital", "afdeling": "Kardiologisk", "api_key": "herlev_ghi789"},
            {"id": 5, "hospital": "Herlev Hospital", "afdeling": "Onkologisk", "api_key": "herlev_xyz123"},
            {"id": 6, "hospital": "Rigshospitalet", "afdeling": "Kardiologisk"},
            {"id": 7, "hospital": "OUH", "afdeling": "Pædiatrisk"},
            {"id": 8, "hospital": "OUH", "afdeling": "Kardiologisk", "api_key": "ouh_abc456"}
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

            if self.request_count >= self.max_requests:
                break

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

            headers = {
                "X-API-KEY": robot.get("api_key", "MANGLER_NØGLE"),
                "Content-Type": "application/json"
            }

            # Send data til C# API'en
            try:
                response = requests.post(self.api_url, json=payload, headers=headers, timeout=2.0)
                
                if response.status_code == 200:
                    self.request_count += 1
                    self.get_logger().info(f"Data sendt succesfuldt! ({self.request_count}/{self.max_requests})")
                elif response.status_code == 403:
                    self.get_logger().error("Afvist: Ugyldig API nøgle (403 Forbidden)")
                elif response.status_code == 401:
                    self.get_logger().error("Afvist: Mangler API nøgle (401 Unauthorized)")
                else:
                    self.get_logger().warning(f"Fejl fra C# API. Status kode: {response.status_code}")

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