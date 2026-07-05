# living-blueprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `design-journal` skill 改名+重写为 `living-blueprint`——维护一份永远当前、只讲功能不讲实现的工具全貌 `BLUEPRINT.md`，让 AI 重构不被旧实现绑架；并同步全仓引用。

**Architecture:** 纯文档 skill（无脚本、无 hook）。三步走：①重写 skill 本体（改目录名 + 全新 SKILL.md）；②改两个消费者（vibe-apps 必用、vibe-scripts 建议用）的引用；③改顶层清单（README / plugin.json / marketplace.json）+ 升版本，末尾用 grep 门禁保证旧名无残留。

**Tech Stack:** Markdown + JSON（Claude Code plugin/skill 约定）。验证靠 `grep`，无自动化测试框架。

## Global Constraints

- skill 名 **`living-blueprint`**；产物文件名 **`BLUEPRINT.md`**——**我方文件绝不再叫 `DESIGN.md`**（`DESIGN.md` 仅可作为「市面 UI 设计系统」的对比词，只允许出现在 `skills/living-blueprint/SKILL.md` 的划界/反模式里）。
- 蓝图**只记功能（what / 可观察行为），绝不记实现（how）**。
- 单份文件、五节骨架（一句话 / 功能与行为 / 边界 / 硬约束+自由声明 / 功能痛点）。
- 两条承重设计必须在 SKILL.md 出现：**行为契约**（给 X→做 Y）+ **硬约束/自由声明分离**。
- 触发**纯手动**；**不加任何 hook / 自动仪式**。更新方式含 subagent 蒸馏(大改)/inline(小改)、三源、subagent 三条死命令。
- 迁移后全仓（`skills/ README.md .claude-plugin/`）**不得残留** `design-journal` / `design_journal` / `踩坑` / `design-intent`。
- `plugin.json` 版本 `0.3.0 → 0.4.0`（破坏性改名）。
- 纯文档：**不新增脚本或 hook**。
- SKILL.md 需含致谢行（ceaksan/living-architecture + SDD 思路）。

---

### Task 1: 重写 skill 本体（改目录名 + 全新 SKILL.md）

**Files:**
- Rename: `skills/design-journal/` → `skills/living-blueprint/`（目录内仅 `SKILL.md`）
- Overwrite: `skills/living-blueprint/SKILL.md`（全文替换）

**Interfaces:**
- Produces（后续任务依赖的对外名）：skill 名 `living-blueprint`；产物文件 `docs/BLUEPRINT.md`；这两个字符串是 Task 2/3 一切引用要写成的目标值。

- [ ] **Step 1: 记录基线（改前 grep，确认旧名存在）**

Run:
```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
grep -rln "design-journal" skills/
```
Expected: 至少列出 `skills/design-journal/SKILL.md`、`skills/vibe-apps/SKILL.md`、`skills/vibe-scripts/SKILL.md`（证明旧名确实在用，后面才好验证清除）。

- [ ] **Step 2: 改目录名（保留 git 历史）**

Run:
```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
git mv skills/design-journal skills/living-blueprint
ls skills/living-blueprint/
```
Expected: 输出 `SKILL.md`；`skills/design-journal/` 不再存在。

- [ ] **Step 3: 全文覆盖 `skills/living-blueprint/SKILL.md`**

用以下**完整内容**覆盖该文件（这是最终稿，勿留占位）：

````markdown
---
name: living-blueprint
description: Use when an AI-built tool/project will live and evolve and you want a single always-current "what it does" doc so AI can refactor from intent without being anchored to the old implementation — 工具活蓝图 BLUEPRINT.md、只讲功能不讲实现、覆盖式当前全貌、行为契约、重构不被旧实现绑架。任何会长期迭代的项目可用(例:vibe-apps 必用、vibe-scripts 建议)。≠ UI 设计系统 DESIGN.md、≠ ADR 历史决策日志。纯手动触发。Stack-independent.
---

# living-blueprint：工具的「活蓝图」

## 总纲

