#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState, Imu, Joy
from std_srvs.srv import Empty
import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

html_content = """<!DOCTYPE html>
<html>
<head>
    <title>双足机器人控制台</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            font-size: 24px;
            margin-bottom: 20px;
            color: #00d4ff;
        }
        .panel {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .panel-title {
            font-size: 14px;
            color: #888;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 20px;
            background: rgba(0,212,255,0.1);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #27ae60;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .state-display {
            font-size: 18px;
            font-weight: bold;
            color: #00d4ff;
        }
        .control-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        .btn {
            padding: 20px 16px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.15s;
            text-align: center;
            user-select: none;
            -webkit-tap-highlight-color: transparent;
            -webkit-user-select: none;
            touch-action: manipulation;
        }
        .btn:active, .btn.pressed {
            transform: scale(0.95);
            filter: brightness(1.2);
        }
        .btn-stand {
            background: linear-gradient(145deg, #27ae60, #2ecc71);
            color: white;
            box-shadow: 0 4px 15px rgba(39,174,96,0.3);
        }
        .btn-stand:hover { background: linear-gradient(145deg, #2ecc71, #27ae60); }
        .btn-squat {
            background: linear-gradient(145deg, #e67e22, #f39c12);
            color: white;
            box-shadow: 0 4px 15px rgba(230,126,34,0.3);
        }
        .btn-squat:hover { background: linear-gradient(145deg, #f39c12, #e67e22); }
        .btn-inference {
            background: linear-gradient(145deg, #3498db, #2980b9);
            color: white;
            box-shadow: 0 4px 15px rgba(52,152,219,0.3);
        }
        .btn-inference:hover { background: linear-gradient(145deg, #2980b9, #3498db); }
        .btn-stop {
            background: linear-gradient(145deg, #e74c3c, #c0392b);
            color: white;
            box-shadow: 0 4px 15px rgba(231,76,60,0.3);
        }
        .btn-stop:hover { background: linear-gradient(145deg, #c0392b, #e74c3c); }
        .btn-step {
            background: linear-gradient(145deg, #9b59b6, #8e44ad);
            color: white;
            box-shadow: 0 4px 15px rgba(155,89,182,0.3);
        }
        .btn-step:hover { background: linear-gradient(145deg, #8e44ad, #9b59b6); }
        .btn-calibrate {
            background: linear-gradient(145deg, #7f8c8d, #95a5a6);
            color: white;
            box-shadow: 0 4px 15px rgba(127,140,141,0.3);
        }
        .btn-calibrate:hover { background: linear-gradient(145deg, #95a5a6, #7f8c8d); }
        .btn-stop:active, .btn-calibrate:active { transform: scale(0.95); }

        .dpad {
            display: grid;
            grid-template-columns: repeat(3, 70px);
            grid-template-rows: repeat(3, 70px);
            gap: 5px;
            justify-content: center;
            margin-top: 15px;
        }
        .dpad-btn {
            border: none;
            border-radius: 12px;
            background: rgba(255,255,255,0.15);
            color: white;
            font-size: 24px;
            cursor: pointer;
            transition: all 0.15s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .dpad-btn:active {
            background: rgba(0,212,255,0.5);
            transform: scale(0.9);
        }
        .dpad-center {
            background: rgba(255,255,255,0.05);
            cursor: default;
        }

        .data-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .data-card {
            background: rgba(0,0,0,0.3);
            border-radius: 12px;
            padding: 15px;
        }
        .data-card h3 {
            font-size: 12px;
            color: #888;
            margin-bottom: 10px;
            text-transform: uppercase;
        }
        .data-row {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .data-row:last-child { border-bottom: none; }
        .data-label { color: #aaa; font-size: 13px; }
        .data-value { color: #00d4ff; font-weight: 600; font-size: 13px; font-family: monospace; }
        .joint-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            margin-top: 10px;
        }
        .joint-item {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 8px 4px;
            text-align: center;
        }
        .joint-item .label { font-size: 10px; color: #666; }
        .joint-item .value { font-size: 12px; color: #00d4ff; font-family: monospace; margin-top: 4px; }

        .speed-control {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 10px;
        }
        .speed-control label { color: #888; font-size: 13px; }
        .speed-control input[type="range"] {
            flex: 1;
            height: 6px;
            -webkit-appearance: none;
            background: rgba(255,255,255,0.2);
            border-radius: 3px;
        }
        .speed-control input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            background: #00d4ff;
            border-radius: 50%;
            cursor: pointer;
        }
        .speed-value { color: #00d4ff; font-weight: bold; min-width: 40px; text-align: right; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🦾 双足机器人控制台</h1>

        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span>已连接</span>
            </div>
            <div class="state-display" id="robotState">待机中</div>
        </div>

        <div class="panel">
            <div class="panel-title">姿态控制</div>
            <div class="control-grid">
                <button class="btn btn-stand" onclick="sendCmd('stand')">🏛️ 站立</button>
                <button class="btn btn-squat" onclick="sendCmd('squat')">🧎 蹲下</button>
                <button class="btn btn-inference" onclick="sendCmd('inference')">🧠 推理</button>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">运动控制</div>
            <div class="dpad">
                <div></div>
                <button class="dpad-btn" onpointerdown="dpadDown('w')" onpointerup="dpadUp()" onpointerleave="dpadUp()">▲</button>
                <div></div>
                <button class="dpad-btn" onpointerdown="dpadDown('a')" onpointerup="dpadUp()" onpointerleave="dpadUp()">◀</button>
                <div class="dpad-btn dpad-center">●</div>
                <button class="dpad-btn" onpointerdown="dpadDown('d')" onpointerup="dpadUp()" onpointerleave="dpadUp()">▶</button>
                <div></div>
                <button class="dpad-btn" onpointerdown="dpadDown('q')" onpointerup="dpadUp()" onpointerleave="dpadUp()">↶</button>
                <button class="dpad-btn" onpointerdown="dpadDown('e')" onpointerup="dpadUp()" onpointerleave="dpadUp()">↷</button>
            </div>
            <div class="speed-control">
                <label>速度</label>
                <input type="range" min="0.1" max="1.0" step="0.1" value="0.5" id="speedSlider" oninput="updateSpeed()">
                <span class="speed-value" id="speedValue">0.5</span>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">特殊功能</div>
            <div class="control-grid">
                <button class="btn btn-step" onclick="sendCmd('step')">🔄 踏步模式</button>
                <button class="btn btn-stop" onclick="sendCmd('stop')">⏹ 停止移动</button>
                <button class="btn btn-calibrate" onclick="sendCmd('calibrate')">⚙️ 电机标定</button>
            </div>
        </div>

        <div class="panel">
            <div class="panel-title">实时数据</div>
            <div class="data-grid">
                <div class="data-card">
                    <h3>IMU 姿态</h3>
                    <div class="data-row"><span class="data-label">Roll</span><span class="data-value" id="imuRoll">0.00</span></div>
                    <div class="data-row"><span class="data-label">Pitch</span><span class="data-value" id="imuPitch">0.00</span></div>
                    <div class="data-row"><span class="data-label">Yaw</span><span class="data-value" id="imuYaw">0.00</span></div>
                </div>
                <div class="data-card">
                    <h3>IMU 角速度</h3>
                    <div class="data-row"><span class="data-label">ωx</span><span class="data-value" id="imuGx">0.00</span></div>
                    <div class="data-row"><span class="data-label">ωy</span><span class="data-value" id="imuGy">0.00</span></div>
                    <div class="data-row"><span class="data-label">ωz</span><span class="data-value" id="imuGz">0.00</span></div>
                </div>
            </div>
            <div class="data-card" style="margin-top:15px;">
                <h3>关节位置</h3>
                <div class="joint-grid">
                    <div class="joint-item"><div class="label">L0</div><div class="value" id="j0">0.00</div></div>
                    <div class="joint-item"><div class="label">L1</div><div class="value" id="j1">0.00</div></div>
                    <div class="joint-item"><div class="label">L2</div><div class="value" id="j2">0.00</div></div>
                    <div class="joint-item"><div class="label">L3</div><div class="value" id="j3">0.00</div></div>
                    <div class="joint-item"><div class="label">L4</div><div class="value" id="j4">0.00</div></div>
                    <div class="joint-item"><div class="label">R0</div><div class="value" id="j5">0.00</div></div>
                    <div class="joint-item"><div class="label">R1</div><div class="value" id="j6">0.00</div></div>
                    <div class="joint-item"><div class="label">R2</div><div class="value" id="j7">0.00</div></div>
                    <div class="joint-item"><div class="label">R3</div><div class="value" id="j8">0.00</div></div>
                    <div class="joint-item"><div class="label">R4</div><div class="value" id="j9">0.00</div></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSpeed = 0.5;
        let currentState = 'IDLE';
        let lastCmdTime = 0;
        let dpadKey = null;

        function sendCmd(cmd) {
            const now = Date.now();
            if (now - lastCmdTime < 100) return;
            lastCmdTime = now;
            fetch('/cmd?k=' + cmd).catch(() => {});
        }

        function dpadDown(key) {
            dpadKey = key;
            sendCmd(key);
        }

        function dpadUp() {
            if (dpadKey) {
                sendCmd('s');
                dpadKey = null;
            }
        }

        function updateSpeed() {
            currentSpeed = document.getElementById('speedSlider').value;
            document.getElementById('speedValue').textContent = currentSpeed;
        }

        function updateIMU(data) {
            document.getElementById('imuRoll').textContent = data.roll.toFixed(2);
            document.getElementById('imuPitch').textContent = data.pitch.toFixed(2);
            document.getElementById('imuYaw').textContent = data.yaw.toFixed(2);
            document.getElementById('imuGx').textContent = data.gx.toFixed(2);
            document.getElementById('imuGy').textContent = data.gy.toFixed(2);
            document.getElementById('imuGz').textContent = data.gz.toFixed(2);
        }

        function updateJoints(data) {
            for (let i = 0; i < 10; i++) {
                const el = document.getElementById('j' + i);
                if (el && data[i] !== undefined) {
                    el.textContent = data[i].toFixed(2);
                }
            }
        }

        function updateState(state) {
            currentState = state;
            const stateMap = {
                'IDLE': '待机中',
                'SQUAT': '蹲下',
                'TRANSITIONING': '过渡中',
                'STAND': '站立',
                'INFERENCE': '推理中'
            };
            document.getElementById('robotState').textContent = stateMap[state] || state;
        }

        function pollData() {
            fetch('/data').then(r => r.json()).then(data => {
                if (data.imu) updateIMU(data.imu);
                if (data.joints) updateJoints(data.joints);
                if (data.state) updateState(data.state);
            }).catch(() => {});
        }

        setInterval(pollData, 100);

        document.addEventListener('keydown', function(e) {
            if (e.repeat) return;
            const k = e.key.toLowerCase();
            if (['w','a','d','q','e'].includes(k) && dpadKey !== k) sendCmd(k);
        });
        document.addEventListener('keyup', function(e) {
            const k = e.key.toLowerCase();
            if (['w','a','d','q','e'].includes(k)) {
                sendCmd('s');
            }
        });

        document.addEventListener('touchmove', function(e) { e.preventDefault(); }, {passive: false});
    </script>
</body>
</html>"""


