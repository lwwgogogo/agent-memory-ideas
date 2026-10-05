# Stage-6A.1 预注册：Oracle-Free Boundary Hardening

## 范围与历史
本轮不改变科学假设，只验证 oracle-free execution boundary。Stage-6A 的 CROSS_POLICY_CERT_NARROW 永久保留。本轮开始时工作区干净，HEAD 与 origin/main 均为 1d95cfa60a30ed40ed3d49ba8aefd2c2be471906。历史八个目录的所有文件与符号链接在写入本阶段前生成基准 SHA256，正式结束再次逐一比较。

## 冻结科学配置
W1/W2：S0 的 A/B 成功率均 9/10，S1 均 1/5。W3/W4：S0 A/B 为 9/10、1/2；S1 A/B 为 7/10、3/10。每状态每 era 1000 条，Fraction 计算整数成功数，逐条导出，禁止随机抽样。P95=(95/100,5/100)，Q95 相反，R50=(1/2,1/2)，P90=(9/10,1/10)，P92=(92/100,8/100)。这些常量仅在私有生成器和评估器存在。
固定 11 个配置：W1 的 K=1/2/5/10/20；W2 的 PQ 与 PQPQ；W3 PQR；W4 P90/P92/P95；M1 ECHO 为 invariant law 下20个P95、DIVERSE 为同一 law 下PQR。无新世界、无新基线、无参数搜索。
epsilon=1e-12；状态平均二元 TV；D_policy 为所有 era pair TV 均值；pair weight=TV。PRESCRIPTIVE 必须 eras>=3、有效pair>=2、D>=.20、max(C_pos,C_neg)>=.80、C_conflict<=.10。零总权重为 DESCRIPTIVE，其余未通过阈值为 PROVISIONAL。符号和 weighted agreement 完全复用原规则。计算机浮点复现采用绝对误差<=1e-12；这不改变生命周期阈值。M1 仅由评估器按均匀 target 从观测重算，候选不读取其输出。

## 边界与正式顺序
私有生成器→匿名逐条 JSONL→临时目录候选 subprocess→评估器。每条输入必须且只能含 era_id/state/action/outcome；era_id 匹配 e 后至少三位数字。文件名 case_001 等只在评估端使用；候选固定看到 input.jsonl、output.json。world/policy 映射只存 results/private，标记 EVALUATOR ONLY。
候选目录只复制 candidate/*.py、固定 public_config.json 和一份 input.jsonl。使用当前 agentmem_lab 的 Python -I -S -B 启动，独立进程、禁用 site、隔离 Python 环境路径，进程环境仅 LANG/LC_ALL。候选 CLI 必须恰有两个固定路径参数。AST 验证导入白名单、禁止动态 eval/exec/import；完整扫描候选源中的禁用字符串。open 审计禁止临时目录和解释器库之外的读取、禁止非 output.json 写入，以及外部执行与网络连接。评估器只在全部正式候选进程退出后才读取 private truth。此结构用于验证受审计的代码执行路径，不声称对恶意代码提供 OS/容器级隔离。

## 变换与拒绝测试
固定 W3 sanitized input 的字节保持不变。基准私有metadata A和5种变换：全部字段改为fake值、单独改world、改effect label、改gamma、改internal identifier。总共6份输入副本和6次候选执行；保存输入/输出 SHA，要求输入相同、直接输出字节相同和canonical JSON相同。候选输出禁止时间/PID/临时目录绝对路径；进程PID只记录于评估器审计。
在完整有效逐条观测上仅修改首条记录，分别注入 gamma、policy_name、world、true_utility、ground_truth、expected_status；再分别缺失四个必需字段；再注入两个语义era ID。必须非零退出、无输出文件，且错误消息对应schema拒绝，防止把其他运行失败误计为通过。另测试父进程污染环境、非法CLI参数与临时目录外读取拒绝。

## Gate 固定
G5 从11个实际子检查的逻辑与计算：schema、额外字段拒绝、AST导入、禁用字符串、匿名era、subprocess、filesystem、metadata invariance、数值复现、缺失字段拒绝、environment。禁止硬编码。
H0：所有历史文件字节/链接相同。
H1：11个固定case逐项复现旧正式JSON的统计、profile、gap、status、sign，并验证精确整数cell和ratio≈18。
H2：所有export严格schema、匿名era，所有缺失字段拒绝。
H3：AST导入与禁用字符串均通过。
H4：所有正式进程独立、环境白名单、临时目录精确复制与open拒绝验证通过。
H5：至少5次私有metadata变换，输入和输出字节完全相同且每次隔离通过。
H6：六种额外字段全部拒绝。
H7：M1 echo/diverse gap均.40、差<=.02，echo不为PRESCRIPTIVE、diverse为PRESCRIPTIVE。
H8：对旧源代码作AST常量审计，核验原world/policy/config/阈值；case序列不变；锁文件全部相符。TV、pair均值、符号/冲突公式由运行前单元测试核验。
H9：实际G5组合成立。
H0–H9全部通过才 ORACLE_FREE_HARDENING_GO，否则 ORACLE_FREE_HARDENING_NO_GO；不能使用NARROW。

## 测试、锁与停止
至少32项预运行测试，全部通过且零skip/错误才锁定。锁 candidate、evaluator、generator、tests 全部Python、public_config、本预注册、历史基准与测试证据。Formal run只运行一次，formal_started.json防止静默重跑。代码bug若需修复，必须停止、记录restart后重测重锁；边界硬Gate失败后保留NO_GO，不自动修到PASS。输出全部审核后提交、推送并停止。

## 局限
synthetic discrete states、exact counts、known era segmentation；无自然语言解析、自动policy-change detection、finite-sample variance、continuous context、full-agent integration；阈值仍是research probes；无novelty、lineage或long-run closed-loop stability证明。本轮仅新增执行边界证据。
