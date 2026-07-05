# xu-skills

通用(非项目专用)的 Claude Code skill 集,打包成一个插件。

## 包含的 skill

### learning-skill
基于 Benjamin Bloom 的 2-Sigma 与掌握学习法的一对一个性化学习工作流:生成课程、判断掌握度、补充讲解、维护学习进度。

### learning-skill-plus
learning-skill 的加强版:在掌握学习之上加入**间隔重复、主动回忆、苏格拉底提问**,以及复习路由、错题/遗漏追踪、复习计划、"多久没学"查询。

### vibe-scripts
写**独立 Python 小工具/脚本**(自动化、数据处理、抓包分析、批量转换、串口调试等)的架构模板与分级规范。生成脚本前先加载它。

### vibe-apps
写**带界面 / 要发给别人 / 可能变网站的 Python 应用**的架构:五层(core/api/web/app.py/pywebview)+ FastAPI + pywebview + PyInstaller。与 vibe-scripts 的分界:命令行单文件脚本→vibe-scripts,有界面/要分发的应用→vibe-apps。搭脚手架前先加载它。

### living-blueprint
**工具活蓝图**(与技术栈无关):在项目里维护一份 `BLUEPRINT.md`——永远当前、只讲功能不讲实现的全貌,让 AI 照功能行为重构而不被旧实现绑架,新会话读一份就懂整个工具。被 vibe-apps(必用)和 vibe-scripts(建议)引用,也可单独用于任何会长期迭代的项目。

### curating-memory
**手动整理 Claude Code 的持久记忆库**:说「整理记忆 / 记忆负担太大」时触发。合并/删除/重分类/瘦身索引,并把「该升级成 skill」「该进 CLAUDE.md」的条目挑出来提名。先出计划表 → 你逐批批准 → 才动文件;删除永不先斩后奏。可按需或深度追溯记忆的来源会话(originSessionId → transcript)。

## 安装(Claude Code)

```
/plugin marketplace add patrick1099/xu-skills
/plugin install xu-skills@xu-skills
```

安装后这六个 skill 即按各自触发条件自动生效。