> 一份**永远当前、只讲功能不讲实现**的工具全貌 `BLUEPRINT.md`。新会话读它就懂整个工具；想重构时，AI 照它**直接开做，不被旧实现的固有思维绑架**。

维护一份 BLUEPRINT 谁都会，本 skill 的价值是那套**纪律**：只写可观察行为、覆盖式当前真相、显式授权重构丢弃旧实现、提炼非流水账——没纪律的文档会退化成夹带实现、自相矛盾的流水账。**与技术栈无关。**

## 何时用 / 不用

- **用**：任何会长期存活、会被重构/迭代的工具/项目（例：vibe-apps 必用、vibe-scripts 建议用）。
- **不用**：跑完即弃的微脚本——建 BLUEPRINT.md 是过度工程。

## 与邻居划界（别串味）

| 对象 | 它是什么 | 本 skill 的不同 |
|---|---|---|
| superpowers spec/plan | 每次改动的详细「怎么做」+ 历史，散在时间线 | 不替代；坐其上，只留「当前功能全貌」。重构先读蓝图把握 what，再让 spec/代码管 how |
| ADR | 不可变、带编号的历史「为什么」 | 不记历史、只记现状、覆盖式。要不可变决策日志请用 ADR 类 skill |
| DESIGN.md（市面 UI 设计系统那种） | 配色/字体/组件的视觉规范 | 完全不同物种。这是**功能架构**——故我方文件用 `BLUEPRINT.md`、不用 `DESIGN.md`，躲开那片红海 |
| CLAUDE.md | 给 AI 的工作规约（how to work here） | 蓝图是工具的功能现状（what it is），不是干活规矩 |

## BLUEPRINT.md（一份文件，五节）

放在项目 `docs/BLUEPRINT.md`。骨架：

```markdown
# <工具名> 蓝图
> 活蓝图：正文永远是当前真相，改了就覆盖。只讲功能不讲实现。
> 重构照本文行为契约重写即可；未列为硬约束的一切都是实现细节，可自由更改。

## 1. 一句话
这工具是什么、给谁、解决什么。

## 2. 功能与行为
逐个功能写成「给它什么 → 它做什么 / 用户看到什么」（可观察行为，不写内部怎么算）。
- <功能A>：给 <输入/操作> → <输出/可见行为>
- <功能B>：给 … → …

## 3. 边界 / 明确不做
故意不做的事，防重构时功能膨胀。

## 4. 硬约束 + 重构自由声明
- 硬约束（重构必须守）：<如 离线运行 / 单文件 / 必须吃某格式 …>
- 重构自由声明：**以上未列出的一切均为实现细节，重构可随意更改。**

## 5. 功能痛点 / 易错点
自然语言：这个功能为什么难做对、容易错在哪。是第 2 节的补充，不是代码 bug 库。
```

### 两条承重设计（做不到这两条，蓝图就防不住「被旧实现绑架」）

1. **行为契约**：功能一律写成「给它 X → 它做 Y / 你看到 Z」的**可观察行为**，与实现无关。AI 拿它重写只需对齐行为，怎么实现随它。
2. **硬约束 / 自由声明分离**：显式列出少数「必须守」的，再补一句「其余皆实现细节，可自由改」。这句**主动授权** AI 丢掉旧实现——否则再功能向的文档 AI 也默认沿用旧结构。

## 触发与维护（纯手动）

- **读**：新会话重新上手、或要重构时，先读 `docs/BLUEPRINT.md`。（可在项目 CLAUDE.md 加一句「开场先读 BLUEPRINT.md」，不强制。）
- **写/更新**：**只在用户说「更新蓝图 / 记一下 X」时才覆盖更新**对应小节。不设 hook、不搞「拍板即自动更新」的仪式。
- **覆盖式**：正文永远当前真相；旧描述被推翻就**直接改写、不留历史**（历史归 ADR/spec）。
- **提炼非流水账**：记功能与行为，不逐字抄对话、不记实现过程。

### 更新方式：subagent 蒸馏（大改）/ inline（小改）

刚泡完实现细节的主 agent 容易把 how 写进蓝图。大改时派一个 fresh subagent 当**防实现泄漏的防火墙**，它也顺带把又大又吵的对话记录消化在一次性上下文里。

