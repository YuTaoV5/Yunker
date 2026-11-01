from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    from robot_control.model_config import MODEL_PATH_DEFAULT, MODEL_PATH_STEP

    return LaunchDescription([
        Node(
            package='robot_control',
            executable='web_teleop',
            name='web_teleop',
            output='screen'
        ),

        Node(
            package='robot_control',
            executable='inference_node',
            name='inference_node',
            output='screen',
            parameters=[{
                'model_path_default': MODEL_PATH_DEFAULT,
                'model_path_step': MODEL_PATH_STEP
            }]
        )
    ])
