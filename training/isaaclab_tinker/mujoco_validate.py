"""Zero-action and URDF inertial audit independent of neural policy."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import mujoco
from mujoco_evaluate import build_model,JOINTS,DEFAULT,KP,KD,LIMIT
b=Path(__file__).parent;m=build_model(b);d=mujoco.MjData(m)
ji=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,n) for n in JOINTS]
qi=m.jnt_qposadr[ji];vi=m.jnt_dofadr[ji]
ai=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_ACTUATOR,n) for n in JOINTS]
d.qpos[qi]=DEFAULT;mujoco.mj_forward(m,d)
root=ET.parse(b/'assets/urdf/TinkerV2_URDF.urdf').getroot()
expected={x.get('name'):float(x.find('inertial/mass').get('value')) for x in root.findall('link') if x.find('inertial/mass') is not None}
audit={'urdf_total_mass':sum(expected.values()),'mujoco_total_mass':float(m.body_mass.sum()),'initial_root_z':float(d.xpos[1,2]),'initial_min_geometry_z':float(d.geom_xpos[:,2].min()),'nq':m.nq,'nv':m.nv,'actuator_joint_ids':m.actuator_trnid[:,0].tolist(),'expected_joint_ids':ji,'samples':[]}
for i in range(int(5/m.opt.timestep)):
    d.ctrl[ai]=np.clip(KP*(DEFAULT-d.qpos[qi])-KD*d.qvel[vi],-LIMIT,LIMIT)
    mujoco.mj_step(m,d)
    if i%100==0:audit['samples'].append({'time':float(d.time),'height':float(d.xpos[1,2]),'contacts':d.ncon,'max_qerror':float(np.abs(d.qpos[qi]-DEFAULT).max()),'max_qvel':float(np.abs(d.qvel[vi]).max())})
audit['final_height']=float(d.xpos[1,2]);audit['final_joint_positions']=d.qpos[qi].tolist()
(b/'mujoco_validation.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit),flush=True)
