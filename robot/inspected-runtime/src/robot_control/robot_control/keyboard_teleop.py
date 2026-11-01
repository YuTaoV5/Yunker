#!/usr/bin/env python3

import sys
import select
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

BUTTON_A = 0
BUTTON_B = 1
BUTTON_X = 2

msg = """
Legged Robot Keyboard Control
---------------------------
Movement commands:
        w
   a    s    d
        x

q/e : turn left/right
s   : force stop (zero velocity)

State Control commands:
1 : Toggle Squat/Stand (Simulates Joy A)
   - IDLE -> SQUAT -> STAND -> SQUAT
2 : Start/Stop Inference (Simulates Joy B)
   - STAND -> INFERENCE -> STAND
3 : Toggle Step-in-place (Simulates Joy X)
   - Only effective during INFERENCE mode

CTRL-C to quit
"""

def getKey(settings):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main():
    settings = termios.tcgetattr(sys.stdin)

    rclpy.init()
    node = rclpy.create_node('keyboard_teleop')
    cmd_pub = node.create_publisher(Twist, 'cmd_vel', 10)
    joy_pub = node.create_publisher(Joy, 'joy', 10)

    x, y, th = 0.0, 0.0, 0.0
    speed, turn = 0.5, 1.0

    print(msg)

    try:
        while rclpy.ok():
            key = getKey(settings)
            
            button_pressed = -1
            if key:
                if key == 'w':
                    x = speed; y = 0.0; th = 0.0
                elif key == 's':
                    x = 0.0; y = 0.0; th = 0.0
                elif key == 'x':
                    x = -speed; y = 0.0; th = 0.0
                elif key == 'a':
                    x = 0.0; y = speed; th = 0.0
                elif key == 'd':
                    x = 0.0; y = -speed; th = 0.0
                elif key == 'q':
                    x = 0.0; y = 0.0; th = turn
                elif key == 'e':
                    x = 0.0; y = 0.0; th = -turn
                elif key == '1':
                    button_pressed = BUTTON_A
                    print("\r[Input] Pressed 1: Joy A (Squat/Stand)")
                elif key == '2':
                    button_pressed = BUTTON_B
                    print("\r[Input] Pressed 2: Joy B (Inference Mode)")
                elif key == '3':
                    button_pressed = BUTTON_X
                    print("\r[Input] Pressed 3: Joy X (Step-in-place)")
                elif key == '\x03':
                    break

            twist = Twist()
            twist.linear.x = float(x)
            twist.linear.y = float(y)
            twist.angular.z = float(th)
            cmd_pub.publish(twist)

            joy_msg = Joy()
            joy_msg.axes = [0.0] * 8
            if button_pressed == BUTTON_A:
                joy_msg.buttons = [1, 0, 0]
                joy_pub.publish(joy_msg)
                joy_msg.buttons = [0, 0, 0]
                joy_pub.publish(joy_msg)
            elif button_pressed == BUTTON_B:
                joy_msg.buttons = [0, 1, 0]
                joy_pub.publish(joy_msg)
                joy_msg.buttons = [0, 0, 0]
                joy_pub.publish(joy_msg)
            elif button_pressed == BUTTON_X:
                joy_msg.buttons = [0, 0, 1]
                joy_pub.publish(joy_msg)
                joy_msg.buttons = [0, 0, 0]
                joy_pub.publish(joy_msg)
            else:
                joy_msg.buttons = [0, 0, 0]
                joy_pub.publish(joy_msg)

    except Exception as e:
        print(e)
    finally:
        twist = Twist()
        cmd_pub.publish(twist)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
