"""Read-only USD collision/support audit inside an initialized Isaac application."""
import json,numpy as np
from pathlib import Path

def audit(env):
    from pxr import Usd,UsdPhysics,UsdGeom,Gf,UsdShade
    import omni.usd
    stage=omni.usd.get_context().get_stage();root=stage.GetPrimAtPath('/World/envs/env_0/Robot')
    assert root.IsValid()
    cache=UsdGeom.XformCache();colliders=[];foot_points={name:[] for name in ['L4_Link_ankle','R4_Link_ankle']}
    for prim in Usd.PrimRange(root,Usd.TraverseInstanceProxies()):
        if not prim.HasAPI(UsdPhysics.CollisionAPI):continue
        path=str(prim.GetPath());r={'path':path,'type':prim.GetTypeName(),'enabled':prim.GetAttribute('physics:collisionEnabled').Get(),'approximation':prim.GetAttribute('physics:approximation').Get()}
        colliders.append(r)
    # The importer authors CollisionAPI on an Xform, with its mesh below it.
    # Include only descendants of enabled collision roots, never visuals.
    mesh_inventory=[]
    for prim in Usd.PrimRange(root,Usd.TraverseInstanceProxies()):
        if not prim.IsA(UsdGeom.Mesh):continue
        path=str(prim.GetPath())
        owners=[r for r in colliders if r['enabled'] is not False and (path==r['path'] or path.startswith(r['path']+'/'))]
        if not owners:continue
        points=UsdGeom.Mesh(prim).GetPointsAttr().Get()
        mesh_inventory.append({'path':path,'collision_roots':[r['path'] for r in owners],'vertices':len(points) if points is not None else 0})
        for name in foot_points:
            if '/'+name+'/' in path and points is not None:
                body=stage.GetPrimAtPath('/World/envs/env_0/Robot/'+name)
                to_world=cache.GetLocalToWorldTransform(prim);to_body=cache.GetLocalToWorldTransform(body).GetInverse()
                foot_points[name].extend([[float(v) for v in to_body.Transform(to_world.Transform(Gf.Vec3d(float(p[0]),float(p[1]),float(p[2]))))] for p in points])
    source=json.loads((Path(__file__).parent/'foot_collision_support.json').read_text());rng=np.random.default_rng(1601)
    normals=np.r_[np.eye(3),-np.eye(3),rng.normal(size=(64,3))];normals/=np.linalg.norm(normals,axis=1,keepdims=True)
    foot_report={}
    for name,points in foot_points.items():
        if not points:
            foot_report[name]={'support_match_pass':False,'error':'No resolved foot collision Mesh; inspect robot_colliders and hierarchy','status':'MISSING_GEOMETRY'}
            continue
        points=np.asarray(points);reference=np.asarray(source['feet'][name])
        error=float(np.abs((points@normals.T).min(0)-(reference@normals.T).min(0)).max())
        foot_report[name]={'collision_mesh_count':sum('/'+name+'/' in r['path'] for r in colliders),'vertices':len(points),'local_min_m':points.min(0).tolist(),'local_max_m':points.max(0).tolist(),'support_error_vs_urdf_m':error,'support_match_tolerance_m':1e-5,'support_match_pass':error<=1e-5}
    ground=[]
    if stage.GetPrimAtPath('/World/ground').IsValid():
        for prim in Usd.PrimRange(stage.GetPrimAtPath('/World/ground'),Usd.TraverseInstanceProxies()):
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                material,relationship=UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial(materialPurpose='physics')
                props={}
                if material:
                    for attr in material.GetPrim().GetAttributes():
                        if any(word in attr.GetName().lower() for word in ['friction','restitution','combine']):props[attr.GetName()]=str(attr.Get())
                ground.append({'path':str(prim.GetPath()),'type':prim.GetTypeName(),'approximation':prim.GetAttribute('physics:approximation').Get(),'bound_physics_material':str(material.GetPath()) if material else None,'material_properties':props})
    return {'audit_revision':2,'collision_mesh_inventory':mesh_inventory,'robot_hierarchy':[{'path':str(p.GetPath()),'type':p.GetTypeName()} for p in Usd.PrimRange(root,Usd.TraverseInstanceProxies())], 'robot_collision_count':len(colliders),'robot_colliders':colliders,'feet':foot_report,'ground':ground,'urdf_sha256':source['urdf_sha256'],'note':'Source USD geometry/material bindings only; runtime randomized material values are recorded separately. Source mesh support agreement does not validate PhysX cooked hull margins.'}
