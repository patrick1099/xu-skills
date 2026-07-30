---
name: skill-retrospective
description: Use only when the user explicitly asks to review, retrospect, improve, or evolve a skill/plugin from the current completed conversation; asks what should become a script or what should change in SKILL.md, its description, references, or tests; or requests a post-task skill retrospective. Launch an independent subagent to review evidence from one real run, separate automation candidates from prompt and validation changes, and return reviewable proposals without editing. Domain-agnostic and usable after any skill. Do not auto-run after ordinary task completion.
---

# Skill Retrospective

把一次真实运行留下的摩擦，转成有证据、可审核、不过拟合的 skill 改进提案。

## 边界

- 只在用户明确调用或明确要求复盘 skill 时运行；不要给每个普通任务自动追加复盘。
- 默认只分析当前对话和本次实际使用的 skill；除非用户明确要求，不扫描历史会话库。
- 必须使用一个新的独立子 agent。没有子 agent 能力时，说明无法满足独立复盘要求，不要假装完成了独立审查。
- 默认只读：不修改 `SKILL.md`、脚本、规则、hook、插件版本或 Git 状态。
- 只提出本次证据能支持的变化。不要把一次性的用户偏好塞进通用 skill。
- 把后续修改交给 `skill-creator` 或对应插件开发流程；本 skill 不替代实现和验证。

## 工作流

### 1. 确定复盘对象

确定：

- 用户这次真正想得到的结果；
- 本次实际触发或显式使用了哪个 skill；
- 可观察的最终结果、失败点和用户验收；
- 复盘范围是一个 skill，还是多个 skill 的边界问题。

用户未点名 skill 时，从当前对话中识别实际使用过的 skill，并明确写出你的范围假设。多个 skill 同时出现时，分别归因，不要把所有问题都堆进一个 `SKILL.md`。

### 2. 组装证据包

给复盘子 agent 提供尽可能原始的材料：

- 当前完整对话；无法直接继承时，提供保真证据包；
- 目标 skill 的完整 `SKILL.md`；
- 本次实际读取或运行过的 references、scripts、assets 和 agent 定义；
- 用户原始目标、纠正、否决、补充和验收；
- 工具调用、报错、重试、被放弃的调查分支；
- 实际改动、测试、构建、产物和最终结果；
- 当前宿主及其子 agent/上下文能力。

保真证据包必须保留具体转折点和可追溯锚点，不要只给成功摘要。优先提供原始对话和原始日志；如果对话已压缩，使用可用的原始 transcript 或高保真会话记录补回缺失证据。

只传与任务有关的内容。去掉令牌、密码、凭据和无关个人材料；不要借复盘扩大读取范围。

### 3. 启动独立复盘子 agent

使用宿主原生的子 agent 机制启动一个新 reviewer：

- 支持完整对话 fork 时，传递当前完整对话。
- 不支持继承对话时，传递第 2 步的证据包和目标 skill 文件。
- 不要先告诉 reviewer 你怀疑哪里有问题，也不要把预期答案写进 prompt。
- 要求 reviewer 只读，不得编辑文件或执行发布操作。

使用以下任务骨架：

```text
独立复盘这次 skill 的真实运行。阅读目标 skill 与原始会话证据，不修改任何文件。

判断：
1. 哪些观察是目标 skill 自身的问题；
2. 哪些重复机械步骤适合脚本化；
3. 哪些属于 description、正文、reference/example 或验证缺口；
4. 哪些其实属于宿主、项目规则、执行不遵从或一次性需求，不应修改该 skill。

每项必须引用具体对话、工具、文件或验证结果；给出最小改进意图、置信度和过拟合风险。
没有证据时明确写“证据不足”，不要补全故事。
```

### 4. 检查九个维度

参考 transcript-analysis/kaizen 的分类思路，但只检查当前运行：

