import numpy as np
import onnxruntime as ort
from collections import deque
import time

class TinkerRealInference:
    def __init__(self, model_path_default, model_path_step, clip_actions=100.0):
        """
        初始化 RDK 推理类
        :param model_path_default: 默认模型路径
        :param model_path_step: 踏步模型路径
        """
        # 1. 初始化两套 ONNX Session
        self.session_default = ort.InferenceSession(model_path_default, providers=['CPUExecutionProvider'])
        self.session_step = ort.InferenceSession(model_path_step, providers=['CPUExecutionProvider'])
    
        # 2. 核心配置参数 (必须与训练时一致)
        self.n_proprio = 39        # 本体感受维度
        self.n_priv_latent = 44    # 特权信息长度 (修正为 44 以满足 660 维总输入)
        self.n_scan = 187          # 扫描数据长度
        self.history_len = 10      # 历史观测长度
        self.num_observations = 660 # 总输入维度 (39 + 44 + 187 + 10*39)
        
        # 3. 归一化系数 (Scales)
        self.obs_scales_ang_vel = 0.25
        self.obs_scales_quat = 1.0
        self.obs_scales_dof_pos = 1.0
        self.obs_scales_dof_vel = 0.05
        self.obs_scales_lin_vel = 2.0  # 用于用户指令
        
        # 4. 机器人控制参数
        self.action_scale = 0.25
        self.clip_actions = float(clip_actions)
        # 默认关节角度 (与 sim2sim_tinker.py 一致)
        self.default_dof_pos = np.array([
            0.0, 0.08, 0.56, -1.12, -0.57,  # 左腿: Yaw, Roll, Pitch, Knee, Ankle
            0.0, -0.08, -0.56, 1.12, 0.57   # 右腿: Yaw, Roll, Pitch, Knee, Ankle
        ], dtype=np.float32)
        
        # 5. 状态缓存
        self.hist_obs = deque(maxlen=self.history_len)
        self.last_action = np.zeros(10, dtype=np.float32)
        self.action_flt = np.zeros(10, dtype=np.float32) # 动作滤波器缓存

        # 6. 硬限位保护 (根据 URDF 设置)
        self.joint_limits_low = np.array([
            -0.7, -0.38, -1.57, -2.35, -1.2,  # 左腿 L0-L4
            -0.7, -0.38, -1.57,  0.0,  -1.2   # 右腿 R0-R4
        ])
        self.joint_limits_high = np.array([
             0.7,  0.46,  1.57,  0.0,   1.2,  # 左腿
             0.7,  0.47,  1.57,  2.35,  1.2   # 右腿
        ])
        
        # 初始化历史缓冲区
        for _ in range(self.history_len):
            self.hist_obs.append(np.zeros(self.n_proprio, dtype=np.float32))

        # 触地后处理状态
        self._prev_target_q = None   # 上一帧实际发送的目标位置
        self._ankle_vel_buffer = deque(maxlen=5)  # 踝关节速度滚动窗口
        self.dt = 0.02  # 50Hz 控制周期

        # 零速踏步抑制
        self._zero_vel_frames = 0   # 连续零速帧计数
        self._step_decay = 1.0      # 动作衰减系数（<1时抑制踏步）

    def quaternion_to_euler(self, quat):
        """ 
        四元数转欧拉角 [roll, pitch, yaw] 
        输入 quat 格式应符合 IMU 输出 (通常为 [x, y, z, w])
        """
        x, y, z, w = quat
        roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x**2 + y**2))
        pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
        yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y**2 + z**2))
        return np.array([roll, pitch, yaw], dtype=np.float32)

    def _swing_smooth(self, target_q):
        """
        触地假阳性后处理 + 零速踏步抑制
        """
        ankle_idx = [4, 9]

        if self._prev_target_q is None:
            self._prev_target_q = target_q.copy()
            return

        dt = self.dt

        ankle_vel = np.abs(target_q[ankle_idx] - self._prev_target_q[ankle_idx]) / dt
        self._ankle_vel_buffer.append(ankle_vel.mean())
        avg_ankle_vel = np.mean(self._ankle_vel_buffer)
        is_quasi_static = avg_ankle_vel < 0.05

        # 零速踏步抑制：踝关节几乎不动且累积超过10帧时，增强衰减
        if is_quasi_static:
            self._zero_vel_frames += 1
        else:
            self._zero_vel_frames = 0
            self._step_decay = min(self._step_decay + 0.05, 1.0)

        if self._zero_vel_frames > 10:
            # 逐渐衰减动作幅度，抑制零速踏步
            self._step_decay = max(self._step_decay - 0.08, 0.05)

        if is_quasi_static:
            alpha_ankle = 0.3
            for idx in ankle_idx:
                target_q[idx] = (self._prev_target_q[idx] * (1 - alpha_ankle) +
                                 target_q[idx] * alpha_ankle)

        max_delta = 0.15
        delta = target_q - self._prev_target_q
        for i in range(10):
            if np.abs(delta[i]) > max_delta:
                target_q[i] = self._prev_target_q[i] + np.sign(delta[i]) * max_delta

        self._prev_target_q = target_q.copy()

    def get_action(self, euler, imu_gyro, joint_pos, joint_vel, cmd_vx, cmd_vy, cmd_dyaw, use_step_model=False):
        """
        核心推理逻辑
        :param euler: 欧拉角 [roll, pitch, yaw]
        :param imu_gyro: IMU 角速度 [wx, wy, wz] (rad/s)
        :param joint_pos: 10个关节的实际位置 (rad)
        :param joint_vel: 10个关节的实际速度 (rad/s)
        :param cmd_vx: 用户前进速度指令 (m/s)
        :param cmd_vy: 用户横移速度指令 (m/s)
        :param cmd_dyaw: 用户转向角速度指令 (rad/s)
        :param use_step_model: 是否强制使用踏步模型
        :return: target_q (10维关节目标位置)
        """
        # A. 构建当前时刻的本体感受观测 (39维)
        obs = np.zeros(self.n_proprio, dtype=np.float32)
        
        # 欧拉角防越界保护 (限制在 -pi 到 pi, 防止 Yaw 连续旋转后数值暴出模型认知范围)
        euler = (euler + np.pi) % (2 * np.pi) - np.pi
        
        # [0:3] 角速度缩放
        obs[0:3] = imu_gyro * self.obs_scales_ang_vel
        # [3:6] 欧拉角缩放
        obs[3:6] = euler * self.obs_scales_quat
        # [6:9] 控制指令缩放
        obs[6] = cmd_vx * self.obs_scales_lin_vel
        obs[7] = cmd_vy * self.obs_scales_lin_vel
        obs[8] = cmd_dyaw * self.obs_scales_ang_vel
        # [9:19] 关节角度偏移缩放
        obs[9:19] = (joint_pos - self.default_dof_pos) * self.obs_scales_dof_pos
        # [19:29] 关节速度缩放
        obs[19:29] = joint_vel * self.obs_scales_dof_vel
        # [29:39] 融入上一时刻动作
        obs[29:39] = self.last_action
        
        # B. 组装输入向量 (对齐训练时的维度排列)
        # 结构: [当前帧(39) | 特权信息+扫描数据(230) | 历史数据(390)]
        policy_input = np.zeros((1, self.num_observations), dtype=np.float32)
        policy_input[0, 0:39] = obs
        # 填充历史数据 (从 deque 中取出 10 帧)
        for i in range(self.history_len):
            start_off = 39 + self.n_priv_latent + self.n_scan # 39 + 44 + 187 = 270
            policy_input[0, start_off + i*39 : start_off + (i+1)*39] = self.hist_obs[i]
            
        # C. ONNX 推理
        session = self.session_step if use_step_model else self.session_default
        ort_inputs = {session.get_inputs()[0].name: policy_input}
        action = session.run(None, ort_inputs)[0][0] 
        
        # D. 动作后处理
        # 1. 裁剪动作范围
        action = np.clip(action, -self.clip_actions, self.clip_actions)

        # 2. 零速踏步抑制（_step_decay 由 _swing_smooth 更新）
        action *= self._step_decay

        # 3. 低通滤波
        flt = 0.1
        action_filtered = self.last_action * flt + action * (1 - flt)
        
        # E. 更新状态机
        self.hist_obs.append(obs)     # 将当前帧加入历史
        self.last_action = action.copy()     # 缓存模型原始输出，供下一帧滤波器使用
        
        # F. 映射到物理量
        # 这里的 action_filtered 才是送往电机的
        target_q = action_filtered * self.action_scale + self.default_dof_pos
        
        # G. 硬限位保护
        target_q = np.clip(target_q, self.joint_limits_low, self.joint_limits_high)

        # H. 触地假阳性后处理
        # 问题：实机无力传感器，电流估算 touch_thr=6N 假阳性高 ->
        # feet_air_time 被重置 -> 踏频被迫加快
        # 解决：检测摆动相，对踝关节加额外平滑
        self._swing_smooth(target_q)

        return target_q

