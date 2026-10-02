import json
from pathlib import Path
out=Path(__file__).parent; families=[('C1','临时条件与长期偏好','偏好'),('C2','偏好与约束','约束'),('C3','规则与例外','例外'),('C4','当前与历史状态','当前'),('C5','证据与结论','证据'),('C6','支持与相关信息','支持'),('C7','条件适用性','条件'),('C8','纠正与否定','纠正')]
cases=[]
templates={
'C1':('用户平时喜欢本地模型，因为更在意隐私。今天服务器不能联网，所以这次必须使用本地模型。','如果网络恢复，用户通常优先什么模型？','本地模型','长期偏好'),
'C2':('用户不是偏爱 Python，只是当前服务器只能运行 Python；如果环境允许，用户更愿意使用云 API。','环境恢复后优先什么？','云 API','约束'),
'C3':('通常项目使用 Python，但这个项目因旧依赖必须使用 Ruby；该例外只适用于当前项目。','新的普通项目默认使用什么？','Python','例外'),
'C4':('用户以前使用模型 A，但上周已经迁移到模型 B，当前配置是模型 B。','当前配置是什么？','模型 B','当前'),
'C5':('观察到工具返回超时。根据这个现象，代理推断服务可能过载。','哪一项是直接观察到的事实？','工具返回超时','证据'),
'C6':('候选 X 价格低、颜色相似，但候选 Y 满足用户要求的续航和重量限制。','应推荐哪一个？','候选 Y','支持'),
'C7':('策略 S 只在网络稳定时有效；当前网络不稳定，应使用策略 T。','当前网络不稳定时使用什么？','策略 T','条件'),
'C8':('前面说推荐 A 是错误的。更正：真正应推荐 B，A 不满足最新限制。','最终应推荐什么？','B','纠正')}
for fam,name,short in families:
    h,q,a,role=templates[fam]
    for i in range(12):
        cases.append({'case_id':f'{fam}_{i:02d}','family':fam,'raw_history':h+f' 表达版本 {i}。','current_query':q,'correct_answer':a,'relevant_source_turns':[0],'required_memory_facts':[role+':'+a],'invalid_old_information':['旧结论不得覆盖当前问题'],'condition':short,'expected_update':role,'ambiguous':False})
(out/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)); print(len(cases))
