"""Screen reference candidates in MuJoCo; diagnostic only, not policy acceptance."""
import json,itertools
from pathlib import Path
import numpy as np
import mujoco
from mujoco_evaluate import build_model,JOINTS,DEFAULT,KP,KD,LIMIT
b=Path(__file__).parent;model=build_model(b)
ids=[mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_JOINT,n) for n in JOINTS];qi=model.jnt_qposadr[ids];vi=model.jnt_dofadr[ids]
feet=[mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,n) for n in ['L4_Link_ankle','R4_Link_ankle']]
results=[]
for amp,lead,knee in itertools.product([.04,.08,.12],[0.,np.pi/4,np.pi/2],[.3,.45]):
    d=mujoco.MjData(model);d.qpos[qi]=DEFAULT;mujoco.mj_forward(model,d);unload=0;minheight=1;peakdifference=0
    for step in range(250):
        t=step*.02;phase=t*2*np.pi/.7;s=np.sin(phase);l=max(s,0);r=max(-s,0)
        ref=np.zeros(10);ref[[1,6]]=-amp*np.sin(phase+lead)
        ref[[2,3,4,7,8,9]]=[knee/2*l,-knee*l,-knee/2*l,-knee/2*r,knee*r,knee/2*r]
        for _ in range(20):
            model.opt.timestep=.001;d.ctrl[:]=np.clip(KP*(DEFAULT+ref-d.qpos[qi])-KD*d.qvel[vi],-LIMIT,LIMIT);mujoco.mj_step(model,d)
        minheight=min(minheight,float(d.xpos[1,2]));difference=abs(float(d.xpos[feet[0],2]-d.xpos[feet[1],2]));peakdifference=max(peakdifference,difference)
        unload+=difference>.015
        if d.xpos[1,2]<.18 or d.xmat[1].reshape(3,3)[2,2]<.7:break
    results.append({'roll_amplitude':amp,'phase_lead':lead,'knee_amplitude':knee,'survived_seconds':float(d.time),'min_height':minheight,'steps_with_foot_height_difference_gt15mm':unload,'peak_foot_height_difference':peakdifference,'x':float(d.xpos[1,0])})
results.sort(key=lambda x:(x['survived_seconds'],x['steps_with_foot_height_difference_gt15mm']),reverse=True)
(b/'reference_screening.json').write_text(json.dumps(results,indent=2));print(json.dumps(results[:5]),flush=True)
