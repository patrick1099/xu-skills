# 安装与平台适配

xu-skills 的文本规则可直接加载；记忆整理提醒和 slide-flow 需要额外接入。首次安装、换宿主或相关能力缺失时，只配置本次需要的部分。

## 记忆整理提醒

现有 [hooks/hooks.json](hooks/hooks.json) 注册 Claude Code 的 SessionStart，调用 [curation_reminder.py](scripts/curation_reminder.py)。清单使用 Bash 和 `py -3`，其他 shell 或系统要先验证解释器与命令写法。当前包没有独立 Codex hooks 清单；本机由其他配置接入的提醒应先核对来源，避免重复注册。

提醒应在会话开始时检查整理日期，仅在满足现有条件时向 AI 提供短提示。它不整理记忆、不扫描全部历史、不阻断用户任务。脚本输出采用 `hookSpecificOutput.additionalContext` 结构；新宿主要按实际支持的上下文注入格式适配，不能假设打印 JSON 就会自动注入。

记忆位置优先从用户主目录下的 `.hub/config.toml` 读取 vault，再按脚本规则查找；未接入 hub 时遵循脚本已有回退。不要把本机金库位置写入共享清单。安装不改变整理日期，也不触发实际整理。

用户要求新宿主接入时，在源仓复用日期判断、增加必要的输入输出适配，查该宿主当前官方事件契约。宿主不能注入开始提示时，明确自动提醒未支持，手动整理技能仍可使用。

## slide-flow

直接复用 [已有安装说明](skills/slide-flow/references/setup.md)。用选定 Python 执行 `skills/slide-flow/scripts/sf.py doctor`，根据结果按需配置 Node、Slidev、D2、WaveDrom 和浏览器。PowerPoint 是可选项；没有它时不要承诺草稿图片导出能力。

该说明中的 Windows 安装方法只适用于对应系统。其他系统按工具官方发布物安装并重新运行 doctor；环境变量写法按当前 shell 转换，浏览器位置沿用 `SF_CHROME` 入口。项目本身不需要 AI 宿主 hooks 才能生成幻灯片。

## 其他技能

[writing-readme](skills/writing-readme/SKILL.md) 的检查脚本和 [cli-ai-spec](skills/cli-ai-spec/SKILL.md) 的工具入口按各自文档运行，先检测 Python。contract-test 若来自外部脚本库，单独定位该工具；不要把它当插件安装后必然存在的命令。纯文本技能不额外安装运行环境。

## 验收与升级

提醒先运行 `scripts/curation_reminder.py selftest`，用其临时记忆目录检查“无需提醒”和“需要提醒”的脚本结果，再从目标宿主新建会话验证提示确实可见且只出现一次。自检不改正式整理日期。slide-flow 用小样例实际预览、截图或导出验证本次需要的链路，doctor 通过只代表依赖检测通过。

升级后核对加载版本和 hooks 的实际来源。卸载只移除本插件的注册，不删除记忆、学习记录或幻灯片工程。
