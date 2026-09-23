---
name: slide-flow
description: 用 Slidev 做好看、能直接上台讲的幻灯片：AI 按确认过的大纲直接出成品，用户在对话里提意见或直接改页面；用户想掌控某几页结构时，也可以自己在 PowerPoint 里画方框箭头当草稿交给 AI（可选，AI 不主动要）；图按类型分工（HTML/CSS 摆放图、D2 连线图和时序图、WaveDrom 位域、draw.io 供用户手调），交付前自动截图查出界。Use when the user wants AI to make a presentation / slide deck / 幻灯片 / 演示 / PPT 效果的网页 / 讲解课件，or hands over a PowerPoint sketch (.pptx 草稿) to turn into polished slides, or asks to revise an existing slide-flow deck. 用户明确要 .pptx 成品文件时用 pptx skill，不用本 skill。
---

# slide-flow：AI 写幻灯片

成品是 Slidev 工程（Markdown + 少量 HTML），AI 改一处只动几行。默认 AI 按大纲直接出成品，用户看了在对话里提意见；PowerPoint 草稿是可选入口，只在用户自己带来时用。所有命令都在 `scripts/sf.py`（`py -3 scripts/sf.py --ai-help` 看完整用法），路径相对本 skill 目录。

## 硬规矩

- **先问后写的只有两处**：大纲（第 3 步）和风格（第 2 步，只在第一次）。其余步骤直接做。
- **草稿不是必经步骤**：只有用户自己丢来 .pptx 草稿、或明说“我先画个草稿”时才走第 4 步。不主动生成空白草稿模板，不劝用户画，大纲确认后直接写成品。
- **不覆盖用户的改动**：改某页前先重读那页文件；用户动过的字句保留，只改你被要求改的部分。
- **每页交付前必须过 `diagrams → lint → qa` 并看截图**。qa 报的问题和截图里看到的问题都修掉再给用户。
- **素材可能保密**：成品和中间产物只留本机，不发到 Artifact、图床或任何在线服务，除非用户明说。
- **用户明确要 .pptx 成品**时换 pptx skill；本 skill 的成品是 Slidev 工程和导出的 PDF。

## 流程

| 步 | 做什么 | 命令 | 先读 |
|---|---|---|---|
| 0 环境 | 查依赖，缺什么按提示装 | `sf.py doctor` | `references/setup.md`（缺东西时） |
| 1 起盘 | 从模板建工程 | `sf.py init <deck> --title ...` | — |
| 2 定风格 | **只在用户还没定过默认主题时**：出三套预览让用户挑，挑完设为默认 | `sf.py preview-themes <dir>` → `sf.py themes --set-default <名>` | — |
| 3 大纲 | 写进 `MAP.md`：每页一行（标题写结论、一句话要点、版式、图的类型）。**给用户确认再往下** | — | `references/design-guardrails.md` |
| 4 草稿（可选） | **默认跳过**。用户带来草稿时读结构，并**打开每页 PNG 亲眼看**；用户说要自己画、问怎么画时，才生成带示范的空白草稿 | `sf.py draft <deck>/drafts/draft.pptx` · `sf.py draft-template <deck>/drafts/draft.pptx` | `references/draft-conventions.md` |
| 5 生成 | 写 `pages/*.md`，图的源文件写进 `diagrams/` | — | `references/authoring.md` · `references/diagram-routing.md` |
| 6 检查 | 渲染图、版面规则、截图出界；读截图修问题；更新 `MAP.md` 状态 | `sf.py diagrams` → `sf.py lint` → `sf.py qa` | — |
| 7 交给用户 | 告诉用户怎么打开：在 `<deck>` 目录跑 `slidev`（浏览器实时预览，改文件自动刷新） | — | — |
| 8 批改循环 | 按用户的改法回到第 5 步（用了草稿的回到第 4 步），只重做受影响的页 | 同上 | — |
| 9 交付 | 导出 PDF | `sf.py export <deck>` | — |

### 第 4 步（可选）：草稿怎么变成页面

只在用户带来草稿时用。没有草稿的页 AI 自己按大纲排版。

1. `sf.py draft` 给出每页的结构摘要（标题、框、连线从谁到谁、红字指令、备注）和 PNG 路径。**摘要和图片都要看**：摘要给准确的文字和连接关系，图片给整体布局感觉。
2. 按草稿的**空间关系**选版式：横排几个框 → `sf-flow` 或 `sf-grid`；框之间有很多连线 → D2 图；左文右图 → `split` 版式。位置只取意图，不照抄坐标。
3. 红字指令优先级最高，照做；做不到时在回复里说明原因。
4. 备注栏的内容写进该页讲稿（`<!-- -->`），不上页面。
5. 在 `MAP.md` 记下“草稿第 N 页 → 成品第 M 页”。

### 第 8 步：用户的改法

- **在对话里提意见**（最常见）：定位到页，改完照样过第 6 步。
- **直接改了 `pages/*.md`**：尊重原文，只修格式和检查报出的问题。
- **改了自己的草稿某几页**（只在本来就用了草稿时）：重跑 `sf.py draft`，只重做对应的成品页，其他页不动。

## 工程目录

```
<deck>/
  slides.md            封面 + 按顺序 src 引入各节
  pages/NN-名字.md      每节一个文件
  layouts/ components/ styles/ setup/   模板自带，一般不改；风格在 styles/theme.css
  diagrams/            图的源文件（.d2 / .wavedrom.json / .drawio.svg）
  public/diagrams/     渲染出的 svg（sf.py diagrams 生成，别手改）
  drafts/draft.pptx    用户草稿（可选，没有就空着）；drafts/read/ 是读出来的结构和图片
  qa/                  截图和 report.json
  MAP.md               页面对照表与状态
```

## 环境要点

Windows 本机、透明加密环境下的读写规则见 `references/windows-env.md`。要点：草稿默认用 PowerPoint 读（能出每页渲染图），没有 PowerPoint 时自动改为直接读文件内容（经 `cmd /c type` 拿明文，没有渲染图）；`slidev build` 出的静态网站在本机以外打不开，要分享就导出 PDF。
