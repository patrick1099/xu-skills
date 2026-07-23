---
name: curating-memory
description: Use when the user asks to 整理/清理/精简记忆, says 记忆负担太大 or 上下文太占, wants to consolidate the hub 金库 shared/memory store, or wants to sweep 还没收编进金库的东西(工具地盘的新记忆、Codex 自蒸馏记忆、游离的 skill/plugin)。铁律:先出计划 → 逐批批准 → 才动文件,绝不自动整理。
---

# Curating Memory

整理**金库**——`$VAULT/shared/memory/` 是记忆的唯一活源。做 合并/删除/重分类/瘦身/
日期归一化/路径符号化/scope 打标,并**判断每条记忆的最佳归宿**(留 memory / CLAUDE.md /
skill / plugin / hook),该"晋升"的**挑出来提名**;顺带扫一遍**还没进金库的东西**。手动触发。

**核心心法**:记忆库是被追溯过的资产。**先出方案 → 用户逐批批准 → 才动文件**。
删除和改动永远不先斩后奏。

## 先认清活源(动手前 30 秒)

| | 是什么 | 手改? |
|---|---|---|
| `$VAULT/shared/memory/*.md` | **唯一活源** | ✅ 整理就是改这里 |
| `$VAULT/MEMORY.md`、`~/.hub/views/<tool>/MEMORY.md` | **派生物**,sync/refresh 整份重算 | ❌ 手改必被覆盖 |
| `$VAULT/<host>/<tool>/memory/` | 备份区,工具地盘的镜像 | ❌ 下次 collect 覆盖 |
| `~/.claude/projects/<slug>/memory/` | **收件箱**(harness 写新记忆的地方) | ✅ 仅"入库后删副本" |
| `~/.codex/memories/` | Codex 自蒸馏的生成态 | ❌ 只取材,永不采集 |

**索引里的摘要句 = 各条记忆的 `description` 字段。想让索引更好读,改 description,
不是改索引文件。**

`$VAULT` / `<host>` / `hub_root` 每次从 `~/.hub/config.toml` 现读,**别硬编码**。
体制细节(命令、lint、scope 语法、frontmatter 子集)见 `references/hub-regime.md`。

## 边界(先划清,别越权)

- ✅ 做:在金库内 合并/删除/重分类(改 type)/瘦身 description/日期归一化/路径符号化/scope 打标。
- ✅ 做:**归宿路由 + 提名**——判断每条记忆的最佳归宿,该晋升的列成候选清单交出去。
- ✅ 做:**收编扫描**——把还没进金库的记忆/skill/plugin 扫出来**提名**。
- ❌ 不做:**自己动手建 skill / plugin / hook**(那是各自要 brainstorm + 测试纪律的另一件事,只提名)。
- ❌ 不做:代跑 `promote` / 改 `device.toml` / 改 `manifest.toml`——提名给用户跑。
- ❌ 不做:未经批准就删/改任何文件。
- ❌ 不做:自动整理——本 skill 永远手动触发、逐批批准。

## 五步流程

1. **定位**:读 `~/.hub/config.toml` 拿 vault/host/hub_root;确认金库在、`vault.toml` 版本对得上。
   **没装 hub**(读不到金库)→ 退回整理宿主注入的 memory 目录(`~/.claude/projects/<slug>/memory/`),
   此时那个目录既是活源也是索引所在,直接改它的 `MEMORY.md`;下面凡是金库/派生物/收编相关的约束一律跳过。
2. **收编扫描**:三个进料口(Claude 收件箱 / Codex 生成态 / 游离 skill·plugin),
   照 `references/intake-sweep.md` 走,产出一张**收编清单**。
3. **廉价扫**:读 `$VAULT/MEMORY.md` + 每条记忆的 frontmatter(name/description/type/scope)。
   先不深读正文。
4. **追溯**(两模式,开场跟用户确认用哪种):
   - **lazy(默认)**:只有可疑条目才回源核对。可疑 = 看着过期/自相矛盾/疑重复/表述不清/裁决拿不准。
   - **deep**(用户说"深挖/额度够/全追"):每条都回源核对再裁决。
   - 来源 = frontmatter 的 `originSessionId`,transcript 在 `~/.claude/projects/*/<id>.jsonl`,
     **跨所有 project 子目录 glob 找**。金库里可能有别的设备写的记忆,**本机没有它的 jsonl**——
     照实标"无法回源",别猜。
5. **出计划表 → 逐批批准 → 执行**:见下。

## 裁决判据

先判**归宿**(这条记忆的最佳去处),再判**动作**:

