"""Iteration 2: explicit gait shaping and simulated communication faults."""
import gymnasium as gym
import torch
from isaaclab.utils import configclass
from isaaclab.managers import RewardTermCfg as Reward, ObservationTermCfg as Obs, EventTermCfg as Event, SceneEntityCfg
from isaaclab.actuators import DelayedPDActuatorCfg
from isaaclab.envs.mdp.actions.joint_actions import JointPositionAction
import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp
from task import TinkerCfg,TinkerPPO

def phase(env):
    t=env.episode_length_buf*env.step_dt*(2*torch.pi/.7)
    return torch.stack((torch.sin(t),torch.cos(t)),dim=-1)

def gait_contact(env):
    sensor=env.scene['contact_forces']; ids,_=sensor.find_bodies(['L4_Link_ankle','R4_Link_ankle'],preserve_order=True)
    contact=sensor.data.net_forces_w[:,ids,:].norm(dim=-1)>1.
    s=phase(env)[:,0]; desired=torch.stack((s<=.15,s>=-.15),-1)
    cmd=env.command_manager.get_command('base_velocity')
    moving=(cmd[:,:2].norm(dim=-1)+cmd[:,2].abs())>.05
    return (contact==desired).float().mean(-1)*moving

def gait_reference(env):
    r=env.scene['robot'];ids,_=r.find_joints(['J_L2','J_L3','J_R2','J_R3'],preserve_order=True)
    s=phase(env)[:,0]; l=torch.clamp(s,min=0);rr=torch.clamp(-s,min=0)
    delta=torch.stack((-.15*l,.3*l,.15*rr,-.3*rr),-1)
    # Left flexion is negative and right flexion positive.
    delta=-delta
    error=(r.data.joint_pos[:,ids]-r.data.default_joint_pos[:,ids]-delta).square().sum(-1)
    cmd=env.command_manager.get_command('base_velocity');moving=(cmd[:,:2].norm(dim=-1)+cmd[:,2].abs())>.05
    return torch.exp(-error/.04)*moving

class LossyJointPositionAction(JointPositionAction):
    """Whole command packet held on loss, including bounded 40–100ms bursts.

    Loss applies to all ten axes together, rather than independent joint packets.
    """
    def __init__(self,cfg,env):
        super().__init__(cfg,env)
        self.held=torch.zeros_like(self._raw_actions)
        self.remaining=torch.zeros(env.num_envs,device=env.device,dtype=torch.long)
    def process_actions(self,actions):
        burst=torch.rand(actions.shape[0],device=actions.device)<.002
        self.remaining=torch.where(burst,torch.randint(2,6,self.remaining.shape,device=actions.device),self.remaining)
        drop=(torch.rand(actions.shape[0],device=actions.device)<.03)|(self.remaining>0)
        self.remaining.clamp_(min=0);self.remaining-= (self.remaining>0).long()
        self.held=torch.where(drop[:,None],self.held,actions)
        super().process_actions(self.held)
    def reset(self,env_ids=None):
        super().reset(env_ids);self.held[env_ids]=0.;self.remaining[env_ids]=0

@configclass
class RobustCfg(TinkerCfg):
    def __post_init__(self):
        super().__post_init__()
        self.actions.joint_pos.class_type=LossyJointPositionAction
        self.observations.policy.gait_phase=Obs(func=phase)
        self.commands.base_velocity.rel_standing_envs=.1
        self.commands.base_velocity.ranges.lin_vel_x=(.05,.3)
        self.commands.base_velocity.ranges.lin_vel_y=(0.,0.)
        self.commands.base_velocity.ranges.ang_vel_z=(-.3,.3)
        self.rewards.track_lin_vel_xy_exp.weight=5.
        self.rewards.track_lin_vel_xy_exp.params['std']=.15
        self.rewards.track_ang_vel_z_exp.weight=2.
        self.rewards.track_ang_vel_z_exp.params['std']=.25
        self.rewards.gait_contact=Reward(func=gait_contact,weight=2.)
        self.rewards.gait_reference=Reward(func=gait_reference,weight=1.)
        self.rewards.feet_air_time.weight=1.
        self.rewards.termination_penalty.weight=-50.
        self.events.physics_material.params['static_friction_range']=(.4,1.2)
        self.events.physics_material.params['dynamic_friction_range']=(.3,1.)
        self.events.add_base_mass=Event(func=mdp.randomize_rigid_body_mass,mode='startup',params={'asset_cfg':SceneEntityCfg('robot',body_names='.*'),'mass_distribution_params':(.9,1.1),'operation':'scale','recompute_inertia':True})
        self.events.base_com=Event(func=mdp.randomize_rigid_body_com,mode='startup',params={'asset_cfg':SceneEntityCfg('robot',body_names='base_link'),'com_range':{'x':(-.015,.015),'y':(-.01,.01),'z':(-.01,.01)}})
        self.events.actuator_gains=Event(func=mdp.randomize_actuator_gains,mode='startup',params={'asset_cfg':SceneEntityCfg('robot',joint_names='.*'),'stiffness_distribution_params':(.85,1.15),'damping_distribution_params':(.85,1.15),'operation':'scale','distribution':'uniform'})
        for name,a in list(self.scene.robot.actuators.items()):
            self.scene.robot.actuators[name]=DelayedPDActuatorCfg(joint_names_expr=a.joint_names_expr,effort_limit=a.effort_limit,velocity_limit=a.velocity_limit,stiffness=a.stiffness,damping=a.damping,min_delay=0,max_delay=6)

@configclass
class RobustPPO(TinkerPPO):
    def __post_init__(self):
        super().__post_init__();self.experiment_name='tinker_robust_v2';self.max_iterations=5000

gym.register(id='Tinker-Robust-v2',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':RobustCfg,'rsl_rl_cfg_entry_point':RobustPPO})
