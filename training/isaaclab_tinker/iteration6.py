"""V6: explicit fore-aft stance/swing progression and yaw reference."""
import gymnasium as gym
import torch
from isaaclab.utils import configclass
from isaaclab.envs.mdp.actions.joint_actions import JointPositionAction
from iteration5 import V5Cfg,V5PPO
from iteration4 import fault_fraction
from robust_task import phase
from reference_v6 import reference
from task import JOINTS

def ref(env):
    sc=phase(env)
    return reference(sc[:,0],sc[:,1],env.command_manager.get_command('base_velocity'))

def reference_reward(env):
    r=env.scene['robot'];ids,_=r.find_joints(JOINTS,preserve_order=True)
    e=(r.data.joint_pos[:,ids]-r.data.default_joint_pos[:,ids]-ref(env)).square().mean(-1)
    return torch.exp(-e/.01)

class V6Action(JointPositionAction):
    def __init__(self,cfg,env):
        super().__init__(cfg,env);self.env=env;self.held=torch.zeros_like(self._raw_actions)
        self.burst=torch.zeros(env.num_envs,device=env.device,dtype=torch.long)
    def process_actions(self,actions):
        total=.25*actions.clamp(-2.,2.)+ref(self.env)/.25
        strength=fault_fraction(self.env)
        new=torch.rand(self.env.num_envs,device=self.env.device)<.002*strength
        self.burst=torch.where(new,torch.randint(2,6,self.burst.shape,device=self.env.device),self.burst)
        lost=(torch.rand(self.env.num_envs,device=self.env.device)<.03*strength)|(self.burst>0)
        self.held=torch.where(lost[:,None],self.held,total);self.burst=(self.burst-1).clamp(min=0)
        super().process_actions(self.held)
    def reset(self,env_ids=None):
        super().reset(env_ids);self.held[env_ids]=0;self.burst[env_ids]=0

@configclass
class V6Cfg(V5Cfg):
    def __post_init__(self):
        super().__post_init__()
        self.actions.joint_pos.class_type=V6Action
        self.rewards.gait_reference.func=reference_reward

@configclass
class V6PPO(V5PPO):
    def __post_init__(self):
        super().__post_init__();self.experiment_name='tinker_robust_v6'

gym.register(id='Tinker-Robust-v6',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':V6Cfg,'rsl_rl_cfg_entry_point':V6PPO})
