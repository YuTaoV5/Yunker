import argparse,json
from pathlib import Path
from isaaclab.app import AppLauncher
p=argparse.ArgumentParser();AppLauncher.add_app_launcher_args(p);args=p.parse_args()
app=AppLauncher(args).app
import gymnasium as gym
import torch
import task
cfg=task.TinkerCfg();cfg.scene.num_envs=8
cfg.events.reset_base.params['pose_range']={}
cfg.events.reset_robot_joints.params['position_range']=(1.,1.)
cfg.observations.policy.enable_corruption=False
env=gym.make('Tinker-Flat-v0',cfg=cfg);env.reset()
r=env.unwrapped.scene['robot']
print('JOINT_ORDER',r.joint_names,flush=True)
print('BODY_ORDER',r.body_names,flush=True)
print('INITIAL_HEIGHT',r.data.root_pos_w[:,2].tolist(),flush=True)
assert len(r.joint_names)==10
resets=0;heights=[]
with torch.inference_mode():
    for i in range(250):
        obs,rew,term,trunc,info=env.step(torch.zeros((8,10),device=env.unwrapped.device))
        assert torch.isfinite(r.data.joint_pos).all()
        resets+=int(term.sum())
        heights.append(float(r.data.root_pos_w[:,2].mean()))
result={'zero_action_5s_terminations':resets,'height_min':min(heights),'height_max':max(heights),'joint_names':r.joint_names,'policy_shape':list(obs['policy'].shape)}
print('VALIDATION_RESULT',json.dumps(result),flush=True)
Path('validation.json').write_text(json.dumps(result,indent=2))
env.close();app.close()
