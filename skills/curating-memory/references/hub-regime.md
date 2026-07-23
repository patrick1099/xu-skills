# hub 体制速查(整理金库前必读)

金库的权威契约是**金库根的 `SCHEMA.md`**。本文件只摘"整理记忆时会撞到"的部分;
两者冲突时**以 SCHEMA.md 为准**,并把冲突报给用户。

## 1. 从哪儿知道金库在哪

`~/.hub/config.toml`:

```toml
vault    = "C:/Users/<你>/hub-vault"        # 金库根
host     = "<本机设备名>"                    # = socket.gethostname().lower()
hub_root = "C:/Users/<你>/ai-cli-migrate"   # hub CLI 所在的仓
```

**别硬编码这三个值**,每次现读。设备名认错的后果很实:本机自产的记忆会被当成
"别的设备来的"。

## 2. 谁是活源,谁是派生物

| 位置 | 身份 | 能不能手改 |
|---|---|---|
| `$VAULT/shared/memory/*.md` | **唯一活源**(权威) | ✅ 整理就是改这里 |
| `$VAULT/MEMORY.md` | 派生物,`hub sync`/`collect` 整份重算 | ❌ 手改必被覆盖 |
| `~/.hub/views/<tool>/MEMORY.md` | 派生物,`register`/`refresh` 整份重渲染 | ❌ 同上 |
| `$VAULT/<host>/<tool>/memory/*.md` | 备份区,是工具地盘的**镜像** | ❌ 改了下次 collect 覆盖 |
| `~/.claude/projects/<slug>/memory/*.md` | **收件箱**(harness 写新记忆的地方) | ✅ 但只做"入库后删副本" |
| `~/.codex/memories/` | Codex 自蒸馏的**生成态** | ❌ 只读取材,永不采集 |

**摘要句(索引里显示的那句)住在各条记忆的 `description` 字段。** 想让索引更好读,
改 description,不是改索引文件。

同名同时出现在 `shared/` 与备份区是**正常的**(SCHEMA §6);冲突时 **`shared/` 是权威**。
在工具里删一条记忆**不等于**从 `shared/` 撤回——撤回只能手动删 `shared/memory/<name>.md`。

## 3. 命令(都在 `hub_root` 里跑)

```bash
cd <hub_root>
py -3 -m hub.cli collect        --vault <金库> --host <名> [--dry-run] [--yes]
py -3 -m hub.cli promote-memory --vault <金库> --host <名> --name <记忆名> [--dry-run]
py -3 -m hub.cli sync           --vault <金库> --host <名> [--refresh]
py -3 -m hub.cli status         --vault <金库> --host <名> [--check]
```

- `collect` = 工具地盘 → 备份区(**镜像**语义:源里没了的,备份区里也删)。
- `promote-memory` = 备份区 → `shared/`(**复制**,同名冲突就停,绝不静默覆盖)。
  所以收件箱里的新记忆要入库,次序是 **先 collect 再 promote-memory**。
- `sync` = 重算 `$VAULT/MEMORY.md` + 跑全部 lint;`--refresh` 顺带重渲染各工具视图。
- 整理收尾**必须**跑 `sync --refresh`,否则索引和视图还是旧的。

## 4. 三道会让 sync 失败的 lint

1. **正文里不许出现裸绝对路径。** 换台机就是死链。一律写符号根,由加载器展开:

       $VAULT/shared/memory/x.md      $CLAUDE_HOME/skills/foo      $CODEX_HOME/AGENTS.md

   符号表 = `device.toml` 的 `[paths]`。表里没有的符号原样留着,别瞎猜。
   逃生舱:`$VAULT/lint-exempt.txt`,一行一个记忆 `name`,只放行"裸路径"这一项。
   **删记忆/改名时顺手清掉这个名单里的死行。**

2. **scope 非法即停**(见下)。

3. **`sensitive: true` 的记忆不入库**(加密层没做完之前)。密钥类内容根本别写进记忆正文。

## 5. scope(v2 语法)——别指望它瘦本机上下文

```
global | class:<名> | project:<名> | tool:<claude|codex|opencode>
```

- `global` / `class:` / `project:` 同属**设备订阅维度**(维度内 OR);`tool:` 是独立维度
  (维度内 OR);两维之间 AND;**某维度没写标签 = 该维度匹配全部**。
- `global` **必须独占**。`[tool:claude]` 本身就是"所有设备、仅 Claude",
  **不许**写成 `[global, tool:claude]`。
- `class:<名>` 对 `device.toml` 的 `class` 数组,`project:<名>` 对 `projects` 数组。

**最容易搞错的一点**:`project:xinao` 是**设备订阅条件**(本机 `projects` 含 xinao 才纳入),
**不是**"只有 xinao 工程的会话才看得见"——视图是**用户级全局视图**。所以在一台
`class=["work"] / projects=["xinao"]` 的机器上,给记忆打 `project:xinao` 或 `class:work`
**本机一条上下文都省不下**,只是为将来别的设备做准备。

→ **真正能立刻瘦某个工具视图的只有 `tool:` 维度**(例:纯 Claude 的 harness 细节打
`[tool:claude]`,codex/opencode 的视图就不再渲染它)。裁决时别拿 class/project 当瘦身手段卖。

## 6. frontmatter 是 YAML 的受控子集

```markdown
---
name: my-note
description: 一句话摘要——索引里显示的就是它
metadata:
  type: user | feedback | project | reference
  scope: [global]
  portable: true
  sensitive: false
  originSessionId: <uuid>     # 提取器看不懂但原样保留,追溯靠它
---
```

- 能用:纯标量、小写不加引号的布尔、行内列表、块状列表、`metadata:` 这一层嵌套。
- **不准用**:锚点/别名、多行标量(`|` `>`)、两层以上嵌套、**行内注释**。
- 行内注释这条最锋利:`description: 摘要  # 备注` **不报错**,`# 备注` 会静默变成摘要的一部分。
- `portable` / `sensitive` 必须是真布尔,写成 `"false"` 会抛错。
- 文件名必须是 `<name>.md`,与 frontmatter 的 `name` 一致。改名 = 改文件名 + 改字段 + 改所有
  `[[反向链接]]`。

## 7. 手工往金库里放东西,只能放这些地方

- `$VAULT/<host>/<tool>/skills/` 被 collect **整个 rmtree 重建**——塞进去的手写内容下次
  collect 一定没,**且不报错**。
- 能放的:`$VAULT/<host>/` 根下(从不 rmtree),或 `shared/` 对应类型区。

## 8. 已知坑

- 本机 `sys.stdout.encoding` 是 gbk;hub CLI 的输出经管道可能显示异常,**别**据此判定命令失败,
  看退出码。
- 写回时沿用目标文件原有换行风格(CRLF 文件别一律按 LF 写回)。
- 金库是 git 仓,提交前**实读 `git config user.email`** 确认走的是个人身份(金库是个人资产,
  别用公司身份提交)。
