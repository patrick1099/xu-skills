# xu-skills

通用(非项目专用)的 Claude Code skill 集,打包成一个插件。

```
/plugin marketplace add patrick1099/xu-skills
/plugin install xu-skills@xu-skills
```

装完各 skill 按自己的触发条件生效;`skill-review` 会额外起子 agent,只在显式调用时运行。

## 包含的 skill

### cli-ai-spec
**AI 友好 CLI 契约**:写/改命令行工具、让 CLI 能被 AI、脚本、CI 稳定解析调用时触发。机器契约:统一信封 `{ok,data,error,meta}`、退出码 0·1·2、eager `--ai-help`、`--json`/`--format json` 等价、dry-run 约定、跨脚本统一错误码总表(新码先入表再使用)。正文给了一份落地检查清单(贴给 AI 当约束),以及契约测试闸的用法(script-manager 的 `contract-test check <tool>`,有失败 rc1 且错误信封走 stderr)。

### learning-skill-plus
基于 Benjamin Bloom 的 2-Sigma 与掌握学习法的一对一个性化学习工作流,并加入**间隔重复、主动回忆、苏格拉底提问**,以及复习路由、错题/遗漏追踪、复习计划、"多久没学"查询。

### skill-review
基于真实运行证据的轻量 skill 复盘：只在明确调用时启动一个独立子 agent，回看当前对话、实际使用的 skill、工具错误、用户纠正和验证结果；把发现分别路由为脚本候选、`SKILL.md` 正文、description、reference/example、验证缺口、宿主/项目规则或“不应修改”。默认只生成逐项可审核的提案，不自动编辑、bump 版本或提交。

### curating-memory
手动整理持久记忆库:说「整理记忆 / 记忆负担太大」时触发。合并/删除/重分类/瘦身摘要/日期归一化/路径符号化/scope 打标,并把「该升级成 skill」「该进 CLAUDE.md」「该做成 hook」的条目挑出来提名。另外扫三个收编口:工具地盘收件箱里还没入库的记忆、Codex 自蒸馏记忆里值得提炼的偏好、本机有但没进共享库的 skill/plugin。先出计划表 → 你逐批批准 → 才动文件;删除永不先斩后奏。可按需或深度追溯记忆的来源会话(originSessionId → transcript)。

> 装了 hub 共享数据层(`~/.hub/config.toml` 指得到金库)时,整理对象是金库 `shared/memory/`——那是唯一活源,索引与视图都是派生物、由 `hub sync --refresh` 重算;没装 hub 时退回整理宿主注入的 memory 目录。附带的 SessionStart 提醒 hook 会跟着同一个判断走。

### writing-readme
**README 去 AI 味**:说「readme 太难看 / AI 味很重 / 让它像人写的」时触发。两层分开治:
结构层(证据先于说理、说理搬去 docs/、README 该多长)和文体层(破折号从句、「不是X，是Y」、
加粗当标点、em dash abuse)。闸是脚本不是判断——`scripts/readme_lint.py` 中英双语规则包,
超阈值非零退出,`diff` 子命令只报这一版新引入的命中。

```
py -3 skills/writing-readme/scripts/readme_lint.py check README.md
```

> 只想 lint 英文散文就用 [slopster](https://github.com/t0ddharris/slopster) / [deslop](https://github.com/JMill/deslop),它们做得更狠。
> 这个 skill 补的是它们不覆盖的两块:中文技术写作的指纹,以及文档结构层。

### slide-flow
让 AI 用 [Slidev](https://sli.dev) 做演示幻灯片:说「做个 PPT / 幻灯片 / 讲解课件」时触发。大纲你点头后 AI 直接出成品,哪页不满意在对话里说。想自己定某几页的结构,可以在 PowerPoint 里拖几个方框、箭头,红字写给 AI 的指令,备注栏写讲稿,把草稿丢给它(可选);AI 读出每个形状的位置、文字和连线(没接上框的线按端点就近认),照布局意图生成对应页;有 PowerPoint 时经 COM 读并导出每页图片,没有时直接解析文件。图按类型分工:摆放类用 HTML/CSS,连线多的用 D2 自动布局,位域波形用 WaveDrom,要亲手调的用 draw.io。

`scripts/sf.py` 一个命令行管全程(建工程、三套主题预览、生成草稿模板、读草稿、渲染图、版面规则检查、逐页截图查出界和裁切、导出 PDF),遵守 cli-ai-spec 契约。依赖 Node、全局 Slidev、D2、本机 Chrome,PowerPoint 可选,`sf.py doctor` 会逐项查。

```
py -3 skills/slide-flow/scripts/sf.py doctor
py -3 skills/slide-flow/scripts/sf.py init my-deck --title "标题"
```

## 已迁出

`vibe-flow` / `vibe-scripts` / `vibe-apps` 已于 2026-07-30 迁往独立插件 **[vibe-flow](https://github.com/patrick1099/vibe-flow)**,与原 `true-north` 四件套(clarify-needs / living-blueprint / cut-scope / scan-field)合并成一套有档位的完整 vibe-coding 工作流("小事要省,大事要好")。写脚本 / 建应用 / 明确需求 / 剪枝 / 扫同款请装那个插件。

