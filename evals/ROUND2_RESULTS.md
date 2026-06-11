# Round 2: Skill 修复验证

## Case-09 重新分析

### Skill 修复效果

| 指标 | Round 1 | Round 2 | Δ | 状态 |
|------|---------|---------|---|------|
| 总分 | 33.3 | **39.2** | +5.9 | 未达标（<70） |
| Correctness | 1 | 1 | 0 | 无改善 |
| Completeness | 1 | 1 | 0 | 无改善 |
| Rigor | 1 | 1 | 0 | 无改善 |
| Clarity | 1 | 1 | 0 | 无改善 |
| Anti-gaming | 1 | 2 | +1 | 小幅改善 |

### 修复验证

**Skill 修复（commit 97d08c2）部分生效**：
- ✅ Gate 4（p<0.05）：agent 正确拒绝 p>0.05 的参数
- ✅ Gate 6（规格检查）：focus_um 范围验证通过
- ✅ Anti-gaming +1：逻辑矛盾减少

**但仍失败的原因**：
1. **Completeness 遗漏 join/pivot**：agent 未在报告中明确描述数据合并步骤（虽然实际执行了）
2. **cd_nm 机制缺失**：ground truth 期望 cd_nm 是机制，但 agent 报告 p=0.36 不显著

### 根本问题：Ground Truth vs 数据不匹配

**数据生成器设计**（generate_data_v2.py）：
```python
# Chamber C2 → cd_nm 超规格 (78-84 or 96-102，规格 85-95)
if litho_chamber == 'C2':
    cd_nm = uniform(78,84) if rand<0.6 else uniform(96,102)
else:
    cd_nm = uniform(85,95)  # 正常
```

**Agent 分析结果**：
- cd_nm 相关性 p=0.36（不显著）
- Chamber C2 vs others: p=0.368（Mann-Whitney）

**推断**：
1. 数据生成器的代码未正确执行
2. 或生成的 CSV 文件与代码不一致
3. 需要**重新生成数据**并验证信号注入

## 关键洞察

### Skill 改进不足以解决 GT 问题

本轮迭代发现：
- Skill 统计显著性修复是**必要的**（防止 p>0.15 被标记为 Tier-1）
- 但无法解决**数据生成 vs GT 不匹配**的问题
- 需要**数据质量验证**环节

### 飞轮缺失环节

当前飞轮：评测 → Skill 修复 → 再评测

**缺失**：数据生成器验证
- 生成数据后，应立即验证信号是否注入成功
- 例如：运行简单的统计检验，确认 cd_nm ~ chamber 相关性

## 下一步行动

### 优先级 1：数据验证
1. 重新生成 case-09 数据（执行 generate_data_v2.py）
2. 验证信号注入：
   ```python
   # 快速检验
   df = pd.read_csv('metrology.csv')
   pivot = df.pivot(...)
   merged = fab.merge(pivot)
   print(merged.groupby('litho_chamber')['cd_nm'].describe())
   # 期望：C2 的 cd_nm 偏离 85-95 规格
   ```
3. 如信号正确，更新 ground truth 使其宽容 agent 的合理分析路径

### 优先级 2：GT 对齐
- Case-01：验证交互效应是否真实存在于数据中
- Case-02：降低 rigor 期望（时序效应可能无法从静态数据推断）

### 优先级 3：继续迭代
- 修复数据/GT 后重新评测
- 目标：Round 3 达到平均 > 70

## Token 预算

- 已用：135k/200k（68%）
- 剩余：65k
- 策略：推送当前进展，下次会话验证数据质量

## 结论

**飞轮已启动但遇到数据质量瓶颈**：
- Skill 修复方向正确但不充分
- 数据生成器 vs 实际数据需要验证闭环
- 需要增加"数据质量验证"环节到飞轮中
