"""V4: phase-conditioned reference targets plus learned residual corrections.

Reference amplitude and fault probability use a documented training curriculum.
Deployment must use the same reference generator; this is not a v3 drop-in.
"""
import gymnasium as gym
import torch
from isaaclab.utils import configclass
import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp
from iteration3 import V3Cfg,V3PPO,stale_measurement
from robust_task import phase

def reference_actions(env):
    c=env.command_manager.get_command('base_velocity')
    moving=(c[:,:2].norm(dim=-1)+c[:,2].abs())>.05
    s=phase(env)[:,0];l=torch.clamp(s,min=0)*moving;r=torch.clamp(-s,min=0)*moving
    a=torch.zeros((env.num_envs,10),device=env.device)
    # 0.45 rad knee flexion, half counter-motion at hip and ankle.
    a[:,2]=.225*l;a[:,3]=-.45*l;a[:,4]=-.225*l
    a[:,7]=-.225*r;a[:,8]=.45*r;a[:,9]=.225*r
    return a/.25

def fault_fraction(env):
    override=getattr(env,'tinker_fault_override',None)
    if override is not None:return float(override)
    # Start physically randomized but with good communication for gait discovery.
    return min(1.,max(0.,(env.common_step_counter-12000)/24000))

class ResidualGaitAction(mdp.JointPositionAction):
    def __init__(self,cfg,env):
        super().__init__(cfg,env);self.env=env
        self.held=torch.zeros_like(self._raw_actions)
        self.burst=torch.zeros(env.num_envs,device=env.device,dtype=torch.long)
    def process_actions(self,actions):
        total=.5*actions.clamp(-2.,2.)+reference_actions(self.env)
        strength=fault_fraction(self.env)
        new=torch.rand(self.env.num_envs,device=self.env.device)<.002*strength
        self.burst=torch.where(new,torch.randint(2,6,self.burst.shape,device=self.env.device),self.burst)
        lost=(torch.rand(self.env.num_envs,device=self.env.device)<.03*strength)|(self.burst>0)
        self.held=torch.where(lost[:,None],self.held,total)
        self.burst=(self.burst-1).clamp(min=0)
        super().process_actions(self.held)
    def reset(self,env_ids=None):
        super().reset(env_ids);self.held[env_ids]=0;self.burst[env_ids]=0

def packet(env):
    value=stale_measurement(env)
    state=env._tinker_sensor_cache
    if state.get('curriculum_tick')!=env.common_step_counter:
        state['curriculum_mask']=torch.rand(env.num_envs,device=env.device)<fault_fraction(env)
        state['curriculum_tick']=env.common_step_counter
    r=env.scene['robot'];from task import JOINTS
    ids,_=r.find_joints(JOINTS,preserve_order=True)
    current=torch.cat((r.data.root_ang_vel_b,r.data.projected_gravity_b,r.data.joint_pos[:,ids]-r.data.default_joint_pos[:,ids],r.data.joint_vel[:,ids]),-1)
    return torch.where(state['curriculum_mask'][:,None],value,current)
def gyro(env):return packet(env)[:,:3]
def gravity(env):return packet(env)[:,3:6]
def pos(env,asset_cfg=None):return packet(env)[:,6:16]
def vel(env,asset_cfg=None):return packet(env)[:,16:26]

@configclass
class V4Cfg(V3Cfg):
    def __post_init__(self):
        super().__post_init__()
        self.actions.joint_pos.class_type=ResidualGaitAction
        self.observations.policy.base_ang_vel.func=gyro
        self.observations.policy.projected_gravity.func=gravity
        self.observations.policy.joint_pos.func=pos
        self.observations.policy.joint_vel.func=vel
        self.commands.base_velocity.ranges.lin_vel_x=(.1,.25)
        self.commands.base_velocity.ranges.ang_vel_z=(-.15,.15)
        self.commands.base_velocity.rel_standing_envs=.1

@configclass
class V4PPO(V3PPO):
    def __post_init__(self):
        super().__post_init__();self.experiment_name='tinker_robust_v4';self.policy.init_noise_std=.4

gym.register(id='Tinker-Robust-v4',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':V4Cfg,'rsl_rl_cfg_entry_point':V4PPO})
