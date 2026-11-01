"""Matched-task reward ledger: V8 moving policy vs V9 policy on V9 rewards."""
import pathlib,subprocess,time,json
b=pathlib.Path(__file__).parent
for _ in range(1800):
    running=False
    for p in pathlib.Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                args=p.joinpath('cmdline').read_bytes().split(b'\0')
                if b'evaluate.py' in args and b'v9_audit_smoke.json' in args:running=True
            except FileNotFoundError:pass
    if not running:break
    time.sleep(1)
else:raise RuntimeError('Audit smoke still running; no new Kit launched')
for version,iteration,label in [(8,400,'v8actor'),(9,100,'v9actor')]:
    ck=sorted(b.glob(f'logs/rsl_rl/tinker_robust_v{version}/*/model_{iteration}.pt'))[-1]
    cmd=['/isaac-sim/python.sh','evaluate.py','--version','9','--nominal','--seconds','20','--warmup-seconds','5','--robots-per-case','1','--checkpoint',str(ck),'--output',f'v9_reward_ledger_{label}.json','--headless']
    code=subprocess.call(cmd,cwd=b,stdout=open(b/f'v9_reward_ledger_{label}.log','w'),stderr=subprocess.STDOUT)
    if code!=0:raise RuntimeError(label+' evaluator failed')
print('Matched V9 reward comparison complete',flush=True)
