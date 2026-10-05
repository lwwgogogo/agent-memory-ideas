#!/usr/bin/env python3
"""Prepare audit JSON from manually verified evidence records and enforce blindspot logic."""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def structural_blindspot(a):
 origin=a.get('experience_origin') in {'SELF_GENERATED','MIXED'}
 outcome=bool(a.get('observed_reward_used_as_utility')) and bool(a.get('utility_affects_future_retrieval') or a.get('utility_affects_future_action'))
 correction=a.get('exposure_correction') in {'NONE','PARTIAL'}
 metadata=not bool(a.get('stores_behavior_policy_id') or a.get('stores_action_propensity'))
 return origin and outcome and correction and metadata
def validate(a):
 required=json.loads((ROOT/'audit_schema.json').read_text())['required']
 missing=[k for k in required if k not in a]
 if missing:raise ValueError(f'missing schema fields: {missing}')
 expected=structural_blindspot(a)
 if bool(a['structural_blindspot'])!=expected:raise ValueError('structural_blindspot inconsistent with evidence fields')
 if not a['evidence']:raise ValueError('audit requires at least one evidence item')
 return a
def main():
 ap=argparse.ArgumentParser();ap.add_argument('system');ap.add_argument('--input',required=True);a=ap.parse_args()
 item=validate(json.loads(Path(a.input).read_text()))
 out=ROOT/'results'/'system_audits'/f'{a.system}.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n');print(out)
if __name__=='__main__':main()
