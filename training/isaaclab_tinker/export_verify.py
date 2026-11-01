"""Verify checkpoint reconstruction and ONNX against an Isaac Lab observation/action pair."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import torch
import onnxruntime as ort
from mujoco_evaluate import actor_from_checkpoint,JOINTS,DEFAULT,KP,KD
p=argparse.ArgumentParser();p.add_argument('--parity',required=True);a=p.parse_args()
data=json.loads(Path(a.parity).read_text());assert not data.get('actor_override'),'Counterfactual actor override is not a standalone checkpoint export';checkpoint=Path(data['checkpoint'])
actor=actor_from_checkpoint(checkpoint);x=torch.tensor([data['observation']],dtype=torch.float32)
with torch.no_grad():actual=actor(x).numpy()
reference=np.array([data['action']],dtype=np.float32)
torch_error=float(np.max(np.abs(actual-reference)))
out=Path(__file__).parent/'exports'/checkpoint.parent.name/checkpoint.stem;out.mkdir(parents=True,exist_ok=True)
torch.onnx.export(actor,x,str(out/'policy.onnx'),input_names=['observation'],output_names=['action'],opset_version=17,dynamo=False)
session=ort.InferenceSession(str(out/'policy.onnx'),providers=['CPUExecutionProvider'])
onnx_error=float(np.max(np.abs(session.run(None,{'observation':x.numpy()})[0]-actual)))
rng=np.random.default_rng(42);random_errors=[]
for _ in range(100):
    z=rng.normal(0,.5,(1,x.shape[1])).astype(np.float32)
    with torch.no_grad():expected=actor(torch.from_numpy(z)).numpy()
    random_errors.append(float(np.max(np.abs(session.run(None,{'observation':z})[0]-expected))))
result={'checkpoint':str(checkpoint),'isaac_to_reconstructed_torch_max_abs_error':torch_error,'onnx_sample_max_abs_error':onnx_error,'onnx_100_random_max_abs_error':max(random_errors),'threshold':1e-5,'pass':max(torch_error,onnx_error,max(random_errors))<=1e-5,'joint_order':JOINTS,'default_angles':DEFAULT.tolist(),'kp':KP.tolist(),'kd':KD.tolist(),'control_hz':50,'action_scale':.25,'obs_dimension':int(x.shape[1]),'observation_terms':data['observation_terms'],'history':'5 samples per term, chronological, oldest first; term histories concatenated','status':'export consistency only; not locomotion acceptance'}
result['checkpoint_sha256']=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
result['onnx_sha256']=hashlib.sha256((out/'policy.onnx').read_bytes()).hexdigest()
result['contract_version']=10 if 'tinker_robust_v10' in str(checkpoint) else 9 if 'tinker_robust_v9' in str(checkpoint) else 8 if 'tinker_robust_v8' in str(checkpoint) else 7 if 'tinker_robust_v7' in str(checkpoint) else 'unspecified'
if result['contract_version'] in (7,8,9,10):
    result['target_mapping']='clip(default + .25 * action, physical joint position limits); direct action, no phase reference'
    result['physics_dt_seconds']=.001
(out/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
