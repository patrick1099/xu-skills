# Windows 与透明加密环境

2026-09-23 在一台装了文件透明加密软件的 Win10 上实测。其他机器没有加密时，本节可以忽略。

## 哪些扩展名会被加密

python 写同样内容的文件，再用 PowerShell 读头字节（`e0 a8 91 e7` 开头就是密文）：

- **加密**：`.css` `.js` `.txt`（以及 `.c` `.py` 等源码）
- **明文**：`.md` `.d2` `.svg` `.drawio` `.vue` `.ts` `.json` `.yaml` `.html` `.png` `.pdf`
- **PowerPoint 保存的 `.pptx` 用 python `open()` 直接读是密文**（`zipfile` 报 BadZipFile）。要拿明文字节就用 `subprocess.run(["cmd.exe", "/d", "/c", "type", 路径])`，stdout 是明文 zip；路径必须用反斜杠，正斜杠会返回 0 字节且不报错。`sf.py draft` 默认先走 PowerPoint COM（能出每页渲染图），不可用时自动改走 cmd type + 解析 XML；`draft-template` 只能走 PowerPoint。

## 影响

- Slidev 本地服务由 node 读文件，node 在白名单里，`.css` 被加密也没关系。
- D2（不在白名单）只读 `.d2`，而 `.d2` 是明文，所以没问题。
- **`slidev build` 打包出的静态网站全是 `.js`/`.css`，在本机以外打不开**。给别人看就 `sf.py export` 出 PDF。
- 截图和 PDF 都是明文。

## 常见坑

- Git Bash 的 heredoc 会吞掉反斜杠。给文件打补丁时用编辑工具或单独的 `.py` 脚本，别把含 `\n`、`\1` 的 python 代码塞进 heredoc。
- PowerShell 5 从标准输入读脚本不会执行；`sf.py` 用 `-EncodedCommand` 传脚本。
- PowerPoint 无窗口打开时，写备注栏不生效（读正常）。
- PowerShell 输出的错误是 CLIXML，`sf.py` 已剥掉。
- `npm root -g` 下的全局包 require 不到时，设 `NODE_PATH` 为 `npm root -g` 的结果（`sf.py qa` 已处理）。
