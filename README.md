# xu-skills

通用(非项目专用)的 Claude Code skill 集,打包成一个插件。

## 包含的 skill

### learning-skill
基于 Benjamin Bloom 的 2-Sigma 与掌握学习法的一对一个性化学习工作流:生成课程、判断掌握度、补充讲解、维护学习进度。

### learning-skill-plus
learning-skill 的加强版:在掌握学习之上加入**间隔重复、主动回忆、苏格拉底提问**,以及复习路由、错题/遗漏追踪、复习计划、"多久没学"查询。

### skill-review
**基于真实运行证据的轻量 skill 复盘**：只在明确调用时启动一个独立子 agent，回看当前对话、实际使用的 skill、工具错误、用户纠正和验证结果；把发现分别路由为脚本候选、`SKILL.md` 正文、description、reference/example、验证缺口、宿主/项目规则或“不应修改”。默认只生成逐项可审核的提案，不自动编辑、bump 版本或提交。

### curating-memory
**手动整理持久记忆库**:说「整理记忆 / 记忆负担太大」时触发。合并/删除/重分类/瘦身摘要/日期归一化/路径符号化/scope 打标,并把「该升级成 skill」「该进 CLAUDE.md」「该做成 hook」的条目挑出来提名。另外扫三个收编口:工具地盘收件箱里还没入库的记忆、Codex 自蒸馏记忆里值得提炼的偏好、本机有但没进共享库的 skill/plugin。先出计划表 → 你逐批批准 → 才动文件;删除永不先斩后奏。可按需或深度追溯记忆的来源会话(originSessionId → transcript)。

> 装了 hub 共享数据层(`~/.hub/config.toml` 指得到金库)时,整理对象是金库 `shared/memory/`——那是唯一活源,索引与视图都是派生物、由 `hub sync --refresh` 重算;没装 hub 时退回整理宿主注入的 memory 目录。附带的 SessionStart 提醒 hook 会跟着同一个判断走。

## 已迁出

`vibe-flow` / `vibe-scripts` / `vibe-apps` 已于 2026-07-30 迁往独立插件 **[vibe-flow](https://github.com/patrick1099/vibe-flow)**,与原 `true-north` 四件套(clarify-needs / living-blueprint / cut-scope / scan-field)合并成一套有档位的完整 vibe-coding 工作流("小事要省,大事要好")。写脚本 / 建应用 / 明确需求 / 剪枝 / 扫同款请装那个插件。

## 安装(Claude Code)

```
/plugin marketplace add patrick1099/xu-skills
/plugin install xu-skills@xu-skills
```

安装后这四个 skill 即按各自触发条件生效；`skill-review` 因为会额外启动子 agent，仅在显式调用时运行。
