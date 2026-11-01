"""Shared NumPy/Torch velocity-conditioned reference, in physical radians."""
def reference(s,c,commands):
    import numpy as np
    is_torch=type(s).__module__.startswith('torch')
    if is_torch:
        import torch
        moving=(torch.linalg.vector_norm(commands[...,:2],dim=-1)+commands[...,2].abs())>.05
        l=s.clamp(min=0)*moving;r=(-s).clamp(min=0)*moving
        delta=torch.zeros((*s.shape,10),device=s.device,dtype=s.dtype)
        stride=commands[...,0].clamp(-.15,.3)*.7
    else:
        moving=(np.linalg.norm(commands[...,:2],axis=-1)+np.abs(commands[...,2]))>.05
        l=np.maximum(s,0)*moving;r=np.maximum(-s,0)*moving
        delta=np.zeros((*s.shape,10),dtype=s.dtype)
        stride=np.clip(commands[...,0],-.15,.3)*.7
    delta[...,1]=delta[...,6]=-.08*s*moving
    step=stride*c*moving
    delta[...,2]=.225*l+step;delta[...,3]=-.45*l;delta[...,4]=-.225*l+step
    delta[...,7]=-.225*r+step;delta[...,8]=.45*r;delta[...,9]=.225*r+step
    turn=commands[...,2]*(.7/4)*c*moving
    delta[...,0]=-turn;delta[...,5]=turn
    return delta
