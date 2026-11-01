"""Unfiltered original-ground contact reports, following installed PhysX demo API."""
import re,torch
class ContactReportSlip:
    def __init__(self,env,pump_render=False):
        from omni.physx import get_physx_simulation_interface
        from pxr import PhysicsSchemaTools,PhysxSchema
        import omni.usd,carb
        self.env=env;self.pump_render=pump_render;self.max_root_transform_change=0.;self.max_callbacks_per_sample=0;self.interface=get_physx_simulation_interface();self.decode=PhysicsSchemaTools.intToSdfPath
        self.cache={};self.total_points=0;self.samples=0;self.headers_seen=0;self.thresholds=[]
        self.last_tick=-1;self.rows=[];self.event_callbacks=0;self.callback_error=None;self.raw_points_received=0
        stage=omni.usd.get_context().get_stage()
        for i in range(env.num_envs):
            for side in ['L','R']:
                path=f'/World/envs/env_{i}/Robot/{side}4_Link_ankle';prim=stage.GetPrimAtPath(path)
                assert prim.IsValid(),path
                api=PhysxSchema.PhysxContactReportAPI(prim)
                assert prim.HasAPI(PhysxSchema.PhysxContactReportAPI),path+' has no contact report API'
                previous=api.GetThresholdAttr().Get();self.thresholds.append(previous)
                api.CreateThresholdAttr().Set(0.)
        carb.settings.get_settings().set_bool('/physics/disableContactProcessing',False)
        self.subscription=self.interface.subscribe_contact_report_events(self._on_contact_report)
        r=env.scene['robot'];self.body_ids={side:r.find_bodies(side+'4_Link_ankle',preserve_order=True)[0][0] for side in ['L','R']}
    def path(self,value):
        key=int(value)
        if key not in self.cache:self.cache[key]=str(self.decode(value))
        return self.cache[key]
    def _on_contact_report(self,headers,data):
        try:self._capture(headers,data)
        except Exception as error:self.callback_error=repr(error)
    def _capture(self,headers,data):
        tick=self.env._sim_step_counter
        if tick!=self.last_tick or self.pump_render:self.rows=[];self.last_tick=tick
        self.headers_seen+=len(headers);self.event_callbacks+=1
        for header in headers:
            paths=[self.path(header.actor0),self.path(header.actor1),self.path(header.collider0),self.path(header.collider1)]
            if not any('/World/ground' in p or '/sloped_ground' in p for p in paths):continue
            foot=next((re.search(r'/env_(\d+)/Robot/([LR])4_Link_ankle(?:/|$)',p) for p in paths if re.search(r'/env_(\d+)/Robot/([LR])4_Link_ankle(?:/|$)',p)),None)
            if foot is None:continue
            env_id=int(foot.group(1));side=foot.group(2)
            assert env_id<self.env.num_envs,paths
            for index in range(header.contact_data_offset,header.contact_data_offset+header.num_contact_data):
                item=data[index];n=[float(item.normal[j]) for j in range(3)]
                try:impulse=[float(item.impulse[j]) for j in range(3)];force=abs(sum(a*v for a,v in zip(n,impulse)))/self.env.physics_dt
                except TypeError:force=abs(float(item.impulse))/self.env.physics_dt
                if force<1.:continue
                self.rows.append(([float(item.position[j]) for j in range(3)],force,env_id,self.body_ids[side]));self.raw_points_received+=1
    def sample(self,normal):
        if self.pump_render:
            view=self.env.scene['robot'].root_physx_view
            before=view.get_root_transforms().clone();callbacks=self.event_callbacks
            self.env.sim.render()
            change=float((view.get_root_transforms()-before).abs().max())
            assert change<=1e-7,'Render unexpectedly advanced physics: '+str(change)
            self.max_root_transform_change=max(self.max_root_transform_change,change)
            self.max_callbacks_per_sample=max(self.max_callbacks_per_sample,self.event_callbacks-callbacks)
        if self.callback_error:raise RuntimeError('PhysX contact callback: '+self.callback_error)
        self.samples+=1
        rows=self.rows if self.last_tick==self.env._sim_step_counter else []
        positions=[r[0] for r in rows];weights=[r[1] for r in rows];envs=[r[2] for r in rows];bodies=[r[3] for r in rows]
        r=self.env.scene['robot'];sq=torch.zeros(self.env.num_envs,device=self.env.device);weight=torch.zeros_like(sq);count=torch.zeros(self.env.num_envs,device=self.env.device,dtype=torch.long)
        if not positions:return sq,weight,count
        e=torch.tensor(envs,device=self.env.device);bid=torch.tensor(bodies,device=self.env.device);p=torch.tensor(positions,device=self.env.device);w=torch.tensor(weights,device=self.env.device)
        v=r.data.body_com_lin_vel_w[e,bid]+torch.linalg.cross(r.data.body_com_ang_vel_w[e,bid],p-r.data.body_com_pos_w[e,bid])
        tangent=v-(v*normal).sum(-1,keepdim=True)*normal
        sq.scatter_add_(0,e,w*tangent.square().sum(-1));weight.scatter_add_(0,e,w);count.scatter_add_(0,e,torch.ones_like(e))
        self.total_points+=len(positions);return sq,weight,count
    def report(self):
        return dict(source='PhysX subscribe_contact_report_events, last physics tick, no ground filter',pump_render=self.pump_render,max_root_transform_change=self.max_root_transform_change,max_callbacks_per_sample=self.max_callbacks_per_sample,event_callbacks=self.event_callbacks,last_event_tick=self.last_tick,final_physics_tick=self.env._sim_step_counter,callback_error=self.callback_error,raw_points_received=self.raw_points_received,sample_steps=self.samples,headers_seen=self.headers_seen,contact_points_above_1N=self.total_points,old_report_thresholds=self.thresholds)
