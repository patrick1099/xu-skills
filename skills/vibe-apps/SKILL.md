---
name: vibe-apps
description: Use when building a personal Python tool/app that has a UI, will be packaged and shared with others (exe), or might later grow into a website — 带界面的小工具、桌面工具、要发给别人的应用、可能变网站的 Python 应用；GUI、界面、打包 exe、pywebview、FastAPI。Load BEFORE scaffolding. For one-shot CLI / single-file scripts use vibe-scripts instead.
---

# vibe-apps：带界面 / 要分发的 Python 应用架构

## 总纲

> 一套栈通吃自用与分发，逻辑与界面物理隔离，核心对"谁"无状态。

省 token 原理：单栈免重构；core 纯逻辑既能 pytest，又为将来多用户/网站留门；HTTP 边界强制低耦合，AI 改一处只读一层。

## 适用判定（先分清 vs vibe-scripts）

| 特征 | 用哪个 |
|---|---|
| 跑完即弃 / 命令行 / 单文件 | **vibe-scripts** |
| 有界面 / 要发给别人(exe) / 要长期活或可能变网站 | **本 skill** |

**REQUIRED 前置**：建新东西先用 superpowers:brainstorming 谈定设计，再用本 skill 落地。

## 技术栈（定死，不再选）

| 位置 | 选什么 |
|---|---|
| 逻辑 | 纯 Python |
| API | FastAPI + uvicorn |
| 前端 | 原生 HTML/CSS/JS + CDN 引 CSS 框架(如 Pico.css)，**零构建、无 npm** |
| 窗口 | pywebview（只当壳；通信走本地 HTTP，**不用其专有 JS 桥**）|
| 打包 | PyInstaller |
| 测试 | pytest |

**禁止**：Tauri / Rust / Electron；默认不上 React/Vue/node 构建。小体积是审美需求、已主动放弃（Python 打包 30~40MB 无所谓）。

## 五层（依赖方向固定 App→Core, Core 不知 UI 存在）

| 层 | 职责 | 性质 |
|---|---|---|
| `core/` | 全部业务逻辑 | 纯 Python，可 pytest，工具"真身" |
| `api/` | 把 core 暴露成 `/api/...` HTTP/JSON | 薄，只做 HTTP↔core 翻译 |
| `web/` | HTML/CSS/JS，`fetch('/api/..')` 调后端 | 只管展示，不含业务逻辑 |
| `app.py` | 后台起 uvicorn + 开 pywebview 窗口 | 只管拼装 |
| pywebview | 把 localhost 页面套成原生窗口 | 纯壳 |

数据流：双击 exe → app.py 后台起 uvicorn(127.0.0.1:随机端口) → pywebview 加载该地址 → 前端 fetch → FastAPI 调 core → JSON → 渲染。

## 头号铁律：core 对"谁"无状态（唯一将来难补的门）

框架里别的都便宜可换，唯独这条焊死了，将来变网站就得回头**重写 core**。

```python
def summarize():                  # ❌ 读全局 DATA_FILE、焊死单用户
    data = load(DATA_FILE); ...
def summarize(data, store):       # ✅ 数据/存储显式传入
    ...
```

**判据**：core 里任何函数都能在 pytest 里直接构造输入调用、不碰全局——能做到，门就开着。这跟"core 要可 pytest"是同一件事，不额外花钱，也正是 vibe-scripts「Core 纯函数不 IO」纪律的放大版。**分寸**：只是别把单用户假设焊进 core，不是现在就建多用户/登录（YAGNI）。

## 换零件规则

- **同语言换零件**（FastAPI↔Django、pywebview↔别的窗口库、原生 HTML↔React）= 便宜，core 和 web 不动。
- **换法改变"逻辑用什么语言写"**（→Rust/Tauri）= 永远贵，core 要整个重写。
- 判据：这次换会不会改变逻辑用的语言。不改=便宜，改=贵。

## 成长为多人网站

同一 `core+api+web`，只换**交付层**：部署 FastAPI 到服务器（丢掉 pywebview/PyInstaller）、`api/` 加登录鉴权、加数据库按用户隔离。`core/` 不动——**前提是它从一开始就对"谁"无状态**。多人+登录+后台恰是 Django 甜区，也是 FastAPI→Django 便宜 swap 兑现之时。别提前建登录（YAGNI）。