**三源并用**：现有 `BLUEPRINT.md`（基底）+ 本次对话/transcript（**意图源**：用户想要什么、为什么——代码常表达不出功能意图，且代码可能正是要被重构掉的旧实现）+ 当前代码（现实源：现在实际长啥样、哪些意图真落地）。

**subagent 三条死命令**：①只写可观察行为、不写实现；②只收最终拍板的意图，弃掉对话中途被否的废案（用代码「实际建了啥」辅助判定）；③覆盖式对账更新，标出「意图 ≠ 当前代码」处（那是下次重构的缺口）。

**graceful + 缩放**：transcript 在就读、不在就退化到「代码 + 主 agent 一句话简报」，不作持久依赖；只加一个功能/记一条痛点的小改，主 agent 直接 inline 覆盖，别为一行字起 subagent。

## 与 superpowers brainstorming 的接缝

蓝图不是 spec、也不替代 spec：大/新功能仍走 brainstorming→writing-plans→execute（产 dated spec/plan 记「怎么做」），完事后把「当前功能全貌」蒸馏进 BLUEPRINT.md（记「是什么」）。小/明确的改动，直接更新 BLUEPRINT.md→动手。一处 what、一处 how，不重复。

## 反模式

- 没建 BLUEPRINT.md 就开写长期项目
- 蓝图里写实现（怎么算/数据结构/用了啥库）——只该写可观察行为
- 只往里堆、不覆盖旧描述 → 正文自相矛盾、夹带过时功能
- 漏掉「硬约束 / 自由声明」→ AI 重构时默认沿用旧实现
- 把它当 ADR 用（要不可变历史日志请用 ADR 类 skill）
- 逐字抄对话当蓝图（要提炼意图与行为）
- 给跑完即弃的微脚本也套（过度工程）

## 致谢

固定骨架与「what/why 非 how-to-work」定位借鉴 ceaksan/living-architecture；「功能写成可验证行为」框法借鉴 Spec-Driven Development（spec-kit/OpenSpec）。均为思路借鉴，未复制代码。
````

- [ ] **Step 4: 验证 SKILL.md 含全部承重要素**

Run:
```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
F=skills/living-blueprint/SKILL.md
grep -q "name: living-blueprint" $F && \
grep -q "行为契约" $F && \
grep -q "重构自由声明" $F && \
grep -q "subagent 三条死命令" $F && \
grep -q "五节" $F && \
grep -q "致谢" $F && echo "OK: 承重要素齐全" || echo "FAIL"
```
Expected: `OK: 承重要素齐全`

- [ ] **Step 5: 验证目录已改名、无旧文件残留**

Run:
```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
test ! -d skills/design-journal && test -f skills/living-blueprint/SKILL.md && echo "OK: 目录已迁移" || echo "FAIL"
```
Expected: `OK: 目录已迁移`

- [ ] **Step 6: Commit**

```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
git add -A skills/living-blueprint skills/design-journal
git commit -m "feat(living-blueprint): design-journal 改名重写为工具活蓝图

单份 BLUEPRINT.md、五节、只讲功能不讲实现；两条承重设计=行为契约+硬约束/自由声明；纯手动触发+subagent蒸馏三源。收敛 DESIGN.md+踩坑.md 为一份。"
```

---

### Task 2: 改两个消费者的引用（vibe-apps / vibe-scripts）

**Files:**
- Modify: `skills/vibe-apps/SKILL.md`（第 71–96、115 行区域）
- Modify: `skills/vibe-scripts/SKILL.md:26`

**Interfaces:**
- Consumes（来自 Task 1）：skill 名 `living-blueprint`、产物文件 `docs/BLUEPRINT.md`。所有引用一律改写成这两个值。

- [ ] **Step 1: 基线 grep（确认这两个文件仍含旧名）**

Run:
```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
grep -n "design-journal\|DESIGN\.md\|踩坑" skills/vibe-apps/SKILL.md skills/vibe-scripts/SKILL.md
```
Expected: 列出 vibe-apps 的第 73/79/80/90/96/115 行与 vibe-scripts 第 26 行（证明待改点存在）。

