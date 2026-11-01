"""Candidate-only native command-manager check. Never starts training or hardware."""
import argparse,json
from pathlib import Path
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args()
app=AppLauncher(args).app
import torch,gymnasium as gym
from iteration11_candidate import V11CandidateCfg,assert_controlled_configs
from balanced_command_sampler import COMMANDS,PROBABILITIES
result=assert_controlled_configs()
cfg=V11CandidateCfg();cfg.scene.num_envs=64;cfg.seed=49;cfg.sim.device=args.device
env=gym.make('Tinker-Robust-v11-candidate',cfg=cfg).unwrapped
term=env.command_manager.get_term('base_velocity');ids=torch.arange(env.num_envs,device=env.device)
counts=torch.zeros(8,device=env.device);total=0
for _ in range(256):
    term._resample_command(ids);term._update_command()
    command=term.command
    assert torch.isfinite(command).all()
    assert command[:,0].min()>=-.100001 and command[:,0].max()<=.300001
    assert command[:,2].abs().max()<=.300001 and command[:,1].abs().max()==0
    for index,expected in enumerate(COMMANDS[:8]):
        counts[index]+=torch.isclose(command,torch.tensor(expected,device=env.device),atol=1e-7,rtol=0).all(-1).sum()
    total+=len(ids)
frequencies=counts/total
assert (frequencies-torch.tensor(PROBABILITIES[:8],device=env.device)).abs().max()<.015
env.step(torch.zeros((64,10),device=env.device))
result.update(native_manager_samples=total,exact_task_frequencies=frequencies.cpu().tolist(),one_physics_step_pass=True,status='IMPLEMENTATION_CHECK_ONLY_NOT_GAIT_ACCEPTANCE')
Path('command_candidate_integration_check.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result));env.close();app.close()
