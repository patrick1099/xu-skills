# xu-skills

通用(非项目专用)的 Claude Code skill 集,打包成一个插件。

## 包含的 skill

### vibe-flow
**轻量 vibe-coding 主流程**：先回答用户此刻的问题，只澄清会改变结果的歧义，再路由到个人脚本、带界面应用或公司项目分支；按生命周期决定是否留文档，按风险决定测试与真实使用验证。需求清楚后仍有重大技术取舍时，可把 `ai-room` 作为一次性的第二 AI 决策升级，而不是必经审查门。

### learning-skill
基于 Benjamin Bloom 的 2-Sigma 与掌握学习法的一对一个性化学习工作流:生成课程、判断掌握度、补充讲解、维护学习进度。

### learning-skill-plus
learning-skill 的加强版:在掌握学习之上加入**间隔重复、主动回忆、苏格拉底提问**,以及复习路由、错题/遗漏追踪、复习计划、"多久没学"查询。

### vibe-scripts
写**独立 Python 小工具/脚本**(自动化、数据处理、抓包分析、批量转换、串口调试等)的架构模板与分级规范。生成脚本前先加载它。

### vibe-apps
写**带界面 / 要发给别人 / 可能变网站的 Python 应用**的架构:五层(core/api/web/app.py/pywebview)+ FastAPI + pywebview + PyInstaller。与 vibe-scripts 的分界:命令行单文件脚本→vibe-scripts,有界面/要分发的应用→vibe-apps。搭脚手架前先加载它。

### curating-memory
**手动整理持久记忆库**:说「整理记忆 / 记忆负担太大」时触发。合并/删除/重分类/瘦身摘要/日期归一化/路径符号化/scope 打标,并把「该升级成 skill」「该进 CLAUDE.md」「该做成 hook」的条目挑出来提名。另外扫三个收编口:工具地盘收件箱里还没入库的记忆、Codex 自蒸馏记忆里值得提炼的偏好、本机有但没进共享库的 skill/plugin。先出计划表 → 你逐批批准 → 才动文件;删除永不先斩后奏。可按需或深度追溯记忆的来源会话(originSessionId → transcript)。

> 装了 hub 共享数据层(`~/.hub/config.toml` 指得到金库)时,整理对象是金库 `shared/memory/`——那是唯一活源,索引与视图都是派生物、由 `hub sync --refresh` 重算;没装 hub 时退回整理宿主注入的 memory 目录。附带的 SessionStart 提醒 hook 会跟着同一个判断走。

## 安装(Claude Code)

```
/plugin marketplace add patrick1099/xu-skills
/plugin install xu-skills@xu-skills
```

安装后这六个 skill 即按各自触发条件自动生效。
