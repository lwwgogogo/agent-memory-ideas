# Stage-6B 预注册：原生映射与方法差异化审计

审计日期：2026-10-06（Asia/Shanghai；起始UTC 2026-10-05）。基线 c23be78318fdd72758a2395ad579b4794454d632，开始时工作区干净且HEAD==origin/main。仅在远程唯一工作区执行。九个历史阶段全只读，历史verdict永久保留。

## 审计范围
Track A 检查JitRL、MemRL、ExpeL、Reflexion、ReasoningBank固定历史commit的源码、持久字段、真实运行信息及生命周期位置。优先既有只读checkout，不git pull、不修改upstream、不运行LLM或benchmark。不可动态确认的结论标记DYNAMIC_VALIDATION_BLOCKED。
Track B 依据公开论文方法/实验/局限正文、官方源码与项目页做查重；不只读摘要，不以关键词命中自动决定novelty。查全用户指定三个概念簇与疑似邻居；找不到可靠来源标NOT VERIFIED，不凭记忆补写。

## Track A 判据
字段NATIVE/DERIVABLE/MISSING/ORACLE_ONLY分别判定；新增日志只能REQUIRES_INSTRUMENTATION，不能算DERIVABLE。episode/task/timestamp不自动等于policy era。区分模型参数变化与memory-conditioned行为变化mu(a|x,M)。
MAP-L0：已有native/可解释可推导state/action/outcome和policy边界，无需修改核心agent即可形成原型。
MAP-L1：state/action/outcome已有非oracle运行信息，仅需policy/update/version/era标记等轻量metadata日志，不改变决策逻辑；不得将缺少动作/反馈对齐、证据链接或必要新算法藏在轻量metadata中。
MAP-L2：必须behavior regime/change-point discovery。MAP-L3：关键信息缺失或不适用。
至少2个MAP-L0/L1且至少一个JitRL/MemRL才NATIVE_MAPPING_GO；仅1个合格为NARROW；无合格为NO_GO。至少2个合格但缺少JitRL/MemRL时保守NARROW。复杂动作只做space/descriptor映射，不强套二元action或实现embedding/detector。

## 纳入与来源质量
优先arXiv、官方会议proceedings、OpenReview、ACL、作者官方代码。关键判断必须包含正文方法段落/章节或源码函数行号，保存标题、作者、年份、venue（未确认则明确unknown/preprint）、标识、URL和阅读范围。目标12–18篇agent/experience memory或learning相关，8–12篇有实质联系的母领域论文；不为数量纳入无关工作。允许审计过程中新增论文，禁止改判据。检索结果缺失/不可读不当作不存在。尽量读完整方法和局限；不提交下载PDF或全文镜像，仅引用、笔记、矩阵。

## 差异化与kill判据
C1 policy-conditioned evidence；C2单策略重复不证明transfer；C3版本数不等于多样性；C4跨策略冲突阻止prescriptive promotion；C5跨策略不变支持用于promotion；C6utility estimation与transfer eligibility不同；C7Policy Support Profile；C8 DESCRIPTIVE/PROVISIONAL/PRESCRIPTIVE生命周期。
每篇close work对C1–C8标NONE/PARTIAL/DIRECT。DIRECT COLLISION要求同问题、关键假设、解决对象和核心claim实质相同。state-aware retrieval、IPS、multi-domain invariance单独出现不自动kill。若同时覆盖LLM经验memory、behavior-policy provenance、多regime稳定性/多样性、未来跨policy reuse资格和相似认证生命周期，则CRITICAL并DIFFERENTIATION_NO_GO。
无直接覆盖且memory对象/生命周期差异明确为GO（仅限本次公开证据）；覆盖大部分且仅剩明确差异、或重要接近工作仍未排除碰撞为BORDERLINE。置信度阈值、ensemble agreement、metadata记录等替代解释必须正面讨论；同utility不同status本身不证明相对这些方法的新颖性。
数学母领域近邻只能形成风险或迁移关系，不能凭memory术语包装为novelty。

## 组合规则（固定）
采用附件第28节的显式定义：任一Track NO_GO → STAGE6B_NO_GO；两者GO → STAGE6B_GO；其余 → STAGE6B_NARROW。附件第27节中“mapping完全无法构造但differentiation GO仍NARROW”与此冲突，明确按第28节优先，不随结果选规则。
达到组合verdict后只完成证据核验、报告、获准状态追加、提交推送；不开始Stage7、算法实现、wrapper、lineage、uncertainty或LLM实验。

## 证据与验证
研究Markdown使用中文。代码证据保存commit+路径+函数+行号，不把未找到当无此机制的绝对证明。记录检索query、来源与阅读范围。历史所有文件/链接基线SHA与结束快照一致；所有CSV枚举、必需字段、唯一论文ID、来源、claim enum、verdict边界由小脚本校验。预注册SHA先保存provenance.json，终局只追加审计证据，不改kill/GO规则。禁止绝对首次或优于原生系统的宣称。
