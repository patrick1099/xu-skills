---
name: cli-ai-spec
description: Use when writing or modifying a CLI script/tool that AI, scripts, or CI will call — 用户说写个命令行工具 / 让 CLI 能被 AI 稳定解析调用 / 加 --json 信封输出 / 统一退出码 0·1·2 / 实现 --ai-help / 把存量脚本改造成 AI 友好 CLI。也用于给已有 CLI 做规范合规检查（信封、退出码、--ai-help、--format json）。
---

# CLI-AI 规范

给命令行脚本定"AI 友好 CLI"的机器契约。目标：任何 CLI 都能被 AI、脚本、CI 稳定解析、可靠调用。
**AI 只看三样东西：`ok` 字段、`error.code`、退出码**——其余都是给人看的。

## When to Use

- 新写 CLI 工具 / 给工具加子命令：按本契约写，一次到位
- 存量脚本要被 AI 调用：按 AI 调用频率渐进迁移（改到哪个命令顺手升到哪个，不一次性推倒重来）
- 给已有 CLI 做合规检查：跑 contract-test 闸（见「验证」）
- 纯一次性内部脚本：至少保证 stdout 纯净、退出码 0/非 0 正确即可，不强求全契约

## 硬性契约

### 1. `--json` 入口（必须）

- 所有命令支持 `--json`，纯净 JSON 到 **stdout**；日志/进度/警告走 **stderr**，绝不混进 stdout
- JSON 模式下禁止交互（不弹确认、不读 TTY）
- `--json` 与 `--format json` **等价**，两者都要可用
- **不做**非 TTY 自动切 JSON——输出形态只由 `--json` 显式决定；TTY 检测只管颜色/进度
- 输出**固定 UTF-8**（GBK 控制台乱码是显示层，数据完好；脚本开头把 stdout/stderr `reconfigure(encoding="utf-8")`）
- **参数/用法错误也要出信封**：带 `--json` 时 argparse 错误必须输出 `E_VALIDATION` 信封到 stderr 并退出 2（继承 ArgumentParser 覆写 `error()`，用原始 argv 检测是否带 `--json`），不能抛纯文本

### 2. 统一轻信封（必须）

成功：

```json
{ "ok": true, "data": {}, "error": null, "meta": {} }
```

失败：

```json
{ "ok": false, "data": null,
  "error": { "code": "E_NOT_FOUND", "message": "给人看的", "details": {}, "retryable": false, "suggestion": "AI 下一步该跑什么" } }
```

- 顶层**永远只有** ok/data/error/meta 四个键；业务字段进 `data`，不要提到顶层
- 失败 `data: null`，信封走 **stderr**、stdout 保持字节级空
- `retryable` **默认一律 false**，只在明确瞬时错误（网络超时/限流）才置 true；磁盘满/写后校验失败/加密态异常原样重试无意义
- `meta` 有才填，不强制 duration/timestamp

### 3. 错误码总表（跨脚本统一，新码先入表再使用）

| 码 | 含义 |
|---|---|
| `E_VALIDATION` | 输入 / 用法 / 路径 / 配置不合法 |
| `E_NOT_FOUND` | 目标不存在 |
| `E_PERMISSION` | 权限不足 |
| `E_NETWORK` | 网络 / 连接失败 |
| `E_IO` | 读写 / 存储失败（非权限） |
| `E_PLATFORM` | 平台 / 环境不支持 |
| `E_EXTERNAL_TOOL` | 外部命令 / 子进程失败 |
| `E_PARTIAL_FAILURE` | 部分成功（批量任务） |
| `E_COMMENTS_FOUND` | 检查器查到违规项（条件未满足 = 失败） |
| `E_CONTRACT_VIOLATION` | 契约检查失败（测试闸） |
| `E_INTERRUPTED` | 用户/外部中断（可捕获的 Ctrl+C / 中断信号），状态已保全可安全重跑 |
| `E_VERIFICATION_FAILED` | 生成物验收失败（非参数错、非内部 bug），如生成后自检不通过 |
| `E_INTERNAL` | 未预期异常（兜底） |

- 错误码分类用 **isinstance 沿 `__cause__` 链**，禁类名映射（底层 `FileNotFoundError`→E_NOT_FOUND、`PermissionError`→E_PERMISSION，其余 IO 类→E_IO），类名重构不应悄悄退化成 E_INTERNAL
- 外部工具非零退出：统一信封 + 退出 1，原退出码 + stderr tail 进 `error.details`，工具缺失归 E_EXTERNAL_TOOL 非 E_INTERNAL

### 4. 退出码（必须）

| 退出码 | 含义 |
|---|---|
| 0 | 成功 |
| 1 | 运行失败（业务 / IO / 网络 / 权限，**含未预期异常 E_INTERNAL**） |
| 2 | 参数 / 用法错误（含 argparse 解析失败） |

不维护第二套细粒度退出码；`error.code` 是唯一细粒度语义源。

### 5. `--ai-help`（必须）

