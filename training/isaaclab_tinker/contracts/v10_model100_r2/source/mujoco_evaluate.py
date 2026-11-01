"""Independent MuJoCo rollout using a URDF-derived model and identical actor contract."""
import argparse,json,math,xml.etree.ElementTree as ET
import os,subprocess
os.environ.setdefault('MUJOCO_GL','egl')
from pathlib import Path
import numpy as np
import torch
import mujoco
from command_schedule import command_at_time
torch.set_num_threads(2)

JOINTS=['J_L0','J_L1','J_L2','J_L3','J_L4_ankle','J_R0','J_R1','J_R2','J_R3','J_R4_ankle']
DEFAULT=np.array([0,.08,.56,-1.12,-.57,0,-.08,-.56,1.12,.57])
KP=np.array([15,17,17,17,15]*2);KD=np.array([.5,1.5,1.5,1.5,.5]*2)
LIMIT=np.array([12,20,20,20,12]*2)

def build_model(base):
    # Use the same source URDF as Isaac Lab, not the upstream hand-edited MJCF.
    model=mujoco.MjModel.from_xml_path(str(base/'assets/urdf/TinkerV2_URDF.urdf'))
    target=base/f'assets/tinker_urdf_mujoco_{os.getpid()}.xml'
    mujoco.mj_saveLastXML(str(target),model)
    tree=ET.parse(target);root=tree.getroot();world=root.find('worldbody')
    compiler=root.find('compiler')
    if compiler is not None:compiler.set('meshdir',str(base/'assets/meshes'))
    # MuJoCo URDF import welds the base into world. Restore the floating
    # base around BOTH legs, retaining base mass/inertia from the source.
    body=ET.Element('body',name='floating_root',pos='0 0 .33')
    for child in list(world):world.remove(child);body.append(child)
    world.append(body);ET.SubElement(body,'freejoint',name='floating_base')
    urdf=ET.parse(base/'assets/urdf/TinkerV2_URDF.urdf').getroot()
    source=urdf.find("link[@name='base_link']/inertial")
    assert source is not None
    origin=source.find('origin');tensor=source.find('inertia')
    xyz=origin.get('xyz','0 0 0') if origin is not None else '0 0 0'
    from scipy.spatial.transform import Rotation
    rot=Rotation.from_euler('xyz',[float(x) for x in origin.get('rpy','0 0 0').split()]).as_matrix() if origin is not None else np.eye(3)
    xx,yy,zz,xy,xz,yz=[float(tensor.get(k)) for k in ['ixx','iyy','izz','ixy','ixz','iyz']]
    matrix=rot@np.array([[xx,xy,xz],[xy,yy,yz],[xz,yz,zz]])@rot.T
    full=[matrix[0,0],matrix[1,1],matrix[2,2],matrix[0,1],matrix[0,2],matrix[1,2]]
    ET.SubElement(body,'inertial',mass=source.find('mass').get('value'),pos=xyz,fullinertia=' '.join(map(str,full)))
    # Match the current Isaac Lab asset's disabled self-collision setting.
    # Robot-ground contacts remain enabled. Full self-collision is a later audit.
    for geom in body.iter('geom'):
        # Preserve URDF visual-only masks. Only real collision shapes touch floor.
        if geom.get('contype','1')=='0' and geom.get('conaffinity','1')=='0':continue
        geom.set('contype','2');geom.set('conaffinity','1');geom.set('friction','.8 .005 .0001')
    ET.SubElement(world,'geom',name='floor',type='plane',size='20 20 .1',friction='.8 .005 .0001',contype='1',conaffinity='2')
    ET.SubElement(world,'light',pos='0 -2 3',dir='0 1 -1',diffuse='.9 .9 .9',ambient='.5 .5 .5')
    option=root.find('option')
    if option is None:option=ET.SubElement(root,'option')
    option.set('timestep','.001');option.set('gravity','0 0 -9.81')
    act=root.find('actuator')
    if act is None:act=ET.SubElement(root,'actuator')
    for name,limit in zip(JOINTS,LIMIT):ET.SubElement(act,'motor',name=name,joint=name,gear='1',ctrllimited='true',ctrlrange=f'{-limit} {limit}')
    tree.write(target)
    return mujoco.MjModel.from_xml_path(str(target))

def actor_from_checkpoint(path):
    saved=torch.load(path,map_location='cpu',weights_only=False)
    state=saved['model_state_dict']
    weights=[(k,v) for k,v in state.items() if k.startswith('actor.') and k.endswith('.weight')]
    weights.sort(key=lambda kv:int(kv[0].split('.')[1]))
    modules=[]
    for i,(k,v) in enumerate(weights):
        layer=torch.nn.Linear(v.shape[1],v.shape[0]);layer.weight.data.copy_(v)
        layer.bias.data.copy_(state[k[:-6]+'bias']);modules.append(layer)
        if i<len(weights)-1:modules.append(torch.nn.ELU())
    actor=torch.nn.Sequential(*modules).eval()
    assert weights[0][1].shape[1] in (195,205),'Unsupported observation contract'
    return actor

