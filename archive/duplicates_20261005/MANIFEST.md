# 重复文件安全审计清单

2026-10-05：5 组、15 个文件均通过 sha256sum 验证为组内字节相同。逐文件运行 git grep 检查完整路径、文件名及 Python 模块名，包含代码、Markdown、README、shell 引用。所有组均为 EXACT_DUPLICATE_REFERENCED；审计清单自身也是文档引用，但保留决定并不只依赖它：各类文件还涉及测试入口、运行代码、复现快照或实验清单。完整匹配保存在 audit.json。

归档组数：0；移动文件数：0；候选保持原位：16（15 个重复文件与 source.tar.gz）。没有执行 git mv、rm 或 git clean。此目录只保存审计记录，不代表已移动研究结果。

| 组 | 原路径 | 新路径 | SHA256 | 决定与保留副本 |
|---|---|---|---|---|
| 1 | `agent_memory_failure_discovery/harness_validation/test_grader.py` | —（未移动） | `4308844090280106baadc327e8f1390ab3be20954066364ad3615c029589a98a` | 原位保留；同组全部副本均保留 |
| 1 | `agent_memory_failure_discovery/harness_validation/tests/test_grader.py` | —（未移动） | `4308844090280106baadc327e8f1390ab3be20954066364ad3615c029589a98a` | 原位保留；同组全部副本均保留 |
| 2 | `outputs/phase_a1_20260929/environment-lock.txt` | —（未移动） | `d06b9e78fb97b3ab9e549c85774aa3d9ae5b44c58c0b67a22a7e36d6f1695c1a` | 原位保留；同组全部副本均保留 |
| 2 | `outputs/phase_a1_dense_20260929/environment-lock.txt` | —（未移动） | `d06b9e78fb97b3ab9e549c85774aa3d9ae5b44c58c0b67a22a7e36d6f1695c1a` | 原位保留；同组全部副本均保留 |
| 2 | `outputs/phase_a1_length_diag_20260929/environment-lock.txt` | —（未移动） | `d06b9e78fb97b3ab9e549c85774aa3d9ae5b44c58c0b67a22a7e36d6f1695c1a` | 原位保留；同组全部副本均保留 |
| 2 | `outputs/phase_a2_20260929/environment-lock.txt` | —（未移动） | `d06b9e78fb97b3ab9e549c85774aa3d9ae5b44c58c0b67a22a7e36d6f1695c1a` | 原位保留；同组全部副本均保留 |
| 2 | `outputs/phase_a_20260924/environment-lock.txt` | —（未移动） | `d06b9e78fb97b3ab9e549c85774aa3d9ae5b44c58c0b67a22a7e36d6f1695c1a` | 原位保留；同组全部副本均保留 |
| 3 | `outputs/phase_a1_20260929/validation.csv` | —（未移动） | `b374163021caa81a3353cea00cc91a390553bb290614c9b2e18ec3af0d60f669` | 原位保留；同组全部副本均保留 |
| 3 | `outputs/phase_a1_dense_20260929/validation.csv` | —（未移动） | `b374163021caa81a3353cea00cc91a390553bb290614c9b2e18ec3af0d60f669` | 原位保留；同组全部副本均保留 |
| 3 | `outputs/phase_a_20260924/validation.csv` | —（未移动） | `b374163021caa81a3353cea00cc91a390553bb290614c9b2e18ec3af0d60f669` | 原位保留；同组全部副本均保留 |
| 4 | `outputs/phase_a1_dense_20260929/postprocessing_source.zip` | —（未移动） | `930c3872f91854f278359471c1d5b622ab7c5d87f469ee1363ac838f95934290` | 原位保留；同组全部副本均保留 |
| 4 | `outputs/phase_a1_length_diag_20260929/postprocessing_source.zip` | —（未移动） | `930c3872f91854f278359471c1d5b622ab7c5d87f469ee1363ac838f95934290` | 原位保留；同组全部副本均保留 |
| 4 | `outputs/phase_a2_20260929/postprocessing_source.zip` | —（未移动） | `930c3872f91854f278359471c1d5b622ab7c5d87f469ee1363ac838f95934290` | 原位保留；同组全部副本均保留 |
| 5 | `outputs/phase_a1_dense_20260929/source_snapshot.zip` | —（未移动） | `6cf560edc64af9092a70d717212e70192561a27925360fc46ae7fee371c7db6e` | 原位保留；同组全部副本均保留 |
| 5 | `outputs/phase_a1_length_diag_20260929/source_snapshot.zip` | —（未移动） | `6cf560edc64af9092a70d717212e70192561a27925360fc46ae7fee371c7db6e` | 原位保留；同组全部副本均保留 |

## 源码归档包

source.tar.gz：SHA256 `d2c2b8e45207392198c77ccffa70ebe7840c4a0a85722ddb966ecbef051cbe16`。分类 UNKNOWN：没有已确认等价主副本，且同步脚本仍上传、解包该路径。保持原位。

## 为什么不移动

字节相同不能证明路径冗余。测试发现、生成脚本的相对路径、各实验 snapshot/manifest 的证据链均可能依赖原位置；不满足“没有任何代码/文档引用”的必要条件。没有 100% 安全可移动文件。

历史 Run 1 目录完全冻结；本次只新增审计文档。
