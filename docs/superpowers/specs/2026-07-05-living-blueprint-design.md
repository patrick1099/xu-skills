# living-blueprint：工具的「活蓝图」设计

> 日期：2026-07-05
> 状态：设计已批准，待写实现计划
> 前身：`design-journal`（本轮改名 + 重定位 + 收敛为一份文件）
> 上游参考（只吸思路，不吸代码）：[ceaksan/living-architecture](https://ceaksan.com/en/living-architecture-ai-architectural-documentation)、Spec-Driven Development（spec-kit/OpenSpec 的「行为契约」框法）

## 1. 背景与根需求

`design-journal` 现状：维护 `DESIGN.md`（活文档）+ `踩坑.md`，让 AI 照设计意图重构、不逆向猜代码，跨会话不丢上下文。方向文档给它的升级方向本是「定位为活文档、与 ADR 划界」，但深聊后发现真正要改的不是定位措辞，而是**把它的根需求想清楚、并据此重定内容**。

**根需求（剥掉一切手段后的唯一目的）：**
> 用 AI 做长期存活的工具时，仓库里有**一份始终反映当前最新、完整功能全貌**的文档；当想让 AI 重构时，AI 照它**能直接开做，且不被原实现的固有思维绑架**。

推导出的三条性质（都是这个根需求的直接后果）：

1. **只讲功能（what），不讲实现（how）**。实现细节留给代码与 superpowers 的 spec。
2. **单份、永远当前、覆盖式**。不是按时间线堆积的增量 spec，也不是历史日志——读一份就掌握「此刻这工具是什么」。
3. **写成「重构契约」**：光「不写实现」不够，还要让 AI 主动敢扔掉旧实现（见 §3 的两条承重设计）。

「需求文档 / 功能文档 / bug 记录」这套三件套是早期猜测，**本设计不采用**：需求与功能同属「what」层，合成一份；原「bug 记录」重定义为**功能层痛点/易错点**（自然语言、非代码 bug），作为功能描述的**补充节**并入同一份文件。**两份文件（DESIGN.md + 踩坑.md）收敛为一份 `BLUEPRINT.md`**，比前身更轻。

## 2. 定位（一句话）

> **`living-blueprint` = 一份永远当前、只讲功能不讲实现的工具全貌文档（`BLUEPRINT.md`）。** superpowers 的 spec/plan 是「细节的、历史的、怎么做」，散在时间线上；这份是「概览的、当下的、是什么」，坐在它们**上面**。新开会话读它就懂整个工具；因为只记 what 不记 how，重构时不被旧实现绑架。与技术栈无关。

### 与邻居划界

| 对象 | 它是什么 | `living-blueprint` 的不同 |
|---|---|---|
| superpowers spec/plan | 每次改动的详细「怎么做」+ 历史 | 不替代；坐其上，只留「当前功能全貌」。重构先读蓝图把握 what，再让 spec/代码管 how |
| ADR | 不可变、带编号的历史「为什么」 | 不记历史、只记现状、覆盖式。要不可变决策日志请用 ADR 类 skill |
| `DESIGN.md`（市面 UI 设计系统那种，如 Stitch/awesome-claude-design） | 配色/字体/组件的视觉设计规范 | 完全不同物种。这里是**功能架构**，不是视觉设计——**正是为躲开这片已成气候的红海，弃用 `DESIGN.md` 文件名，改用 `BLUEPRINT.md`** |
| `CLAUDE.md` | 给 AI 的工作规约（how to work here） | 蓝图是工具的功能现状（what it is），不是干活规矩 |

## 3. 内容模型：`BLUEPRINT.md`（一份文件，五节）

```markdown
# <工具名> 蓝图
> 活蓝图：正文永远是当前真相，改了就覆盖。只讲功能不讲实现。
> 重构时照本节行为契约重写即可；未列为硬约束的一切都是实现细节，可自由更改。

## 1. 一句话
这工具是什么、给谁、解决什么。

## 2. 功能与行为
逐个功能写成「给它什么 → 它做什么 / 用户看到什么」（可观察行为，不写内部怎么算）。
- <功能A>：给 <输入/操作> → <输出/可见行为>
- <功能B>：给 … → …

## 3. 边界 / 明确不做
列出故意不做的事，防重构时功能膨胀。

## 4. 硬约束 + 重构自由声明
- 硬约束（重构必须守）：<如 离线运行 / 单文件 / 必须吃某格式 …>
- 重构自由声明：**以上未列出的一切均为实现细节，重构可随意更改。**

## 5. 功能痛点 / 易错点（原「踩坑」，功能层补充）
自然语言：这个功能为什么难做对、容易错在哪。是第 2 节的补充，不是代码 bug 库。
```

### 两条承重设计（本 skill 的真正差异点，无同类插件在做）

1. **行为契约**：功能一律写成「给它 X → 它做 Y / 你看到 Z」的**可观察行为**。行为级描述天生与实现无关，AI 拿它重写只需对齐行为，怎么实现随它——直接兑现「不被绑架」。
2. **硬约束 / 自由声明分离**：显式列出「必须守」的少数几条，再补一句「其余皆实现细节，可自由改」。这一句最便宜也最承重——它**主动授权** AI 丢掉旧实现，否则再功能向的文档 AI 也会默认沿用旧结构。

## 4. 触发与维护（纯手动，不加仪式）

- **读**：新开会话重新上手、或要重构时 → 先读 `BLUEPRINT.md` 掌握工具全貌。（可在项目 `CLAUDE.md` 加一句「开场先读 BLUEPRINT.md」，但不强制。）
- **写/更新**：**只在用户说「更新蓝图 / 记一下 X」时才覆盖更新**对应小节。**不设 SessionStart hook，不搞「拍板决策就自动更新」那套自动仪式。**
- **覆盖式**：正文永远是当前真相；被推翻的旧描述**直接改写、不保留历史**（历史归 ADR/spec，蓝图不背这个包袱）。
- **提炼非流水账**：记功能与行为，不逐字抄对话、不记实现过程。

## 5. 从 `design-journal` 迁移

本轮是**改名 + 重写 + 收敛**，不是新建：

- skill 目录 `skills/design-journal/` → `skills/living-blueprint/`。
- `SKILL.md` 按 §2–§4 重写；front-matter `name: living-blueprint`、`description` 重配（通用为主、vibe-* 降为举例、末尾标注「≠ UI 设计系统 DESIGN.md、≠ ADR 历史日志」）。
- 产物文件名 `DESIGN.md` → `BLUEPRINT.md`；原独立的 `踩坑.md` 折叠为 §3 内容模型的第 5 节（不再单开文件）。
- 引用方同步：`skills/vibe-apps/SKILL.md`（必用）、`skills/vibe-scripts/SKILL.md`（建议用）中对 design-journal / DESIGN.md 的引用改为 living-blueprint / BLUEPRINT.md。
- 顶层：`README.md`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` 的 skill 名/描述/keywords 同步。
- 版本：`plugin.json` 0.3.0 → **0.4.0**（skill 改名+重定位属破坏性变更）。**是否升版留待用户拍板**，spec 默认建议升。

## 6. 吸收清单（只吸思路）

| 来源 | 吸收什么 | 不吸什么 |
|---|---|---|
| ceaksan/living-architecture | ①「用固定小骨架保证完整、别写成散文」的做法（骨架已按功能层重定为 §3 五节）；②「讲 what/why、不讲 how-to-work」的定位话术 | L1/L2/L3 按文件数分级、数据模型表字段/安全头/热点文件等实现向重节、GitHub Action staleness 检查（我们手动） |
| SDD（spec-kit/OpenSpec） | 「功能写成可验证行为（given→then）」这一条纪律 = §3 的行为契约 | 每功能一份详细 spec 的重机器（那正是本 skill 要坐其上的东西） |
| ADR / dream-skill / 自动生成架构 | 无 | 全不吸，与根需求不搭 |

**承重的那条（行为契约 + 硬约束/自由声明）无任何同类插件在做——这是差异点。**

## 7. 明确不做（YAGNI）

- 自动触发 hook（SessionStart / 决策即更新）——只手动。
- L1/L2/L3 深度分级机器。
- 单独的代码级 bug 追踪器（原踩坑.md 那种）——功能层痛点并入第 5 节即可。
- 引入 SDD 的 spec 生成/校验机器。
- 打成 vsix / 独立发布——它仍是 xu-skills 插件里的一个 skill。

## 8. 测试与验收

本 skill 是纯文档 skill（无脚本、无 hook），验收靠**文档自洽 + 引用一致**，不涉及自动化测试：

- **内容模型完整**：`SKILL.md` 含 §3 五节骨架、§3 两条承重设计（行为契约 + 硬约束/自由声明）、§4 手动触发规则、§2 四条划界。
- **迁移无残留**：仓库内不再出现 `design-journal` / `DESIGN.md` / `踩坑.md` 旧引用（vibe-apps、vibe-scripts、README、plugin.json、marketplace.json 全部改净）；`grep -ri "design-journal\|DESIGN.md\|踩坑" skills/ README.md .claude-plugin/` 应为空（除本 spec 与致谢处刻意提及）。
- **定位不串味**：description 能让触发判定把它和「UI 设计系统 DESIGN.md」「ADR 历史日志」区分开。
- **致谢**：SKILL.md 或 README 补一句来源致谢（ceaksan/living-architecture、SDD 思路）。

## 9. 致谢

固定骨架与「what/why 非 how-to-work」定位思路借鉴 ceaksan/living-architecture；「功能写成可验证行为」框法借鉴 Spec-Driven Development（spec-kit/OpenSpec）。均为思路借鉴，未复制代码。
