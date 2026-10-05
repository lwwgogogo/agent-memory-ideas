# Idea 2：Clean Confirmatory Replication

本轮是独立确认性复现；Run 1 目录保持冻结，原结论 IDEA2_RUN1_NO_GO / IDEA2_NO_GO 不改写。生成机制完全复用，只有输出协议、Left/Right 标签配对和顺序平衡按用户要求重新固定。

唯一环境：agentmem_lab，Python 3.10.21。模型：qwq:32b。唯一研究工作区是当前远程仓库，无本地项目副本。

完整设计、retry policy、G0—G7 与 verdict 规则见 preregistration.md；320 planned runs，20 个基础场景。正式推理前必须生成病例、检测现有 Ollama 格式能力并运行全部 pytest。所有输出与失败尝试保留，不按结果重试超额。

```bash
cd /home/liaoweiwen/projects/agent-memory-ideas/idea_validation/idea2_policy_confounding_confirmatory
~/miniconda3/bin/conda run --no-capture-output -n agentmem_lab python generate_cases.py
~/miniconda3/bin/conda run --no-capture-output -n agentmem_lab python preflight.py
~/miniconda3/bin/conda run --no-capture-output -n agentmem_lab python run_llm_test.py
~/miniconda3/bin/conda run --no-capture-output -n agentmem_lab python evaluate.py
```

preflight.py 首次执行独立格式探测并记录已有服务信息，之后复用探测记录，不重新发送探测。正式 runner 使用可恢复的 attempt journal，已完成 run 不重发；配置或测试源码变化则拒绝混合运行。绘图单独成图，不使用 subplot。
