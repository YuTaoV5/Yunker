"""Small independent communication-boundary subset; not full acceptance."""
import argparse,json
from pathlib import Path
from mujoco_evaluate import rollout
p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);p.add_argument('--seconds',type=float,default=20);p.add_argument('--output',default='boundary_probe.json');a=p.parse_args()
b=Path(__file__).parent
scenarios=[('nominal',{}),('delay20',{'delay_ms':20}),('delay20_jitter10',{'delay_ms':20,'jitter_ms':10}),('drop5percent',{'drop':.05}),('burst100',{'burst_ms':100}),('sensor_age40',{'sensor_age_ms':40}),('sensor_drop5percent',{'sensor_drop':.05})]
result={'checkpoint':a.checkpoint,'simulator':'MuJoCo','contract_version':7,'command':[.1,0,0],'scope':'single command, single seed communication subset; no acceptance PASS implied','cases':{}}
for name,params in scenarios:
    settings={'delay_ms':0.,'drop':0.};settings.update(params)
    result['cases'][name]=rollout(b,a.checkpoint,(.1,0,0),123,a.seconds,version=7,**settings)
(b/a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
