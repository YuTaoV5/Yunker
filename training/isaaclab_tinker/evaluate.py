"""Deterministic command tracking and contact evaluation; never connects to hardware."""
import argparse,json,math
from pathlib import Path
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--asset-audit',action='store_true');p.add_argument('--contact-point-audit',action='store_true');p.add_argument('--contact-report-audit',action='store_true');p.add_argument('--contact-report-pump-render',action='store_true');p.add_argument('--fault-profile',default=None);p.add_argument('--actor-override',default=None);p.add_argument('--command-suite',choices=['fixed','full'],default='fixed');p.add_argument('--robust',action='store_true');p.add_argument('--version',type=int,default=1);p.add_argument('--nominal',action='store_true');p.add_argument('--seed',type=int,default=123);p.add_argument('--seconds',type=float,default=20);p.add_argument('--warmup-seconds',type=float,default=5.);p.add_argument('--robots-per-case',type=int,default=12);p.add_argument('--output',default='evaluation.json');AppLauncher.add_app_launcher_args(p);args=p.parse_args()
app=AppLauncher(args).app
import gymnasium as gym
import torch
import task
from orientation_metric import max_abs_roll_pitch
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
from rsl_rl.runners import OnPolicyRunner
if args.version==10:
    import iteration10,iteration7
    cfg=iteration10.V10Cfg();agent=iteration7.V7PPO();task_id='Tinker-Robust-v10'
elif args.version==9:
    import iteration9,iteration7
    cfg=iteration9.V9Cfg();agent=iteration7.V7PPO();task_id='Tinker-Robust-v9'
elif args.version in (7,8):
    import iteration7
    cfg=iteration7.V7Cfg();agent=iteration7.V7PPO();task_id='Tinker-Robust-v7'
elif args.version==5:
    import iteration5
    cfg=iteration5.V5Cfg();agent=iteration5.V5PPO();task_id='Tinker-Robust-v5'
elif args.version==4:
    import iteration4
    cfg=iteration4.V4Cfg();agent=iteration4.V4PPO();task_id='Tinker-Robust-v4'
elif args.version==3:
    import iteration3
    cfg=iteration3.V3Cfg();agent=iteration3.V3PPO();task_id='Tinker-Robust-v3'
elif args.robust:
    import robust_task
    cfg=robust_task.RobustCfg();agent=robust_task.RobustPPO();task_id='Tinker-Robust-v2'
else:
    cfg=task.TinkerCfg();agent=task.TinkerPPO();task_id='Tinker-Flat-v0'
cases=[('stand',(0,0,0)),('forward_010',(.1,0,0)),('forward_025',(.25,0,0)),('backward',(-.1,0,0)),('turn_left',(0,0,.3)),('turn_right',(0,0,-.3))]
if args.command_suite=='full':cases += [('walk_turn',(.15,0,.3)),('start_stop',(0,0,0))]
case_count=len(cases)
cfg.sim.device=args.device
if args.device=='cpu':torch.set_num_threads(2)
batch=args.robots_per_case
cfg.scene.num_envs=case_count*batch;cfg.seed=args.seed
cfg.episode_length_s=args.seconds+2.
if args.nominal or args.fault_profile:
    import isaaclab_tasks.manager_based.locomotion.velocity.mdp as mdp
    from isaaclab.envs.mdp.actions.joint_actions import JointPositionAction
    if args.version not in (4,5):cfg.actions.joint_pos.class_type=JointPositionAction
    for actuator in cfg.scene.robot.actuators.values():
        if hasattr(actuator,'min_delay'):actuator.min_delay=actuator.max_delay=0
    cfg.events.add_base_mass=None;cfg.events.base_com=None
    if hasattr(cfg.events,'actuator_gains'):cfg.events.actuator_gains=None
    cfg.events.physics_material.params['static_friction_range']=(.8,.8)
    cfg.events.physics_material.params['dynamic_friction_range']=(.6,.6)
    cfg.observations.policy.base_ang_vel.func=mdp.base_ang_vel
    cfg.observations.policy.projected_gravity.func=mdp.projected_gravity
    cfg.observations.policy.joint_pos.func=mdp.joint_pos_rel
    cfg.observations.policy.joint_vel.func=mdp.joint_vel_rel
