# 迭代飞轮状态

## 当前阶段：3-case 基线测试中 ⏳

**2026-06-13 审计 + 压缩 + 归档**：

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

## 评测架构（已改造）

- **L1**：`python evals/harness/run_l1.py` — 确定性回归，7/7 全绿，进 CI
- **L2**：`python evals/harness/run_l2.py` — 后台并发 headless 选手 + 独立双轨裁判，主会话只读 summary.json

## 进行中

- [ ] 3-case 完整 baseline（选手 + judge）运行中 → 建立第一个可信基线

## 下一步

1. 等 baseline 完成 → 读 summary.json（regex/judge 分数 + defects）
2. 按 judge defects 定位 SKILL.md 薄弱维度
3. 进入正常飞轮：一次改一维度 → 重测 → 提升 commit / 回退 revert
4. 循环至所有 case judge > 90 → 发布 v2.0