| 归宿/裁决 | 命中信号 |
|---|---|
| **留 memory** | 跨项目偏好(feedback)/用户事实(user)/在进行的项目状态(project)/外部资源指针(reference),且无更强归宿。 |
| **→ CLAUDE.md** | **项目专属或全局的静态约定/规则**,AI 每次读上下文即可遵守。项目专属→该仓库 CLAUDE.md;跨项目通用→全局 `~/.claude/CLAUDE.md`。若已被现有 CLAUDE.md 完整覆盖 → 直接**删**,否则**提名**补进去。 |
| **→ skill** | 可复用的**操作流程/技法**("怎么做",会反复照做的步骤/checklist)。**提名**(建 skill 另走 writing-skills)。 |
| **→ plugin** | 比单个 skill 更大的能力集合,或需分发/多件打包(多 skill+hook+命令)。**提名**并指出并入哪个现有插件或新建。 |
| **→ hook** | **自动行为**("从今往后每次 X 就/之前/之后 Y"),靠"记住"办不到、必须 harness 执行。**提名**(SessionStart/PreToolUse 等)。信号:正文像"每次/每当/以后都/自动"。 |
| **删** | 一次性/仅本轮会话、已被取代、已证伪、或已被代码/CLAUDE.md/git 完整覆盖。**证伪或取代类必须回源核对**。 |
| **并** | 近重复,或同一主题系列(如 phaseN 进度条目)。合成一条,留最新真相 + 必要沿革。 |
| **重分类** | 事实没错但 type 标错。改 frontmatter 的 `type`。 |
| **归一** | 正文含相对日期(上周/3天前/昨天/最近/前几天/下个月…)。用该条 `originSessionId` 会话日期(或文件 mtime)作锚换算成绝对 `YYYY-MM-DD`。**锚不可靠就不猜,列进计划表让用户确认**。 |
| **压摘要** | `description` 长到在索引里读不动。**改 description 字段**,不是改索引文件。够辨识即可,不一刀切砍短。 |
| **符号化** | 正文里有裸绝对路径 → 换成 `$VAULT` / `$CLAUDE_HOME` / `$CODEX_HOME`(符号表 = `device.toml` 的 `[paths]`)。留着 `hub sync` 会直接拒。纯信息性、无符号可映射的 → 登记 `$VAULT/lint-exempt.txt`。 |
| **打 scope 标** | 默认 `[global]` 名不副实时。**只有 `tool:` 维度能立刻瘦某个工具的视图**;`class:`/`project:` 是**设备订阅条件**,在本机一条上下文都省不下(细节见 references/hub-regime.md §5)。`global` 必须独占。**收窄 = 让别的工具从此看不见它,按收窄处理、进批准表。** |
| **→ 提升 shared** | 收件箱里值得入库的记忆。次序:先 `hub collect` 再 `hub promote-memory --name`。 |
| **收编提名** | 游离的 skill/plugin(本机有、金库没有)。**只提名**,不代跑。 |

判据冲突时:**先问、别猜**(见 [[feedback_no_silent_behavior_change]])。
一条记忆可同时命中多档:先做 归一/符号化/压摘要 这类**内容修**,再定**归宿**。

## 计划表 → 批准 → 执行

先只输出**收编清单 + 整理计划表**,**不动文件**:

```
| 文件 | 现type/scope | 裁决 | 理由 | 来源核对 |
|------|--------------|------|------|----------|
| project_indent_tabs.md | project/global | 删 | 已被用户改口取代(4空格) | jsonl 已确认 |
| project_sim_phase1/2.md | project/global | 并 | 同一模拟器进度系列 | — |
| reference_vscode_cli.md | reference/global | 打 scope 标 [tool:claude] | 纯 Claude harness 细节,codex 视图不该有 | — |
| reference_dev_toolchain.md | reference/global | 符号化 | 正文含 C:\Users\... 裸路径,sync 会拒 | — |
| feedback_always_vsix.md | feedback/global | → hook | "每次发版就打 vsix"是自动行为,记忆保证不了 | — |
```

按裁决分组呈现。**删除组必须逐条亮出正文 + 理由,等用户明确点头**才删。用户批准后:

1. 执行 合并/删除/改 type/改 description/日期归一化/路径符号化/scope 打标。
2. **收尾链路**(缺一步整理就没生效):
   - `hub sync --refresh` —— 重算 `$VAULT/MEMORY.md`、重渲染各工具视图、跑全部 lint。
     **lint 报错就停下来修**(裸路径 / scope 非法 / sensitive),别绕过。
   - 删记忆或改名时,顺手清 `$VAULT/lint-exempt.txt` 里的死行,以及别处记忆里指向它的
     `[[反向链接]]`。
   - 金库 git 提交前**先实读 `git config user.email`**:金库是个人资产,别用公司身份提交
     (见 [[feedback_commit_identity_judgment]])。
3. 输出**归宿提名清单**(skill / plugin / hook / CLAUDE.md / 收编 候选),含建议归属与一句话理由,
   交给用户或后续流程——本 skill 到此为止,不建 skill/plugin/hook、不自动改 CLAUDE.md、不代跑 promote。
4. **写时间戳**:在 `$VAULT/shared/memory/` 写 `.curated` 文件,内容为首行今日 `YYYY-MM-DD`
   (供久未整理提醒 hook 读取)。

## 反模式

- ❌ 未批准就删/改文件。
- ❌ **手改 `$VAULT/MEMORY.md` 或 `~/.hub/views/*/MEMORY.md`** —— 派生物,下次 sync 整份覆盖。
  改摘要要改各条记忆的 `description`。
- ❌ 改完不跑 `hub sync --refresh` —— 索引与视图仍是旧的,等于没整理。
- ❌ 只整理收件箱,不碰金库 —— 收件箱只是入口,别的工具/别的机器吃的是金库。
- ❌ 删了收件箱副本却没确认金库里真有那份(删掉唯一副本)。
- ❌ 把 `~/.codex/memories/` 当可采集的源接进 `device.toml` —— 自我复制回环。它只是素材。
- ❌ 整份读 Codex 的 `MEMORY.md`/`raw_memories.md`(合计 800KB+)—— 只读 summary 和按段 grep。
- ❌ 往正文写裸绝对路径 —— `hub sync` 会拒绝,整批整理卡死。
- ❌ 拿 `class:`/`project:` 当本机瘦身手段卖 —— 它们是设备订阅条件,不改本机视图。
- ❌ 把"证伪/取代"当显然,不回源就删 —— 这类最容易删错真相。
- ❌ 顺手把提名的 skill 直接建出来(绕过 writing-skills 测试纪律),或代用户跑 promote。
- ❌ 把"每次 X 就 Y"型自动行为记忆当普通 feedback 留着 —— 它保证不了执行,应路由→hook。
- ❌ 留着相对日期不归一化(未来无法定位到底哪天)。
