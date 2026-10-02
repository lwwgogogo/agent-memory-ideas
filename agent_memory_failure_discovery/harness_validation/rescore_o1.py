import json,re,sys
p=sys.argv[1]; r=json.load(open(p)); gold={'C1':'LOCAL','C2':'CLOUD','C3':'PYTHON','C4':'B','C5':'OBSERVATION','C6':'Y','C7':'T','C8':'B'}
for x in r:
 raw=x['result']['raw']; ms=list(re.finditer(r'\{[^{}]*"choice"\s*:\s*"?([A-Za-z]+)"?[^{}]*\}',raw,re.S)); v=ms[-1].group(1).upper() if ms else None
 x['result']['choice']=v; x['result']['method']='json_embedded' if v else 'unresolved'; x['result']['correct']=v==gold[x['family']]
open(p,'w').write(json.dumps(r,ensure_ascii=False,indent=2)); print(sum(x['result']['correct'] for x in r),len(r))
from collections import Counter
print(Counter((x['family'],x['result']['correct']) for x in r))
