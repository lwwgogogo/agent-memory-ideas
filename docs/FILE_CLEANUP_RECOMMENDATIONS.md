# 文件清理建议

2026-10-04 清点：根目录及深度三层文件列表保存在 /tmp/agent_memory_file_inventory.txt。排除 .git、环境、缓存、模型和 runtime；另外对 420 个受版本控制文件中不超过 5 MB 的文件进行 SHA256 比较。没有删除、移动、重命名任何文件。

## 数量与结论

发现 5 组内容完全相同的文件，共 15 个文件；这些多为复现快照或实验随附记录，不能简单去重。另有 1 个待审查归档候选 source.tar.gz，共 16 个需审查条目。根目录未发现带 (1)/(2)/(3)/old copy 的副本。当前可确认安全移动的文件：0。

## 疑似重复文件

### 第 1 组

- `agent_memory_failure_discovery/harness_validation/test_grader.py`
- `agent_memory_failure_discovery/harness_validation/tests/test_grader.py`

### 第 2 组

- `outputs/phase_a1_20260929/environment-lock.txt`
- `outputs/phase_a1_dense_20260929/environment-lock.txt`
- `outputs/phase_a1_length_diag_20260929/environment-lock.txt`
- `outputs/phase_a2_20260929/environment-lock.txt`
- `outputs/phase_a_20260924/environment-lock.txt`

### 第 3 组

- `outputs/phase_a1_20260929/validation.csv`
- `outputs/phase_a1_dense_20260929/validation.csv`
- `outputs/phase_a_20260924/validation.csv`

### 第 4 组

- `outputs/phase_a1_dense_20260929/postprocessing_source.zip`
- `outputs/phase_a1_length_diag_20260929/postprocessing_source.zip`
- `outputs/phase_a2_20260929/postprocessing_source.zip`

### 第 5 组

- `outputs/phase_a1_dense_20260929/source_snapshot.zip`
- `outputs/phase_a1_length_diag_20260929/source_snapshot.zip`

## 可归档候选与不能确认依赖的文件

- source.tar.gz：根目录历史源码包，66,152 字节；scripts/sync_server.ps1 第 19、21 行仍上传并解包该文件；未验证它与当前源代码的信息等价性，保留原位，不能删。
- 两处 test_grader.py：字节相同，但测试入口与相对导入依赖未全面审定，保留原位。
- environment-lock.txt、validation.csv 及 zip 快照：虽然部分字节相同，但属于不同实验的复现证据，保留各自实验路径。
- docs 的 execution / frozen / protocol 历史文件仍被 README 引用，不移动。
- 根 README、requirements.txt 与 scripts/ 属于旧路线的运行说明和依赖，不覆盖、不混装进新环境。
- Formation Sanity 实际位于 agent_memory_failure_discovery/formation_sanity/；根目录同名路径不存在，索引使用真实位置。

本轮只补充索引与建议，不执行 git mv，也不删除任何研究结果。

## 2026-10-05 逐组安全审计

5 组 / 15 个文件组内 SHA256 完全一致，均分类为 EXACT_DUPLICATE_REFERENCED。另一个 source.tar.gz 分类 UNKNOWN，存在同步脚本依赖且没有确认的等价主副本。没有符合安全移动全部条件的文件：归档 0 组、移动 0 个、16 个候选全部保留原位。未删除任何研究文件。完整 SHA256 与引用证据见 ../archive/duplicates_20261005/MANIFEST.md 和 audit.json。
