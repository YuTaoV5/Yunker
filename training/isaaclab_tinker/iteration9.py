"""V9 candidate: lateral oscillation cost, phase-free qualified landing reward.
195D direct-action deployment unchanged. Source and exact deltas saved before run.
"""
import torch,gymnasium as gym
from isaaclab.utils import configclass
from isaaclab.managers import RewardTermCfg as Reward
from iteration8 import V8Cfg,V8PPO
from task import JOINTS

def lateral_velocity_error(env):
    c=env.command_manager.get_command('base_velocity')
    return (env.scene['robot'].data.root_lin_vel_b[:,1]-c[:,1]).square()

def target_tracking_error(env):
    r=env.scene['robot'];ids,_=r.find_joints(JOINTS,preserve_order=True)
    target=env.action_manager.get_term('joint_pos').processed_actions
    return (target-r.data.joint_pos[:,ids]).square().mean(-1)

def alternating_landing(env):
    tick=env.common_step_counter;state=getattr(env,'_tinker_landing_state',None)
    if state is not None and state['tick']==tick:return state['reward']
    ids,_=env.scene['contact_forces'].find_bodies(['L4_Link_ankle','R4_Link_ankle'],preserve_order=True)
    contact=env.scene['contact_forces'].data.net_forces_w[:,ids,:].norm(dim=-1)>=1.
    if state is None:
        state={'air':torch.zeros((env.num_envs,2),device=env.device),'last':torch.full((env.num_envs,),-1,device=env.device,dtype=torch.long),'contact':contact.clone()}
    reset=env.episode_length_buf<=1;state['air'][reset]=0;state['last'][reset]=-1;state['contact'][reset]=contact[reset]
    landing=contact & ~state['contact'] & (state['air']>=.04)
    one=landing.sum(-1)==1;foot=landing.long().argmax(-1)
    duration=state['air'].gather(1,foot[:,None]).squeeze(1).clamp(max=.2)
    qualified=one & (state['last']!=foot)
    cmd=env.command_manager.get_command('base_velocity');moving=(cmd[:,:2].norm(dim=-1)+cmd[:,2].abs())>.05
    reward=duration*qualified*moving
    state['last']=torch.where(one,foot,state['last'])
    state['air']=torch.where(contact,0.,state['air']+env.step_dt)
    state.update(contact=contact,tick=tick,reward=reward);env._tinker_landing_state=state
    return reward

@configclass
class V9Cfg(V8Cfg):
    def __post_init__(self):
        super().__post_init__()
        self.rewards.single_support=None
        self.rewards.alternating_landing=Reward(func=alternating_landing,weight=35.)
        self.rewards.lateral_velocity_error=Reward(func=lateral_velocity_error,weight=-30.)
        self.rewards.target_tracking_error=Reward(func=target_tracking_error,weight=-.5)
        self.events.actuator_gains.params.update(stiffness_distribution_params=(.8,1.2),damping_distribution_params=(.8,1.2))
        self.events.add_base_mass.params['mass_distribution_params']=(.85,1.15)
        self.events.base_com.params['com_range']={'x':(-.02,.02),'y':(-.02,.02),'z':(-.01,.01)}

@configclass
class V9PPO(V8PPO):
    def __post_init__(self):
        super().__post_init__();self.experiment_name='tinker_robust_v9';self.policy.init_noise_std=.05
        self.algorithm.anchor_action_weights=[1.,.1,1.,1.,1.,1.,.1,1.,1.,1.]

gym.register(id='Tinker-Robust-v9',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':V9Cfg,'rsl_rl_cfg_entry_point':V9PPO})
