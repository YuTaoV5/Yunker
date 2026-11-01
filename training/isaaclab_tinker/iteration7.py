"""V7: 1ms physics, teacher-cloned 195D actor, phase-free robust PPO."""
import gymnasium as gym
import torch
from isaaclab.utils import configclass
from isaaclab.managers import RewardTermCfg as Reward
from isaaclab.envs.mdp.actions.joint_actions import JointPositionAction
from iteration4 import V4Cfg,V4PPO,fault_fraction
from task import JOINTS

class V7Action(JointPositionAction):
    def __init__(self,cfg,env):
        super().__init__(cfg,env);self.env=env;self.held=torch.zeros_like(self._raw_actions)
        self.burst=torch.zeros(env.num_envs,device=env.device,dtype=torch.long)
    def process_actions(self,actions):
        strength=fault_fraction(self.env)
        new=torch.rand(self.env.num_envs,device=self.env.device)<.002*strength
        self.burst=torch.where(new,torch.randint(2,6,self.burst.shape,device=self.env.device),self.burst)
        lost=(torch.rand(self.env.num_envs,device=self.env.device)<.03*strength)|(self.burst>0)
        self.held=torch.where(lost[:,None],self.held,actions)
        self.burst=(self.burst-1).clamp(min=0);super().process_actions(self.held)
    def reset(self,env_ids=None):
        super().reset(env_ids);self.held[env_ids]=0;self.burst[env_ids]=0

def commanded_progress(env):
    c=env.command_manager.get_command('base_velocity')[:,:2]
    v=env.scene['robot'].data.root_lin_vel_b[:,:2]
    return ((v*c).sum(-1)/(c.square().sum(-1)+1e-6)).clamp(-1.,1.)*(c.norm(dim=-1)>.05)

def single_support(env):
    s=env.scene['contact_forces'];ids,_=s.find_bodies(['L4_Link_ankle','R4_Link_ankle'],preserve_order=True)
    contact=s.data.net_forces_w[:,ids,:].norm(dim=-1)>1.
    c=env.command_manager.get_command('base_velocity')
    return (contact.sum(-1)==1).float()*((c[:,:2].norm(dim=-1)+c[:,2].abs())>.05)

def velocity_error(env):
    c=env.command_manager.get_command('base_velocity')
    return (env.scene['robot'].data.root_lin_vel_b[:,:2]-c[:,:2]).norm(dim=-1)

@configclass
class V7Cfg(V4Cfg):
    def __post_init__(self):
        super().__post_init__()
        self.sim.dt=.001;self.decimation=20;self.sim.render_interval=20
        self.scene.contact_forces.update_period=.001
        for a in self.scene.robot.actuators.values():a.min_delay=0;a.max_delay=30
        self.observations.policy.gait_phase=None
        self.actions.joint_pos.class_type=V7Action
        lows=[-.7,-.38,-1.57,-2.35,-1.2,-.7,-.38,-1.57,0.,-1.2]
        highs=[.7,.46,1.57,0.,1.2,.7,.47,1.57,2.35,1.2]
        self.actions.joint_pos.clip={name:(lo,hi) for name,lo,hi in zip(JOINTS,lows,highs)}
        self.rewards.gait_contact=None;self.rewards.gait_reference=None;self.rewards.stuck_contact=None;self.rewards.feet_air_time=None
        self.rewards.progress=Reward(func=commanded_progress,weight=2.)
        self.rewards.single_support=Reward(func=single_support,weight=1.5)
        self.rewards.velocity_error=Reward(func=velocity_error,weight=-2.)
        self.rewards.track_lin_vel_xy_exp.params['std']=.08
        self.commands.base_velocity.ranges.lin_vel_x=(-.1,.3)
        self.commands.base_velocity.ranges.ang_vel_z=(-.3,.3)
        self.commands.base_velocity.rel_standing_envs=.2

@configclass
class V7PPO(V4PPO):
    def __post_init__(self):
        super().__post_init__();self.experiment_name='tinker_robust_v7'
        self.policy.init_noise_std=.08;self.algorithm.learning_rate=1e-4;self.algorithm.entropy_coef=.001

gym.register(id='Tinker-Robust-v7',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':V7Cfg,'rsl_rl_cfg_entry_point':V7PPO})
