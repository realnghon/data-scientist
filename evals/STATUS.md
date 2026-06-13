# 迭代飞轮状态

## 当前阶段：审计完成 ✅ → 基线重测中 ⏳

**2026-06-13 审计结论**（详见 AUDIT_20260613.md）：

- 9/9 case 的数据信号经独立脚本验证，与 ground truth 一致（case-03 尖峰 bug 已修复重生成）
- 修复 3 个 P0：L1 崩溃（dataset/datasets schema）、case-09 prompt/GT/数据三方不一致、judge 3000 字截断
- 版本混乱清理：全部 case 统一为 `prompt.txt + ground_truth.json + generate_data.py + csv`
- **历史分数全部作废**：regex 100 分靠放宽正则刷出，judge 分数受截断影响，均不可作飞轮基线

## 评测架构（已改造）

- **L1**：`python evals/harness/run_l1.py` — 确定性回归，当前 7/7 全绿，进 CI
- **L2**：`python evals/harness/run_l2.py` — 后台并发 headless 选手 + 独立双轨裁判
  （regex 冒烟 + agent judge 主信号），主会话只读 summary.json，上下文隔离

## 进行中

- [ ] 全量 9-case L2 基线重测（后台 batch 运行中）→ 产出第一个可信基线

## 下一步（飞轮正常循环）

1. 读基线 summary.json → 按 judge defects 定位 SKILL.md 薄弱维度
2. 一次改一个维度 → 重跑受影响 case → record_result.py 记录
3. 提升 commit / 回退 revert，循环至所有 case judge > 90
4. 饱和后：README 评测章节更新，发布 v2.0

## 原则（审计教训）

- 分数下降优先怀疑评测系统，分数暴涨优先怀疑正则放水——两个方向都要人工抽查
- ground truth 修正与 skill 修改不混 commit
- 历史 judge/regex 分数与新基线**不可比**（截断与正则口径都变了）
