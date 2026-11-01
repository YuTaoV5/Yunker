"""Diagnostic deployment filter ablation; no robot access and no acceptance claim."""
from pathlib import Path
import json,numpy as np
from mujoco_evaluate import rollout
b=Path(__file__).parent;ck=sorted(b.glob('logs/rsl_rl/tinker_robust_v8/*/model_200.pt'))[-1]
r={'checkpoint':str(ck),'scope':'single-command diagnostic changed filter contract, not v8 acceptance','cases':{}}
for name,value,axes in [('baseline',1.,[1,6]),('roll08',.8,[1,6]),('roll05',.5,[1,6]),('roll03',.3,[1,6]),('all05',.5,list(range(10)))]:
    alpha=np.ones(10);alpha[axes]=value
    out=rollout(b,ck,[.1,0,0],123,20.,0.,0.,version=8,action_filter_alpha=alpha)
    r['cases'][name]={k:out[k] for k in ['fell','survived_seconds','xy_axis_rmse','liftoffs_per_foot','action_filter_alpha']};print(name,r['cases'][name],flush=True)
(b/'v8_filter200_ablation.json').write_text(json.dumps(r,indent=2))