- [ ] **Step 2: 改 `skills/vibe-apps/SKILL.md`「## 设计记录」段（第 73 行）**

将：
```markdown
**REQUIRED SUB-SKILL**：用 design-journal 建并维护 `CLAUDE.md` 规约段 + `docs/DESIGN.md` + `docs/踩坑.md`（模式 C、活文档、brainstorming 接缝都在那里）。vibe-apps **必用**——让 AI 照意图重构而非逆向猜代码。
```
替换为：
```markdown
**REQUIRED SUB-SKILL**：用 living-blueprint 建并维护 `docs/BLUEPRINT.md`（活蓝图、行为契约、更新方式都在那里）。vibe-apps **必用**——让 AI 照功能全貌重构而非被旧实现绑架。
```

- [ ] **Step 3: 改 vibe-apps 脚手架树（第 79–80 行）**

将：
```
├── CLAUDE.md              # design-journal 规约段 + 下方 vibe-apps 架构约束段
├── docs/{DESIGN.md,踩坑.md}   # ← 由 design-journal 建
```
替换为：
```
├── CLAUDE.md              # 「开场先读 BLUEPRINT.md」提示 + 下方 vibe-apps 架构约束段
├── docs/BLUEPRINT.md      # ← 由 living-blueprint 建(活蓝图)
```

- [ ] **Step 4: 改 vibe-apps 架构约束段引言与末句（第 90、96 行）**

将第 90 行：
```markdown
**CLAUDE.md 追加 vibe-apps 架构约束段**（在 design-journal 规约段之外）：
```
替换为：
```markdown
**CLAUDE.md 追加 vibe-apps 架构约束段**（与 living-blueprint 提示并列）：
```

将第 96 行：
```
DESIGN.md 的「## 架构」按此五层填写。
```
替换为：
```
五层属实现架构，记在本 CLAUDE.md 约束段即可；BLUEPRINT.md 只记功能与行为，不记五层。
```

- [ ] **Step 5: 改 vibe-apps 反模式行（第 115 行）**

将：
```
- 没建 DESIGN.md/踩坑.md 就开写
```
替换为：
```
- 没建 BLUEPRINT.md 就开写
```

- [ ] **Step 6: 改 `skills/vibe-scripts/SKILL.md:26`**

将：
```markdown
**工具包级 / 会长期迭代的脚本**：配合 **design-journal** 记设计意图与踩坑（微/标准级跑完即弃的通常不必）。
```
替换为：
```markdown
**工具包级 / 会长期迭代的脚本**：配合 **living-blueprint** 记功能全貌 `BLUEPRINT.md`（微/标准级跑完即弃的通常不必）。
```

- [ ] **Step 7: 验证两个消费者已无旧名**

Run:
```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
grep -n "design-journal\|DESIGN\.md\|踩坑" skills/vibe-apps/SKILL.md skills/vibe-scripts/SKILL.md && echo "FAIL: 仍有残留" || echo "OK: 消费者已清干净"
```
Expected: `OK: 消费者已清干净`（grep 无命中）。

- [ ] **Step 8: Commit**

```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
git add skills/vibe-apps/SKILL.md skills/vibe-scripts/SKILL.md
git commit -m "refactor(vibe-apps,vibe-scripts): 引用 design-journal→living-blueprint / DESIGN.md→BLUEPRINT.md"
```

---

### Task 3: 改顶层清单 + 升版本 + 全仓门禁

**Files:**
- Modify: `README.md:19-20`
- Modify: `.claude-plugin/plugin.json`（第 4「version」、第 6「description」、第 8「keywords」）
- Modify: `.claude-plugin/marketplace.json:11`

**Interfaces:**
- Consumes（来自 Task 1）：`living-blueprint` / `BLUEPRINT.md`。
- Produces：全仓迁移完成的终态（本任务末尾门禁保证）。

- [ ] **Step 1: 改 `README.md` design-journal 段（第 19–20 行）**

