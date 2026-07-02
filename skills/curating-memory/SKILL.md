---
name: curating-memory
description: Use when the user asks to 整理/清理/精简记忆, says memory burden is too heavy, or wants to consolidate their Claude Code persistent memory store — including deciding which memories should instead become skills or move into CLAUDE.md, tracing a memory back to its origin session, and pruning stale/duplicate entries.
---

# Curating Memory

整理 Claude Code 的持久记忆库:合并、删除、重分类、瘦身索引,并把「该变成 skill」「该进 CLAUDE.md」的条目**挑出来提名**。手动触发。

**核心心法**:记忆库是被追溯过的资产。**先出方案 → 用户逐批批准 → 才动文件**。删除和改动永远不先斩后奏。

## 边界(先划清,别越权)

- ✅ 做:在记忆库内 合并/删除/重分类(改 type)/瘦身 + 同步 MEMORY.md。
- ✅ 做:**提名**——把「该升级成 skill」「该进 CLAUDE.md」的条目列成候选清单交出去。
- ❌ 不做:**自己动手建 skill**(那是要 brainstorm + writing-skills 测试的另一件大事,只提名)。
- ❌ 不做:未经批准就删/改任何文件。

## 找到记忆库与来源(路径不在一起)

- 记忆库:宿主注入的 memory 目录(形如 `~/.claude/projects/<项目slug>/memory/`),含各 `*.md` + `MEMORY.md`。
- 来源会话:frontmatter 的 `originSessionId` 对应的 transcript 在 `~/.claude/projects/*/<originSessionId>.jsonl`——**跨所有 project 子目录 glob 找**(worktree 会各有自己的目录,不在 memory 旁边)。

## 四步流程

1. **廉价扫**:读 `MEMORY.md` + 每个文件的 frontmatter(name/description/type)。先不深读正文。
2. **初判 + 聚类**:按下方判据给每条一个裁决;把疑似重复/系列的聚到一起。
3. **追溯**(两模式,开场跟用户确认用哪种):
   - **lazy(默认)**:只有可疑条目才 glob 打开来源 jsonl 核对。可疑 = 看着过期/自相矛盾/疑重复/表述不清/裁决拿不准。
   - **deep(用户说"深挖/额度够/全追")**:每条都回源核对再裁决。
4. **出计划表 → 逐批批准 → 执行**:见下。

## 裁决判据(整理的"正确归纳")

| 裁决 | 命中条件 |
|---|---|
| **提名→skill** | 描述的是**可复用的操作流程/技法**(会反复照着执行的"怎么做"),而非静态事实。信号:正文像步骤、像 checklist、像"每次都这么做"。 |
| **提名→CLAUDE.md** | **项目专属**的约定/约束,应随那个仓库走。项目专属→该项目 CLAUDE.md;跨项目通用偏好→全局 `~/.claude/CLAUDE.md`。常与现有 CLAUDE.md 重叠 → 若已被 CLAUDE.md 完整覆盖则直接**删**,否则提名补进去。 |
| **留** | 跨项目偏好(feedback)、用户事实(user)、在进行的项目状态(project)、外部资源指针(reference)。 |
| **删** | 一次性/仅本轮会话、已被取代、已证伪、或已被代码/CLAUDE.md/git 完整覆盖。**证伪或取代类必须回源核对**(lazy 模式下这类算"可疑")。 |
| **并** | 近重复,或同一主题的系列(如 phaseN 进度条目)。合成一条,保留最新真相 + 必要沿革。 |
| **重分类** | 事实没错但 type 标错(如一条 feedback 被记成 project)。改 frontmatter 的 type。 |

判据冲突时:**先问、别猜**(见 [[feedback_no_silent_behavior_change]] 心法——冲突先问不擅自改)。

## 计划表 → 批准 → 执行

先只输出一张表,**不动文件**:

```
| 文件 | 现type | 裁决 | 理由 | 来源核对 |
|------|--------|------|------|----------|
| project_indent_tabs.md | project | 删 | 已被用户改口取代(4空格) | jsonl 已确认 |
| project_sim_phase1/2.md | project | 并 | 同一模拟器进度系列 | — |
| feedback_vsix_release_steps.md | feedback | 提名→skill | 是发版固定流程 | — |
...
```

按裁决分组呈现。**删除组必须逐条亮出正文 + 理由,等用户明确点头**才删。用户批准后:

1. 执行 合并/删除/改 type/瘦身。
2. **同步 `MEMORY.md`**:删掉对应行、更新合并后的行、修好指向。
3. 输出**提名清单**(skill 候选 / CLAUDE.md 候选),含建议归属与一句话理由,交给用户或后续流程——本 skill 到此为止,不建 skill、不自动改 CLAUDE.md。

## 反模式

- ❌ 未批准就删/改文件。
- ❌ 删了记忆却不更新 MEMORY.md(索引与实体脱节)。
- ❌ 把"证伪/取代"当显然,不回源就删——这类最容易删错真相。
- ❌ 顺手把提名的 skill 直接建出来(绕过 writing-skills 测试纪律)。
- ❌ 在 memory 旁边找 jsonl——来源在 `~/.claude/projects/*/`,要跨目录 glob。