- 输出 AI 优化使用说明到 stdout，退出 0，**eager**：在完整 parse_args **之前**扫原始 argv，命中即输出返回（否则 `required=True` 子命令会先拦下裸 `--ai-help`）；尊重 `--` 终止语义（`--` 之后是操作数）
- 主 `--help` 加一行：`LLMs/agents: run '<tool> --ai-help' for usage guidance.`
- Markdown + 精简 front matter：`name / description / ai_help_version` 三键必填
- 正文：Quick Reference（放最前，2-3 条最常用命令）→ When to Use → Command Reference（标注必填 / 可选 / 默认）→ Side Effects & Safety（写文件 / 联网 / 破坏性逐命令写明）→ Exit Codes → Errors & Recovery（错 → 对对照）
- 非业务命令（self-test 等直接传播子进程输出、不走信封）必须在 --ai-help 显式标注，不许含糊称"全部合规"

### 6. dry-run（破坏性 / 变更类命令）

- `--dry-run --json` 预演计划变更不落盘；预演与真跑**共用同一条写入路径**（闸设在写函数里，绝不靠改配置假装预览）
- 信封里 data 统一带 `dry_run: true/false`，禁自创命名（如旧版 `applied`）

### 7. 自由文本参数的非命令行通道（必须）

任何接受**自由文本**的参数（prompt、消息正文、提交说明、查询语句、代码片段），除了 `--x VALUE` 这一种命令行形式，**必须另有一条不经过 shell 的通道**：`--x-file <路径>`，或约定 `--x -` 表示从 stdin 读。

- **为什么必须**：信封是输出侧合同，**管不到输入侧**。参数在 `exec` 之前就已被 shell 处理过一轮——文本里含反引号、`$`、引号、反斜杠时，程序拿到的可能是被替换或截断过的东西，而它**从自己的角度看参数完全合法**，照常返回 `ok:true` 的信封。**用输出格式检测不出输入已被污染**，这是结构性的，不是实现没做好。
- 两种实测形态：① prompt 含反引号，bash 在双引号内当命令替换**真执行**，整条调用根本没发出去（2026-08-14）；② Windows 上经 `cmd` / `.cmd` shim 传多行文本被截断。
- `--x-file` 按 UTF-8 读；文件不存在 → `E_NOT_FOUND`，不是普通文件或解码失败 → `E_VALIDATION`
- `--x` 与 `--x-file` **同时给 → `E_VALIDATION`**，不许猜哪个优先
- stdin 形式沿用已有那条：期望管道输入但 stdin 是 TTY 时不挂起，打印简略提示后退出
- **调用方那一侧的配套做法**（写进 `--ai-help` 的 Quick Reference）：用 `subprocess.run([...])` 传 list argv，绝不拼命令行字符串

## 落地检查清单（贴给 AI 当约束）

- [ ] 所有命令支持 --json，stdout 只有 JSON，日志全进 stderr
- [ ] JSON 模式无交互
- [ ] 信封 {ok,data,error,meta} 正确，失败 error 含 code/message/retryable
- [ ] 退出码 0/1/2 语义正确（未预期异常 = 1；参数错误 = 2）
- [ ] --json 时参数/用法错误也出 E_VALIDATION 信封
- [ ] --ai-help 存在、解析前 eager、尊重 --、含 Quick Reference/Side Effects/Exit Codes
- [ ] 输出固定 UTF-8
- [ ] 写操作有 --dry-run，预演与真跑同一写路径，data 带 dry_run
- [ ] 错误码来自总表，新码先入表再使用
- [ ] 外部工具非零退出码归一退出 1，原退出码进 error.details
- [ ] 期望管道输入但 stdin 是 TTY 时不挂起（打印简略提示后退出）
- [ ] 自由文本参数有 `--x-file` 或 stdin 通道；两者同给报 E_VALIDATION

## 验证：契约测试闸

script-manager 的 `contract-test check <tool>` 是现成契约测试闸：跑通用骨架检查（argparse 错误信封化、--ai-help 完整性、--format json 等价、`--` 终止语义、--help LLM 行）+ 每工具业务探针。改完 CLI 后跑一遍，全绿才算完：

```
contract-test check <tool>   # 全部通过 rc0；有失败 rc1，错误信封在 stderr
```

- 成功探针不断言 stderr（规范允许进度走 stderr）；失败探针要求 stdout 为空、stderr 是失败信封
- 新增工具要在 contract-test 的 TOOLS 注册表登记 entry + success/failure 探针

## 常见错误

- 进度 / 日志混进 stdout —— AI 解析不到 JSON 或解析出残片
- `retryable` 按类别批量默认 true —— 磁盘满 / 校验失败重试无意义，默认 false
- 用异常类名字符串映射错误码 —— 类名重构会静默退化成 E_INTERNAL，用 isinstance + `__cause__`
- `--ai-help` 做成子命令或放到 parse 之后 —— 裸 `--ai-help` 会被 required 子命令拦下
- 成功信封里把业务字段提到顶层 —— AI 只看 data 内
- 自创 dry-run 字段名 —— 统一 `dry_run`
- GBK 控制台直接 print 中文 —— 先 reconfigure 成 UTF-8
- 自由文本只给 `--x VALUE` 一种传法 —— 文本里的反引号 / `$` / 引号会在 exec 前被 shell 改写，程序收到污染值却照常返回 ok:true，信封查不出来

## 参考

契约形态来自对市面规范的调研取舍：dashdash（--ai-help + Markdown/front matter）、jira-cli（统一信封 + error.code + retryable + suggestion）、POSIX Agent Spec（语义退出码，收缩为 0/1/2）、Agent CLI SDK（JSONL 分流给 --jsonl）、Agentic CLI Design（非交互 / dry-run / 自省）。