将：
```markdown
### design-journal
**意图驱动的设计记录**(与技术栈无关):在项目里维护 DESIGN.md(活文档)+ 踩坑.md,让 AI 照设计意图重构而非逆向猜代码,跨会话不丢上下文。被 vibe-apps(必用)和 vibe-scripts(工具包级)共同引用,也可单独用于任何会长期迭代的项目。
```
替换为：
```markdown
### living-blueprint
**工具活蓝图**(与技术栈无关):在项目里维护一份 `BLUEPRINT.md`——永远当前、只讲功能不讲实现的全貌,让 AI 照功能行为重构而不被旧实现绑架,新会话读一份就懂整个工具。被 vibe-apps(必用)和 vibe-scripts(建议)引用,也可单独用于任何会长期迭代的项目。
```

- [ ] **Step 2: 改 `.claude-plugin/plugin.json` version（第 4 行）**

将 `"version": "0.3.0",` 替换为 `"version": "0.4.0",`。

- [ ] **Step 3: 改 `.claude-plugin/plugin.json` description（第 6 行）里的 design-journal 片段**

将子串：
```
design-journal(意图驱动设计记录 DESIGN.md/踩坑.md,与栈无关,被 vibe-* 共用)
```
替换为：
```
living-blueprint(工具活蓝图 BLUEPRINT.md:单份·当前·只讲功能不讲实现,让 AI 重构不被旧实现绑架,与栈无关,被 vibe-* 引用)
```

- [ ] **Step 4: 改 `.claude-plugin/plugin.json` keywords（第 8 行）**

将 keywords 数组里的 `"design-journal", "design-intent"` 两项替换为 `"living-blueprint", "blueprint", "refactor"`。替换后该行为：
```json
  "keywords": ["learning", "tutor", "spaced-repetition", "python", "scripting", "gui", "pywebview", "fastapi", "desktop-app", "living-blueprint", "blueprint", "refactor", "memory", "curation", "consolidation", "hooks", "routing"]
```

- [ ] **Step 5: 改 `.claude-plugin/marketplace.json:11`**

将：
```
"learning-skill + learning-skill-plus + vibe-scripts + vibe-apps + design-journal 五个通用 skill 打包"
```
替换为：
```
"learning-skill + learning-skill-plus + vibe-scripts + vibe-apps + living-blueprint 五个通用 skill 打包"
```

- [ ] **Step 6: 校验 JSON 合法**

Run:
```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
python3 -m json.tool .claude-plugin/plugin.json >/dev/null && \
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null && echo "OK: JSON 合法" || echo "FAIL: JSON 语法错误"
```
Expected: `OK: JSON 合法`

- [ ] **Step 7: 全仓门禁 —— 旧名彻底清除**

Run:
```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
echo "--- 旧 skill 名 / 旧文件名 必须全清（应为空）---"
grep -rn "design-journal\|design_journal\|踩坑\|design-intent" skills/ README.md .claude-plugin/
echo "--- DESIGN.md 只允许出现在 living-blueprint 的划界/反模式里（下面应只列 living-blueprint/SKILL.md）---"
grep -rln "DESIGN\.md" skills/ README.md .claude-plugin/
```
Expected:
- 第一段 grep **无任何输出**（`design-journal`/`踩坑`/`design-intent` 全清）。
- 第二段 grep **只列 `skills/living-blueprint/SKILL.md`** 一个文件（那是刻意保留的对比词），不得出现 vibe-apps / vibe-scripts / README / 清单文件。

- [ ] **Step 8: 版本号确认**

Run:
```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
grep '"version"' .claude-plugin/plugin.json
```
Expected: `"version": "0.4.0",`

- [ ] **Step 9: Commit**

```bash
cd /Users/xu/MyDocuments/my-repos/xu-skills
git add README.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(xu-skills): 升 0.4.0——design-journal→living-blueprint(README/plugin/marketplace 同步)"
```

---

## 备注：版本号

Global Constraints 定为 `0.4.0`。若用户希望**暂不升版本**，Task 3 Step 2/8 跳过、其余照做——不影响功能，仅清单版本停在 0.3.0。执行者遇到此偏好按用户口径处理。
