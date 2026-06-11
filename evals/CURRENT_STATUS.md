# 评测飞轮当前状态 (2026-06-12)

## 📊 所有 Case 评测状态总览

### ✅ 已饱和（100分）- 6个case
| Case | 版本 | 得分 | 最后评测 | 状态 |
|------|------|------|----------|------|
| case-01 | v2 | 100/100 | 2026-06-11 | ✅ 饱和（交互效应检测） |
| case-02 | v2 | 100/100 | 2026-06-11 | ✅ 饱和（A/B多指标权衡） |
| case-03 | v2 | 100/100 | 2026-06-11 | ✅ 饱和（时序季节性+异常） |
| case-04 | v2 | 100/100 | 2026-06-11 | ✅ 饱和（多线SPC分层） |
| case-05 | v2 | 100/100 | 2026-06-11 | ✅ 饱和（Simpson+时间序列） |
| case-09 | v2 | 100/100 | 2026-06-11 | ✅ 饱和（多源join+RCA） |

### ✅ 路由测试通过（100分）- 2个case
| Case | 得分 | 最后评测 | 类型 |
|------|------|----------|------|
| case-07 | 100/100 | 2026-06-12 | 路由：named-method（假设检验前置） |
| case-08 | 100/100 | 2026-06-12 | 路由：blocked（数据质量阻断） |

### ⚠️ 需要重新评测 - 1个case
| Case | 旧得分 | 新得分 | 问题 | 修复 |
|------|--------|--------|------|------|
| case-06 | 100 | 84 | 数据文件被玩具数据覆盖 | ✅ 已修复（commit 95b4ee9） |

## 📈 完成度统计

- **饱和case**: 6/9 (67%)
- **通过case**: 8/9 (89%)
- **待重测**: 1/9 (11%)

## 🔍 详细分析

### Case-06 退化原因
**问题**：
- 旧版评测使用 `examples/manufacturing_yield/dataset.csv`（500行，含 humidity_pct 列）
- 新版评测被本地玩具数据覆盖（5行，无 humidity 列）
- 导致 `missingness_noted` 检查失败（正则要求匹配 "humidity.*missing"）

**修复**：
- 删除 `evals/cases/case-06-routing-profile-only/dataset.csv`
- Ground truth 现在正确指向 `examples/manufacturing_yield/dataset.csv`
- 需要重新运行 L2 评测验证修复

### 路由测试案例表现
**case-07 (named-method)**：
- 测试目标：用户强制指定 t-test，skill 需要检测假设违反并建议替代方法
- 通过项：假设检查、违反检测、替代方法建议、纪律性（未盲目执行）
- 稳定性：2次评测均100分

**case-08 (blocked)**：
- 测试目标：45% 缺失率应触发 blocked 决策并生成 data_request
- 通过项：缺失检测、blocked 决策、data_request、日期格式问题标记
- 稳定性：2次评测均100分

## 🎯 下一步行动

### 1. Case-06 重新评测（优先级：高）
```bash
# 运行 L2 评测
claude -p "用 data-scientist skill profile 一下 examples/manufacturing_yield/dataset.csv"

# 评分
python evals/harness/score_case.py \
  evals/cases/case-06-routing-profile-only \
  evals/.runs/l2/case-06-retest-$(date +%Y%m%d) \
  --json score.json
```

**预期结果**：84 → 100（missingness_noted 应通过）

### 2. 验证 Skill 稳定性（优先级：中）
所有6个饱和case基于 commit `67873ad`（2026-06-11 21:12）的 SKILL.md。

**需要确认**：
- 最新的 SKILL.md（commit `be243e0`）是否引入退化
- 可通过重新评测 case-01~05,09 验证

### 3. 扩展评测覆盖（优先级：低）
当前9个case已覆盖：
- ✅ 统计方法：A/B测试、回归、SPC、时序分解
- ✅ 数据复杂度：交互效应、Simpson悖论、多源join
- ✅ 路由决策：profile-only、named-method、blocked
- ❌ 缺失：生存分析、分类模型、非线性检测、DOE

## 🏆 成就解锁

### Round 1-2 迭代成果（2026-06-11）
- ✅ 6个核心能力case从基线（27-90分）提升至饱和（100分）
- ✅ 评测系统从regex升级至agent judge
- ✅ 发现并修复2类缺陷：
  - Skill Gate 4/6（统计显著性、规格合理性）
  - 数据生成器（case-09 cd_nm 信号强度）

### 当前会话发现（2026-06-12）
- ✅ 识别 case-06 数据文件错误（回归测试价值验证）
- ✅ 确认 case-07/08 路由测试稳定性
- ✅ 整理完整评测状态（9/9 case已至少评测1次）

## 📝 备注

### agents/ 和 commands/ 未更新原因
从 git 历史看：
- Commit `3e7e8c9`: 移除 `plugins/data-scientist/agents/` 和 `commands/` 目录
- Commit `be243e0`: 文档说明架构简化

**现存结构**：
- `plugins/data-scientist/skills/analysis-workflow/agents/` - 子agent定义（7个stage）
- 这些是 skill 内部调用的子模块，不是独立的顶层 agents

**为什么没更新**：
- 过去迭代聚焦 SKILL.md 的 Gate 规则（统计显著性、产物强制、报告质量）
- 子agent会自动遵守 SKILL.md 中的约束（通过 system prompt 注入）
- 如果需要修改子agent行为，应该先确认是 SKILL.md Gate 不足还是子agent prompt问题

### 评测系统说明
- **L1（deterministic）**：regex匹配，0 token，CI友好
- **L2（agent judge）**：语义评分，~30k token/case，发现深层问题
- 当前使用 L2 为主要评测模式
- Score计算：加权平均（routing × 3 + artifacts × 2 + findings × 4 + charts × 2 + anti_patterns × 3）

---

**结论**：飞轮运转正常，9个case中8个已达标，1个待重测修复。继续按既定路径迭代。
