"""Compare reference-only and learned target tracking, without changing training."""
import argparse,json
from pathlib import Path
import numpy as np
import torch,mujoco
from mujoco_evaluate import build_model,actor_from_checkpoint,JOINTS,DEFAULT,KP,KD,LIMIT
p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);a=p.parse_args();base=Path(__file__).parent
def run(learned):
    m=build_model(base);d=mujoco.MjData(m)
    ids=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,j) for j in JOINTS]
    qi=m.jnt_qposadr[ids];vi=m.jnt_dofadr[ids]
    feet=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,j) for j in ['L4_Link_ankle','R4_Link_ankle']]
    d.qpos[qi]=DEFAULT;mujoco.mj_forward(m,d)
    actor=actor_from_checkpoint(a.checkpoint);raw=np.zeros(10);hist=None;rows=[]
    for step in range(250):
        phase=step*.02*2*np.pi/.7;s=np.sin(phase);l=max(s,0);r=max(-s,0)
        ref=np.zeros(10);ref[[2,3,4,7,8,9]]=[.225*l,-.45*l,-.225*l,-.225*r,.45*r,.225*r]
        rotation=d.xmat[1].reshape(3,3);velocity=np.zeros(6);mujoco.mj_objectVelocity(m,d,mujoco.mjtObj.mjOBJ_BODY,1,velocity,0)
        terms=[rotation.T@velocity[:3]*.25,rotation.T@np.array([0.,0.,-1.]),np.array([.1,0,0]),d.qpos[qi]-DEFAULT,d.qvel[vi]*.05,raw,np.array([np.sin(phase),np.cos(phase)])]
        if hist is None:hist=[[t.copy() for _ in range(5)] for t in terms]
        else:
            for h,t in zip(hist,terms):h.pop(0);h.append(t.copy())
        if learned:
            with torch.no_grad():raw=actor(torch.tensor(np.concatenate([np.concatenate(h) for h in hist])[None],dtype=torch.float32))[0].numpy()
        residual=.125*np.clip(raw,-2,2);target=DEFAULT+ref+residual
        for _ in range(20):
            torque=np.clip(KP*(target-d.qpos[qi])-KD*d.qvel[vi],-LIMIT,LIMIT);d.ctrl[:]=torque;mujoco.mj_step(m,d)
        rows.append({'time':float(d.time),'root_z':float(d.xpos[1,2]),'foot_z':d.xpos[feet,2].tolist(),'q':d.qpos[qi].tolist(),'target':target.tolist(),'ref':ref.tolist(),'residual':residual.tolist(),'torque':torque.tolist()})
    q=np.array([r['q'] for r in rows]);target=np.array([r['target'] for r in rows]);feet_z=np.array([r['foot_z'] for r in rows]);height=np.array([r['root_z'] for r in rows])
    return {'learned':learned,'height_min':float(height.min()),'height_mean':float(height.mean()),'q_tracking_rmse':np.sqrt(((q-target)**2).mean(0)).tolist(),'foot_z_range':(feet_z.max(0)-feet_z.min(0)).tolist(),'max_foot_height_difference':float(np.max(np.abs(feet_z[:,0]-feet_z[:,1]))),'rows':rows}
result={'checkpoint':a.checkpoint,'reference_only':run(False),'learned':run(True)}
(base/'v4_tracking_diagnosis.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:{x:y for x,y in v.items() if x!='rows'} if isinstance(v,dict) else v for k,v in result.items()}),flush=True)
