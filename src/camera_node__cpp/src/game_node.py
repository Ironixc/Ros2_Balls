import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Int32
from cv_bridge import CvBridge
import cv2
import random
import math
from ultralytics import YOLO
from std_msgs.msg import String
import numpy as np
from rcl_interfaces.msg import SetParametersResult
from rclpy.parameter import Parameter

class gamenode(Node):
    def __init__(self):
        super().__init__('game_node')

        path = '/home/ironic/ros2_game/src/camera_node__cpp/Detection/best.pt'
        self.model = YOLO(path)

        self.declare_parameter('balls', 3)
        self.declare_parameter('holdd', 2.0)
        self.declare_parameter('v', 150.0)
        self.declare_parameter('radius', 40)
        self.declare_parameter('marea', 300)
        self.declare_parameter('timer', 120.0)
    
        self.balls_count = self.get_parameter('balls').value
        self.holduration = self.get_parameter('holdd').value
        self.v = self.get_parameter('v').value
        self.radius = self.get_parameter('radius').value
        self.marea = self.get_parameter('marea').value
        self.last_time = self.get_clock().now()
        self.start_time = self.get_clock().now()
        self.duration = self.get_parameter('timer').value

        self.ball_list = []
        for _ in range(self.balls_count):
            random_v = self.v * random.uniform(0.5, 1.5)
            speed_per_frame = random_v / 30.0
            angle = random.uniform(0.4, 1.2)
            vx = speed_per_frame * math.cos(angle) * random.choice([-1, 1])
            vy = speed_per_frame * math.sin(angle) * random.choice([-1, 1])
            self.ball_list.append({
                'x': random.randint(self.radius + 10, 640 - self.radius - 10),
                'y': random.randint(self.radius + 10, 480 - self.radius - 10),
                'vx': vx,
                'vy': vy,
                'timer': 0.0
            })

        self.subscription = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.listener_callback,
            10
        )
        self.debug_pub = self.create_publisher(Image, '/game/debug_image', 10)
        self.score_pub = self.create_publisher(String, '/game/score', 10)
        self.score = 0
        self.br = CvBridge()

        self.add_on_set_parameters_callback(self.parameter_callback)

    def add_new_ball(self):
        random_v = self.v * random.uniform(0.5, 1.5)
        speed_per_frame = random_v / 30.0
        angle = random.uniform(0.4, 1.2)
        vx = speed_per_frame * math.cos(angle) * random.choice([-1, 1])
        vy = speed_per_frame * math.sin(angle) * random.choice([-1, 1])
        self.ball_list.append({
            'x': random.randint(self.radius + 10, 640 - self.radius - 10),
            'y': random.randint(self.radius + 10, 480 - self.radius - 10),
            'vx': vx,
            'vy': vy,
            'timer': 0.0,
            'is_touched': False
        })

    def parameter_callback(self, params):
        for param in params:
            if param.name == 'holdd':
                self.holduration = param.value
                self.get_logger().info(f"Parameter 'holdd' diubah ke: {self.holduration} detik")
            elif param.name == 'v':
                self.v = param.value
                self.get_logger().info(f"Parameter 'v' diubah ke: {self.v}")
            elif param.name == 'radius':
                self.radius = param.value
                self.get_logger().info(f"Parameter 'radius' diubah ke: {self.radius}")
            elif param.name == 'marea':
                self.marea = param.value
                self.get_logger().info(f"Parameter 'marea' diubah ke: {self.marea}")
            elif param.name == 'timer':
                self.duration = param.value
                self.get_logger().info(f"Parameter 'timer' diubah ke: {self.duration} detik")
            elif param.name == 'balls':
                new_count = param.value
                if new_count > len(self.ball_list):
                    for _ in range(new_count - len(self.ball_list)):
                        self.add_new_ball()
                elif new_count < len(self.ball_list):
                    self.ball_list = self.ball_list[:new_count]
                
                self.balls_count = new_count
                self.get_logger().info(f"Jumlah bola ('balls') saat ini: {self.balls_count}")

        return SetParametersResult(successful=True)

    def listener_callback(self, data):
        frame = self.br.imgmsg_to_cv2(data, desired_encoding='bgr8')
        height, width, _ = frame.shape

        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        self.last_time = current_time
        e_time = (current_time - self.start_time).nanoseconds / 1e9

        if e_time >= self.duration:
            self.get_logger().info(f"TIMES UP")
            rclpy.shutdown()
            return

        results = self.model(frame, verbose=False)
        annotated_frame = results[0].plot()

        valid_boxes = []
        for box in results[0].boxes:
            conf = float(box.conf[0])
            if conf > 0.6:
                x1, y1, x2, y2 = map(float, box.xyxy[0])
                valid_boxes.append((x1, y1, x2, y2))
                area = (x2 - x1) * (y2 - y1)
                if area >= self.marea:
                    valid_boxes.append((x1, y1, x2, y2))

        for ball in self.ball_list:
            ball['is_touched'] = False

        for (x1, y1, x2, y2) in valid_boxes:
            box_cx = (x1 + x2) / 2.0
            box_cy = (y1 + y2) / 2.0
            
            closest_ball = None
            min_dist = float('inf')
            
            for ball in self.ball_list: 
                if x1 <= ball['x'] <= x2 and y1 <= ball['y'] <= y2:
                    dist = math.hypot(ball['x'] - box_cx, ball['y'] - box_cy)
                    if dist < min_dist:
                        min_dist = dist
                        closest_ball = ball
                        
            if closest_ball is not None:
                closest_ball['is_touched'] = True

        for ball in self.ball_list:
            ball['x'] += ball['vx']
            ball['y'] += ball['vy']

            if ball['x'] - self.radius <= 0:
                ball['x'], ball['vx'] = self.radius, -ball['vx']
            elif ball['x'] + self.radius >= width:
                ball['x'], ball['vx'] = width - self.radius, -ball['vx']

            if ball['y'] - self.radius <= 0:
                ball['y'], ball['vy'] = self.radius, -ball['vy']
            elif ball['y'] + self.radius >= height:
                ball['y'], ball['vy'] = height - self.radius, -ball['vy']

            if ball['is_touched']:
                ball['timer'] += dt
            else:
                ball['timer'] = 0.0

            if ball['timer'] >= self.holduration:
                self.score += 1

                score_msg = String()
                score_msg.data = f"Score: {self.score}"
                self.score_pub.publish(score_msg)

                
                ball['x'] = random.randint(self.radius + 10, width - self.radius - 10)
                ball['y'] = random.randint(self.radius + 10, height - self.radius - 10)
                random_v = self.v * random.uniform(0.5, 1.5)
                speed_per_frame = random_v / 30.0
                angle = random.uniform(0.4, 1.2)
                ball['vx'] = speed_per_frame * math.cos(angle) * random.choice([-1, 1])
                ball['vy'] = speed_per_frame * math.sin(angle) * random.choice([-1, 1])
                ball['timer'] = 0.0

            center = (int(ball['x']), int(ball['y']))
            cv2.circle(annotated_frame, center, self.radius, (0, 0, 0), -1)

            if ball['timer'] > 0:
                timer_text = f"{ball['timer']:.1f}s"
                cv2.putText(annotated_frame, timer_text, (center[0] - 20, center[1] + 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.putText(annotated_frame, f"Score: {self.score}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

        debug_msg = self.br.cv2_to_imgmsg(annotated_frame, encoding='bgr8')
        self.debug_pub.publish(debug_msg)

        cv2.imshow("wak", annotated_frame)
        if cv2.waitKey(1) == 32:
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = gamenode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()