"""Tinker flat-ground baseline for installed Isaac Lab 2.3.2.

Adapted from Isaac Lab H1 flat locomotion configuration (BSD-3-Clause).
This is a new policy contract, not a drop-in replacement for finall.onnx.
"""
from pathlib import Path
import gymnasium as gym
import isaaclab.sim as sim
from isaaclab.assets import ArticulationCfg
from isaaclab.actuators import IdealPDActuatorCfg
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass
from isaaclab_tasks.manager_based.locomotion.velocity.config.h1.flat_env_cfg import H1FlatEnvCfg
from isaaclab_tasks.manager_based.locomotion.velocity.config.h1.agents.rsl_rl_ppo_cfg import H1FlatPPORunnerCfg

JOINTS = ['J_L0','J_L1','J_L2','J_L3','J_L4_ankle','J_R0','J_R1','J_R2','J_R3','J_R4_ankle']
DEFAULT = dict(zip(JOINTS,[0,.08,.56,-1.12,-.57,0,-.08,-.56,1.12,.57]))

@configclass
class TinkerCfg(H1FlatEnvCfg):
    def __post_init__(self):
        super().__post_init__()
        self.scene.num_envs = 1024
        self.scene.terrain.visual_material = None
        self.scene.sky_light.spawn.texture_file = None
        self.scene.robot = ArticulationCfg(
            prim_path='{ENV_REGEX_NS}/Robot',
            spawn=sim.UsdFileCfg(
                usd_path=str(Path(__file__).parent/'assets/usd/tinker.usd'),
                activate_contact_sensors=True,
                rigid_props=sim.RigidBodyPropertiesCfg(disable_gravity=False, max_depenetration_velocity=1.0),
                articulation_props=sim.ArticulationRootPropertiesCfg(enabled_self_collisions=False, solver_position_iteration_count=8, solver_velocity_iteration_count=4),
            ),
            init_state=ArticulationCfg.InitialStateCfg(pos=(0,0,.33),joint_pos=DEFAULT,joint_vel={'.*':0.0}),
            soft_joint_pos_limit_factor=.95,
            actuators={
                'small':IdealPDActuatorCfg(joint_names_expr=['J_[LR]0','J_[LR]4_ankle'],effort_limit=12.0,velocity_limit=20.0,stiffness=15.0,damping=.5),
                'large':IdealPDActuatorCfg(joint_names_expr=['J_[LR][123]'],effort_limit=20.0,velocity_limit=20.0,stiffness=17.0,damping=1.5),
            },
        )
        self.sim.dt=.005
        self.decimation=4
        self.actions.joint_pos.joint_names=JOINTS
        self.actions.joint_pos.preserve_order=True
        self.actions.joint_pos.scale=.25
        # Actor uses only IMU, commands, encoders and action history.
        self.observations.policy.base_lin_vel=None
        self.observations.policy.joint_pos.params={'asset_cfg':SceneEntityCfg('robot',joint_names=JOINTS,preserve_order=True)}
        self.observations.policy.joint_vel.params={'asset_cfg':SceneEntityCfg('robot',joint_names=JOINTS,preserve_order=True)}
        self.observations.policy.base_ang_vel.scale=.25
        self.observations.policy.joint_vel.scale=.05
        self.observations.policy.history_length=5
        self.commands.base_velocity.debug_vis=False
        self.commands.base_velocity.heading_command=False
        self.commands.base_velocity.rel_heading_envs=0.0
        self.commands.base_velocity.rel_standing_envs=.25
        self.commands.base_velocity.ranges.lin_vel_x=(-.1,.35)
        self.commands.base_velocity.ranges.lin_vel_y=(-.05,.05)
        self.commands.base_velocity.ranges.ang_vel_z=(-.5,.5)
        self.events.base_external_force_torque=None
        self.events.physics_material.params['static_friction_range']=(.6,1.0)
        self.events.physics_material.params['dynamic_friction_range']=(.5,.8)
        self.rewards.feet_air_time.params['sensor_cfg']=SceneEntityCfg('contact_forces',body_names='[LR]4_Link_ankle')
        self.rewards.feet_air_time.params['threshold']=.25
        self.rewards.feet_air_time.weight=.5
        self.rewards.feet_slide.params['sensor_cfg']=SceneEntityCfg('contact_forces',body_names='[LR]4_Link_ankle')
        self.rewards.feet_slide.params['asset_cfg']=SceneEntityCfg('robot',body_names='[LR]4_Link_ankle')
        self.rewards.dof_pos_limits.params['asset_cfg']=SceneEntityCfg('robot',joint_names=JOINTS)
        self.rewards.joint_deviation_hip.params['asset_cfg']=SceneEntityCfg('robot',joint_names=['J_[LR]0','J_[LR]1'])
        self.rewards.joint_deviation_arms=None
        self.rewards.joint_deviation_torso=None
        self.rewards.dof_torques_l2.weight=-1e-5
        self.terminations.base_contact.params['sensor_cfg']=SceneEntityCfg('contact_forces',body_names='base_link')

@configclass
class TinkerPPO(H1FlatPPORunnerCfg):
    def __post_init__(self):
        super().__post_init__()
        self.experiment_name='tinker_flat_baseline'
        self.max_iterations=3000
        self.save_interval=100
        self.policy.actor_hidden_dims=[256,128,128]
        self.policy.critic_hidden_dims=[256,128,128]

gym.register(id='Tinker-Flat-v0',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':TinkerCfg,'rsl_rl_cfg_entry_point':TinkerPPO})
