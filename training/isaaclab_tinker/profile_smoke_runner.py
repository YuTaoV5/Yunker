"""Sequential evaluator checks; waits for the pre-existing long evaluation."""
import pathlib,subprocess,time,json
b=pathlib.Path(__file__).parent
# Do not add a third Kit process while the previous long evaluation runs.
for _ in range(1800):
    active=False
    for p in pathlib.Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                args=p.joinpath('cmdline').read_bytes().split(b'\0')
                if b'evaluate.py' in args and b'v8_nominal100_60.json' in args:active=True
            except (FileNotFoundError,PermissionError):pass
    if not active:break
    time.sleep(1)
else:raise RuntimeError('Previous evaluator still active after 30min; no new Kit launched')
ck=sorted(b.glob('logs/rsl_rl/tinker_robust_v8/*/model_100.pt'))[-1]
summary={'checkpoint':str(ck),'scope':'independent fault evaluator implementation smoke, not gait acceptance','runs':{}}
for name,extra in [('nominal',['--nominal']),('zero',['--fault-profile','profile_zero.json']),('delay20',['--fault-profile','profile_delay20.json'])]:
    output='isaac_profile_smoke_'+name+'.json'
    cmd=['/isaac-sim/python.sh','evaluate.py','--version','8','--checkpoint',str(ck),'--seconds','2','--warmup-seconds','.5','--robots-per-case','1','--output',output,'--headless']+extra
    code=subprocess.call(cmd,cwd=b,stdout=open(b/('isaac_profile_smoke_'+name+'.log'),'w'),stderr=subprocess.STDOUT)
    summary['runs'][name]={'exit_code':code}
    (b/'isaac_profile_smoke_summary.json').write_text(json.dumps(summary,indent=2))
    if code!=0:raise RuntimeError(name+' evaluator failed')
zero=json.loads((b/'isaac_profile_smoke_zero.json').read_text());delay=json.loads((b/'isaac_profile_smoke_delay20.json').read_text())
assert all(v==0 for v in zero['command_channel_stats']['dropped'])
assert min(delay['command_channel_stats']['max_received_age_ms'])>=20.
assert max(delay['command_channel_stats']['queue_overwrites'])==0
nom=json.loads((b/'isaac_profile_smoke_nominal.json').read_text())
difference=max(abs(nom['cases'][k]['xy_rmse']-zero['cases'][k]['xy_rmse']) for k in nom['cases'])
summary['zero_profile_xy_rmse_max_difference']=difference
summary['zero_profile_parity_pass']=difference<=1e-5
summary['delay_injection_pass']=True
(b/'isaac_profile_smoke_summary.json').write_text(json.dumps(summary,indent=2))
assert difference<=1e-5,'Zero fault profile changed clean dynamics'
print(json.dumps(summary),flush=True)
