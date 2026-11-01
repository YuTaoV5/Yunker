"""Behavior cloning on whole-trajectory splits; no random row-level leakage."""
import json,hashlib
from pathlib import Path
import numpy as np,torch
b=Path(__file__).parent;torch.manual_seed(702);torch.set_num_threads(4)
source=b/'teacher_isaac_rollouts_1ms.npz';d=np.load(source)
x=d['observations'];y=d['targets'];success=d['trajectory_success']
assert x.ndim==3 and x.shape[1]==24 and x.shape[2]==195
train_ids=[i for i in range(24) if i%4!=3 and success[i]]
val_ids=[i for i in range(24) if i%4==3 and success[i]]
assert train_ids and val_ids
xt=torch.tensor(x[:,train_ids].reshape(-1,195),dtype=torch.float32);yt=torch.tensor(y[:,train_ids].reshape(-1,10),dtype=torch.float32)
xv=torch.tensor(x[:,val_ids].reshape(-1,195),dtype=torch.float32);yv=torch.tensor(y[:,val_ids].reshape(-1,10),dtype=torch.float32)
actor=torch.nn.Sequential(torch.nn.Linear(195,256),torch.nn.ELU(),torch.nn.Linear(256,128),torch.nn.ELU(),torch.nn.Linear(128,128),torch.nn.ELU(),torch.nn.Linear(128,10))
opt=torch.optim.Adam(actor.parameters(),lr=1e-3);best=float('inf');log=[]
for epoch in range(150):
    actor.train();order=torch.randperm(len(xt))
    for ix in order.split(1024):
        loss=(actor(xt[ix])-yt[ix]).square().mean();opt.zero_grad();loss.backward();opt.step()
    actor.eval()
    with torch.no_grad():val=float((actor(xv)-yv).square().mean());train=float((actor(xt)-yt).square().mean())
    if val<best:
        best=val;torch.save({'actor_state_dict':actor.state_dict(),'input_dim':195,'seed':702,'train_env_ids':train_ids,'validation_env_ids':val_ids,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'validation_mse':val,'epoch':epoch},b/'cloned_actor.pt')
    if epoch%10==0:log.append({'epoch':epoch,'train_mse':train,'validation_mse':val});print(log[-1],flush=True)
result={'best_validation_action_mse':best,'best_validation_target_angle_rmse_rad':float(np.sqrt(best)*.25),'train_trajectories':train_ids,'validation_trajectories':val_ids,'scope':'same seed held-out whole trajectories; independent simulation rollout not yet passed','learning_curve':log}
(b/'clone_report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
