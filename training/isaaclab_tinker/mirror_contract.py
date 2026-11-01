"""Reflection about body Y=0 for the 195D Tinker direct-action contract.
This is a kinematic transform, not a claim of exact mass/contact symmetry.
"""
import torch
DEFAULT=[0.,.08,.56,-1.12,-.57,0.,-.08,-.56,1.12,.57]
LOW=[-.7,-.38,-1.57,-2.35,-1.2,-.7,-.38,-1.57,0.,-1.2]
HIGH=[.7,.46,1.57,0.,1.2,.7,.47,1.57,2.35,1.2]
PERM=[5,6,7,8,9,0,1,2,3,4]
def mirror_actions(actions):
    assert actions.shape[-1]==10
    return -actions[...,PERM]
def mirror_observation(observation):
    assert observation.shape[-1]==195
    out=observation.clone()
    for start,width,sign in [(0,3,[-1.,1.,-1.]),(15,3,[1.,-1.,1.]),(30,3,[1.,-1.,-1.])]:
        out[...,start:start+15]=(observation[...,start:start+15].reshape(*observation.shape[:-1],5,width)*torch.tensor(sign,device=observation.device,dtype=observation.dtype)).reshape(*observation.shape[:-1],15)
    for start in [45,95,145]:
        out[...,start:start+50]=mirror_actions(observation[...,start:start+50].reshape(*observation.shape[:-1],5,10)).reshape(*observation.shape[:-1],50)
    return out
def physical_mirror_mask(observation,actions=None):
    default=torch.tensor(DEFAULT,device=observation.device,dtype=observation.dtype)
    low=torch.tensor(LOW,device=observation.device,dtype=observation.dtype);high=torch.tensor(HIGH,device=observation.device,dtype=observation.dtype)
    q=observation[...,45:95].reshape(*observation.shape[:-1],5,10)+default
    mirrored=mirror_actions(q)
    valid=((q>=low)&(q<=high)&(mirrored>=low)&(mirrored<=high)).all(-1).all(-1)
    if actions is not None:
        target=default+.25*actions;mirror_target=mirror_actions(target)
        valid&=((target>=low)&(target<=high)&(mirror_target>=low)&(mirror_target<=high)).all(-1)
    return valid

def self_test(device='cpu'):
    torch.manual_seed(91);x=torch.randn((64,195),device=device);a=torch.randn((64,10),device=device)
    assert torch.equal(mirror_observation(mirror_observation(x)),x)
    assert torch.equal(mirror_actions(mirror_actions(a)),a)
    zeros=torch.zeros((1,195),device=device);assert physical_mirror_mask(zeros,torch.zeros((1,10),device=device)).all()
    # Actual left/right hip-roll limits differ. Reject mirrored states outside them.
    invalid=zeros.clone();invalid[:,85+1]=.46-.08
    assert not physical_mirror_mask(invalid).any()
    return dict(device=device,involution=True,history_layout=True,asymmetric_limit_guard=True)
if __name__=='__main__':
    import json
    print(json.dumps(self_test()))
    if torch.cuda.is_available():print(json.dumps(self_test('cuda')))
