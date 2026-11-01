"""Shared desired-command clock for both simulators; seconds at policy evaluation."""
def command_at_time(schedule,time_seconds,base=(0.,0.,0.)):
    assert time_seconds>=0
    if schedule=='start_stop':return (.2 if int((time_seconds+1e-9)//10)%3==1 else 0.,0.,0.)
    if schedule=='walk_turn_switch':return (.15,0.,.3 if time_seconds>=10.-1e-9 else 0.)
    if schedule=='walk_turn':return (.15,0.,.3)
    if schedule in (None,'fixed'):return tuple(base)
    raise ValueError('Unknown command schedule: '+str(schedule))
def self_test():
    expected={0.:0.,9.98:0.,10.:.2,19.98:.2,20.:0.,29.98:0.,30.:0.,40.:.2}
    for time,value in expected.items():assert command_at_time('start_stop',time)[0]==value
    assert command_at_time('walk_turn_switch',9.98)==(.15,0.,0.)
    assert command_at_time('walk_turn_switch',10.)==(.15,0.,.3)
    assert command_at_time('walk_turn',0.)==(.15,0.,.3)
    return {'policy_boundary_times':'pass','walk_turn_semantics':'pass'}
if __name__=='__main__':print(self_test())
