# 迭代飞轮状态

## 当前阶段：SKILL.md 修复完成 ✅ → 第 2 轮 baseline 测试中 ⏳

**2026-06-13 审计 + 压缩 + 飞轮迭代第 1 轮**：

### 审计结论（详见 AUDIT_20260613.md）
- 9/9 case 的数据信号经独立脚本验证，与 ground truth 一致
- 修复 3 个 P0：L1 崩溃、case-09 三方不一致、judge 3000 字截断
- 版本规范化：全部 case 统一为 `prompt.txt + ground_truth.json + generate_data.py + csv`
- **历史分数全部作废**（regex 靠放宽正则刷出，judge 受截断影响）

### Case 压缩（9 → 3，token 成本 -60%）
压缩后的 3 个复合 case，领域独立、覆盖全面：

| Case | 融合来源 | 覆盖能力 | 数据规模 |
|---|---|---|---|
| **A: 制造业质量综合** | 01+04+09 | 交互效应 + 分层 SPC + 多表整合根因 + 机制解释 | 4 表（fab_log 1200 行 + metrology 1200 + spc_daily 2160 + final_test 300）|
| **B: 商业决策与悖论** | 02+05 | 多指标权衡 + Simpson 悖论 + 市场迁移机制 | 单表 19200 订单（24 月 × 3 地区）|
| **C: 时序监控与路由** | 03+06+07+08 | 时序分解 + 异常分类 + 数据就绪性判断 + 路由 3 模式 | 单表 4320 小时读数（180 天）|

**信号验证**（全部通过）：
- Case A: L3 SPC 失控 +0.78mm、C2 chamber cd_nm 82 vs 90（良率 67 vs 90）、温度×年龄交互 p=0.053
- Case B: Simpson 悖论成立（整体 Treatment +0.39pp，各地区 -3.25/-1.37/-0.21pp，市场迁移 68.9% North）
- Case C: 前 90 天缺失 4.4%、后 90 天 43.7%、10 尖峰 + day90-95 偏移 + day120+ 漂移

**冒烟测试**（3/3 通过）：
- Case A: 620.8s, 321 行报告 ✅
- Case B: 446.8s, 307 行报告 ✅
- Case C: 617.5s, 224 行报告 ✅

**归档完成**：原 9-case 移至 `_archived-9case-20260613/`，保留作深度调试套件。

### 飞轮迭代第 1 轮（完成）

**Baseline 分数**（20260613-1055）：
- Case A: regex=81.0 judge=70.6（制造业）
- Case B: regex=80.3 judge=84.3（商业）✅
- Case C: regex=68.0 judge=62.7（时序）❌

**SKILL.md 修复**（5 个 commits）：
1. **bf56e37** — 尖峰检测阈值（k=1.5）+ 多周期季节性（日+周+月）+ data_request 格式明确
2. **385a4f5** — 交互效应 MANDATORY 触发 + SPC 失控时间定位
3. **2ace08f** — Tier-1 判定例外（CUSUM 等专用算法）+ 季节性趋势检验（对 trend 成分）
4. **b7b929c** — Case A 交互效应降级 optional_claim（数据信号 p~0.05 边界不稳定）
5. **ed5cae0** — A/B test rigor（时间混淆+revenue 条件均值+假设检查）+ 时序假设（ACF+ADF）

**测试结果**：
- Case C: 62.7 → 82.4（+19.7）✅ correctness defects 全部修复
- Case A: 70.6 → 待测（交互降级后）
- Case B: 84.3 → 待测（rigor 增强后）

## 评测架构（已改造）

- **L1**：`python evals/harness/run_l1.py` — 确定性回归，7/7 全绿，进 CI
- **L2**：`python evals/harness/run_l2.py` — 后台并发 headless 选手 + 独立双轨裁判，主会话只读 summary.json

## 进行中

- [ ] 3-case 第 2 轮 baseline（SKILL.md 修复后）→ 验证修复效果

## 下一步

1. 读第 2 轮 baseline summary.json → 对比改进幅度
2. 如果平均 judge >85 → 继续定位剩余 defects
3. 如果某 case 仍 <80 → 针对性修复该 case
4. 目标：所有 case judge >90 → 发布 v2.0
