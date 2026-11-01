"""Candidate integration, not registered into active training."""
from isaaclab.envs.mdp.commands.velocity_command import UniformVelocityCommand
from balanced_command_sampler import sample_commands
class BalancedVelocityCommand(UniformVelocityCommand):
    def _resample_command(self,env_ids):
        super()._resample_command(env_ids)
        command,modes=sample_commands(len(env_ids),self.device)
        self.vel_command_b[env_ids]=command
        self.is_standing_env[env_ids]=modes==0
