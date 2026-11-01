"""Not active: controlled command-coverage candidate, preserving V10 otherwise."""
import gymnasium as gym
from isaaclab.utils import configclass
from iteration10 import V10Cfg,V10PPO
from balanced_velocity_command_candidate import BalancedVelocityCommand

@configclass
class V11CandidateCfg(V10Cfg):
    def __post_init__(self):
        super().__post_init__()
        self.commands.base_velocity.class_type=BalancedVelocityCommand

@configclass
class V11CandidatePPO(V10PPO):
    def __post_init__(self):
        super().__post_init__()
        self.experiment_name='tinker_robust_v11_candidate'

def assert_controlled_configs():
    new=V11CandidateCfg().to_dict();old=V10Cfg().to_dict()
    new_class=new['commands']['base_velocity'].pop('class_type')
    old_class=old['commands']['base_velocity'].pop('class_type')
    assert new_class!=old_class
    assert new==old,'Candidate changed more than the command sampler'
    new=V11CandidatePPO().to_dict();old=V10PPO().to_dict()
    new.pop('experiment_name');old.pop('experiment_name')
    assert new==old,'Candidate changed PPO settings'
    return {'candidate_only':True,'task_difference':'commands.base_velocity.class_type only','algorithm_difference':'experiment_name only','deployment_contract':'unchanged V10 195D direct action','initialization_plan':'same DAgger1 actor and seed49; not started'}

gym.register(id='Tinker-Robust-v11-candidate',entry_point='isaaclab.envs:ManagerBasedRLEnv',disable_env_checker=True,kwargs={'env_cfg_entry_point':V11CandidateCfg,'rsl_rl_cfg_entry_point':V11CandidatePPO})
