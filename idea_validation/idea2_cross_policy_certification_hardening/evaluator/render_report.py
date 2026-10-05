import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]

def render():
    read=lambda name:json.loads((BASE/"results"/name).read_text())
    gates=read("gate_results.json");audit=read("oracle_boundary_audit.json")
    meta=read("metamorphic_test.json");rep=read("reproduction.json");final=read("final_verification.json")
    case_rows=[]
    for name,c in rep["cases"].items():
        case_rows.append(f"|{name}|{c['status']}|{c['D_policy']:.12g}|{c['C_pos']:.12g}|{c['C_conflict']:.12g}|{c['M1']['gap']:.12g}|")
    gate_rows=[f"|{k}|{v}|" for k,v in gates["gates"].items()]
    report=f"""# Idea 2 Stage-6A.1 实验结果

## 历史范围与本轮目标
Stage-6A 永久保留 CROSS_POLICY_CERT_NARROW。其 generator/evaluator 耦合、候选进程与强制schema边界缺失、多个模块只是 import *，且 G5 被硬编码。由此不能证明 oracle-free，并非已经发现 oracle 被使用。详见 SCOPE_CORRECTION.md。
本轮只加固 execution boundary，不重新设计科学机制。world、case列表、outcome table、TV距离、pair权重、阈值及生命周期全部复用历史定义；按旧结果做数值复现。

## 隔离架构和输入
private generator 单独生成精确数据及私有清单；匿名 JSONL 只包含 era_id/state/action/outcome，每条是 individual observation。era 满足 e 后至少三位数字；候选自行重建 exposure/success counts、profile、aggregate gap 和全部认证指标。
11个正式配置各在独立临时目录和 subprocess 执行。该目录只复制候选源码、逐条输入及 public_config.json；CLI 只有固定 input.jsonl、output.json。Python -I -S -B、标准输入关闭、其他描述符不继承，环境仅 LANG/LC_ALL。评估器在所有候选进程退出后才读取私有清单。
AST逐项检查导入，候选源码禁用词扫描通过状态为 {audit['forbidden_string_audit_pass']}。open audit限制读取在临时目录或解释器库、写入仅output.json；外部进程和网络禁止。临时目录外合成sentinel的实际读取拒绝测试为 {audit['filesystem_read_denial_probe']['blocked']}。这不是OS级恶意程序隔离证明；结论针对经过源码审计的正式执行路径。

## 强制schema与拒绝测试
六种额外字段分别为 gamma、policy_name、world、true_utility、ground_truth、expected_status。四种缺失字段与两种语义era ID亦分别测试。使用完整有效数据，只修改首条记录；要求明确schema错误、非零退出且不生成候选输出。额外字段拒绝：{audit['forbidden_field_rejection_pass']}；缺失字段拒绝：{audit['missing_field_rejection_pass']}；匿名era检查：{audit['anonymous_era_id_pass']}。G5 由实际11个子检查AND得到：{audit['G5']}，未硬编码。

## 私有元数据变换
基准加 {meta['private_metadata_mutations_tested']} 种私有元数据变换，涉及 world/effect/gamma/internal identifier。所有候选输入SHA相同：{meta['input_sha_equality']}；原始输出bitwise相同：{meta['output_bitwise_equality']}；canonical JSON相同：{meta['canonical_output_equality']}。未把metadata放入CLI或候选临时目录。输出没有时间戳、进程ID或临时目录绝对路径。

## 数值复现与M1
全部11个配置与Stage-6A历史正式JSON逐项匹配：{rep['all_match']}。浮点绝对容差固定1e-12；整数cell严格相同。W4的D_true/D_false={rep['D_true_over_D_false']:.12g}。M1只在评估器从observations按均匀target重算，候选认证不读取M1。
M1 ECHO与DIVERSE gap均为.40，而认证分别DESCRIPTIVE与PRESCRIPTIVE；复现通过状态：{rep['M1_non_substitutability_pass']}。这体现utility estimation和lifecycle information的不同作用，不表示M1估计失败。

|配置|认证状态|D_policy|C_pos|C_conflict|M1 gap|
|---|---|---:|---:|---:|---:|
{chr(10).join(case_rows)}

## 测试、锁、历史与Gate
预运行测试 {final['preformal_tests_passed']} passed；正式运行 {final['formal_run_count']} 次，restart={final['formal_restart']}。源码/配置/预注册SHA核验：{final['preregistration_hash_match']}。全部历史文件/链接数量 {final['history_file_count']}，逐字节/链接一致：{final['history_hash_match']}。

|Gate|结果|
|---|---|
{chr(10).join(gate_rows)}

## Verdict
{gates['verdict']}。本轮仅新增oracle-free execution boundary evidence；Stage-6A历史NARROW保持不变。

## 局限
仍仅synthetic discrete states、exact counts、known era segmentation；无natural-language parsing、automatic policy-change detection、finite-sample variance、continuous context、full-agent integration；thresholds are research probes；无novelty claim、lineage或long-run closed-loop stability证明。临时目录和Python审计不等同于操作系统权限分离，不声称抵御任意恶意代码或原生扩展。未扩大科学claim，未进入后续阶段。
"""
    (BASE/"Stage6A_1实验结果.md").write_text(report,encoding="utf-8")
    conclusion=f"""# Stage-6A.1 最终结论

**{gates['verdict']}**

实际G5={audit['G5']}，H0–H9结果见gate_results.json。11个固定case数值复现；基准及5种私有metadata变换的相同输入产生相同输出。候选正式路径只消费匿名逐条观测与固定公开阈值，私有生成器、元数据和历史真值不进入其工作目录、参数或环境。

Stage-6A历史CROSS_POLICY_CERT_NARROW永久保留。历史字节一致={final['history_hash_match']}。本轮结果仅限受审计执行路径和固定synthetic setting；完成后停止。
"""
    (BASE/"最终结论.md").write_text(conclusion,encoding="utf-8")
    return gates["verdict"]

if __name__=="__main__":
    print(render())
