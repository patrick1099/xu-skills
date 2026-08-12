---
name: writing-readme
description: Use when writing or rewriting a README (or any outward-facing project doc) and it must not read as machine-generated — 用户说 readme 太难看 / AI 味很重 / 帮我写个 readme / 重写文档 / 让它像人写的。Diagnoses two layers with a deterministic bilingual linter (中文 + English): structure (证据先于说理、说理搬去 docs/、README 该多长) and prose tells (破折号从句、不是X是Y、buzzwords、em dash abuse). Runs `scripts/readme_lint.py` as a real gate with a non-zero exit code — never eyeball it. Also use before publishing a plugin/tool repo.
---

# Writing README

让 README 读起来像人写的。两层病，分开治：**结构层**决定读者留不留下，**文体层**决定
他信不信你。市面工具只做其中一层（详见文末「与市面工具的关系」）。

**铁律：闸是脚本，不是我的判断。** 改完必须跑 `readme_lint.py`，退出码 0 才算完。

## 一、先跑基线

```bash
py -3 skills/writing-readme/scripts/readme_lint.py check <README 路径>
```

**默认只跑中文包。** 英文文档要显式 `--lang en`，真双语的加 `--lang both`。跑错包会静默
报「干净」，所以文档语言和所跑的包对不上时，末尾会多打一行提示，看到就补跑。

退出码 `0` 通过 / `1` 有超阈值命中 / `2` 出错。

先看它报了什么，再决定重写还是微调：**结构层报错 → 得重排；只有文体层报错 → 逐条改句子。**

## 二、结构：倒金字塔

按读者流失率排，每节服务的人比上一节少。

| 位置 | 放什么 | 对应检查 |
|---|---|---|
| 第 1 句 | 这东西替读者解决什么。**不许**用「X 是一个 Y」开头 | `*-definition-opener` |
| 前 45 行 | 一屏能看见的证据：真实终端输出 / 截图 / gif | `struct-evidence-first` |
| 紧接着 | 装 + 跑，两个代码块之内能用上 | `struct-install-pos` |
| 再往后 | 凭什么用它：2–3 条差异化，每条给证据 | — |
| 最后 | 配置 / 结构 / 测试 / License | — |
| 全篇 | 每个模块留一个 `docs/` 出口 | `struct-no-exit` |

**证据必须是真跑出来的。** 编一段像模像样的终端输出是这件事上最容易犯、也最贵的错：
README 的全部说服力就在那一块。跑不出漂亮输出就换个能跑出来的仓库跑，或者如实展示
它平淡的样子。真输出含敏感信息时只做最小替换（路径、工程名），**并在下面注明哪些是
替换过的**，别把整块重写成想象中的样子。

**说理不许跑在使用前面。** 任何一段「为什么这样设计」超过 3 行 → 搬进 `docs/`，正文
留一句结论 + 链接。搬走的内容不是删掉，是换个地方；`struct-preamble` 和 `struct-length`
就是在数这件事。

## 三、文体：三道删除闸

跑 `rules` 看全部规则和阈值：

```bash
py -3 scripts/readme_lint.py rules --lang zh
```

改的时候盯住这三类（其余的脚本会报）：

1. **加粗当标点用** —— 每节最多一处，只用于术语首次出现。中文 LLM 写作最容易被认出的
   排版特征，实测能占到每 3 行一处。
2. **破折号从句 / em dash** —— 全篇 3 处封顶。
3. **对称否定句「不是 X，是 Y」/「not just X, but Y」** —— 全篇 1 处封顶，且只在真要
   纠正一个常见误解时用。

还有一条脚本查不了、只能自己看的：**表格在替谁干活。** 表格是给人查的（安装方式、
参数对照、错误码），不是用来讲道理的。用表格组织论证是模型压缩信息的习惯。

## 四、收尾

```bash
py -3 scripts/readme_lint.py check <README>     # 必须 exit 0
py -3 scripts/readme_lint.py diff <README>      # 只看这一版新引入的
```

`diff` 用于**已经很脏、这轮只改一部分**的文档：拿 git HEAD 当基线，只报新增的命中，
存量不淹没增量。想跟别的版本比用 `--rev <ref>`。

`--strict` 让 warn 也算不通过；`--skip <检查名>` 跳过某项结构检查（例如纯 API 参考文档
本来就不该有证据块，可 `--skip evidence-first`）。

## 加规则

规则包是 `rules/zh.json` / `rules/en.json`，加一条 = 加一个 JSON 对象：

```json
{ "id": "zh-xxx", "name": "显示名", "pattern": "正则", "max": 允许次数,
  "sev": "error|warn", "msg": "为什么这是问题", "fix": "怎么改",
  "scope": "line" }
```

- `max: 0` 表示出现即报；`max: 3` 表示第 4 次才报（用于本身合法、只是不能滥用的东西）。
- 默认**按自然段扫**，因为文档是硬折行的，跨行的命中按行扫会整条漏掉。只有 `^` 锚定的
  规则才写 `"scope": "line"`。
- 包级 `"flags": "i"` 让整个包大小写不敏感（英文包已开）。
- 加一门新语言 = 加一个 `rules/<lang>.json`，脚本不用改；但它不会自动被跑，要 `--lang <lang>`。
- 结构检查在脚本的 `STRUCTURE_CHECKS` 表里，加一条 = 加一个纯函数 + 一个表项。

改完跑 `py -3 scripts/readme_lint.py selftest`（只跑纯函数，不碰磁盘）。

## 与市面工具的关系

生成器（readme-generator / create-readme / readme.so）规定的是
`Title / Features / Installation / Usage / License` 那套万能骨架，**那正是产 AI 味的机器**，
不要用。

文体检查器做得比这里狠，但只有英文：[slopster](https://github.com/t0ddharris/slopster)
（Vale 规则 + Tagore skill + slop-diff）、[deslop](https://github.com/JMill/deslop)、
[vale-llm-slop](https://github.com/Syntaf/vale-llm-slop)。**只需要 lint 英文散文就直接用
slopster，别用这个 skill。**

本 skill 补的是它们都不覆盖的两块：**中文技术写作的指纹**（[slop-gate](https://github.com/hwajongpark/awesome-slop)
的中文包打的是公文腔，另一批指纹）和**文档结构层**（文体派全是 prose linter，只管句子）。
`diff` 的「只报新增」思路借自 slopster 的 `slop-diff`。
