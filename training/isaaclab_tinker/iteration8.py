"""V8: same deployment contract as v7; PPO with forward demonstration rehearsal."""
import gymnasium as gym
from pathlib import Path
from isaaclab.utils import configclass
from iteration7 import V7Cfg,V7PPO
from anchored_ppo import AnchoredPPO
import rsl_rl.runners.on_policy_runner as runner_module
runner_module.AnchoredPPO=AnchoredPPO

@configclass
class V8Cfg(V7Cfg):
    pass

@configclass
class V8PPO(V7PPO):
    def __post_init__(self):
        super().__post_init__();self.experiment_name='tinker_robust_v8'
        self.algorithm.class_name='AnchoredPPO'
        self.algorithm.schedule='fixed';self.algorithm.learning_rate=3e-5
        b=Path(__file__).parent
        self.algorithm.anchor_sources=[str(b/'teacher_isaac_rollouts_1ms.npz'),str(b/'teacher_isaac_rollouts_dagger1.npz')]
        self.algorithm.anchor_coefficient=10.

gym.register(id='Tinker-Robust-v8',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':V8Cfg,'rsl_rl_cfg_entry_point':V8PPO})
