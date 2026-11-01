"""Behavioral counterexamples for qualified, alternating landings."""
import ast,torch
from pathlib import Path
from types import SimpleNamespace
src=Path(__file__).with_name('iteration9.py').read_text();tree=ast.parse(src);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='alternating_landing')
namespace={'torch':torch};exec(compile(ast.Module(body=[node],type_ignores=[]),'<landing_reward>','exec'),namespace);reward=namespace['alternating_landing']
forces=torch.ones((2,2,3));cmd=torch.tensor([[.1,0.,0.],[0.,0.,0.]])
sensor=SimpleNamespace(data=SimpleNamespace(net_forces_w=forces),find_bodies=lambda *a,**k:([0,1],None))
env=SimpleNamespace(num_envs=2,device='cpu',step_dt=.02,episode_length_buf=torch.ones(2,dtype=torch.long)*5,scene={'contact_forces':sensor},command_manager=SimpleNamespace(get_command=lambda _:cmd))
events={}
for tick in range(20):
    env.common_step_counter=tick;forces[:]=1.
    foot=0 if 1<=tick<=5 or 7<=tick<=11 else 1 if 13<=tick<=17 else None
    if foot is not None:forces[:,foot,:]=0.
    out=reward(env);assert out[1]==0,'Standing command received gait reward'
    if out[0]>0:events[tick]=float(out[0])
assert set(events)=={6,18},events
assert abs(events[6]-.1)<1e-6 and abs(events[18]-.1)<1e-6
# Calling a reward twice in one control step must not advance its state.
assert torch.equal(reward(env),out)
print('PASS alternating touchdown, repeated same foot rejection, standing exclusion, per-tick cache',events)
