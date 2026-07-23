# 收编扫描:三个进料口

整理金库之前先扫一遍**还没进金库的东西**。三个口各扫各的,结论一律进计划表,
**只提名、不自己动手收编**。

先从 `~/.hub/config.toml` 取 `vault` / `host` / `hub_root`,下文用 `$VAULT` `<host>` 代指。

---

## 口 1:Claude 收件箱 `~/.claude/projects/*/memory/`

harness 写新记忆就写这儿,而且**这个目录自带的 `MEMORY.md` 也会注入上下文**——
所以已入库的条目会让用户每会话吃两份几乎一样的索引。这是"记忆负担太大"最常见的真实来源。

**怎么扫**:比对收件箱与 `$VAULT/shared/memory/` 的文件名集合。

| 情况 | 裁决 |
|---|---|
| 两边都有,内容一致 | **删收件箱那份**(金库是活源,收件箱只是入口) |
| 两边都有,**内容分岔** | 停下来问:哪份是新的?通常 `shared/` 权威,但用户可能刚在收件箱里写了新事实 |
| 只在收件箱 | 判它值不值得入库:值 → **提升**(先 `collect` 再 `promote-memory --name`),不值 → 删 |
| 只在 `shared/` | 正常,不用管 |

**删收件箱副本前必须确认金库那份真的在**(读到文件,不是靠索引推断)。删错了就是删掉唯一副本。

多个项目 slug 各有一个收件箱,`~/.claude/projects/` 下逐个看,别只扫当前工程那个。

---

## 口 2:Codex 生成态 `~/.codex/memories/`

**铁律:这个目录永远不接进 `device.toml` 的采集源。** 它是 Codex 后台自动蒸馏的生成态,
格式不保证稳定,接进去会触发**自我复制回环**(hub 灌给它 → 它当"学到的事实"再蒸馏 → 又收回金库)。

它只是**素材**。取材方式:

1. 读 `memory_summary.md`(约 10KB,可以整份读)。
2. `MEMORY.md`(250KB+)和 `raw_memories.md`(600KB+)**绝不整份读** —— 只 grep
   `## User preferences` 段和自己关心的关键词,按段读。
3. 从中挑**跨会话稳定的偏好/事实**(不是某次任务的过程记录),按金库 frontmatter 规范
   重写成一条正常记忆,提名写进 `$VAULT/shared/memory/`。
   - 写进去的是**你重写的规范记忆**,不是原文搬运。
   - 出处在正文里注明"取自 Codex 自蒸馏记忆(YYYY-MM-DD)",避免以后当成一手事实。
4. 一次任务里的临时上下文、rollout 文件名、thread_id 之类**一律不入库**。

---

## 口 3:游离资产(skill / plugin 没进金库)

金库 `shared/` 是"每台机都该有"的稳态活源。只存在于本机某个目录、没进金库的能力,
换机就没了、别的工具也吃不到。

**三查**:

1. **skill**:`$CLAUDE_HOME/skills/*` 与 `$CODEX_HOME/skills/*`(以及 `~/.agents/skills/*`)
   里,哪些不在 `$VAULT/shared/skills/` 里?
   - 注意:已被 hub 注册的 skill 在工具地盘是**指向金库的链接**,不算游离。看它是不是真目录。
   - 提名动作:`hub promote --tool <claude|codex> --name <skill>`(由用户跑)。
2. **plugin**:平台装着/启用着的自有插件,是否都在 `$VAULT/shared/plugins/manifest.toml` 里?
   反过来,manifest 里有、但 `device.toml` 的 `[plugins.<tool>] enabled` 没列的,是**已注册未启用**
   ——这可能是有意的,别当缺陷报,列出来让用户确认。
3. **采集盲区**:`device.toml` 的 `[sources.*]` 有没有漏掉本机确实存在的源?
   漏了的东西 collect 根本看不见,连备份都没有。

**只提名。** 提升 skill、改 manifest、改 device.toml 都是用户点头后由用户跑的动作,
本 skill 不代跑,更不建新 skill/plugin。

---

## 输出形态

三个口的结论合并成**一张收编清单**,附在整理计划表前面:

```
| 口 | 对象 | 现状 | 提名动作 |
|----|------|------|----------|
| 1  | reference_img2md_script | 收件箱与金库各一份,内容一致 | 删收件箱副本 |
| 1  | project_xxx             | 只在收件箱                  | collect → promote-memory |
| 2  | "用户要先给字段偏移再讲协议" | Codex 自蒸馏里反复出现     | 重写成 feedback 记忆入库 |
| 3  | ai-room (skill)         | claude/codex 地盘有,金库没有 | hub promote --tool claude --name ai-room |
```
