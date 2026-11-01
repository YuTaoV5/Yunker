"""V3: reject static-contact reward exploitation and add stale-sensor faults."""
import gymnasium as gym
import torch
from isaaclab.utils import configclass
from isaaclab.managers import RewardTermCfg as Reward
import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp
from robust_task import RobustCfg,RobustPPO,phase
from task import JOINTS

def exact_contact(env):
    sensor=env.scene['contact_forces'];ids,_=sensor.find_bodies(['L4_Link_ankle','R4_Link_ankle'],preserve_order=True)
    contact=sensor.data.net_forces_w[:,ids,:].norm(dim=-1)>1.
    s=phase(env)[:,0];desired=torch.stack((s<=.15,s>=-.15),-1)
    c=env.command_manager.get_command('base_velocity')
    moving=(c[:,:2].norm(dim=-1)+c[:,2].abs())>.05
    return (contact==desired).all(-1).float()*moving

def yaw_error(env):
    c=env.command_manager.get_command('base_velocity')
    return (env.scene['robot'].data.root_ang_vel_b[:,2]-c[:,2]).abs()

def stuck_contact(env):
    sensor=env.scene['contact_forces'];ids,_=sensor.find_bodies(['L4_Link_ankle','R4_Link_ankle'],preserve_order=True)
    contact=sensor.data.net_forces_w[:,ids,:].norm(dim=-1)>1.
    c=env.command_manager.get_command('base_velocity');moving=(c[:,:2].norm(dim=-1)+c[:,2].abs())>.05
    return contact.all(-1).float()*moving*(phase(env)[:,0].abs()>.3)

def stale_measurement(env):
    """Coherent IMU+encoder packets, per-env jitter, hold-last and burst loss.

    Observation noise is applied by the observation manager after this function.
    Cache by physics-control step so four observation terms share the same packet.
    """
    tick=env.common_step_counter
    cache=getattr(env,'_tinker_sensor_cache',None)
    if cache is not None and cache['tick']==tick:return cache['value']
    r=env.scene['robot'];ids,_=r.find_joints(JOINTS,preserve_order=True)
    v=torch.cat((r.data.root_ang_vel_b,r.data.projected_gravity_b,r.data.joint_pos[:,ids]-r.data.default_joint_pos[:,ids],r.data.joint_vel[:,ids]),-1)
    if cache is None:
        cache={'ring':v.unsqueeze(0).repeat(4,1,1),'value':v.clone(),'burst':torch.zeros(env.num_envs,device=env.device,dtype=torch.long),'bias':torch.empty((env.num_envs,10),device=env.device).uniform_(-.01,.01)}
    reset=env.episode_length_buf<=1
    cache['ring'][:,reset]=v[reset];cache['burst'][reset]=0
    cache['ring']=torch.roll(cache['ring'],1,0);cache['ring'][0]=v
    age=torch.randint(0,3,(env.num_envs,),device=env.device)
    delayed=cache['ring'][age,torch.arange(env.num_envs,device=env.device)].clone()
    delayed[:,6:16]+=cache['bias']
    start=torch.rand(env.num_envs,device=env.device)<.001
    cache['burst']=torch.where(start,torch.randint(2,6,(env.num_envs,),device=env.device),cache['burst'])
    lost=((torch.rand(env.num_envs,device=env.device)<.03)|(cache['burst']>0))&~reset
    cache['value']=torch.where(lost[:,None],cache['value'],delayed)
    cache['burst']=(cache['burst']-1).clamp(min=0);cache['tick']=tick
    env._tinker_sensor_cache=cache
    return cache['value']

def stale_gyro(env):return stale_measurement(env)[:,:3]
def stale_gravity(env):return stale_measurement(env)[:,3:6]
def stale_pos(env,asset_cfg=None):return stale_measurement(env)[:,6:16]
def stale_vel(env,asset_cfg=None):return stale_measurement(env)[:,16:26]

@configclass
class V3Cfg(RobustCfg):
    def __post_init__(self):
        super().__post_init__()
        self.rewards.gait_contact.func=exact_contact
        self.rewards.gait_contact.weight=4.
        self.rewards.stuck_contact=Reward(func=stuck_contact,weight=-2.)
        self.rewards.yaw_error=Reward(func=yaw_error,weight=-1.5)
        self.rewards.feet_slide.weight=-.8
        self.rewards.flat_orientation_l2.weight=-3.
        self.rewards.track_ang_vel_z_exp.weight=3.
        self.commands.base_velocity.ranges.lin_vel_x=(-.1,.3)
        self.commands.base_velocity.ranges.ang_vel_z=(-.3,.3)
        self.observations.policy.base_ang_vel.func=stale_gyro
        self.observations.policy.projected_gravity.func=stale_gravity
        self.observations.policy.joint_pos.func=stale_pos
        self.observations.policy.joint_vel.func=stale_vel

@configclass
class V3PPO(RobustPPO):
    def __post_init__(self):
        super().__post_init__();self.experiment_name='tinker_robust_v3'
        self.algorithm.entropy_coef=.003

gym.register(id='Tinker-Robust-v3',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':V3Cfg,'rsl_rl_cfg_entry_point':V3PPO})
