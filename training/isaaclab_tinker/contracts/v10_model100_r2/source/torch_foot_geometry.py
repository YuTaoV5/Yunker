"""Collision mesh support distance, in link frames and WXYZ quaternions."""
import json,torch
from pathlib import Path
class FootGeometry:
    names=['L4_Link_ankle','R4_Link_ankle']
    def __init__(self,path,device):
        data=json.loads(Path(path).read_text());self.urdf_sha256=data['urdf_sha256']
        self.points=[torch.tensor(data['feet'][name],device=device,dtype=torch.float32) for name in self.names]
    def clearance(self,pos,quat,normal=None,origin=None):
        n=torch.zeros_like(pos[:,0,:]);n[:,2]=1.
        if normal is not None:n[:]=normal
        o=torch.zeros_like(n) if origin is None else origin
        result=[]
        for foot,vertices in enumerate(self.points):
            q=quat[:,foot,:];u=q[:,1:];w=q[:,:1]
            cross=torch.linalg.cross(u,n);local_n=n-2*w*cross+2*torch.linalg.cross(u,cross)
            result.append((local_n@vertices.T).amin(-1)+((pos[:,foot,:]-o)*n).sum(-1))
        return torch.stack(result,-1)

def verify(device='cpu'):
    b=Path(__file__).parent;d=json.loads((b/'foot_geometry_test_vectors.json').read_text());g=FootGeometry(b/'foot_collision_support.json',device)
    actual=g.clearance(torch.tensor(d['positions'],device=device),torch.tensor(d['quaternions_wxyz'],device=device))
    expected=torch.tensor(d['expected_clearance'],device=device);error=float((actual-expected).abs().max())
    assert error<1e-6,error
    return {'device':device,'max_abs_error_m':error,'pass':True}
if __name__=='__main__':
    torch.set_num_threads(2);print(json.dumps(verify()))
    if torch.cuda.is_available():print(json.dumps(verify('cuda')))
