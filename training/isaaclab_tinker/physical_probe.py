"""Independent physical injection smoke/probe, never full acceptance."""
import json
from pathlib import Path
from mujoco_evaluate import rollout
b=Path(__file__).parent
ck=sorted(b.glob('logs/rsl_rl/tinker_robust_v8/*/model_100.pt'))[-1]
cases=[('mass085',{'mass_scale':.85},None),('mass115',{'mass_scale':1.15},None),('com_plus02',{'com_xy':[.02,.02]},None),('friction03',{'friction':.3},None),('gain08',{'gain_scale':.8},None),('encoder_plus02',{'encoder_offset':.02},None),('slope_plus3',{'slope_deg':3.},None),('push02',{'push_delta_v':.2},None),('start_stop',{},'start_stop'),('walk_turn',{},'walk_turn_switch')]
report={'checkpoint':str(ck),'contract_version':8,'scope':'single seed, selected independent physical boundaries and schedules; not full matrix','cases':{}}
for name,physics,schedule in cases:
    r=rollout(b,ck,[.1,0,0],123,31. if schedule else 20.,0.,0.,version=8,physics_config=physics,command_schedule=schedule)
    if 'mass_scale' in physics:assert abs(r['actual_total_mass_kg']-8.4175075*physics['mass_scale'])<1e-4
    if 'push_delta_v' in physics and r['survived_seconds']>5.:assert r['push_applied']
    report['cases'][name]=r
    (b/'v8_physical_probe100.json').write_text(json.dumps(report,indent=2))
    print(name,json.dumps(r),flush=True)
