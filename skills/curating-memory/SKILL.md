---
name: curating-memory
description: Use when the user asks to 整理/清理/精简记忆, says memory burden is too heavy, or wants to consolidate their Claude Code persistent memory store — 判断每条记忆的最佳归宿(留 memory / 进 CLAUDE.md / 成 skill / 并入 plugin / 做成 hook)并提名, 追溯记忆到来源会话(originSessionId), 相对日期归一化为绝对日期, 精简 MEMORY.md 索引。铁律:先出计划→逐批批准→才动文件,绝不自动整理。
---

# Curating Memory

整理 Claude Code 的持久记忆库:合并、删除、重分类、瘦身索引、相对日期归一化,并**判断每条记忆的最佳归宿**(留 memory / 进 CLAUDE.md / 成 skill / 并入 plugin / 做成 hook),把该"晋升"的条目**挑出来提名**。手动触发。

**核心心法**:记忆库是被追溯过的资产。**先出方案 → 用户逐批批准 → 才动文件**。删除和改动永远不先斩后奏。

## 边界(先划清,别越权)

- ✅ 做:在记忆库内 合并/删除/重分类(改 type)/瘦身 + 同步 MEMORY.md + 相对日期归一化。
- ✅ 做:**归宿路由 + 提名**——判断每条记忆的最佳归宿(留 memory / CLAUDE.md / skill / plugin / hook),把该"晋升"的列成候选清单交出去。
- ❌ 不做:**自己动手建 skill / plugin / hook**(那是要各自 brainstorm + 测试纪律的另一件大事,只提名)。
- ❌ 不做:未经批准就删/改任何文件。
- ❌ 不做:自动整理——本 skill 永远手动触发、逐批批准。

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

先判**归宿**(这条记忆的最佳去处),再判**动作**:

| 归宿/裁决 | 命中信号 |
|---|---|
| **留 memory** | 跨项目偏好(feedback)/用户事实(user)/在进行的项目状态(project)/外部资源指针(reference),且无更强归宿。 |
| **→ CLAUDE.md** | **项目专属或全局的静态约定/规则**,AI 每次读上下文即可遵守。项目专属→该仓库 CLAUDE.md;跨项目通用→全局 `~/.claude/CLAUDE.md`。若已被现有 CLAUDE.md 完整覆盖 → 直接**删**,否则**提名**补进去。 |
| **→ skill** | 可复用的**操作流程/技法**("怎么做",会反复照做的步骤/checklist)。**提名**(建 skill 另走 writing-skills)。 |
| **→ plugin** | 比单个 skill 更大的能力集合,或需分发/多件打包(多 skill+hook+命令)。**提名**并指出并入哪个现有插件或新建。 |
| **→ hook** | **自动行为**("从今往后每次 X 就/之前/之后 Y"),靠"记住"办不到、必须 harness 执行。**提名**(SessionStart/PreToolUse 等 + settings 或插件 hooks)。信号:正文像"每次/每当/以后都/自动"。 |
| **删** | 一次性/仅本轮会话、已被取代、已证伪、或已被代码/CLAUDE.md/git 完整覆盖。**证伪或取代类必须回源核对**。 |
| **并** | 近重复,或同一主题系列(如 phaseN 进度条目)。合成一条,留最新真相 + 必要沿革。 |
| **重分类** | 事实没错但 type 标错。改 frontmatter 的 type。 |
| **归一** | 正文含相对日期(上周/3天前/昨天/最近/前几天/下个月…)。用该条 originSessionId 会话日期(或文件 mtime)作锚换算成绝对 `YYYY-MM-DD`。**锚不可靠就不猜,列进计划表让用户确认**——绝不擅自写可能错的日期。 |

判据冲突时:**先问、别猜**(见 [[feedback_no_silent_behavior_change]])。
一条记忆可同时命中"归宿"与"归一/精简":先归一,再定归宿。

## 计划表 → 批准 → 执行

先只输出一张表,**不动文件**:

```
| 文件 | 现type | 裁决 | 理由 | 来源核对 |
|------|--------|------|------|----------|
| project_indent_tabs.md | project | 删 | 已被用户改口取代(4空格) | jsonl 已确认 |
| project_sim_phase1/2.md | project | 并 | 同一模拟器进度系列 | — |
| feedback_vsix_release_steps.md | feedback | → skill | 是发版固定流程 | — |
| feedback_always_vsix_on_release.md | feedback | → hook | "每次发版就打 vsix"是自动行为,记忆保证不了 | — |
...

(裁决列填裁决判据表里的短码:留 memory / → CLAUDE.md / → skill / → plugin / → hook / 删 / 并 / 重分类 / 归一。)
```

按裁决分组呈现。**删除组必须逐条亮出正文 + 理由,等用户明确点头**才删。用户批准后:

1. 执行 合并/删除/改 type/日期归一化/瘦身。
2. **同步并精简 `MEMORY.md`(收尾审计,当独立资产审一遍)**:
   - 一条记忆 ↔ 恰好一行(不重不漏,实体与索引对不上即 bug);
   - 摘要句只答「未来的我 0.5 秒判断这条相关吗」——**够辨识即可,不一刀切砍短**;沿革/细节留详情文件。压明显超标的长摘要句;
   - 相关条目尽量相邻(借已有 `[[link]]` 关联);
   - 索引字符/行数超软上限 → 进**建议清单**提示"索引在膨胀,考虑合并同主题",不自动删。
3. 输出**归宿提名清单**(skill / plugin / hook / CLAUDE.md 候选),含建议归属与一句话理由,交给用户或后续流程——本 skill 到此为止,不建 skill/plugin/hook、不自动改 CLAUDE.md。
4. **写时间戳**:整理完成后,在 memory 目录写 `.curated` 文件,内容为首行今日 `YYYY-MM-DD`(供久未整理提醒 hook 读取)。

## 反模式

- ❌ 未批准就删/改文件。
- ❌ 删了记忆却不更新 MEMORY.md(索引与实体脱节)。
- ❌ 把"证伪/取代"当显然,不回源就删——这类最容易删错真相。
- ❌ 顺手把提名的 skill 直接建出来(绕过 writing-skills 测试纪律)。
- ❌ 在 memory 旁边找 jsonl——来源在 `~/.claude/projects/*/`,要跨目录 glob。
- ❌ 把"每次 X 就 Y"型自动行为记忆当普通 feedback 留着——它保证不了执行,应路由→hook。
- ❌ 留着相对日期不归一化(未来无法定位到底哪天)。