1. **用户纠正与分歧**：用户是否重复解释、否决方案或指出行为偏离。
2. **错误与恢复**：是否重复报错、走错入口、靠临时绕路才恢复。
3. **绕路与最短路径**：是否出现无产出的调查分支或可明显缩短的步骤。
4. **机械序列与工具缺口**：是否反复执行相同、确定性的读写/转换/校验序列。
5. **委派与上下文缺口**：子 agent 是否缺材料、收到泄露结论，或任务边界不清。
6. **触发与归属**：description 是否漏触发、误触发，或问题其实属于相邻 skill。
7. **正文与资源缺口**：步骤顺序、决策边界、guardrail、reference/example 是否缺失、冲突或含糊。
8. **验证缺口**：是否缺少代表性输入、真实入口、回归检查或独立前向测试。
9. **宿主与系统干扰**：压缩、权限、工具缺失或平台差异是否被误判成 skill 缺陷。

### 5. 路由每个发现

每个发现只能选一个主要归宿：

| 路由 | 适用情况 |
|---|---|
| `SCRIPT_CANDIDATE` | 输入输出明确、判断少、可重复、失败可测试的机械步骤 |
| `SKILL_BODY` | 目标、步骤、顺序、决策边界或 guardrail 缺失/冲突 |
| `SKILL_DESCRIPTION` | 触发条件过窄、过宽或归属不清 |
| `REFERENCE_OR_EXAMPLE` | 正文不应膨胀，但需要可按需读取的细节或代表性例子 |
| `VALIDATION_OR_EVAL` | 指令可能合理，但缺少验证、回归或前向测试来证明 |
| `HOST_OR_PROJECT_RULE` | 问题属于宿主能力、全局偏好、项目规则、权限或环境 |
| `NO_CHANGE` | 一次性需求、证据不足、已有指令已清楚，或修改会过拟合 |

判定脚本候选时，先检查目标 skill 和项目里是否已有脚本、模板或工具；不要把“没看到”直接写成“应该新建”。

如果 skill 已经明确要求正确行为，而 agent 仍未遵从，不要靠重复加粗或堆更多文字修复。优先路由到验证、宿主执行、触发或上下文问题。

### 6. 设证据门槛和优先级

每个非 `NO_CHANGE` 发现必须包含：

- `证据`：具体用户轮次、工具调用、错误、文件、diff、测试或产物；
- `观察`：实际发生了什么；
- `影响`：浪费、错误、风险或用户成本；
- `根因假设`：为什么把它归到这个路由；
- `最小改进意图`：改变什么行为，不先写大段补丁；
- `置信度`：高 / 中 / 低；
- `过拟合风险`：为什么这不是只对本次有效。

按以下顺序排优先级：

1. 频率与影响；
2. 自动化价值；
3. 影响范围；
4. 实现和维护成本。

当前会话只有一次出现时，可以提出高影响的安全修复；普通脚本化建议必须说明它为何会在未来重复，而不是仅凭一次长命令就建工具。

### 7. 返回固定报告

默认在对话中返回，不写文件。只有用户明确要求持久化时才写报告，并遵守当前工作区的文档落地规则。

```markdown
# Skill 复盘

- 对象：
- 本次目标：
- 实际结果：
- 总判断：保持 / 小改 / 需要脚本 / 需要重新设计 / 证据不足

## 发现

| ID | 路由 | 证据 | 影响 | 最小改进意图 | 置信度 |
|---|---|---|---|---|---|

## 脚本候选

每项写明输入、输出、重复场景、失败模式和建议验证。

## 提示词与 skill 候选

每项写明目标文件/章节、缺陷类型和期望行为；不要直接应用。

## 不建议修改

列出一次性要求、证据不足项和不属于目标 skill 的问题。

## 待批准项

- [ ] R1 ...
```

### 8. 交回人工闸门

主 agent 复核 reviewer 的证据是否真的存在、归因是否对应当前 skill，然后把逐项提案交给用户决定。

用户未批准前：

- 不编辑 skill；
- 不创建脚本；
- 不更新版本；
- 不提交或推送；
- 不把提案写进长期记忆。

用户批准后，调用 `skill-creator` 做最小修改并验证。复杂或高影响的改动要让新的独立 agent 使用修改后的 skill 完成代表性任务，与本次失败点对照；一次复盘报告本身不等于改进已被证明。
