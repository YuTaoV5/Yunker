"""Quasi-static weight-transfer sweep with actual foot forces; no policy training."""
import itertools,json
from pathlib import Path
import numpy as np
import mujoco
from mujoco_evaluate import build_model,JOINTS,DEFAULT,KP,KD,LIMIT
b=Path(__file__).parent;m=build_model(b)
j=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,n) for n in JOINTS];qi=m.jnt_qposadr[j];vi=m.jnt_dofadr[j]
feet=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,n) for n in ['L4_Link_ankle','R4_Link_ankle']]
result=[]
for roll,extension in itertools.product([.08,.16,.24,.30],[0.,.1,.2]):
    d=mujoco.MjData(m);d.qpos[qi]=DEFAULT;mujoco.mj_forward(m,d);rows=[];fell=False
    for tick in range(250):
        t=tick*.02;lean=np.clip((t-.5)/1.5,0,1);lift=np.clip((t-2.)/1.5,0,1)
        ref=np.zeros(10);ref[[1,6]]=-roll*lean
        ref[[2,3,4]]=[.225*lift,-.45*lift,-.225*lift]
        ref[[7,8,9]]=[extension/2*lean,-extension*lean,-extension/2*lean]
        target=DEFAULT+ref
        for _ in range(20):
            d.ctrl[:]=np.clip(KP*(target-d.qpos[qi])-KD*d.qvel[vi],-LIMIT,LIMIT);mujoco.mj_step(m,d)
        normal=np.zeros(2)
        for k in range(d.ncon):
            con=d.contact[k];f=np.zeros(6);mujoco.mj_contactForce(m,d,k,f)
            for z,bid in enumerate(feet):
                if bid in (m.geom_bodyid[con.geom1],m.geom_bodyid[con.geom2]):normal[z]+=abs(f[0])
        rows.append({'t':float(d.time),'root_z':float(d.xpos[1,2]),'foot_force':normal.tolist(),'foot_z':d.xpos[feet,2].tolist(),'com':d.subtree_com[1].tolist(),'q':d.qpos[qi].tolist()})
        if d.xpos[1,2]<.18 or d.xmat[1].reshape(3,3)[2,2]<.7:fell=True;break
    final=[r for r in rows if r['t']>=4]
    result.append({'roll':roll,'support_knee_extension':extension,'fell':fell,'seconds':float(d.time),'left_unloaded_fraction_last_second':sum(r['foot_force'][0]<1 for r in final)/len(final) if final else 0,'mean_final_forces':np.mean([r['foot_force'] for r in final],axis=0).tolist() if final else [],'rows':rows})
(b/'support_transfer_probe.json').write_text(json.dumps(result,indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='rows'} for r in result]))