cfg.observations.policy.enable_corruption=not (args.nominal or args.fault_profile)
cfg.events.reset_base.params['pose_range']={}
cfg.events.reset_robot_joints.params['position_range']=(1.,1.)
cfg.commands.base_velocity.rel_standing_envs=0.
cfg.commands.base_velocity.resampling_time_range=(1000.,1000.)
cfg.commands.base_velocity.ranges.lin_vel_x=(0.,0.)
cfg.commands.base_velocity.ranges.lin_vel_y=(0.,0.)
cfg.commands.base_velocity.ranges.ang_vel_z=(0.,0.)
profile=json.loads(Path(args.fault_profile).read_text()) if args.fault_profile else None
if profile is not None:
    from isaac_fault_profile import configure
    configure(cfg,profile)
if args.contact_point_audit:
    from isaac_contact_slip import configure as configure_contact_slip,sample as sample_contact_slip
    configure_contact_slip(cfg,profile)
from isaac_safety_audit import configure as configure_audit,report as audit_report,audit
configure_audit(cfg)
raw=gym.make(task_id,cfg=cfg);env=RslRlVecEnvWrapper(raw)
if args.version in (4,5,7,8,9,10):raw.unwrapped.tinker_fault_override=0. if (args.nominal or args.fault_profile) else 1.
runner=OnPolicyRunner(env,agent.to_dict(),log_dir=None,device=cfg.sim.device)
runner.load(args.checkpoint)
if args.actor_override:
    actor_state=torch.load(args.actor_override,map_location=cfg.sim.device,weights_only=False)['actor_state_dict']
    runner.alg.policy.actor.load_state_dict(actor_state)
policy=runner.get_inference_policy(device=cfg.sim.device)
contact_report_sampler=None
if args.contact_report_audit:
    from physx_contact_report_slip import ContactReportSlip
    contact_report_sampler=ContactReportSlip(raw.unwrapped,pump_render=args.contact_report_pump_render)
robot=raw.unwrapped.scene['robot'];sensor=raw.unwrapped.scene['contact_forces']
feet,_=sensor.find_bodies('[LR]4_Link_ankle')
from torch_foot_geometry import FootGeometry
foot_geometry=FootGeometry(Path(__file__).parent/'foot_collision_support.json',cfg.sim.device)
geometry_body_ids,_=robot.find_bodies(foot_geometry.names,preserve_order=True)
geometry_data=json.loads((Path(__file__).parent/'foot_collision_support.json').read_text())
expected_relative=torch.tensor([geometry_data['default_positions_relative_root'][name] for name in foot_geometry.names],device=cfg.sim.device)
actual_relative=robot.data.body_link_pos_w[:,geometry_body_ids,:]-robot.data.root_pos_w[:,None,:]
geometry_initial_alignment_error=float((actual_relative-expected_relative).abs().max())

cmd=torch.tensor([v for _,v in cases],device=cfg.sim.device).repeat_interleave(batch,dim=0)
slope=math.radians(profile.get('slope_deg',0.)) if profile else 0.
profile_floor_normal=torch.tensor([math.sin(slope),0.,math.cos(slope)],device=cfg.sim.device)
push_applied=False;push_actual_delta=None
term=raw.unwrapped.command_manager.get_term('base_velocity')
# Install fixed commands before constructing the very first history, and keep
# them fixed when automatic episode resets call the command manager.
term.vel_command_b[:]=cmd
schedule_reference_tick=raw.unwrapped.common_step_counter
from command_schedule import command_at_time
def update_evaluation_command():
    if args.command_suite=='full':
        start=next(j for j,(name,_) in enumerate(cases) if name=='start_stop')*batch
        now=(raw.unwrapped.common_step_counter-schedule_reference_tick)*raw.unwrapped.step_dt
        cmd[start:start+batch]=torch.tensor(command_at_time('start_stop',now),device=cfg.sim.device)
    term.vel_command_b.copy_(cmd)
