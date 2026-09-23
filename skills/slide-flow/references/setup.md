# 安装依赖（一次性）

`sf.py doctor` 列出缺的东西，按下表装。都是免管理员的装法。

| 依赖 | 装法 | 用途 |
|---|---|---|
| Node.js ≥ 20 | 免安装 zip 解压并加进用户 PATH | Slidev、截图、WaveDrom |
| Slidev + 截图库 | `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i -g @slidev/cli @slidev/theme-default playwright-chromium` | 生成、预览、导出 |
| WaveDrom | `npm i -g wavedrom-cli` | 位域和波形图 |
| D2 | 从 https://github.com/terrastruct/d2/releases 下 `d2-vX-windows-amd64.tar.gz`，把 `bin/d2.exe` 放进 PATH（如 `%LOCALAPPDATA%\Programs\bin`） | 连线图、时序图 |
| Chrome 或 Edge | 本机已有即可；装在非常规位置时设 `SF_CHROME` 指向 exe | 截图、导出 PDF |
| PowerPoint | 可选，2007 及以上 | 读草稿时出每页图片、生成草稿模板；没有也能读草稿（没有图片） |

- 跳过 playwright 自带浏览器的下载，用本机 Chrome，省约 150 MB。
- Slidev、主题装在全局一份，每套幻灯片不用 `npm install`。
- 用户在自己的终端里打开幻灯片：`cd <deck>` 然后 `slidev`。
