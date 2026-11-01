"""Deterministic simulated transport: whole packets, delay/jitter, loss, sequence checks."""
import heapq
import numpy as np

class PacketChannel:
    def __init__(self,initial,seed=0,delay_ms=0.,jitter_ms=0.,drop_probability=0.,burst_start_ms=5000.,burst_ms=0.):
        assert delay_ms>=0 and jitter_ms>=0 and 0<=drop_probability<=1 and burst_ms>=0
        self.value=np.asarray(initial).copy();self.rng=np.random.default_rng(seed)
        self.delay=delay_ms;self.jitter=jitter_ms;self.drop=drop_probability
        self.burst_start=burst_start_ms;self.burst_ms=burst_ms;self.queue=[];self.seq=0;self.delivered_seq=-1;self.sent_time=None
        self.stats={'sent':0,'dropped':0,'delivered':0,'out_of_order_discarded':0,'max_received_age_ms':0.}
    def send(self,value,time_ms):
        seq=self.seq;self.seq+=1;self.stats['sent']+=1
        if self.burst_start<=time_ms<self.burst_start+self.burst_ms or self.rng.random()<self.drop:
            self.stats['dropped']+=1;return
        latency=max(0.,self.delay+self.rng.uniform(-self.jitter,self.jitter))
        heapq.heappush(self.queue,(time_ms+latency,seq,time_ms,np.asarray(value).copy()))
    def receive(self,time_ms):
        while self.queue and self.queue[0][0]<=time_ms+1e-8:
            _,seq,sent,value=heapq.heappop(self.queue)
            if seq<=self.delivered_seq:self.stats['out_of_order_discarded']+=1;continue
            self.value=value;self.delivered_seq=seq;self.sent_time=sent;self.stats['delivered']+=1
        age=time_ms-self.sent_time if self.sent_time is not None else time_ms
        self.stats['max_received_age_ms']=max(self.stats['max_received_age_ms'],age)
        return self.value.copy(),age

def self_test():
    c=PacketChannel([0.],delay_ms=10)
    c.send([1.],0);assert c.receive(9)[0][0]==0 and c.receive(10)[0][0]==1
    c=PacketChannel([0.],drop_probability=1.)
    c.send([1.],0);assert c.receive(100)[0][0]==0 and c.stats['dropped']==1
    c=PacketChannel([0.],burst_start_ms=20,burst_ms=40)
    for t in [0,20,40,60]:c.send([t],t);c.receive(t)
    assert c.stats['dropped']==2 and c.value[0]==60
    # A delayed old packet must not overwrite a newer one.
    c=PacketChannel([0.]);c.queue=[(20.,0,0.,np.array([1.])),(10.,1,10.,np.array([2.]))];heapq.heapify(c.queue)
    c.receive(30);assert c.value[0]==2 and c.stats['out_of_order_discarded']==1
    a=PacketChannel([0.],seed=7,delay_ms=20,jitter_ms=10,drop_probability=.1)
    b=PacketChannel([0.],seed=7,delay_ms=20,jitter_ms=10,drop_probability=.1)
    for t in range(0,1000,20):
        a.send([t],t);b.send([t],t);assert np.array_equal(a.receive(t)[0],b.receive(t)[0])
    assert a.stats==b.stats
    return {'fixed_delay':'pass','complete_loss_hold':'pass','burst_duration':'pass','sequence_order':'pass','seed_reproducibility':'pass'}

if __name__=='__main__':
    import json
    print(json.dumps(self_test()))
