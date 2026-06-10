## 改进方向（从 L2 闭环提炼）

### 1. 已实施（本轮）

- **readiness helper grain 修复**（commit 待定）：优先用唯一 ID 列（`order_id`/`run_id` 等）推断粒度，避免 case-08 中"同日同渠道多单被误报重复"的问题。95% 唯一性阈值自动识别实体级 key。

### 2. 结构性改进（留待后续）

从 case-04（SPC）和 case-05（Simpson 交互）暴露的问题：

- **SPC 控制图与过程能力计算**不在 `method-registry.md` → agent 只能写脚本但不按流程套用模板。需补充：失控规则（Western Electric 8 rules）、Cp/Cpk/Pp/Ppk 计算、受控段判定。
- **Simpson 悖论与交互效应检测**未在标准流程明确 → case-05 agent 部分完成后停止。需在 `references/workflow.md` 或 method-registry 中明确：何时分层检验、pooled vs stratified 比较、交互项显著性检验。
- **数据生成脚本中文注释与 prompt 语言不一致**：`case-04-spc/generate_data.py` 和 `case-05-simpson-interaction/generate_data.py` 用中文注释描述注入信号，但 ground_truth.json 的 finding 正则是中英混合。建议统一为英文或在 prompt.txt 中明示"报告可用中文"。

### 3. 已验证稳定的部分

- **路由判定**：4/4 正确（profile-only、named-method、blocked、full）
- **artifact gate 遵守**：所有案例均按路由产出对应产物，未越界
- **readiness 阻断机制**：Y 缺失 44% 时正确停止，未强行结论
- **假设违反检测与替代方法**：Levene 失败 → Welch t 为主、Student's t 并列

### 4. Ground truth 校准记录

commit 82a276f 中两处正则扩展（非 skill 修改）：
- `temperature` 方向匹配：补"温度"、"越低"等中文同义词
- `equipment_age` 混淆：补"非独立驱动"、"协变量后消失"等表述
- `order_date` 格式问题：补"混用"的中文表述

下一轮建议先补 SPC + Simpson 方法到 registry，再重跑 case-04/05。
