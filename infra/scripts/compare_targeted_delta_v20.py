import json
from pathlib import Path
import sys
from collections import Counter, defaultdict
sys.path.insert(0,'infra/scripts')
from ground_truth_scorer import score_observation

root=Path('infra/benchmarks/reports/overnight_20260614')
old_files=[
 root/'final_run_laneA_kimi_v19.checkpoint.jsonl',
 root/'final_run_laneB_ministral_v19.checkpoint.jsonl',
 root/'final_run_laneC_qwen_v19.checkpoint.jsonl',
]
new_file=root/'targeted_retry_run_v20.checkpoint.jsonl'

gt=json.loads(Path('infra/benchmarks/ollama_cloud_ground_truth_v2.json').read_text(encoding='utf-8'))
idx={k:{s['sample_id']:s for s in v} for k,v in gt.items() if isinstance(v,list)}

def load(paths):
 rows=[]
 for p in paths:
  if p.exists():
   rows.extend(json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip())
 by={}
 for r in rows:
  k=(r.get('stage'),r.get('model'),r.get('sample_id'),int(r.get('repeat',0)))
  by[k]=r
 return by

def stats(by):
 s=defaultdict(Counter)
 for (st,_,sid,_),r in by.items():
  ref=idx.get(st,{}).get(sid)
  if not ref: continue
  sr=score_observation(st,r.get('raw_response',''),ref,r)
  s[st][sr.match_type]+=1
 return s

old=load(old_files)
new=load([new_file])
merged=dict(old)
merged.update(new)

old_s=stats(old)
new_s=stats(merged)

def pct(c):
 t=sum(c.values()); return (100*c['exact']/t if t else 0.0),t

print('stage,old_exact,new_exact,delta,total')
for st in sorted(set(old_s)|set(new_s)):
 oe,ot=pct(old_s[st]); ne,nt=pct(new_s[st])
 print(f"{st},{oe:.1f},{ne:.1f},{(ne-oe):+.1f},{nt}")

out=root/'targeted_retry_delta_v20.csv'
out.write_text('\n'.join(['stage,old_exact,new_exact,delta,total'] + [
 f"{st},{pct(old_s[st])[0]:.1f},{pct(new_s[st])[0]:.1f},{(pct(new_s[st])[0]-pct(old_s[st])[0]):+.1f},{pct(new_s[st])[1]}"
 for st in sorted(set(old_s)|set(new_s))
]), encoding='utf-8')
print('wrote', out)
