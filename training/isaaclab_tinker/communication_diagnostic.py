"""Single-seed 20s communication diagnostic; not the complete acceptance matrix."""
from pathlib import Path
import json
from mujoco_evaluate import rollout
b=Path(__file__).parent;ck=sorted(b.glob('logs/rsl_rl/tinker_robust_v10/*/model_600.pt'))[-1]
profiles={'nominal':{},'delay60':{'delay_ms':60},'jitter20':{'delay_ms':20,'jitter_ms':20},'drop10percent':{'drop':.1},'burst200':{'burst_ms':200},'sensor_age80':{'sensor_age_ms':80},'combined':{'delay_ms':40,'jitter_ms':20,'drop':.05,'burst_ms':100,'sensor_age_ms':40,'sensor_drop':.03}}
report={'checkpoint':str(ck),'contract_version':10,'scope':'single seed 123, 20s/5s warmup, two commands; no acceptance PASS','cases':{}}
for speed in [.1,.25]:
    for name,p in profiles.items():
        r=rollout(b,ck,[speed,0.,0.],123,20.,delay_ms=p.get('delay_ms',0.),drop=p.get('drop',0.),version=10,jitter_ms=p.get('jitter_ms',0.),sensor_age_ms=p.get('sensor_age_ms',0.),sensor_drop=p.get('sensor_drop',0.),burst_ms=p.get('burst_ms',0.))
        report['cases'][str(speed)+'_'+name]=r
        (b/'v10_communication600_v2.json').write_text(json.dumps(report,indent=2))
        print(speed,name,'fell',r['fell'],'xy',r['xy_rmse'],'unloads',r['geometric_liftoff_diagnostics']['qualified_unloads_per_foot'],flush=True)
