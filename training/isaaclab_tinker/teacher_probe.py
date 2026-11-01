"""Run the hash-matched existing robot policy as a simulation diagnostic baseline."""
import hashlib,json
from pathlib import Path
import numpy as np,mujoco
from scipy.spatial.transform import Rotation
from mujoco_evaluate import build_model,JOINTS,DEFAULT,KP,KD,LIMIT
from real_teacher import TinkerRealInference
b=Path(__file__).parent;path=b/'teacher_finall.onnx'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='9da84f4596ed2c3428d78f3c9f7cb5a61036fe0060b5d49ec11356fdd91d0808'
results=[]
for post in [True,False]:
    for vx in [0.,.1,.25]:
        m=build_model(b);d=mujoco.MjData(m);j=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,n) for n in JOINTS];qi=m.jnt_qposadr[j];vi=m.jnt_dofadr[j]
        feet=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,n) for n in ['L4_Link_ankle','R4_Link_ankle']]
        d.qpos[qi]=DEFAULT;mujoco.mj_forward(m,d);policy=TinkerRealInference(str(path),str(path))
        if not post:policy._swing_smooth=lambda q:None
        errors=[];liftoffs=np.zeros(2,dtype=int);prev=np.ones(2,dtype=bool);fell=False
        for i in range(500):
            rot=d.xmat[1].reshape(3,3);vel=np.zeros(6);mujoco.mj_objectVelocity(m,d,mujoco.mjtObj.mjOBJ_BODY,1,vel,0)
            euler=Rotation.from_matrix(rot).as_euler('xyz')
            target=policy.get_action(euler,rot.T@vel[:3],d.qpos[qi].copy(),d.qvel[vi].copy(),vx,0,0,use_step_model=vx!=0)
            for _ in range(20):d.ctrl[:]=np.clip(KP*(target-d.qpos[qi])-KD*d.qvel[vi],-LIMIT,LIMIT);mujoco.mj_step(m,d)
            normal=np.zeros(2)
            for k in range(d.ncon):
                con=d.contact[k];f=np.zeros(6);mujoco.mj_contactForce(m,d,k,f)
                for z,bid in enumerate(feet):
                    if bid in (m.geom_bodyid[con.geom1],m.geom_bodyid[con.geom2]):normal[z]+=abs(f[0])
            contact=normal>=1;liftoffs+=prev&~contact;prev=contact
            if i>=100:errors.append((float((rot.T@vel[3:])[0])-vx)**2)
            if d.xpos[1,2]<.18 or d.xmat[1].reshape(3,3)[2,2]<.7:fell=True;break
        results.append({'postprocessing_enabled':post,'vx':vx,'fell':fell,'seconds':float(d.time),'liftoffs':liftoffs.tolist(),'vx_rmse':float(np.sqrt(np.mean(errors))) if errors else None,'final_step_decay':float(policy._step_decay)})
(b/'teacher_probe.json').write_text(json.dumps(results,indent=2));print(json.dumps(results),flush=True)
