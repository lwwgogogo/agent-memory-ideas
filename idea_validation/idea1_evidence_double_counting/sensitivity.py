import pathlib,json,collections,statistics
from evaluate import summary,NAMES
P=pathlib.Path(__file__).resolve().parent
rows=json.loads((P/'results/llm_results.json').read_text());groups=collections.defaultdict(list)
for r in rows:
 x=json.loads(r['raw']);assert set(x)=={'choice','confidence','reason'} and type(x['confidence']) in [int,float] and 0<=x['confidence']<=1
 if r['status']!='OK':assert x['choice']=='H0' and x['confidence']==.5
 groups[(r['case_id'],r['condition'])].append(x['confidence'])
ids=sorted({r['case_id'] for r in rows});means={i:{n:statistics.mean(groups[(i,n)]) for n in NAMES} for i in ids}
s={'note':'事后敏感性分析：原样使用模型报告的 P(H1)=0.5，不转换概率、不猜测。正式 UNRESOLVED 保留；不是主分析替代。','n':len(ids),'conditions':{n:summary([means[i][n] for i in ids]) for n in NAMES},'effects':{k:summary([means[i][a]-means[i][b] for i in ids]) for k,a,b in [('CI3','Derived3','OneSource'),('CI5','Derived5','OneSource'),('IEG','Independent3','OneSource'),('PC','Derived5','ProvenanceAware5')]}}
s['DCR']=s['effects']['CI5']['mean']/s['effects']['IEG']['mean']
(P/'results/tie_sensitivity.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
text='\n## 平局规则与事后敏感性分析\n\n正式轮 240/240 均为合法 JSON 且满足所需字段与概率范围。29 条 UNRESOLVED 全部为 choice=H0、P(H1)=0.5，违反提示规定的平局选择规则；并非 JSON 语法解析失败。本文前述解析统计使用严格校验口径，须据此区别。该规则排除部分低置信回答，造成主分析选择偏差；商业领域全部被排除，主分析不能视为五领域完整结果。\n\n不改写正式标记，不猜测概率，事后单独使用所有原样报告的概率进行敏感性分析，场景数为 20。结果如下：\n\n| 指标 | 均值 | 95% 区间 |\n|---|---:|---|\n'
for k,v in {**s['conditions'],**s['effects']}.items():text+='| %s | %.6f | [%.6f, %.6f] |\n'%(k,v['mean'],v['ci_low'],v['ci_high'])
text+='\n敏感性 DCR=%.6f。CI5 区间仍覆盖零，且 Derived5<Derived3，未出现稳定的数量递增膨胀趋势。因此 NO_GO 不仅是预设平局规则导致的缺失，也有全量原始概率的敏感性结果支持；这仍不构成对其他模型、场景或真实记忆系统的否定。来源提示显著降低自报概率，但不能单凭 PC 将其解释为纠正已证实的重复计数。\n'%s['DCR']
for name in ['Idea1实验结果.md','最终结论.md']:
 path=P/name;original=path.read_text().split('\n## 平局规则与事后敏感性分析')[0];path.write_text(original+text)
print('Sensitivity complete: 20 cases, CI5',s['effects']['CI5'])
