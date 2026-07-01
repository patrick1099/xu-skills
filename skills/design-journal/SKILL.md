---
name: design-journal
description: Use when a tool/project will live and evolve (not throwaway) and you want AI to work from recorded design intent instead of reverse-engineering the code, or when you keep re-explaining decisions / re-hitting the same bugs across sessions — 记录设计意图、DESIGN.md 活文档、踩坑记录、意图驱动开发、别让 AI 逆向猜代码。Referenced by vibe-apps(必用) and vibe-scripts(工具包级建议用). Set up early in a project. Stack-independent.
---

# design-journal：意图驱动的设计记录

## 总纲

> 自然语言的设计意图是源头，代码是它的派生物。AI 照**意图**重构，不逆向猜代码。

跨会话不丢：设计意图 + 已踩的坑都活在仓库里，新会话开场读一遍即可接上，不用你重讲、也不重复踩坑。**与技术栈无关**——任何会长期迭代的项目都能用。

## 何时用 / 不用

- **用**：会长期存活、会迭代的工具/项目（vibe-apps 必用；vibe-scripts 工具包级建议用）。
- **不用**：跑完即弃的微脚本——建 DESIGN.md 是过度工程。

## 三件套（放在项目仓库）

`CLAUDE.md` 规约段（让 AI 开场自动读+遵守）+ `docs/DESIGN.md`（活文档）+ `docs/踩坑.md`（bug 库）。

## 更新时机（模式 C：自动 + 手动）

- **自动**：拍板一个设计决策、或发现一个 bug/gotcha → 更新完对应文档再继续。
- **手动**：用户说「记一下 X」→ 立即记；「别记这个 / 撤掉」→ 移除或不记。

## DESIGN.md 是活文档

正文永远是"当前真相"，改主意就**直接改写正文**；被推翻的旧决定压成一句挪到文末「变更史」，注明"为什么从 A 改到 B"。**正文绝不自相矛盾。提炼不是流水账**（记意图与理由，不逐字抄对话）。

## 踩坑.md

每条 = **现象 / 根因 / 怎么防**。写新功能前先扫一遍，别重复踩。

## 会话开场

先读 `docs/DESIGN.md` 和 `docs/踩坑.md`，以其为准，照意图重构，不逆向猜代码。

## 与 superpowers brainstorming 的接缝

brainstorming 谈定的设计**直接落成该项目的初始 DESIGN.md**（覆盖 superpowers 默认 spec 位置，skill 自身允许），不另写 `docs/superpowers/specs/`；一处不留两份（小项目跳过 dated spec）；按大小缩放（大/新走完整 brainstorming→writing-plans→execute，小/明确的轻量→直接 DESIGN.md→动手）。

## 骨架（三文件内容）

**CLAUDE.md 规约段**（并入项目已有 CLAUDE.md）：
```markdown
## 设计记录规约（意图驱动开发）
会话开始先读 docs/DESIGN.md 和 docs/踩坑.md，以其为准，不逆向猜代码。
更新(自动+手动)：拍板决策/发现 bug → 更新对应文档再继续；用户「记一下 X」立即记、「别记这个」撤销。
DESIGN.md 是活文档：正文=当前真相可覆盖，旧决定压一句进文末「变更史」，正文不自相矛盾。提炼不是流水账。
踩坑.md：每 bug 一条 = 现象/根因/怎么防，写新功能前先扫。
```

**docs/DESIGN.md**：
```markdown
# <项目名> 设计意图
> 活文档：正文=当前真相可覆盖；改主意更新正文，旧决定进文末变更史。
## 一句话：这东西干嘛的
## 设计意图 / 关键决策
## 架构（本项目的分层/模块与依赖方向）
## 变更史（只追加，每条一句：从 A 改到 B，因为…）
```

**docs/踩坑.md**：
```markdown
# 踩坑记录
> 每条：现象/根因/怎么防。写新功能前先扫一遍。
## (日期) <一句话现象>
- 现象： / 根因： / 怎么防：
```

## 反模式

- 没建 DESIGN.md/踩坑.md 就开写
- DESIGN.md 只往里堆、不覆盖旧决定 → 正文自相矛盾
- 逐字抄对话当设计记录（要提炼意图）
- 开场不读 DESIGN.md/踩坑.md 就动手，逆向猜代码
- 给跑完即弃的微脚本也套这套（过度工程）