class WebTeleopNode(Node):
    def __init__(self):
        super().__init__('web_teleop')
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.joy_pub = self.create_publisher(Joy, 'joy', 10)
        self.speed = 0.45
        self.turn = 1.3
        self.calibration_client = self.create_client(Empty, 'set_zero_position')

        self.latest_imu_roll = 0.0
        self.latest_imu_pitch = 0.0
        self.latest_imu_yaw = 0.0
        self.latest_imu_gx = 0.0
        self.latest_imu_gy = 0.0
        self.latest_imu_gz = 0.0
        self.latest_joints = [0.0] * 10
        self.current_state = 'IDLE'

        self.create_subscription(Imu, 'imu/data', self.imu_callback, 10)
        self.create_subscription(JointState, 'joint_states', self.joint_callback, 10)

    def imu_callback(self, msg):
        import math
        q = msg.orientation
        sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
        cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2 * (q.w * q.y - q.z * q.x)
        if abs(sinp) >= 1:
            pitch = math.sign(sinp) * math.pi / 2
        else:
            pitch = math.asin(sinp)

        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        self.latest_imu_roll = roll
        self.latest_imu_pitch = pitch
        self.latest_imu_yaw = yaw
        self.latest_imu_gx = msg.angular_velocity.x
        self.latest_imu_gy = msg.angular_velocity.y
        self.latest_imu_gz = msg.angular_velocity.z

    def joint_callback(self, msg):
        if len(msg.position) >= 10:
            self.latest_joints = list(msg.position[:10])

    def send_cmd(self, key):
        twist = Twist()
        x, y, th = 0.0, 0.0, 0.0
        joy_buttons = [0, 0, 0, 0, 0]
        publish_joy = False

        if key == 'w': x = self.speed
        elif key == 'x': x = -self.speed
        elif key == 'a': y = self.speed
        elif key == 'd': y = -self.speed
        elif key == 'q': th = self.turn
        elif key == 'e': th = -self.turn
        elif key == 's': pass

        elif key == 'stand':
            joy_buttons[0] = 1
            publish_joy = True
            self._auto_release_joy(joy_buttons)

        elif key == 'squat':
            joy_buttons[0] = 1
            publish_joy = True
            self._auto_release_joy(joy_buttons)

        elif key == 'inference':
            joy_buttons[1] = 1
            publish_joy = True
            self._auto_release_joy(joy_buttons)

        elif key == 'step':
            joy_buttons[2] = 1
            publish_joy = True
            self._auto_release_joy(joy_buttons)

        elif key == 'stop':
            twist.linear.x = 0.0
            twist.linear.y = 0.0
            twist.angular.z = 0.0
            self.cmd_pub.publish(twist)
            return

        elif key == 'calibrate':
            if self.calibration_client.wait_for_service(timeout_sec=1.0):
                req = Empty.Request()
                self.calibration_client.call_async(req)
                self.get_logger().info('Calibration command sent')
            else:
                self.get_logger().warn('Calibration service not available')
            return

        if key in ['w', 'x', 'a', 'd', 'q', 'e', 's']:
            twist.linear.x = float(x)
            twist.linear.y = float(y)
            twist.angular.z = float(th)
            self.cmd_pub.publish(twist)

        if publish_joy:
            joy_msg = Joy()
            joy_msg.buttons = joy_buttons
            joy_msg.axes = [0.0] * 8
            self.joy_pub.publish(joy_msg)

    def _auto_release_joy(self, buttons):
        def release():
            joy_m = Joy()
            joy_m.buttons = [0, 0, 0, 0, 0]
            joy_m.axes = [0.0] * 8
            self.joy_pub.publish(joy_m)
        threading.Timer(0.05, release).start()

    def get_data(self):
        return {
            'imu': {
                'roll': self.latest_imu_roll,
                'pitch': self.latest_imu_pitch,
                'yaw': self.latest_imu_yaw,
                'gx': self.latest_imu_gx,
                'gy': self.latest_imu_gy,
                'gz': self.latest_imu_gz,
            },
            'joints': self.latest_joints,
            'state': self.current_state
        }


ros_node = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        elif parsed.path == '/cmd':
            qs = parse_qs(parsed.query)
            key = qs.get('k', [''])[0]
            if ros_node and key:
                ros_node.send_cmd(key)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
        elif parsed.path == '/data':
            if ros_node:
                data = ros_node.get_data()
            else:
                data = {'imu': {}, 'joints': [], 'state': 'IDLE'}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        self.send_response(404)
        self.end_headers()


def run_server():
    server = HTTPServer(('0.0.0.0', 8080), Handler)
    server.serve_forever()


def main(args=None):
    global ros_node
    rclpy.init(args=args)
    ros_node = WebTeleopNode()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    ros_node.get_logger().info('=' * 60)
    ros_node.get_logger().info(' WEB TELEOP SERVER STARTED!')
    ros_node.get_logger().info(' >> OPEN YOUR BROWSER AND GO TO: http://<IP>:8080')
    ros_node.get_logger().info('=' * 60)

    try:
        rclpy.spin(ros_node)
    except KeyboardInterrupt:
        pass
    finally:
        ros_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
