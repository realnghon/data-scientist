## 改进方向（从 L2 闭环提炼）

### 1. 已实施（本轮）

**Commit 36b4ab8** — readiness helper grain 修复：
- 优先用唯一 ID 列（`order_id`/`run_id` 等）推断粒度，避免 case-08 中"同日同渠道多单被误报重复"的问题。95% 唯一性阈值自动识别实体级 key。

**Commit 6e11194** — method-registry 扩展（SPC + Simpson）：
- Western Electric / Nelson 8 run rules 明确定义（规则 2: 连续 9 点同侧、规则 6: 5 点中 4 点超±1σ）
- Critical workflow: 必须先跑规则 1-8 检测稳定性，**只在稳定段**计算 Cp/Cpk
- Simpson 悖论检测协议（分层 vs 合并比较、交互项检测）加入 method-registry 2a 新章节

**Commit 待定** — leakage 检测 + pivot 指引强化：
- **Same-event measurement leakage**（data-readiness.md）：X 和 Y 在同一站点/时间戳测量 → 标记 partial，需排查因果方向（如 wafer final_test 的 speed 与 yield 同时产生，speed 可能是 yield 的副作用）
- **Pivot 反模式**（SKILL.md）：明确"entity×attribute 长格式必须先 pivot 成 entity 级宽表再做驱动排序"，否则混淆实体信号与测量类型噪声
- **同行结果特征反模式**（SKILL.md）：与 Y 在同一时间戳/事件测量的特征应验证时序，避免误把"效果"当"原因"

### 2. 结构性改进（留待后续）

从 case-04（SPC）和 case-05（Simpson 交互）暴露的问题：

- **SPC 控制图与过程能力计算**不在 `method-registry.md` → agent 只能写脚本但不按流程套用模板。需补充：失控规则（Western Electric 8 rules）、Cp/Cpk/Pp/Ppk 计算、受控段判定。✅ **已解决（commit 6e11194）**
- **Simpson 悖论与交互效应检测**未在标准流程明确 → case-05 agent 部分完成后停止。✅ **已解决（commit 6e11194）**
- **数据生成脚本中文注释与 prompt 语言不一致**：`case-04-spc/generate_data.py` 和 `case-05-simpson-interaction/generate_data.py` 用中文注释描述注入信号，但 ground_truth.json 的 finding 正则是中英混合。建议统一为英文或在 prompt.txt 中明示"报告可用中文"。

### 3. Case-09（wafer RCA）暴露的新问题

**场景**：300 片 wafer，5 站点，4500 行长格式（entity×station×param），需 pivot 后找根因。

**结果**：86.4% (12/14)
- ✅ Pivot 执行了（"pivot_executed" 通过）
- ✅ Litho 站点被识别（"litho_station_identified" 通过）
- ❌ **cd_nm 未被识别为根因**：agent 把 `final_test_speed_mhz` 排第一（Spearman 0.834），cd_nm 仅 0.210 排第三 → speed 是同站点测量（与 yield 同时刻），可能是 yield 的副产物而非上游驱动
- ❌ **data_transformations 缺失**：analysis_plan.json 没记录 pivot 步骤

**根因**：
1. **Leakage 检测漏洞**：final_test 的 speed 与 yield 同站点同时刻，但没被标记为"可能泄漏"
2. **Pivot 未被强制记录**：虽然执行了 pivot，但 analysis_plan 没要求记录 data_transformations

### 4. 已验证稳定的部分

- **路由判定**：4/4 正确（profile-only、named-method、blocked、full）
- **artifact gate 遵守**：所有案例均按路由产出对应产物，未越界
- **readiness 阻断机制**：Y 缺失 44% 时正确停止，未强行结论
- **假设违反检测与替代方法**：Levene 失败 → Welch t 为主、Student's t 并列

### 5. Ground truth 校准记录

Commit 82a276f 中两处正则扩展（非 skill 修改）：
- `temperature` 方向匹配：补"温度"、"越低"等中文同义词
- `equipment_age` 混淆：补"非独立驱动"、"协变量后消失"等表述
- `order_date` 格式问题：补"混用"的中文表述

下一轮建议：
- 测试 case-09 修复后的 leakage 检测能否排除 speed_mhz
- 考虑在 readiness helper 中自动检测"同站点特征"并标记
