import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    from robot_control.model_config import MODEL_PATH_DEFAULT, MODEL_PATH_STEP

    inference_node = Node(
        package='robot_control',
        executable='inference_node',
        name='inference_node',
        output='screen',
        parameters=[{
            'model_path_default': MODEL_PATH_DEFAULT,
            'model_path_step': MODEL_PATH_STEP
        }]
    )

    return LaunchDescription([
        inference_node
    ])
