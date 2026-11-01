"""Force-derived unload sequence diagnostics; not geometric foot clearance."""
import numpy as np

def summarize_unloading(contact, dt=.02, minimum_air_seconds=.04):
    contact=np.asarray(contact,dtype=bool)
    assert contact.ndim==2 and contact.shape[1]==2
    events=[];durations=[[],[]]
    for foot in range(2):
        airborne=~contact[:,foot]
        edges=np.diff(np.r_[False,airborne,False].astype(int))
        for start,end in zip(np.flatnonzero(edges==1),np.flatnonzero(edges==-1)):
            # Incomplete flights at either window boundary cannot establish a stride.
            if start==0 or end==len(contact):continue
            duration=(end-start)*dt
            if duration+1e-9>=minimum_air_seconds:
                events.append((int(start),foot));durations[foot].append(duration)
    events.sort();simultaneous={tick for tick in set(t for t,_ in events) if sum(t==tick for t,_ in events)>1}
    sequence=[foot for tick,foot in events if tick not in simultaneous]
    changes=sum(a!=b for a,b in zip(sequence,sequence[1:]))
    return dict(qualified_unloads_per_foot=[len(d) for d in durations],median_unload_seconds_per_foot=[float(np.median(d)) if d else None for d in durations],alternating_transition_fraction=changes/(len(sequence)-1) if len(sequence)>1 else None,unload_sequence=sequence,simultaneous_unload_events=len(simultaneous),minimum_unload_seconds=minimum_air_seconds,measurement='normal-force threshold; geometric clearance not established')