term._update_command=update_evaluation_command
update_evaluation_command()
raw.unwrapped.observation_manager.reset()
obs=raw.unwrapped.observation_manager.compute(update_history=True)
stats=torch.zeros((case_count*batch,9),device=cfg.sim.device)
ever_failed=torch.zeros(case_count*batch,dtype=torch.bool,device=cfg.sim.device)
liftoffs=torch.zeros((case_count*batch,2),device=cfg.sim.device,dtype=torch.long)
previous_contact=torch.ones((case_count*batch,2),device=cfg.sim.device,dtype=torch.bool)
tilt_samples=[];initial_position=robot.data.root_pos_w[:,:2].clone();max_drift=torch.zeros(case_count*batch,device=cfg.sim.device)
warmup_steps=int(round(args.warmup_seconds/.02))
steps=int(round(args.seconds/.02));measure_steps=steps-warmup_steps
contact_history=[];velocity_history=[];reward_history=[];clearance_history=[];geometric_contact_history=[]
slip_squared=torch.zeros(case_count*batch,device=cfg.sim.device);slip_weight=torch.zeros_like(slip_squared);slip_points=torch.zeros(case_count*batch,device=cfg.sim.device,dtype=torch.long)
assert measure_steps>0
# Preserve an exact simulator observation/action pair for independent export parity.
with torch.inference_mode():
    sample=obs['policy'][0].detach().cpu().tolist()
    output=policy(obs)[0].detach().cpu().tolist()
Path(args.output+'.parity.json').write_text(json.dumps({'checkpoint':args.checkpoint,'actor_override':args.actor_override,'observation':sample,'action':output,'observation_terms':raw.unwrapped.observation_manager.active_terms['policy'],'default_joint_positions_in_sim_order':robot.data.default_joint_pos[0].cpu().tolist(),'sim_joint_names':robot.joint_names},indent=2))
command_switch_events=[]
command_observation_error=torch.zeros((),device=cfg.sim.device)
with torch.inference_mode():
    for i in range(steps):
        command_for_step=cmd.clone()
        command_observation_error=torch.maximum(command_observation_error,(obs['policy'][:,42:45]-command_for_step).abs().amax())
        if args.command_suite=='full' and i%500==0:
            start=next(j for j,(name,_) in enumerate(cases) if name=='start_stop')*batch
            command_switch_events.append({'time_seconds':i*.02,'desired':command_for_step[start].cpu().tolist(),'observed_by_policy':obs['policy'][start,42:45].cpu().tolist()})
        if profile and 'push_delta_v' in profile and not push_applied and i*.02>=5.:
            velocity=robot.data.root_vel_w.clone();old_x=velocity[:,0].clone();velocity[:,0]+=float(profile['push_delta_v'])
            robot.write_root_velocity_to_sim(velocity)
            push_actual_delta=(robot.data.root_vel_w[:,0]-old_x).cpu().tolist();push_applied=True
        term.vel_command_b[:]=cmd
        actions=policy(obs);obs,reward,done,info=env.step(actions)
        timeouts=info.get('time_outs',torch.zeros_like(done)).bool()
        invalid=~torch.isfinite(robot.data.joint_pos).all(-1)|~torch.isfinite(actions).all(-1)
        ever_failed|=(done.bool() & ~timeouts)|invalid
        if i>=warmup_steps:
            if args.contact_point_audit or args.contact_report_audit:
                sq,weight,count=contact_report_sampler.sample(profile_floor_normal) if args.contact_report_audit else sample_contact_slip(raw.unwrapped,profile_floor_normal)
                slip_squared+=sq;slip_weight+=weight;slip_points+=count
            force=sensor.data.net_forces_w[:,feet,:].norm(dim=-1)
            contact=force>=1.
            contact_history.append(contact.detach().cpu())
            clearance=foot_geometry.clearance(robot.data.body_link_pos_w[:,geometry_body_ids,:],robot.data.body_link_quat_w[:,geometry_body_ids,:],normal=profile_floor_normal,origin=raw.unwrapped.scene.env_origins)
            clearance_history.append(clearance.detach().cpu())
            geometric_contact_history.append((contact | (clearance<=.002)).detach().cpu())
            reward_history.append(raw.unwrapped.reward_manager._step_reward.detach().cpu().clone())
            velocity_history.append(torch.cat((robot.data.root_lin_vel_b[:,:2],robot.data.root_ang_vel_b[:,2:3]),-1).detach().cpu())
            liftoffs+=(previous_contact & ~contact).long();previous_contact=contact
            tilt_samples.append(max_abs_roll_pitch(robot.data.projected_gravity_b,torch))
            max_drift=torch.maximum(max_drift,(robot.data.root_pos_w[:,:2]-initial_position).norm(dim=-1))
            stats[:,0]+=((robot.data.root_lin_vel_b[:,:2]-command_for_step[:,:2])**2).sum(-1)
            stats[:,1]+=(robot.data.root_ang_vel_b[:,2]-command_for_step[:,2])**2
            stats[:,2]+=done.float()
            stats[:,3]+=(force<1).any(-1).float()
            stats[:,4]+=(force<1).all(-1).float()
            stats[:,5]+=robot.data.root_pos_w[:,2]
            stats[:,6]+=robot.data.projected_gravity_b[:,:2].norm(dim=-1)
            timeouts=info.get('time_outs',torch.zeros_like(done)).bool()
            stats[:,7]+=(done.bool() & ~timeouts).float()
            stats[:,8]+=timeouts.float()
