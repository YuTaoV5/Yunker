"""Freeze all specified OAT points plus fixed-seed sampled combinations. No PASS inferred."""
import json,hashlib,random
from pathlib import Path
b=Path(__file__).parent;raw=(b/'acceptance.json').read_bytes();a=json.loads(raw);s=a['boundary_sweeps']
mapping={'command_delay_ms':'delay_ms','jitter_ms':'jitter_ms','independent_packet_drop_probability':'drop','consecutive_command_loss_ms':'burst_ms','observation_age_ms':'sensor_age_ms','mass_scale':'mass_scale','friction':'friction','kp_kd_scale':'gain_scale','encoder_offset_rad':'encoder_offset','floor_slope_deg':'slope_deg','push_delta_velocity_m_s':'push_delta_v'}
assert set(s)==set(mapping)|{'base_com_offset_xy_m'},'Unmapped required acceptance field'
profiles=[dict(id='nominal',tier='nominal',profile={})]
for key,values in s.items():
    for index,value in enumerate(values):
        if key=='base_com_offset_xy_m':
            for axis in [0,1]:
                vector=[0.,0.];vector[axis]=value
                profiles.append(dict(id=f'{key}_axis{axis}_{index}',tier='robust',profile={'com_xy':vector},required_axis=key,value=value))
        else:
            p={mapping[key]:value}
            if key=='jitter_ms':p['delay_ms']=20 # Explicit reference latency, so +/- jitter has physical meaning.
            profiles.append(dict(id=f'{key}_{index}',tier='robust',profile=p,required_axis=key,value=value))
rng=random.Random(2026)
for index in range(64):
    p={mapping[key]:rng.choice(values) for key,values in s.items() if key in mapping}
    p['com_xy']=[rng.choice(s['base_com_offset_xy_m']),rng.choice(s['base_com_offset_xy_m'])]
    profiles.append(dict(id=f'combination_seed2026_{index:02d}',tier='robust',profile=p))
jobs=[dict(id=f"{p['id']}_seed{seed}",profile_id=p['id'],seed=seed,trials_per_command=a['trials_per_case_per_seed'],commands=list(a['commands']),seconds=a['trial_seconds'],warmup_seconds=a['warmup_seconds'],status='NOT_RUN') for p in profiles for seed in a['seeds']]
plan=dict(acceptance_sha256=hashlib.sha256(raw).hexdigest(),same_checkpoint_and_contract_required=True,combination_sampling_seed=2026,combinations=64,profiles=profiles,jobs=jobs,estimated_trials_per_simulator=len(jobs)*len(a['commands'])*a['trials_per_case_per_seed'],state='PLAN_ONLY_NOT_ACCEPTED',required_evidence=['checkpoint SHA256','contract SHA256','backend/source revisions','actual injected parameters','all seeds and trials','per-command failures and coverage','missing-data handling'],known_blockers=['Original-ground contact-point slip is not yet readable; USD inventory identifies Plane, prior triangle label was incorrect','Document and test >200ms watchdog response','Verify stochastic trial independence instead of identical repeated rollouts','Complete runner and aggregate validator; do not infer coverage from files existing'])
payload=json.dumps(plan,sort_keys=True,separators=(',',':')).encode();plan['plan_payload_sha256']=hashlib.sha256(payload).hexdigest();(b/'acceptance_matrix_plan.json').write_text(json.dumps(plan,indent=2));print(dict(profiles=len(profiles),grouped_seed_jobs=len(jobs),trials_per_simulator=plan['estimated_trials_per_simulator'],state=plan['state']))
