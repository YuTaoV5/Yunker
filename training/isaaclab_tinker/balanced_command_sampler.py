"""Candidate sampler only; active V10 training does not import this module."""
import torch
PROBABILITIES=[.15,.15,.15,.10,.10,.10,.05,.05,.15]
COMMANDS=[[0.,0.,0.],[.1,0.,0.],[.25,0.,0.],[-.1,0.,0.],[0.,0.,.3],[0.,0.,-.3],[.15,0.,.3],[.15,0.,-.3],[0.,0.,0.]]
def sample_commands(count,device,generator=None):
    probs=torch.tensor(PROBABILITIES,device=device);modes=torch.multinomial(probs,count,replacement=True,generator=generator)
    command=torch.tensor(COMMANDS,device=device)[modes].clone();continuous=modes==8
    random_x=torch.rand(count,device=device,generator=generator)*.4-.1
    random_yaw=torch.rand(count,device=device,generator=generator)*.6-.3
    command[continuous,0]=random_x[continuous];command[continuous,2]=random_yaw[continuous]
    return command,modes

def audit_uniform(count=200000,device='cpu'):
    g=torch.Generator(device=device).manual_seed(1029)
    x=torch.rand(count,device=device,generator=g)*.4-.1;yaw=torch.rand(count,device=device,generator=g)*.6-.3
    standing=torch.rand(count,device=device,generator=g)<.2;x[standing]=0.;yaw[standing]=0.
    pure_turn=(x.abs()<.005)&(yaw.abs()>.25)
    backward=(x<-.05)&(yaw.abs()<.05)
    return dict(near_pure_turn_fraction=float(pure_turn.float().mean()),near_straight_backward_fraction=float(backward.float().mean()),standing_fraction=float(standing.float().mean()),definition='turn |vx|<.005 & |yaw|>.25; backward vx<-.05 & |yaw|<.05')

def self_test(device='cpu'):
    g=torch.Generator(device=device).manual_seed(1029);c,m=sample_commands(200000,device,g)
    freq=torch.bincount(m,minlength=9).float()/len(m)
    assert (freq-torch.tensor(PROBABILITIES,device=device)).abs().max()<.005
    assert torch.equal(c[m==4],torch.tensor([0.,0.,.3],device=device).expand((m==4).sum(),3))
    assert c[:,0].min()>=-.100001 and c[:,0].max()<=.300001 and c[:,2].abs().max()<=.300001
    return dict(device=device,mode_frequencies=freq.cpu().tolist(),pure_turn_fraction=float(((c[:,0]==0.)&(c[:,2].abs()>.25)).float().mean()),candidate_only=True)
if __name__=='__main__':
    import json
    print(json.dumps({'uniform_audit':audit_uniform(),'candidate':self_test()}))
    if torch.cuda.is_available():print(json.dumps(self_test('cuda')))