def rollout(base,checkpoint,command,seed,seconds,delay_ms,drop,version=3,video=None,jitter_ms=0.,sensor_age_ms=0.,sensor_drop=0.,burst_ms=0.,warmup_seconds=5.,physics_config=None,command_schedule=None,trace_path=None,action_filter_alpha=1.):
    rng=np.random.default_rng(seed);m=build_model(base);d=mujoco.MjData(m)
    physics_config=physics_config or {}
    allowed={'mass_scale','com_xy','friction','gain_scale','encoder_offset','slope_deg','push_delta_v'}
    assert not set(physics_config)-allowed,'Unknown physics injection'
    mass_scale=float(physics_config.get('mass_scale',1.));gain_scale=float(physics_config.get('gain_scale',1.))
    assert mass_scale>0 and gain_scale>0
    m.body_mass[:]*=mass_scale;m.body_inertia[:]*=mass_scale
    m.body_ipos[1,:2]+=np.asarray(physics_config.get('com_xy',[0.,0.]))
    if 'friction' in physics_config:m.geom_friction[:,0]=float(physics_config['friction'])
    if 'slope_deg' in physics_config:
        angle=np.deg2rad(physics_config['slope_deg']);floor=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'floor');m.geom_quat[floor]=[np.cos(angle/2),0,np.sin(angle/2),0]
    mujoco.mj_setConst(m,d)
    original_command=list(command);push_applied=False;trace=[];command_events=[];previous_command=None;command_observation_error=0.
    jids=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,j) for j in JOINTS]
    qi=m.jnt_qposadr[jids];vi=m.jnt_dofadr[jids]
    ai=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_ACTUATOR,j) for j in JOINTS]
    d.qpos[qi]=DEFAULT;mujoco.mj_forward(m,d)
    from packet_channel import PacketChannel
    action_channel=PacketChannel(np.zeros(10),seed+1,delay_ms,jitter_ms,drop,burst_ms=burst_ms)
    initial_packet=np.concatenate((np.zeros(3),np.array([0.,0.,-1.]),np.zeros(20)))
    sensor_channel=PacketChannel(initial_packet,seed+2,sensor_age_ms,0.,sensor_drop)
    actor=actor_from_checkpoint(checkpoint);raw=np.zeros(10);held=np.zeros(10);filtered_action=np.zeros(10)
    alpha=np.broadcast_to(np.asarray(action_filter_alpha,dtype=float),(10,));assert ((alpha>0)&(alpha<=1)).all()
    hist=None;queue=[];metrics=[];fell=False;contact_history=[]
    foot_ids=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,n) for n in ['L4_Link_ankle','R4_Link_ankle']]
    from mujoco_contact_metrics import FootMetrics
    foot_metrics=FootMetrics(m,foot_ids);clearance_history=[];geometric_contact_history=[];slip_squared=0.;slip_weight=0.
    joint_limit_samples=0;maximum_joint_limit_excursion=0.;nonfinite_samples=0
    liftoffs=np.zeros(2,dtype=int);prev_contact=np.ones(2,dtype=bool);unloaded=0;contact_samples=0
    renderer=None;encoder=None
    if video:
        renderer=mujoco.Renderer(m,height=480,width=640)
        camera=mujoco.MjvCamera();camera.distance=1.6;camera.azimuth=140;camera.elevation=-15
        encoder=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','640x480','-r','25','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p',str(video)],stdin=subprocess.PIPE)
    for step in range(int(seconds/.02)):
        command=command_at_time(command_schedule,step*.02,original_command)
        if not push_applied and step*.02>=5. and 'push_delta_v' in physics_config:
            d.qvel[0]+=float(physics_config['push_delta_v']);push_applied=True
        rotation=d.xmat[1].reshape(3,3)
        velocity=np.zeros(6);mujoco.mj_objectVelocity(m,d,mujoco.mjtObj.mjOBJ_BODY,1,velocity,0)
        phase=step*.02*2*np.pi/.7
        packet=np.concatenate((rotation.T@velocity[:3],rotation.T@np.array([0.,0.,-1.]),d.qpos[qi]-DEFAULT+float(physics_config.get('encoder_offset',0.)),d.qvel[vi]))
        sensor_channel.send(packet,d.time*1000);measured,_=sensor_channel.receive(d.time*1000)
        terms=[measured[:3]*.25,measured[3:6],np.array(command),measured[6:16],measured[16:26]*.05,raw,np.array([np.sin(phase),np.cos(phase)])]
        if version in (7,8,9,10):terms=terms[:-1]
        if hist is None:hist=[[t.copy() for _ in range(5)] for t in terms]
        else:
            for h,t in zip(hist,terms):h.pop(0);h.append(t.copy())
        observation=np.concatenate([np.concatenate(h) for h in hist]).astype(np.float32)
        command_observation_error=max(command_observation_error,float(np.max(np.abs(observation[42:45]-command))))
        if previous_command!=tuple(command):command_events.append({'time_seconds':step*.02,'desired':list(command),'observed_by_policy':observation[42:45].tolist()});previous_command=tuple(command)
        with torch.no_grad():raw=actor(torch.from_numpy(observation).unsqueeze(0))[0].numpy()
        if version in (4,5):
            ref=np.zeros(10)
            if np.linalg.norm(command[:2])+abs(command[2])>.05:
                l=max(np.sin(phase),0);rr=max(-np.sin(phase),0)
                ref[[2,3,4,7,8,9]]=[.225*l,-.45*l,-.225*l,-.225*rr,.45*rr,.225*rr]
                if version==5:ref[[1,6]]=-.08*np.sin(phase)
            transported=(.25 if version==5 else .5)*np.clip(raw,-2,2)+ref/.25
        else:transported=raw.copy()
        filtered_action=alpha*transported+(1-alpha)*filtered_action
        action_channel.send(filtered_action,d.time*1000)
        for _ in range(20):
            applied,_=action_channel.receive(d.time*1000)
            target=DEFAULT+.25*applied
            if version in (7,8,9,10):
                target=np.clip(target,[-.7,-.38,-1.57,-2.35,-1.2,-.7,-.38,-1.57,0.,-1.2],[.7,.46,1.57,0.,1.2,.7,.47,1.57,2.35,1.2])
            d.ctrl[ai]=np.clip(gain_scale*(KP*(target-d.qpos[qi])-KD*d.qvel[vi]),-LIMIT,LIMIT)
            mujoco.mj_step(m,d)
            excursion=np.maximum(m.jnt_range[jids,0]-d.qpos[qi],d.qpos[qi]-m.jnt_range[jids,1])
            maximum_joint_limit_excursion=max(maximum_joint_limit_excursion,float(excursion.max()))
            joint_limit_samples+=int((excursion>0).any())
            nonfinite_samples+=int(not np.isfinite(d.qpos).all() or not np.isfinite(d.qvel).all() or not np.isfinite(d.ctrl).all())
        if trace_path is not None:
            trace.append(dict(time=float(d.time),q=d.qpos[qi].copy(),dq=d.qvel[vi].copy(),target=target.copy(),torque=d.ctrl[ai].copy(),velocity_body=np.r_[rotation.T@velocity[3:],rotation.T@velocity[:3]],gravity=rotation.T@np.array([0.,0.,-1.])))
        if renderer is not None and step%2==0:
            camera.lookat[:]=d.xpos[1]+np.array([0.,0.,.12])
            renderer.update_scene(d,camera=camera);encoder.stdin.write(renderer.render().tobytes())
        if not np.isfinite(d.qpos).all():fell=True;break
        height=float(d.xpos[1,2]);gravity=rotation.T@np.array([0.,0.,-1.])
        if height<.18 or gravity[2]>-.7:fell=True;break
        if step*.02>=warmup_seconds:
            normal=np.zeros(2)
            for contact_id in range(d.ncon):
                con=d.contact[contact_id];force=np.zeros(6);mujoco.mj_contactForce(m,d,contact_id,force)
                for k,bid in enumerate(foot_ids):
                    if bid in (m.geom_bodyid[con.geom1],m.geom_bodyid[con.geom2]):normal[k]+=abs(force[0])
            contact=normal>=1.
            contact_history.append(contact.copy())
            clearance=foot_metrics.clearance(d);clearance_history.append(clearance)
            geometric_contact_history.append(~((~contact)&(clearance>.002)))
            sq,w=foot_metrics.slip(m,d);slip_squared+=sq;slip_weight+=w
            liftoffs+=(prev_contact & ~contact);prev_contact=contact
            unloaded+=bool((~contact).any());contact_samples+=1
            local=rotation.T@velocity[3:];metrics.append([np.sum((local[:2]-np.array(command[:2]))**2),(velocity[2]-command[2])**2,height,local[0],local[1],velocity[2],(local[0]-command[0])**2,(local[1]-command[1])**2])
    if renderer is not None:
        renderer.close();encoder.stdin.close();assert encoder.wait()==0
    if trace_path is not None and trace:
        np.savez_compressed(trace_path,**{k:np.asarray([r[k] for r in trace]) for k in trace[0]})
    v=np.array(metrics)
    from gait_events import summarize_unloading
    sequence_diagnostics=summarize_unloading(np.asarray(contact_history).reshape(-1,2))
    geometric_diagnostics=summarize_unloading(np.asarray(geometric_contact_history).reshape(-1,2))
    geometric_diagnostics['measurement']='collision mesh minimum signed distance >2mm AND unloaded normal force; flat/sloped plane'
    return {'geometric_liftoff_diagnostics':geometric_diagnostics,'clearance_threshold_m':.002,'maximum_mesh_clearance_per_foot_m':np.asarray(clearance_history).max(0).tolist() if clearance_history else None,'stance_contact_point_slip_rms_m_s':float(np.sqrt(slip_squared/slip_weight)) if slip_weight else None,'joint_limit_violation_physics_samples':joint_limit_samples,'maximum_joint_limit_excursion_rad':maximum_joint_limit_excursion,'nonfinite_physics_samples':nonfinite_samples,'audit_sample_hz':1000,'action_filter_alpha':alpha.tolist(),'physics_config':physics_config,'actual_total_mass_kg':float(m.body_mass.sum()),'actual_base_com_local_m':m.body_ipos[1].tolist(),'actual_friction_coefficients':sorted(set(m.geom_friction[:,0].tolist())),'gain_scale':gain_scale,'push_applied':push_applied,'command_switch_events':command_events,'max_command_observation_error':command_observation_error,'command_observation_alignment_pass':command_observation_error<=1e-6,'command_contract_revision':2,'command_schedule':command_schedule,'initial_command':original_command,'warmup_seconds':warmup_seconds,'unload_sequence_diagnostics':sequence_diagnostics,'seed':seed,'command':command,'fell':fell,'survived_seconds':float(d.time),'xy_rmse':float(np.sqrt(v[:,0].mean())) if len(v) else None,'yaw_rmse':float(np.sqrt(v[:,1].mean())) if len(v) else None,'mean_height':float(v[:,2].mean()) if len(v) else None,'mean_velocity_body':v[:,3:6].mean(0).tolist() if len(v) else None,'xy_axis_rmse':np.sqrt(v[:,6:8].mean(0)).tolist() if len(v) else None,'evaluation_backend_revision':'mujoco_urdf_v2_visual_masks_preserved','nominal_friction_model':'robot and floor explicitly .8; earlier probes had default robot1.0','delay_ms':delay_ms,'drop_probability':drop,'liftoffs_per_foot':liftoffs.tolist(),'fraction_any_foot_unloaded':unloaded/contact_samples if contact_samples else None,'jitter_ms':jitter_ms,'sensor_age_ms':sensor_age_ms,'sensor_drop':sensor_drop,'burst_ms':burst_ms,'command_channel_stats':action_channel.stats,'sensor_channel_stats':sensor_channel.stats}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--version',type=int,default=3);p.add_argument('--seconds',type=float,default=20);p.add_argument('--delay-ms',type=float,default=0);p.add_argument('--drop',type=float,default=0);p.add_argument('--output',default='mujoco_evaluation.json');p.add_argument('--video',default=None)
    p.add_argument('--seed',type=int,default=123)
    p.add_argument('--command-suite',choices=['fixed','full'],default='fixed')
    p.add_argument('--warmup-seconds',type=float,default=5.)
    p.add_argument('--jitter-ms',type=float,default=0.)
    p.add_argument('--sensor-age-ms',type=float,default=0.)
    p.add_argument('--sensor-drop',type=float,default=0.)
    p.add_argument('--burst-ms',type=float,default=0.)
    a=p.parse_args()
    base=Path(__file__).parent
    cases=[('stand',(0,0,0)),('forward_010',(.1,0,0)),('forward_025',(.25,0,0)),('backward',(-.1,0,0)),('turn_left',(0,0,.3)),('turn_right',(0,0,-.3))]
    if a.command_suite=='full':cases += [('walk_turn',(.15,0,.3)),('start_stop',(0,0,0))]
    result={'checkpoint':a.checkpoint,'contract_version':a.version,'model_source':'same URDF as Isaac Lab','command_suite':a.command_suite,'scope':'preliminary; full acceptance matrix not implemented','cases':[]}
    for name,c in cases:
        r=rollout(base,a.checkpoint,c,a.seed,a.seconds,a.delay_ms,a.drop,a.version,base/a.video if a.video and name=='forward_010' else None,jitter_ms=a.jitter_ms,sensor_age_ms=a.sensor_age_ms,sensor_drop=a.sensor_drop,burst_ms=a.burst_ms,warmup_seconds=a.warmup_seconds,command_schedule='start_stop' if name=='start_stop' else None)
        r['case_name']=name;result['cases'].append(r)
    (base/a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
