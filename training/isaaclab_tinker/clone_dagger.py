"""Aggregate expert rollouts and safe student-visited states, split by trajectory."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np,torch
p=argparse.ArgumentParser();p.add_argument('--round',type=int,default=1);a=p.parse_args()
b=Path(__file__).parent;torch.manual_seed(703+a.round);torch.set_num_threads(4)
sources=[b/'teacher_isaac_rollouts_1ms.npz']+[b/f'teacher_isaac_rollouts_dagger{i}.npz' for i in range(1,a.round+1)]
train_x=[];train_y=[];val_x=[];val_y=[];metadata=[]
for source in sources:
    d=np.load(source);x=d['observations'];y=d['targets'];valid=d['valid_state'] if 'valid_state' in d else np.ones(x.shape[:2],bool)
    valid&=np.isfinite(x).all(-1)&np.isfinite(y).all(-1)
    train=np.broadcast_to(np.arange(24)%4!=3,valid.shape)&valid
    val=np.broadcast_to(np.arange(24)%4==3,valid.shape)&valid
    train_x.append(x[train]);train_y.append(y[train]);val_x.append(x[val]);val_y.append(y[val])
    metadata.append({'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'train_rows':int(train.sum()),'validation_rows':int(val.sum())})
xt=torch.tensor(np.concatenate(train_x));yt=torch.tensor(np.concatenate(train_y));xv=torch.tensor(np.concatenate(val_x));yv=torch.tensor(np.concatenate(val_y))
actor=torch.nn.Sequential(torch.nn.Linear(195,256),torch.nn.ELU(),torch.nn.Linear(256,128),torch.nn.ELU(),torch.nn.Linear(128,128),torch.nn.ELU(),torch.nn.Linear(128,10))
initial=b/('cloned_actor_bc0.pt' if a.round==1 else f'cloned_actor_dagger{a.round-1}.pt')
actor.load_state_dict(torch.load(initial,map_location='cpu',weights_only=False)['actor_state_dict'])
opt=torch.optim.Adam(actor.parameters(),lr=2e-4);best=float('inf');curve=[]
for epoch in range(150):
    actor.train()
    for ix in torch.randperm(len(xt)).split(1024):
        loss=(actor(xt[ix])-yt[ix]).square().mean();opt.zero_grad();loss.backward();opt.step()
    actor.eval()
    with torch.no_grad():validation=float((actor(xv)-yv).square().mean())
    if validation<best:
        best=validation;torch.save({'actor_state_dict':actor.state_dict(),'input_dim':195,'round':a.round,'sources':metadata,'validation_mse':best,'epoch':epoch,'split':'whole trajectory/env IDs, every fourth held out'},b/f'cloned_actor_dagger{a.round}.pt')
    if epoch%10==0:curve.append({'epoch':epoch,'validation_mse':validation});print(curve[-1],flush=True)
report={'round':a.round,'best_validation_mse':best,'target_angle_rmse_rad':float(np.sqrt(best)*.25),'sources':metadata,'curve':curve,'scope':'same-seed trajectory-held-out fitting only; closed-loop and independent seeds still required'}
(b/f'dagger{a.round}_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
