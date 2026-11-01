"""V5: one reference for action and reward; add weight shift and clearance."""
import gymnasium as gym
import torch
from isaaclab.utils import configclass
from isaaclab.managers import RewardTermCfg as Reward
from isaaclab.envs.mdp.actions.joint_actions import JointPositionAction
from iteration4 import V4Cfg,V4PPO,fault_fraction
from robust_task import phase
from task import JOINTS

def reference_delta(env):
    c=env.command_manager.get_command('base_velocity')
    moving=((c[:,:2].norm(dim=-1)+c[:,2].abs())>.05).float()
    s=phase(env)[:,0];l=s.clamp(min=0)*moving;r=(-s).clamp(min=0)*moving
    delta=torch.zeros((env.num_envs,10),device=env.device)
    delta[:,1]=delta[:,6]=-.08*s*moving
    delta[:,2]=.225*l;delta[:,3]=-.45*l;delta[:,4]=-.225*l
    delta[:,7]=-.225*r;delta[:,8]=.45*r;delta[:,9]=.225*r
    return delta

def reference_reward(env):
    r=env.scene['robot'];ids,_=r.find_joints(JOINTS,preserve_order=True)
    e=(r.data.joint_pos[:,ids]-r.data.default_joint_pos[:,ids]-reference_delta(env)).square().mean(-1)
    return torch.exp(-e/.01)

def clearance_reward(env):
    r=env.scene['robot'];ids,_=r.find_bodies(['L4_Link_ankle','R4_Link_ankle'],preserve_order=True)
    z=r.data.body_pos_w[:,ids,2];s=phase(env)[:,0]
    c=env.command_manager.get_command('base_velocity');moving=(c[:,:2].norm(dim=-1)+c[:,2].abs())>.05
    return torch.exp(-((z[:,0]-z[:,1]-.035*s)/.012).square())*moving

def height_reward(env):return torch.exp(-((env.scene['robot'].data.root_pos_w[:,2]-.30)/.025).square())

def velocity_error(env):
    c=env.command_manager.get_command('base_velocity')
    return (env.scene['robot'].data.root_lin_vel_b[:,:2]-c[:,:2]).norm(dim=-1)

class V5Action(JointPositionAction):
    def __init__(self,cfg,env):
        super().__init__(cfg,env);self.env=env;self.held=torch.zeros_like(self._raw_actions)
        self.burst=torch.zeros(env.num_envs,device=env.device,dtype=torch.long)
    def process_actions(self,actions):
        total=.25*actions.clamp(-2.,2.)+reference_delta(self.env)/.25
        strength=fault_fraction(self.env)
        new=torch.rand(self.env.num_envs,device=self.env.device)<.002*strength
        self.burst=torch.where(new,torch.randint(2,6,self.burst.shape,device=self.env.device),self.burst)
        lost=(torch.rand(self.env.num_envs,device=self.env.device)<.03*strength)|(self.burst>0)
        self.held=torch.where(lost[:,None],self.held,total);self.burst=(self.burst-1).clamp(min=0)
        super().process_actions(self.held)
    def reset(self,env_ids=None):
        super().reset(env_ids);self.held[env_ids]=0;self.burst[env_ids]=0

@configclass
class V5Cfg(V4Cfg):
    def __post_init__(self):
        super().__post_init__()
        self.actions.joint_pos.class_type=V5Action
        self.rewards.gait_reference.func=reference_reward
        self.rewards.gait_reference.weight=2.
        self.rewards.foot_clearance=Reward(func=clearance_reward,weight=2.)
        self.rewards.base_height=Reward(func=height_reward,weight=2.)
        self.rewards.velocity_error=Reward(func=velocity_error,weight=-2.)
        self.rewards.track_lin_vel_xy_exp.params['std']=.08
        # Replace the upstream >0.1m/s-gated air-time term: contact/clearance
        # shaping above applies to slow walking and in-place turning alike.
        self.rewards.feet_air_time=None

@configclass
class V5PPO(V4PPO):
    def __post_init__(self):
        super().__post_init__();self.experiment_name='tinker_robust_v5'

gym.register(id='Tinker-Robust-v5',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':V5Cfg,'rsl_rl_cfg_entry_point':V5PPO})
