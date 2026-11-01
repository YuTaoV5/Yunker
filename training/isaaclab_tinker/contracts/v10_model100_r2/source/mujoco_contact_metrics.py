"""Exact mesh support clearance against the configured plane, plus contact-point slip."""
import numpy as np
import mujoco
class FootMetrics:
    def __init__(self,m,feet):
        self.feet=feet;self.meshes=[];self.jac=np.zeros((3,m.nv))
        self.floor=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'floor')
        for bid in feet:
            shapes=[]
            for gid in range(m.ngeom):
                if m.geom_bodyid[gid]!=bid or m.geom_contype[gid]==0:continue
                assert m.geom_type[gid]==mujoco.mjtGeom.mjGEOM_MESH,'Unsupported foot collision primitive'
                mesh=m.geom_dataid[gid];start=m.mesh_vertadr[mesh];end=start+m.mesh_vertnum[mesh]
                shapes.append((gid,m.mesh_vert[start:end].copy()))
            assert len(shapes)==1,'Expected one true collision mesh per foot'
            self.meshes.append(shapes)
    def clearance(self,d):
        n=d.geom_xmat[self.floor].reshape(3,3)[:,2];origin=d.geom_xpos[self.floor]
        heights=[]
        for shapes in self.meshes:
            heights.append(min(float((vertices@(d.geom_xmat[gid].reshape(3,3).T@n)).min()+(d.geom_xpos[gid]-origin)@n) for gid,vertices in shapes))
        return np.asarray(heights)
    def slip(self,m,d):
        weight=0.;squared=0.;n=d.geom_xmat[self.floor].reshape(3,3)[:,2]
        for index in range(d.ncon):
            contact=d.contact[index];ids=(m.geom_bodyid[contact.geom1],m.geom_bodyid[contact.geom2])
            foot=next((bid for bid in self.feet if bid in ids),None)
            if foot is None:continue
            force=np.zeros(6);mujoco.mj_contactForce(m,d,index,force);normal=abs(force[0])
            if normal<1.:continue
            mujoco.mj_jac(m,d,self.jac,None,contact.pos,foot)
            velocity=self.jac@d.qvel;velocity-=n*(velocity@n)
            weight+=normal;squared+=normal*(velocity@velocity)
        return squared,weight