stats[:,:2]*=900./measure_steps
stats[:,3:7]*=900./measure_steps
tilts=torch.stack(tilt_samples)
from gait_events import summarize_unloading
contact_history=torch.stack(contact_history).numpy()
velocity_history=torch.stack(velocity_history)
reward_history=torch.stack(reward_history)
clearance_history=torch.stack(clearance_history)
geometric_contact_history=torch.stack(geometric_contact_history).numpy()
audit(raw.unwrapped) # Include the final physics state after the final application.
result={'checkpoint':args.checkpoint,'seed':args.seed,'seconds':args.seconds,'warmup_seconds':args.warmup_seconds,'robots_per_case':batch,'cases':{}}
for j,(name,command) in enumerate(cases):
    sl=slice(j*batch,(j+1)*batch);s=stats[sl]
    result['cases'][name]={'command':command,'xy_rmse':float((s[:,0].mean()/900).sqrt()),'yaw_rmse':float((s[:,1].mean()/900).sqrt()),'episode_ends_in_measurement':int(s[:,2].sum()),'non_timeout_terminations':int(s[:,7].sum()),'normal_timeouts':int(s[:,8].sum()),'fraction_any_foot_unloaded':float(s[:,3].mean()/900),'fraction_both_feet_unloaded':float(s[:,4].mean()/900),'mean_base_height':float(s[:,5].mean()/900),'mean_gravity_xy_norm':float(s[:,6].mean()/900)}
    result['cases'][name].update({'success_fraction_no_fall':float((~ever_failed[sl]).float().mean()),'tilt_p99_deg':float(torch.quantile(tilts[:,sl].flatten(),.99)*180/torch.pi),'max_drift_m':float(max_drift[sl].max()),'mean_liftoffs_per_foot':liftoffs[sl].float().mean(0).cpu().tolist(),'scope':args.command_suite+' command suite; diagnostic only, full boundary matrix and independent trials pending'})
    # Reward manager exposes already weighted reward rates (step reward / dt).
    result['cases'][name]['mean_weighted_reward_rate']={term:float(reward_history[:,sl,index].mean()) for index,term in enumerate(raw.unwrapped.reward_manager.active_terms)}
    result['cases'][name]['maximum_source_mesh_clearance_per_foot_m']=clearance_history[:,sl,:].amax(dim=(0,1)).tolist()
    result['cases'][name]['source_mesh_geometric_unload_diagnostics']=[summarize_unloading(geometric_contact_history[:,k,:]) for k in range(j*batch,(j+1)*batch)]
    for diagnostic in result['cases'][name]['source_mesh_geometric_unload_diagnostics']:
        diagnostic['measurement']='normal-force unloaded AND source collision mesh clearance >2mm'
    result['cases'][name]['geometry_measurement_note']='URDF collision support vertices applied to Isaac link frame, >2mm AND force unloaded; default link alignment verified, cooked hull/margins not validated'
    if args.contact_point_audit or args.contact_report_audit:
        total_weight=float(slip_weight[sl].sum())
        result['cases'][name]['stance_contact_point_slip_rms_m_s']=float((slip_squared[sl].sum()/slip_weight[sl].sum()).sqrt()) if total_weight>0 else None
        result['cases'][name]['contact_points_above_1N']=int(slip_points[sl].sum())
    audit_state=raw.unwrapped._tinker_safety_audit
    result['cases'][name]['trial_records']=[{'trial_index':k-j*batch,'failed':bool(ever_failed[k]),'xy_rmse':float((stats[k,0]/900).sqrt()),'yaw_rmse':float((stats[k,1]/900).sqrt()),'abs_roll_pitch_p99_deg':float(torch.quantile(tilts[:,k],.99)*180/torch.pi),'max_drift_m':float(max_drift[k]),'joint_limit_violation_physics_samples':int(audit_state['violation_samples'][k]),'nonfinite_physics_samples':int(audit_state['nonfinite_samples'][k]),'maximum_joint_limit_excursion_rad':float(audit_state['max_excursion'][k])} for k in range(j*batch,(j+1)*batch)]
    result['cases'][name]['trial_start_note']='Controlled identical reset pose; independent initial-state fixtures not yet implemented'
    result['cases'][name]['mean_velocity_body']=velocity_history[:,sl,:].mean((0,1)).tolist()
    result['cases'][name]['unload_sequence_diagnostics']=[summarize_unloading(contact_history[:,k,:]) for k in range(j*batch,(j+1)*batch)]
