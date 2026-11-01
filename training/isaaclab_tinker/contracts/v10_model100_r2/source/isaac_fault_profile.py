"""Independent evaluation faults; no modification of active training modules."""
import torch
from isaaclab.envs.mdp.actions.joint_actions import JointPositionAction
from torch_packet_channel import TorchPacketChannel
from task import JOINTS

def clock_ms(env):return env._sim_step_counter*env.physics_dt*1000.

class ProfileAction(JointPositionAction):
    def __init__(self,cfg,env):
        super().__init__(cfg,env);self.env=env
        p=env.cfg.tinker_eval_profile
        initial=self._asset.data.default_joint_pos[:,self._joint_ids].clone()
        self.channel=TorchPacketChannel(initial,seed=env.cfg.seed+100,delay_ms=p.get('delay_ms',0.),jitter_ms=p.get('jitter_ms',0.),drop_probability=p.get('drop',0.),burst_ms=p.get('burst_ms',0.))
        env._tinker_eval_command_channel=self.channel
    def process_actions(self,actions):
        super().process_actions(actions)
        self.channel.send(self._processed_actions,clock_ms(self.env))
    def apply_actions(self):
        self._processed_actions,_=self.channel.receive(clock_ms(self.env))
        super().apply_actions()
    def reset(self,env_ids=None):
        super().reset(env_ids)
        if env_ids is None:env_ids=slice(None)
        self.channel.reset(env_ids,self._asset.data.default_joint_pos[env_ids][:,self._joint_ids],clock_ms(self.env))

def measurement(env):
    tick=env._sim_step_counter
    cache=getattr(env,'_tinker_eval_sensor_cache',None)
    if cache is not None and cache['tick']==tick:return cache['value']
    r=env.scene['robot'];ids,_=r.find_joints(JOINTS,preserve_order=True)
    v=torch.cat((r.data.root_ang_vel_b,r.data.projected_gravity_b,r.data.joint_pos[:,ids]-r.data.default_joint_pos[:,ids],r.data.joint_vel[:,ids]),-1)
    p=env.cfg.tinker_eval_profile;v[:,6:16]+=p.get('encoder_offset',0.)
    if cache is None:
        channel=TorchPacketChannel(v,seed=env.cfg.seed+200,delay_ms=p.get('sensor_age_ms',0.),drop_probability=p.get('sensor_drop',0.))
        cache={'channel':channel};env._tinker_eval_sensor_channel=channel
    channel=cache['channel'];reset=env.episode_length_buf<=1
    channel.reset(reset,v[reset],clock_ms(env))
    channel.send(v,clock_ms(env));value,_=channel.receive(clock_ms(env))
    cache.update(tick=tick,value=value);env._tinker_eval_sensor_cache=cache
    return value

def gyro(env):return measurement(env)[:,:3]
def gravity(env):return measurement(env)[:,3:6]
def position(env,asset_cfg=None):return measurement(env)[:,6:16]
def velocity(env,asset_cfg=None):return measurement(env)[:,16:26]

def configure(cfg,p):
    allowed={'delay_ms','jitter_ms','drop','burst_ms','sensor_age_ms','sensor_drop','encoder_offset','mass_scale','com_xy','friction','gain_scale','slope_deg','push_delta_v','ground_box'}
    assert not set(p)-allowed,'Unsupported independent Isaac boundary: '+str(set(p)-allowed)
    cfg.tinker_eval_profile=p
    cfg.actions.joint_pos.class_type=ProfileAction
    cfg.observations.policy.base_ang_vel.func=gyro;cfg.observations.policy.projected_gravity.func=gravity
    cfg.observations.policy.joint_pos.func=position;cfg.observations.policy.joint_vel.func=velocity
    # Fixed physical boundaries, no residual randomization from the training task.
    import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp
    from isaaclab.managers import EventTermCfg as Event,SceneEntityCfg
    if 'mass_scale' in p:cfg.events.add_base_mass=Event(func=mdp.randomize_rigid_body_mass,mode='startup',params={'asset_cfg':SceneEntityCfg('robot',body_names='.*'),'mass_distribution_params':(p['mass_scale'],p['mass_scale']),'operation':'scale','recompute_inertia':True})
    if 'com_xy' in p:
        x,y=p['com_xy'];cfg.events.base_com=Event(func=mdp.randomize_rigid_body_com,mode='startup',params={'asset_cfg':SceneEntityCfg('robot',body_names='base_link'),'com_range':{'x':(x,x),'y':(y,y),'z':(0.,0.)}})
    if 'gain_scale' in p:
        v=p['gain_scale'];cfg.events.actuator_gains=Event(func=mdp.randomize_actuator_gains,mode='startup',params={'asset_cfg':SceneEntityCfg('robot',joint_names='.*'),'stiffness_distribution_params':(v,v),'damping_distribution_params':(v,v),'operation':'scale','distribution':'uniform'})
    if 'friction' in p:
        v=p['friction'];cfg.events.physics_material.params.update(static_friction_range=(v,v),dynamic_friction_range=(v,v))

    if abs(p.get('slope_deg',0.))>0 or p.get('ground_box',False):
        import math,copy
        import isaaclab.sim as sim
        from isaaclab.assets import RigidObjectCfg
        angle=math.radians(p.get('slope_deg',0.));normal=(math.sin(angle),0.,math.cos(angle))
        material=copy.deepcopy(cfg.scene.terrain.physics_material)
        cfg.scene.terrain=None
        cfg.scene.sloped_ground=RigidObjectCfg(
            prim_path='{ENV_REGEX_NS}/sloped_ground',
            spawn=sim.CuboidCfg(size=(100.,100.,.1),rigid_props=sim.RigidBodyPropertiesCfg(kinematic_enabled=True,disable_gravity=True),mass_props=sim.MassPropertiesCfg(mass=1.),collision_props=sim.CollisionPropertiesCfg(),physics_material=material),
            init_state=RigidObjectCfg.InitialStateCfg(pos=tuple(-.05*x for x in normal),rot=(math.cos(angle/2),0.,math.sin(angle/2),0.)))
