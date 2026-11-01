"""V10 controlled initialization study: V9 task/algorithm, DAgger actor init."""
import gymnasium as gym
from isaaclab.utils import configclass
from iteration9 import V9Cfg,V9PPO
@configclass
class V10Cfg(V9Cfg):
    pass
@configclass
class V10PPO(V9PPO):
    def __post_init__(self):
        super().__post_init__();self.experiment_name='tinker_robust_v10'
def assert_controlled_configs():
    assert V10Cfg().to_dict()==V9Cfg().to_dict(),'Task changed in initialization-only study'
    a=V10PPO().to_dict();b=V9PPO().to_dict();a.pop('experiment_name');b.pop('experiment_name')
    assert a==b,'Algorithm changed in initialization-only study'
    print('CONTROLLED_CONFIG_CHECK: identical V9/V10 task and algorithm, excluding experiment name',flush=True)
gym.register(id='Tinker-Robust-v10',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':V10Cfg,'rsl_rl_cfg_entry_point':V10PPO})
