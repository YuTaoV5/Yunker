"""Evaluation-only 1kHz joint-state audit, read-only with respect to controls."""
import torch

@torch.inference_mode()
def audit(env):
    r=env.scene['robot'];q=r.data.joint_pos;dq=r.data.joint_vel;limits=r.data.joint_pos_limits
    state=getattr(env,'_tinker_safety_audit',None)
    if state is None:
        state={'violation_samples':torch.zeros(env.num_envs,device=env.device,dtype=torch.long),'nonfinite_samples':torch.zeros(env.num_envs,device=env.device,dtype=torch.long),'max_excursion':torch.zeros(env.num_envs,device=env.device),'ticks':0}
    excess=torch.maximum(limits[:,:,0]-q,q-limits[:,:,1]).amax(-1).clamp(min=0.)
    state['violation_samples']+=(excess>0).long()
    state['nonfinite_samples']+=(~torch.isfinite(q).all(-1)|~torch.isfinite(dq).all(-1)).long()
    state['max_excursion']=torch.maximum(state['max_excursion'],excess);state['ticks']+=1
    env._tinker_safety_audit=state

class AuditMixin:
    def apply_actions(self):
        audit(self._env)
        super().apply_actions()

def configure(cfg):
    original=cfg.actions.joint_pos.class_type
    cfg.actions.joint_pos.class_type=type('Audited'+original.__name__,(AuditMixin,original),{})

def report(env):
    state=env._tinker_safety_audit
    return {'joint_limit_violation_physics_samples':state['violation_samples'].cpu().tolist(),'nonfinite_joint_state_physics_samples':state['nonfinite_samples'].cpu().tolist(),'maximum_joint_limit_excursion_rad':state['max_excursion'].cpu().tolist(),'sample_hz':1/env.physics_dt,'ticks':state['ticks'],'tolerance_rad':0.}
