# Idea 2 Stage-6B：原生映射与方法差异化审计
审计日期2026-10-06，环境agentmem_lab / Python3.10.21；唯一工作区 /home/liaoweiwen/projects/agent-memory-ideas。

- Track A：**NATIVE_MAPPING_GO**。JitRL L1、MemRL L3、ExpeL L1、Reflexion L0、ReasoningBank L3；均限报告明确的原生路径。
- Track B：**DIFFERENTIATION_BORDERLINE**。16篇agent论文、8篇母领域论文；保留3项不可替代性碰撞风险。
- Combined：**STAGE6B_NARROW**。不进入Stage7，不设计或实现方法。

[研究结果](Stage6B研究结果.md)给出完整解释；[原生总结](native_mapping/mapping_summary.md)、[差异化总结](literature/novelty_summary.md)和两类CSV是主要证据。研究来源只提交标识、笔记和方法定位，不提交全文缓存。preregistration.md保持冻结，SHA与九个历史目录基线见results/provenance.json和history_before.json。

校验：在项目根用agentmem_lab Python执行本目录validate_audit.py及test_validate_audit.py。只读取源码/CSV/历史文件；不导入agent、provider或模型。final_verification记录实际最终校验结果。潜在hook不代表已实现gate；MAP-L0/L1不代表动态效果通过。