result['safety_audit']=audit_report(raw.unwrapped)
result['physical_parameters']={'body_names':robot.body_names,'total_mass_per_env_kg':robot.root_physx_view.get_masses().sum(-1).tolist(),'body_com_local':robot.root_physx_view.get_coms().tolist(),'robot_materials':robot.root_physx_view.get_material_properties().tolist(),'actuators':{name:{'joint_indices':a.joint_indices.tolist() if hasattr(a.joint_indices,'tolist') else a.joint_indices,'stiffness':a.stiffness.cpu().tolist(),'damping':a.damping.cpu().tolist()} for name,a in robot.actuators.items()}}
result['contact_report_metadata']=contact_report_sampler.report() if contact_report_sampler else None
if args.asset_audit:
    from usd_asset_audit import audit as audit_usd_asset
    result['usd_asset_audit']=audit_usd_asset(raw.unwrapped)
result['observation_corruption_enabled']=bool(cfg.observations.policy.enable_corruption)
result['metric_revision']=3
result['physics_device']=str(cfg.sim.device)
result['command_suite']=args.command_suite
result['observation_bootstrap_revision']=2
result['observation_bootstrap']='reset history then append current state, repeat first real sample'
result['command_contract_revision']=2
result['command_switch_events']=command_switch_events
result['max_command_observation_error']=float(command_observation_error)
result['command_observation_alignment_pass']=float(command_observation_error)<=1e-6
result['start_stop_schedule']='0 -> .2 -> 0, each10s repeating' if args.command_suite=='full' else None
result['push_applied']=push_applied
result['push_actual_delta_v_x']=push_actual_delta
if profile and (abs(profile.get('slope_deg',0.))>0 or profile.get('ground_box',False)):
    ground=raw.unwrapped.scene['sloped_ground']
    result['sloped_ground_transform']={'position_relative_env':(ground.data.root_pos_w-raw.unwrapped.scene.env_origins).cpu().tolist(),'quaternion_wxyz':ground.data.root_quat_w.cpu().tolist()}
result['ground_geometry']='kinematic_box' if profile and (abs(profile.get('slope_deg',0.))>0 or profile.get('ground_box',False)) else 'original_ground'
result['floor_normal_world']=profile_floor_normal.cpu().tolist()
result['actor_override']=args.actor_override
result['geometry_default_link_alignment_error_m']=geometry_initial_alignment_error
result['geometry_default_link_alignment_pass']=geometry_initial_alignment_error<1e-4
result['geometry_urdf_sha256']=foot_geometry.urdf_sha256
result['independent_fault_profile']=profile
if profile is not None:
    result['command_channel_stats']=raw.unwrapped._tinker_eval_command_channel.report()
    result['sensor_channel_stats']=raw.unwrapped._tinker_eval_sensor_channel.report()
result['task']=task_id
result['contract_version']=args.version
result['physics_task_alias']='Tinker-Robust-v7' if args.version==8 else None
result['training_fault_model_active']=(args.robust or args.version in (3,4,5,7,8,9,10)) and not (args.nominal or args.fault_profile)
result['fault_curriculum_override']=0. if (args.nominal or args.fault_profile) else 1. if args.version in (4,5,7,8,9,10) else None
Path(args.output).write_text(json.dumps(result,indent=2));print('EVALUATION_RESULT',json.dumps(result),flush=True)
env.close();app.close()
