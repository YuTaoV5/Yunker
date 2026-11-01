"""Per-contact-point tangent velocity audit using raw PhysX contacts."""
import torch

def point_slip_sums(contact_data,com_position,linear_velocity,angular_velocity,normal):
    forces,points,_,_,counts,starts=contact_data
    counts=counts.reshape(-1).long();starts=starts.reshape(-1).long();n=com_position.shape[0]
    filters=counts.numel()//n
    rows=torch.repeat_interleave(torch.arange(counts.numel(),device=counts.device),counts)
    offsets=counts.cumsum(0)-counts
    indices=starts[rows]+torch.arange(rows.numel(),device=counts.device)-offsets[rows]
    env=rows//filters
    force=forces.reshape(-1)[indices].abs()
    velocity=linear_velocity[env]+torch.linalg.cross(angular_velocity[env],points[indices]-com_position[env])
    tangent=velocity-(velocity*normal).sum(-1,keepdim=True)*normal
    valid=force>=1.;weight=torch.where(valid,force,0.)
    squared=torch.zeros(n,device=points.device);total=torch.zeros_like(squared)
    squared.scatter_add_(0,env,weight*tangent.square().sum(-1));total.scatter_add_(0,env,weight)
    number=torch.zeros(n,device=points.device,dtype=torch.long);number.scatter_add_(0,env,valid.long())
    return squared,total,number

def configure(cfg,profile=None):
    from isaaclab.sensors import ContactSensorCfg
    floor='{ENV_REGEX_NS}/sloped_ground' if profile and (abs(profile.get('slope_deg',0.))>0 or profile.get('ground_box',False)) else '/World/ground/.*'
    for side in ['L','R']:
        setattr(cfg.scene,'audit_contact_'+side,ContactSensorCfg(prim_path=cfg.scene.robot.prim_path+'/'+side+'4_Link_ankle',update_period=0.,track_contact_points=True,max_contact_data_count_per_prim=16,filter_prim_paths_expr=[floor]))

def sample(env,normal):
    robot=env.scene['robot'];n=env.num_envs
    squared=torch.zeros(n,device=env.device);weight=torch.zeros_like(squared);number=torch.zeros(n,device=env.device,dtype=torch.long)
    for side in ['L','R']:
        ids,_=robot.find_bodies(side+'4_Link_ankle',preserve_order=True);body=ids[0]
        data=env.scene['audit_contact_'+side].contact_physx_view.get_contact_data(dt=env.physics_dt)
        s,w,c=point_slip_sums(data,robot.data.body_com_pos_w[:,body],robot.data.body_com_lin_vel_w[:,body],robot.data.body_com_ang_vel_w[:,body],normal)
        squared+=s;weight+=w;number+=c
    return squared,weight,number

def self_test(device='cpu'):
    forces=torch.zeros((6,1),device=device);forces[[0,2,3,5],0]=torch.tensor([5.,2.,3.,4.],device=device)
    points=torch.zeros((6,3),device=device);norm=torch.tensor([0.,0.,1.],device=device)
    counts=torch.tensor([[2,0],[1,1]],device=device);starts=torch.tensor([[2,0],[5,0]],device=device)
    pos=torch.zeros((2,3),device=device);lin=torch.tensor([[.1,0.,0.],[.2,0.,0.]],device=device);ang=torch.zeros_like(pos)
    s,w,c=point_slip_sums((forces,points,None,None,counts,starts),pos,lin,ang,norm)
    assert torch.allclose(w,torch.tensor([5.,9.],device=device));assert torch.allclose(s/w,torch.tensor([.01,.04],device=device))
    points[:,0]=1.;lin[:]=0.;ang[:,2]=2.
    s,w,c=point_slip_sums((forces,points,None,None,counts,starts),pos,lin,ang,norm);assert torch.allclose(s/w,torch.ones(2,device=device)*4.)
    counts[:]=0;s,w,c=point_slip_sums((forces,points,None,None,counts,starts),pos,lin,ang,norm);assert not c.any() and not w.any()
    return dict(device=device,noncontiguous_contact_buffer=True,rigid_rotation=True,no_contact=True)
if __name__=='__main__':
    import json
    print(json.dumps(self_test()))
    if torch.cuda.is_available():print(json.dumps(self_test('cuda')))
