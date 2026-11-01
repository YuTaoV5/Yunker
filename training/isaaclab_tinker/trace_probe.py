from pathlib import Path
import json,numpy as np
from mujoco_evaluate import rollout,LIMIT,JOINTS
b=Path(__file__).parent;ck=sorted(b.glob('logs/rsl_rl/tinker_robust_v8/*/model_200.pt'))[-1]
report={'checkpoint':str(ck),'cases':{}}
for name,physics in [('nominal',{}),('gain08',{'gain_scale':.8}),('gain12',{'gain_scale':1.2})]:
    path=b/f'v8_trace200_{name}.npz'
    r=rollout(b,ck,[.1,0,0],123,20.,0.,0.,version=8,physics_config=physics,trace_path=path)
    d=np.load(path);valid=d['time']>min(5.,float(d['time'][-1])*.2);vy=d['velocity_body'][valid,1]
    spec=np.abs(np.fft.rfft(vy-vy.mean()));freq=np.fft.rfftfreq(len(vy),.02);spec[0]=0
    roll=np.arctan2(-d['gravity'][valid,1],-d['gravity'][valid,2])
    summary={k:r[k] for k in ['fell','survived_seconds','xy_axis_rmse','liftoffs_per_foot']}
    summary.update(vy_dominant_hz=float(freq[spec.argmax()]),roll_rms_deg=float(np.sqrt((roll**2).mean())*180/np.pi),joint_tracking_rmse=np.sqrt(((d['target'][valid]-d['q'][valid])**2).mean(0)).tolist(),sampled_torque_saturation_fraction=(np.abs(d['torque'][valid])>=LIMIT*.99).mean(0).tolist(),joint_order=JOINTS,trace=str(path))
    report['cases'][name]=summary;print(name,json.dumps(summary),flush=True)
(b/'v8_trace200_diagnosis.json').write_text(json.dumps(report,indent=2))