## 意图驱动设计记录（模式 C：自动 + 手动）

每个工具仓库放三样（骨架见下）：`CLAUDE.md` 规约段 + `docs/DESIGN.md`（活文档）+ `docs/踩坑.md`（bug 库）。

- **更新时机**：自动——拍板设计决策/发现 bug 时主动更新对应文档再继续；手动——用户说「记一下 X」立即记、「别记这个」撤销。
- **DESIGN.md 是活文档**：正文=当前真相可覆盖改写；被推翻的旧决定压成一句挪文末「变更史」。正文绝不自相矛盾。提炼不是流水账。
- **踩坑.md**：每条 = 现象/根因/怎么防。写新功能前先扫。
- 开场先读这两份，照**意图**重构，不逆向猜代码。

**与 brainstorming 接缝**：brainstorming 谈定的设计**直接落成该工具的初始 DESIGN.md**（覆盖 superpowers 默认 spec 位置，skill 自身允许），不另写 `docs/superpowers/specs/`；一处不留两份（小工具跳过 dated spec）；按大小缩放（大/新走完整 brainstorming→writing-plans→execute，小/明确的轻量→直接 DESIGN.md→动手）。

## 脚手架（建目录 + 三文件）

```
mytool/
├── CLAUDE.md              # ← 规约段(下)
├── docs/{DESIGN.md,踩坑.md}   # ← 骨架(下)
├── core/*.py              # 纯逻辑, 可 pytest, 对"谁"无状态
├── api/server.py          # FastAPI 薄适配
├── web/{index.html,app.js,style.css}   # fetch 调 api; CDN 引 Pico.css
├── tests/test_*.py        # pytest 测 core
├── app.py                 # 起 uvicorn + 开 pywebview
├── requirements.txt       # fastapi uvicorn pywebview (+pyinstaller)
└── build.spec             # PyInstaller
```

**CLAUDE.md 规约段**：
```markdown
## 设计记录规约（意图驱动开发）
会话开始先读 docs/DESIGN.md 和 docs/踩坑.md，以其为准，不逆向猜代码。
更新(自动+手动)：拍板决策/发现 bug → 更新对应文档再继续；用户「记一下 X」立即记、「别记这个」撤销。
DESIGN.md 是活文档：正文=当前真相可覆盖，旧决定压一句进文末「变更史」，正文不自相矛盾。提炼不是流水账。
踩坑.md：每 bug 一条 = 现象/根因/怎么防，写新功能前先扫。
架构：core(纯逻辑可 pytest, 对"谁"无状态) / api(FastAPI 薄适配) / web(HTML+fetch) / app.py(拼装) / pywebview(壳)。
逻辑只放 core；前端默认原生 HTML/CSS/JS + CDN CSS，零构建无 npm。
```

**docs/DESIGN.md**：
```markdown
# <工具名> 设计意图
> 活文档：正文=当前真相可覆盖；改主意更新正文，旧决定进文末变更史。
## 一句话：这工具干嘛的
## 设计意图 / 关键决策
## 架构（core 纯逻辑 + api 薄 FastAPI + web 前端 + pywebview 壳；core 对"谁"无状态）
## 变更史（只追加，每条一句：从 A 改到 B，因为…）
```

**docs/踩坑.md**：
```markdown
# 踩坑记录
> 每条：现象/根因/怎么防。写新功能前先扫一遍。
## (日期) <一句话现象>
- 现象： / 根因： / 怎么防：
```

## 开发 / 交付两态

- **开发**：`uvicorn` 起服务，浏览器开 localhost，用 Chrome devtools 调 UI（pywebview 平时不参与，这正是不用专有桥的原因）。
- **交付**：pywebview 套窗口 + PyInstaller 打 exe 发人。

## 反模式（出现即返工）

- 业务逻辑写进 api/ 或 web/（必须只在 core/）
- core 读全局 / 写死数据文件 / 假设单用户
- 用 pywebview 专有 JS 桥（不可移植、没法浏览器调）
- 为了小体积去上 Tauri/Rust（小体积是审美，已放弃）
- 默认就上 React/Vue + node 构建
- 没建 DESIGN.md/踩坑.md 就开写
