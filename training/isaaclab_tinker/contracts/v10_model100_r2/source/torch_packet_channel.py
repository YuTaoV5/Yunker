"""Batched CPU/CUDA whole-packet channel for independent Isaac fault evaluation.
Clock is supplied in milliseconds; receive must run at physics rate for commands.
No global RNG consumption: each channel owns an explicit generator.
"""
import torch
class TorchPacketChannel:
    def __init__(self,initial,seed=0,delay_ms=0.,jitter_ms=0.,drop_probability=0.,burst_start_ms=5000.,burst_ms=0.,capacity=64):
        assert initial.ndim==2 and delay_ms>=0 and jitter_ms>=0 and 0<=drop_probability<=1 and burst_ms>=0
        self.value=initial.clone();self.n,self.width=initial.shape;self.device=initial.device
        self.generator=torch.Generator(device=self.device).manual_seed(seed)
        self.delay=delay_ms;self.jitter=jitter_ms;self.drop=drop_probability;self.burst_start=burst_start_ms;self.burst_ms=burst_ms
        self.capacity=capacity;self.next_seq=0
        self.arrival=torch.full((capacity,self.n),float('inf'),device=self.device,dtype=torch.float64)
        self.sent_at=torch.zeros_like(self.arrival)
        self.sequence=torch.full((capacity,self.n),-1,device=self.device,dtype=torch.long)
        self.payload=torch.zeros((capacity,*initial.shape),device=self.device,dtype=initial.dtype)
        self.last_seq=torch.full((self.n,),-1,device=self.device,dtype=torch.long)
        self.last_sent=torch.zeros(self.n,device=self.device,dtype=torch.float64)
        self.stats={k:torch.zeros(self.n,device=self.device,dtype=torch.long) for k in ['sent','dropped','delivered','queue_overwrites']}
        self.maximum_age=torch.zeros(self.n,device=self.device,dtype=torch.float64)
    def send(self,value,time_ms):
        assert value.shape==self.value.shape
        slot=self.next_seq%self.capacity
        pending=(self.sequence[slot]>self.last_seq)&torch.isfinite(self.arrival[slot])
        self.stats['queue_overwrites']+=pending.long()
        lost=torch.rand(self.n,device=self.device,generator=self.generator)<self.drop
        if self.burst_start<=time_ms<self.burst_start+self.burst_ms:lost[:]=True
        delay=(self.delay+(torch.rand(self.n,device=self.device,generator=self.generator)*2-1)*self.jitter).clamp(min=0.)
        self.payload[slot]=value;self.sequence[slot]=self.next_seq;self.sent_at[slot]=time_ms
        self.arrival[slot]=torch.where(lost,float('inf'),time_ms+delay.double())
        self.stats['sent']+=1;self.stats['dropped']+=lost.long();self.next_seq+=1
    def receive(self,time_ms):
        ready=(self.arrival<=time_ms+1e-8)&(self.sequence>self.last_seq[None,:])
        seq=torch.where(ready,self.sequence,-1)
        newest,slot=seq.max(0);valid=newest>=0;env=torch.arange(self.n,device=self.device)
        self.value=torch.where(valid[:,None],self.payload[slot,env],self.value)
        self.last_sent=torch.where(valid,self.sent_at[slot,env],self.last_sent)
        self.last_seq=torch.where(valid,newest,self.last_seq)
        self.stats['delivered']+=valid.long()
        age=time_ms-self.last_sent;self.maximum_age=torch.maximum(self.maximum_age,age)
        return self.value.clone(),age
    def reset(self,env_ids,initial,time_ms):
        self.value[env_ids]=initial
        self.arrival[:,env_ids]=float('inf');self.sequence[:,env_ids]=-1
        self.last_seq[env_ids]=-1;self.last_sent[env_ids]=time_ms
    def report(self):
        r={k:v.cpu().tolist() for k,v in self.stats.items()}
        r['max_received_age_ms']=self.maximum_age.cpu().tolist();return r

def self_test(device='cpu'):
    z=torch.zeros((2,1),device=device)
    c=TorchPacketChannel(z,delay_ms=10.);c.send(z+1,0.)
    assert (c.receive(9.)[0]==0).all() and (c.receive(10.)[0]==1).all()
    c=TorchPacketChannel(z,drop_probability=1.);c.send(z+1,0.);assert (c.receive(100.)[0]==0).all()
    c=TorchPacketChannel(z,burst_start_ms=20.,burst_ms=40.)
    for t in [0.,20.,40.,60.]:c.send(z+t,t);c.receive(t)
    assert (c.stats['dropped']==2).all() and (c.value==60).all()
    # A later-arriving older packet must never overwrite a newer packet.
    c=TorchPacketChannel(z);c.send(z+1,0.);c.arrival[0]=20.;c.send(z+2,10.);c.receive(10.);assert (c.receive(30.)[0]==2).all()
    # Reset one environment with an old command still in flight.
    c=TorchPacketChannel(z,delay_ms=20.);c.send(z+5,0.);c.reset([0],torch.zeros((1,1),device=device),10.);v,_=c.receive(20.)
    assert v[0,0]==0 and v[1,0]==5
    a=TorchPacketChannel(z,seed=7,delay_ms=20,jitter_ms=10,drop_probability=.1)
    b=TorchPacketChannel(z,seed=7,delay_ms=20,jitter_ms=10,drop_probability=.1)
    for t in range(0,1000,20):
        a.send(z+t,t);b.send(z+t,t);assert torch.equal(a.receive(t)[0],b.receive(t)[0])
    assert not a.stats['queue_overwrites'].any()
    return dict(device=device,fixed_delay=True,complete_loss=True,burst_duration=True,sequence_order=True,per_environment_reset=True,reproducible=True)
if __name__=='__main__':
    import json
    torch.set_num_threads(2)
    print(json.dumps(self_test()))
    if torch.cuda.is_available():print(json.dumps(self_test('cuda')))
