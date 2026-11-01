"""Vectorized hash-matched teacher baseline and supervised rollout collection."""
import argparse,sys,json,hashlib
from pathlib import Path
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=20);p.add_argument('--physics-dt',type=float,default=.005);p.add_argument('--tag',default='');p.add_argument('--student',default=None);AppLauncher.add_app_launcher_args(p);args=p.parse_args();app=AppLauncher(args).app
import gymnasium as gym
import numpy as np
import torch
from scipy.spatial.transform import Rotation
import task
from isaaclab.managers import SceneEntityCfg

b=Path(__file__).parent
assert hashlib.sha256((b/'teacher_finall.onnx').read_bytes()).hexdigest()=='9da84f4596ed2c3428d78f3c9f7cb5a61036fe0060b5d49ec11356fdd91d0808'
# Append, never prepend: retain Isaac's versions of NumPy, Torch and other packages.
for vendor in Path('/root/gpufree-data/envs').glob('*/lib/python3.11/site-packages'):
    if (vendor/'onnxruntime').is_dir():sys.path.append(str(vendor));break
import onnxruntime as ort
options=ort.SessionOptions();options.intra_op_num_threads=1;options.inter_op_num_threads=1
session=ort.InferenceSession(str(b/'teacher_finall.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
cases=[('stand',(0,0,0)),('forward_010',(.1,0,0)),('forward_025',(.25,0,0)),('backward',(-.1,0,0)),('turn_left',(0,0,.3)),('turn_right',(0,0,-.3))]
batch=4;n=24;cfg=task.TinkerCfg();cfg.scene.num_envs=n;cfg.seed=701;cfg.episode_length_s=args.seconds+2
cfg.sim.dt=args.physics_dt;cfg.decimation=int(round(.02/args.physics_dt));cfg.sim.render_interval=cfg.decimation
cfg.scene.contact_forces.update_period=args.physics_dt
cfg.observations.policy.enable_corruption=False
cfg.events.reset_base.params['pose_range']={};cfg.events.reset_robot_joints.params['position_range']=(1.,1.)
cfg.commands.base_velocity.rel_standing_envs=0.;cfg.commands.base_velocity.resampling_time_range=(1000.,1000.)
raw=gym.make('Tinker-Flat-v0',cfg=cfg);obs,_=raw.reset()
student=None
if args.student:
    saved=torch.load(args.student,map_location=raw.unwrapped.device,weights_only=False)
    student=torch.nn.Sequential(torch.nn.Linear(195,256),torch.nn.ELU(),torch.nn.Linear(256,128),torch.nn.ELU(),torch.nn.Linear(128,128),torch.nn.ELU(),torch.nn.Linear(128,10)).to(raw.unwrapped.device)
    student.load_state_dict(saved['actor_state_dict']);student.eval()
r=raw.unwrapped.scene['robot'];sensor=raw.unwrapped.scene['contact_forces'];feet,_=sensor.find_bodies(['L4_Link_ankle','R4_Link_ankle'],preserve_order=True)
ids,_=r.find_joints(task.JOINTS,preserve_order=True)
command=np.repeat(np.array([x[1] for x in cases],dtype=np.float32),batch,axis=0)
cmd=torch.tensor(command,device=raw.unwrapped.device);term=raw.unwrapped.command_manager.get_term('base_velocity')
# Fixed per-case commands must be installed before observation histories are
# initialized, and must survive automatic episode resets.
term._update_command=lambda:term.vel_command_b.copy_(cmd)
term.vel_command_b[:]=cmd
raw.unwrapped.observation_manager.reset()
obs=raw.unwrapped.observation_manager.compute(update_history=True)
history=np.zeros((n,10,39),np.float32);last=np.zeros((n,10),np.float32)
default=np.array(list(task.DEFAULT.values()),np.float32)
low=np.array([-.7,-.38,-1.57,-2.35,-1.2,-.7,-.38,-1.57,0,-1.2]);high=np.array([.7,.46,1.57,0,1.2,.7,.47,1.57,2.35,1.2])
stats=np.zeros((n,4));ever=np.zeros(n,bool);prev=np.ones((n,2),bool);samples_x=[];samples_y=[];valid_states=[]
steps=int(round(args.seconds/.02));count=0
with torch.inference_mode():
    for i in range(steps):
        term.vel_command_b[:]=cmd
        q=r.data.joint_pos[:,ids].cpu().numpy();dq=r.data.joint_vel[:,ids].cpu().numpy();quat=r.data.root_quat_w.cpu().numpy()
        euler=Rotation.from_quat(quat[:,[1,2,3,0]]).as_euler('xyz').astype(np.float32)
        proprio=np.concatenate((r.data.root_ang_vel_b.cpu().numpy()*.25,euler,command*np.array([2,2,.25]),q-default,dq*.05,last),-1).astype(np.float32)
        inp=np.zeros((n,660),np.float32);inp[:,:39]=proprio;inp[:,270:]=history.reshape(n,-1)
        action=np.clip(session.run(None,{session.get_inputs()[0].name:inp})[0],-100,100)
        target=np.clip(default+.25*(.9*action+.1*last),low,high)
        teacher_applied=((target-default)/.25).astype(np.float32)
        applied=teacher_applied
        if student is not None:
            prediction=student(obs['policy']).cpu().numpy()
            applied=((np.clip(default+.25*prediction,low,high)-default)/.25).astype(np.float32)
        samples_x.append(obs['policy'].cpu().numpy().copy());samples_y.append(teacher_applied.copy())
        valid_states.append(((r.data.root_pos_w[:,2]>.18)&(r.data.projected_gravity_b[:,2]<-.7)).cpu().numpy())
        history=np.roll(history,-1,axis=1);history[:,-1]=proprio
        last=action.copy() if student is None else applied.copy()
        obs,reward,terminated,truncated,info=raw.step(torch.tensor(applied,device=raw.unwrapped.device))
        failed=terminated.cpu().numpy();ever|=failed
        reset=(terminated|truncated).cpu().numpy();history[reset]=0;last[reset]=0
        force=sensor.data.net_forces_w[:,feet,:].norm(dim=-1).cpu().numpy();contact=force>=1
        if i>=100:
            v=r.data.root_lin_vel_b.cpu().numpy();w=r.data.root_ang_vel_w[:,2].cpu().numpy()
            stats[:,0]+=np.sum((v[:,:2]-command[:,:2])**2,-1);stats[:,1]+=(w-command[:,2])**2
            stats[:,2:]+=(prev&~contact);count+=1
        prev=contact
results={'teacher_sha256':'9da84f4596ed2c3428d78f3c9f7cb5a61036fe0060b5d49ec11356fdd91d0808','physics_dt':args.physics_dt,'control_dt':cfg.sim.dt*cfg.decimation,'seconds':args.seconds,'robots_per_case':batch,'postprocessing':'0.1 previous raw + 0.9 raw, joint limits; no swing_smooth','scope':'diagnostic, no faults, seed701; not full acceptance','cases':{}}
results['controller']='teacher' if student is None else args.student
for j,(name,c) in enumerate(cases):
    s=stats[j*batch:(j+1)*batch];results['cases'][name]={'command':c,'xy_rmse':float(np.sqrt(s[:,0].mean()/count)),'yaw_rmse':float(np.sqrt(s[:,1].mean()/count)),'no_base_contact_termination_fraction':float((~ever[j*batch:(j+1)*batch]).mean()),'mean_liftoffs':s[:,2:].mean(0).tolist()}
np.savez_compressed(b/f'teacher_isaac_rollouts{args.tag}.npz',observations=np.stack(samples_x),targets=np.stack(samples_y),commands=command,trajectory_success=~ever,valid_state=np.stack(valid_states))
(b/f'teacher_isaac_probe{args.tag}.json').write_text(json.dumps(results,indent=2));print('TEACHER_RESULT',json.dumps(results),flush=True)
raw.close();app.close()
