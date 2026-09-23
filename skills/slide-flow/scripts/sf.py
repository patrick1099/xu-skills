#!/usr/bin/env python3
"""slide-flow：AI 做 Slidev 幻灯片的配套命令行。

子命令：doctor / themes / init / preview-themes / draft / diagrams / lint / qa / export
所有子命令支持 --json（等价 --format json），信封 {ok,data,error,meta}；退出码 0 成功 / 1 运行失败 / 2 用法错误。
只用标准库。
"""
import argparse
import base64
import colorsys
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_DIR / "templates"
DECK_TEMPLATE = TEMPLATES / "deck"
THEMES_DIR = TEMPLATES / "themes"
QA_JS = Path(__file__).resolve().parent / "qa.cjs"
USER_CONFIG = Path.home() / ".slide-flow.json"
TEXT_SUFFIXES = {".md", ".vue", ".ts", ".css", ".d2", ".json", ".cjs"}
D2_PREAMBLE = ["**.style.font-size: 20", "(** -> **)[*].style.font-size: 16", "(** <-> **)[*].style.font-size: 16", "(** -- **)[*].style.font-size: 16"]

AI_HELP = """---
name: sf
description: slide-flow 幻灯片工具链：建 Slidev 工程、读 PowerPoint 草稿、渲染 D2/WaveDrom 图、版面规则检查、截图出界检查、导出 PDF
ai_help_version: 1
---

## Quick Reference

- 查环境：`py -3 sf.py doctor --json`
- 读草稿：`py -3 sf.py draft <deck>/drafts/draft.pptx --out <deck>/drafts/read --json`
- 生成后检查：`py -3 sf.py diagrams <deck> --json` → `py -3 sf.py lint <deck> --json` → `py -3 sf.py qa <deck> --json`

调用时用 list argv（`subprocess.run([...])`），不要拼命令行字符串。

## When to Use

- 起一套新幻灯片：`init`；第一次还没定主题：先 `preview-themes` 让用户挑
- 用户给了 PowerPoint 草稿：`draft`，读结构 JSON 和每页图片
- 写完或改完页面：`diagrams` → `lint` → `qa`，看截图、修问题
- 交付：`export` 出 PDF

## Command Reference

- `doctor`：检查 node、Slidev、playwright-chromium、Chrome、D2、WaveDrom、PowerPoint。无参数。
  PowerPoint 是可选项：缺了只进 data.optional_missing，不影响 all_ok。
- `themes [--set-default NAME]`：列出主题；`--set-default` 写用户默认主题到 ~/.slide-flow.json。
- `init DECK [--theme NAME] [--title TEXT | --title-file PATH] [--force] [--dry-run]`：从模板建工程。
  DECK 已存在且非空时需 `--force`（只覆盖模板文件，不删别的）。主题缺省取用户默认，再缺省 instrument。
- `preview-themes OUTDIR [--themes a,b]`：每个主题各建一份示例工程并截图，data.previews 给出每个主题的图片路径。
- `draft-template PPTX [--force] [--dry-run]`：用 PowerPoint 生成一份空白草稿，第一页是画法示范。
- `draft PPTX [--out DIR] [--no-render] [--via auto|powerpoint|xml]`：读草稿（形状位置/文字/颜色/连线/备注），
  写 DIR/draft.json，默认同时导出每页 PNG。DIR 缺省为 PPTX 同目录下的 read/。
  `--via auto`（默认）先用 PowerPoint 读，PowerPoint 不可用或失败时自动改为直接读文件；`xml` 只直接读文件，不开 PowerPoint；
  `powerpoint` 只用 PowerPoint，失败就报错。data.reader 说明实际走了哪条；走 xml 时没有 PNG（png 为 null），
  data.reader_note 写明限制，data.fallback_reason 写明 PowerPoint 为什么没用上。
- `diagrams DECK [--only NAME]`：渲染 diagrams/*.d2（D2）、*.wavedrom.json（WaveDrom）、复制 *.drawio.svg，
  输出到 public/diagrams/。以下划线开头的 .d2 是被引入的公共片段，不单独渲染。
- `lint DECK [--strict]`：按版面规则检查每页（字数、要点数、代码行数、是否有视觉元素、标题是否写结论）。
  默认只报告；`--strict` 时有问题返回 E_VERIFICATION_FAILED。
- `qa DECK [--slides 1,3-5] [--no-shots] [--port N] [--strict]`：起本地服务、逐页截图到 qa/，查文字出界、块出界、
  内容被裁切、图片加载失败。默认只报告；`--strict` 有问题返回 E_VERIFICATION_FAILED。
- `export DECK [--out FILE.pdf]`：用 Slidev 导出 PDF（本机 Chrome）。

## Side Effects & Safety

- init：在 DECK 写模板文件（支持 --dry-run 预演，data.dry_run 标明）。
- preview-themes：在 OUTDIR 下建示例工程并写截图。
- draft：启动 PowerPoint（无窗口、只读打开草稿）；写 draft.json 和 PNG，并删掉 DIR 里旧的 draft-*.png。用户本来开着的 PowerPoint 不会被关掉。
  走 xml 时只读文件（经 `cmd /c type` 拿明文），不启动任何程序。
- draft-template：启动 PowerPoint（无窗口）写一份新 .pptx；已存在时需 --force。
- diagrams：写 public/diagrams/*.svg。
- qa：临时起一个 Slidev 本地服务，结束后关掉；写 qa/*.png 和 qa/report.json。
- export：写 PDF。
- 全部命令不联网（npm/D2 安装不在本工具里）。

## Exit Codes

0 成功；1 运行失败（含外部工具失败、检查不通过的 --strict）；2 参数/用法错误（含 E_VALIDATION）。

## Errors & Recovery

- E_EXTERNAL_TOOL（缺 d2/slidev/Chrome/PowerPoint 或其运行失败）→ 先跑 `doctor --json`，按 data.missing 的提示装。
- E_NOT_FOUND（DECK 不是 slide-flow 工程 / 草稿文件不存在）→ 先 `init`，或检查路径。
- E_VALIDATION（主题名不对 / --slides 写法错 / DECK 非空未加 --force）→ 按 message 改参数。
- E_PARTIAL_FAILURE（diagrams 部分图渲染失败）→ 看 error.details.failed 里每个文件的报错，改源文件再跑。
- E_VERIFICATION_FAILED（--strict 下检查有问题）→ 看 error.details 的问题清单修页面，再跑。
"""


# ---------------------------------------------------------------- 信封与错误

class CliError(Exception):
    def __init__(self, code, message, details=None, suggestion=None, retryable=False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.suggestion = suggestion
        self.retryable = retryable


def classify(exc):
    e = exc
    while e is not None:
        if isinstance(e, CliError):
            return e.code
        if isinstance(e, FileNotFoundError):
            return "E_NOT_FOUND"
        if isinstance(e, PermissionError):
            return "E_PERMISSION"
        if isinstance(e, KeyboardInterrupt):
            return "E_INTERRUPTED"
        if isinstance(e, OSError):
            return "E_IO"
        e = e.__cause__
    return "E_INTERNAL"


def emit_ok(args, data, human=None, meta=None):
    if getattr(args, "json", False):
        sys.stdout.write(json.dumps({"ok": True, "data": data, "error": None, "meta": meta or {}}, ensure_ascii=False))
        sys.stdout.write("\n")
    else:
        sys.stdout.write((human if human is not None else json.dumps(data, ensure_ascii=False, indent=2)) + "\n")
    return 0


def emit_err(want_json, code, message, details=None, suggestion=None, retryable=False, exit_code=1):
    if want_json:
        env = {"ok": False, "data": None, "error": {"code": code, "message": message, "details": details or {},
                                                   "retryable": retryable, "suggestion": suggestion}}
        sys.stderr.write(json.dumps(env, ensure_ascii=False) + "\n")
    else:
        sys.stderr.write(f"错误 [{code}] {message}\n")
        if suggestion:
            sys.stderr.write(f"建议：{suggestion}\n")
    return exit_code


class Parser(argparse.ArgumentParser):
    def error(self, message):
        want_json = any(a in ("--json",) for a in sys.argv[1:]) or _format_json(sys.argv[1:])
        sys.exit(emit_err(want_json, "E_VALIDATION", f"参数错误：{message}", suggestion="跑 `sf.py --ai-help` 看用法", exit_code=2))


def _format_json(argv):
    for i, a in enumerate(argv):
        if a == "--":
            return False
        if a == "--format=json" or (a == "--format" and i + 1 < len(argv) and argv[i + 1] == "json"):
            return True
    return False


# ---------------------------------------------------------------- 环境探测

def which_node():
    p = shutil.which("node")
    if not p:
        raise CliError("E_EXTERNAL_TOOL", "找不到 node", suggestion="装 Node.js 并加入 PATH")
    return p


_NPM_ROOT = None


def npm_root():
    global _NPM_ROOT
    if _NPM_ROOT:
        return _NPM_ROOT
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        raise CliError("E_EXTERNAL_TOOL", "找不到 npm", suggestion="装 Node.js（自带 npm）")
    r = subprocess.run([npm, "root", "-g"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise CliError("E_EXTERNAL_TOOL", "npm root -g 失败", details={"stderr": r.stderr[-800:]})
    _NPM_ROOT = Path(r.stdout.strip())
    return _NPM_ROOT


def slidev_entry():
    p = npm_root() / "@slidev" / "cli" / "bin" / "slidev.mjs"
    if not p.exists():
        raise CliError("E_EXTERNAL_TOOL", "没装 Slidev 命令行", suggestion="npm i -g @slidev/cli @slidev/theme-default playwright-chromium（设 PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 用本机 Chrome）")
    return p


def wavedrom_entry():
    p = npm_root() / "wavedrom-cli" / "wavedrom-cli.js"
    if not p.exists():
        raise CliError("E_EXTERNAL_TOOL", "没装 wavedrom-cli", suggestion="npm i -g wavedrom-cli")
    return p


def find_chrome():
    env = os.environ.get("SF_CHROME")
    cands = [env] if env else []
    local = os.environ.get("LOCALAPPDATA", "")
    cands += [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              os.path.join(local, r"Google\Chrome\Application\chrome.exe"),
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
    for c in cands:
        if c and Path(c).exists():
            return c
    raise CliError("E_EXTERNAL_TOOL", "找不到 Chrome 或 Edge", suggestion="装 Chrome，或设环境变量 SF_CHROME 指向浏览器 exe")


def find_d2():
    p = shutil.which("d2")
    if p:
        return p
    alt = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "bin" / "d2.exe"
    if alt.exists():
        return str(alt)
    raise CliError("E_EXTERNAL_TOOL", "找不到 d2", suggestion="从 github.com/terrastruct/d2/releases 下 windows-amd64 包，把 d2.exe 放进 PATH")


def run_ps(script, timeout=600):
    """把脚本编码后交给 PowerShell 执行，避开引号转义；stdout 按 UTF-8 解码。"""
    full = "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n$ProgressPreference = 'SilentlyContinue'\n" + script
    enc = base64.b64encode(full.encode("utf-16-le")).decode()
    r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc],
                       capture_output=True, timeout=timeout)
    out = r.stdout.decode("utf-8", "replace")
    err = r.stderr.decode("utf-8", "replace")
    if "#< CLIXML" in err:
        msgs = re.findall(r'<S S="Error">(.*?)</S>', err)
        err = "".join(msgs).replace("_x000D__x000A_", "\n") if msgs else ""
    return r.returncode, out, err


# ---------------------------------------------------------------- 工程与主题

def load_user_config():
    try:
        return json.loads(USER_CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def list_themes():
    out = []
    for d in sorted(THEMES_DIR.iterdir()):
        meta = d / "theme.json"
        if meta.exists():
            out.append(json.loads(meta.read_text(encoding="utf-8")))
    return out


def theme_meta(name):
    p = THEMES_DIR / name / "theme.json"
    if not p.exists():
        raise CliError("E_VALIDATION", f"没有主题 {name}", details={"themes": [t["name"] for t in list_themes()]},
                       suggestion="跑 `sf.py themes` 看可选主题")
    return json.loads(p.read_text(encoding="utf-8"))


def require_deck(deck):
    deck = Path(deck).resolve()
    if not (deck / "slides.md").exists():
        raise CliError("E_NOT_FOUND", f"{deck} 不是 slide-flow 工程（缺 slides.md）", suggestion="先 `sf.py init <deck>`")
    return deck


class Writer:
    """所有落盘都走这里；dry_run 时只记录计划。"""

    def __init__(self, dry_run):
        self.dry_run = dry_run
        self.planned = []

    def write_bytes(self, path, data):
        self.planned.append(str(path))
        if self.dry_run:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def mkdir(self, path):
        if self.dry_run:
            return
        path.mkdir(parents=True, exist_ok=True)


def build_deck(deck, theme, title, writer):
    meta = theme_meta(theme)
    repl = {"__TITLE__": title, "__SCHEME__": meta.get("scheme", "light"),
            "__SHIKI_LIGHT__": meta.get("shiki_light", "github-light"),
            "__SHIKI_DARK__": meta.get("shiki_dark", "github-dark")}
    for src in sorted(DECK_TEMPLATE.rglob("*")):
        rel = src.relative_to(DECK_TEMPLATE)
        dst = deck / rel
        if src.is_dir():
            writer.mkdir(dst)
            continue
        data = src.read_bytes()
        if src.suffix in TEXT_SUFFIXES:
            text = data.decode("utf-8")
            for k, v in repl.items():
                text = text.replace(k, v)
            data = text.encode("utf-8")
        writer.write_bytes(dst, data)
    tdir = THEMES_DIR / theme
    writer.write_bytes(deck / "styles" / "theme.css", (tdir / "theme.css").read_bytes())
    writer.write_bytes(deck / "diagrams" / "_theme.d2", (tdir / "_theme.d2").read_bytes())
    for sub in ("public/diagrams", "qa", "drafts/read"):
        writer.mkdir(deck / sub)
    cfg = {"theme": theme, "title": title, "created": time.strftime("%Y-%m-%d %H:%M")}
    writer.write_bytes(deck / "slide-flow.json", json.dumps(cfg, ensure_ascii=False, indent=2).encode("utf-8"))


def read_text_arg(value, file_value, name):
    if value is not None and file_value is not None:
        raise CliError("E_VALIDATION", f"--{name} 和 --{name}-file 只能给一个")
    if file_value is not None:
        p = Path(file_value)
        if not p.exists():
            raise CliError("E_NOT_FOUND", f"{p} 不存在")
        if not p.is_file():
            raise CliError("E_VALIDATION", f"{p} 不是文件")
        try:
            return p.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError as e:
            raise CliError("E_VALIDATION", f"{p} 不是 UTF-8 文本") from e
    return value


# ---------------------------------------------------------------- 本地服务

def free_port(preferred=None):
    if preferred:
        return preferred
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class SlidevServer:
    def __init__(self, deck, port, log_path):
        self.deck = deck
        self.port = port
        self.log_path = log_path
        self.proc = None

    def __enter__(self):
        self.log = open(self.log_path, "wb")
        self.proc = subprocess.Popen([which_node(), str(slidev_entry()), "slides.md", "--port", str(self.port)],
                                     cwd=str(self.deck), stdout=self.log, stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        url = f"http://localhost:{self.port}/"
        deadline = time.time() + 90
        while time.time() < deadline:
            if self.proc.poll() is not None:
                break
            try:
                with urllib.request.urlopen(url, timeout=2) as r:
                    if r.status == 200:
                        return self
            except OSError:
                time.sleep(0.8)
        self.__exit__(None, None, None)
        tail = Path(self.log_path).read_bytes()[-1500:].decode("utf-8", "replace")
        raise CliError("E_EXTERNAL_TOOL", "Slidev 本地服务没起来", details={"log_tail": tail},
                       suggestion="看 details.log_tail；常见原因是 slides.md 语法错或端口被占")

    def __exit__(self, *exc):
        if self.proc and self.proc.poll() is None:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(self.proc.pid)], capture_output=True)
        try:
            self.log.close()
        except Exception:
            pass


def parse_slide_spec(spec):
    if not spec:
        return None
    out = []
    for part in spec.split(","):
        part = part.strip()
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not m:
            raise CliError("E_VALIDATION", f"--slides 写法不对：{part}", suggestion="例如 1,3-5")
        a = int(m.group(1))
        b = int(m.group(2) or a)
        out.extend(range(min(a, b), max(a, b) + 1))
    return sorted(set(out))


def run_qa(deck, slides, shots, port):
    qa_dir = deck / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    if shots:
        for old in qa_dir.glob("slide-*.png"):
            if not slides:
                old.unlink()
    port = free_port(port)
    chrome = find_chrome()
    with SlidevServer(deck, port, qa_dir / "dev.log"):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"port": port, "outDir": str(qa_dir), "slides": slides, "chrome": chrome, "shots": shots}, f)
            cfg_path = f.name
        env = dict(os.environ, NODE_PATH=str(npm_root()))
        r = subprocess.run([which_node(), str(QA_JS), cfg_path], capture_output=True, env=env, timeout=900)
        os.unlink(cfg_path)
    if r.returncode != 0:
        raise CliError("E_EXTERNAL_TOOL", "截图检查脚本失败", details={"exit": r.returncode, "stderr": r.stderr.decode("utf-8", "replace")[-1500:]})
    return json.loads(r.stdout.decode("utf-8"))


# ---------------------------------------------------------------- 草稿读取

DRAFT_PS = r"""
$ErrorActionPreference = 'Stop'
$pptxPath = '__PPTX__'
$outDir = '__OUT__'
$render = __RENDER__
$app = New-Object -ComObject PowerPoint.Application
$hadOpen = $app.Presentations.Count -gt 0
$pres = $null
function RgbOf($c) { try { return [int]$c.RGB } catch { return $null } }
function TextInfo($sh) {
  $paras = @()
  try {
    if (-not $sh.HasTextFrame) { return $paras }
    if (-not $sh.TextFrame.HasText) { return $paras }
    $tr = $sh.TextFrame.TextRange
    $pc = $tr.Paragraphs().Count
    for ($i = 1; $i -le $pc; $i++) {
      $p = $tr.Paragraphs($i)
      $runs = @()
      $rc = $p.Runs().Count
      for ($j = 1; $j -le $rc; $j++) {
        $r = $p.Runs($j)
        $runs += @{ text = $r.Text; rgb = (RgbOf $r.Font.Color); size = $r.Font.Size; bold = [int]$r.Font.Bold }
      }
      $paras += @{ text = $p.Text.TrimEnd("`r", "`n"); level = $p.IndentLevel; runs = $runs }
    }
  } catch {}
  return $paras
}
function ShapeInfo($sh, $parent) {
  $o = @{ id = $sh.Id; name = $sh.Name; type = [int]$sh.Type; left = $sh.Left; top = $sh.Top; width = $sh.Width; height = $sh.Height; rotation = $sh.Rotation; parent = $parent }
  try { $o.autoshape = [int]$sh.AutoShapeType } catch {}
  try { $o.hflip = [int]$sh.HorizontalFlip; $o.vflip = [int]$sh.VerticalFlip } catch {}
  try { $o.connector = [int]$sh.Connector } catch { $o.connector = 0 }
  try { $o.fill = @{ visible = [int]$sh.Fill.Visible; rgb = (RgbOf $sh.Fill.ForeColor) } } catch {}
  try { $o.line = @{ visible = [int]$sh.Line.Visible; rgb = (RgbOf $sh.Line.ForeColor); dash = [int]$sh.Line.DashStyle; begin_arrow = [int]$sh.Line.BeginArrowheadStyle; end_arrow = [int]$sh.Line.EndArrowheadStyle } } catch {}
  try { $o.placeholder = [int]$sh.PlaceholderFormat.Type } catch {}
  if ($o.connector -ne 0) {
    try { if ($sh.ConnectorFormat.BeginConnected) { $o.begin_shape = $sh.ConnectorFormat.BeginConnectedShape.Id } } catch {}
    try { if ($sh.ConnectorFormat.EndConnected) { $o.end_shape = $sh.ConnectorFormat.EndConnectedShape.Id } } catch {}
  }
  $o.paras = @(TextInfo $sh)
  try {
    if ($sh.HasTable) {
      $rows = @()
      $t = $sh.Table
      for ($ri = 1; $ri -le $t.Rows.Count; $ri++) {
        $cells = @()
        for ($ci = 1; $ci -le $t.Columns.Count; $ci++) { $cells += $t.Cell($ri, $ci).Shape.TextFrame.TextRange.Text }
        $rows += ,$cells
      }
      $o.table = $rows
    }
  } catch {}
  return $o
}
function Walk($shapes, $parent, [ref]$acc) {
  foreach ($sh in $shapes) {
    $acc.Value += ShapeInfo $sh $parent
    if ([int]$sh.Type -eq 6) { Walk $sh.GroupItems $sh.Id $acc }
  }
}
try {
  $pres = $app.Presentations.Open($pptxPath, -1, 0, 0)
  $W = $pres.PageSetup.SlideWidth; $H = $pres.PageSetup.SlideHeight
  $slides = @()
  $idx = 0
  foreach ($s in $pres.Slides) {
    $idx++
    $acc = @()
    Walk $s.Shapes $null ([ref]$acc)
    $notes = ''
    try { foreach ($ns in $s.NotesPage.Shapes) { try { if ([int]$ns.PlaceholderFormat.Type -eq 2) { $notes = $ns.TextFrame.TextRange.Text } } catch {} } } catch {}
    $png = $null
    if ($render) {
      $png = Join-Path $outDir ('draft-{0:D2}.png' -f $idx)
      $s.Export($png, 'PNG', 1280, [int](1280 * $H / $W))
    }
    $slides += @{ index = $idx; shapes = $acc; notes = $notes; png = $png; hidden = [int]$s.SlideShowTransition.Hidden }
  }
  $result = @{ width = $W; height = $H; slides = $slides }
  $pres.Close()
  $pres = $null
  ConvertTo-Json $result -Depth 12 -Compress
} finally {
  if ($pres -ne $null) { try { $pres.Close() } catch {} }
  if (-not $hadOpen) { try { $app.Quit() } catch {} }
}
"""

DRAFT_TEMPLATE_PS = r"""
$ErrorActionPreference = 'Stop'
$outPath = '__OUT__'
$app = New-Object -ComObject PowerPoint.Application
$hadOpen = $app.Presentations.Count -gt 0
$pres = $null
try {
  $pres = $app.Presentations.Add(0)
  $pres.PageSetup.SlideWidth = 960; $pres.PageSetup.SlideHeight = 540
  $s = $pres.Slides.Add(1, 12)
  $t = $s.Shapes.AddTextbox(1, 40, 24, 880, 50); $t.TextFrame.TextRange.Text = '标题写这页的结论（最上面、字最大的那行会被当成标题）'; $t.TextFrame.TextRange.Font.Size = 26
  $a = $s.Shapes.AddShape(1, 60, 160, 200, 80); $a.TextFrame.TextRange.Text = '方框 = 一个元素'
  $b = $s.Shapes.AddShape(5, 380, 160, 200, 80); $b.TextFrame.TextRange.Text = '圆角、椭圆都行'
  $c = $s.Shapes.AddShape(9, 700, 160, 200, 80); $c.TextFrame.TextRange.Text = '框里写关键词'
  $l1 = $s.Shapes.AddConnector(1, 0, 0, 10, 10); $l1.ConnectorFormat.BeginConnect($a, 4); $l1.ConnectorFormat.EndConnect($b, 2); $l1.Line.EndArrowheadStyle = 2
  $l2 = $s.Shapes.AddLine(582, 200, 698, 200); $l2.Line.EndArrowheadStyle = 2; $l2.Line.DashStyle = 4
  $k = $s.Shapes.AddTextbox(1, 60, 270, 840, 60); $k.TextFrame.TextRange.Text = '箭头 = 关系/顺序；虚线 = 次要或可选；线不必接在框上，端点靠近框就行'; $k.TextFrame.TextRange.Font.Size = 16
  $r = $s.Shapes.AddTextbox(1, 60, 350, 840, 80); $r.TextFrame.TextRange.Text = '红字 = 给 AI 的指令，例如：这三个框做成时间线；这里放某函数的代码并逐行高亮'; $r.TextFrame.TextRange.Font.Color.RGB = 255; $r.TextFrame.TextRange.Font.Size = 16
  $n = $s.Shapes.AddTextbox(1, 60, 450, 840, 40); $n.TextFrame.TextRange.Text = '讲稿要点写在下方备注栏；这一页示范可以删掉'; $n.TextFrame.TextRange.Font.Size = 14
  $s2 = $pres.Slides.Add(2, 12)
  $pres.SaveAs($outPath, 24)
  $pres.Close(); $pres = $null
  'ok'
} finally {
  if ($pres -ne $null) { try { $pres.Close() } catch {} }
  if (-not $hadOpen) { try { $app.Quit() } catch {} }
}
"""

# PowerPoint 形状编号（MsoAutoShapeType）与 pptx 里 prstGeom 名字的对应，2026-09-23 用 PowerPoint 画一遍再看 XML 核对过
AUTOSHAPE_NAMES = {1: "矩形", 5: "圆角矩形", 9: "椭圆", 7: "三角形", 4: "菱形", 33: "右箭头", 34: "左箭头",
                   35: "上箭头", 36: "下箭头", 51: "五边形箭头", 52: "燕尾箭头", 179: "云形", 61: "流程-过程",
                   63: "流程-判断", 69: "流程-终止"}
PRST_TO_MSO = {"rect": 1, "roundRect": 5, "ellipse": 9, "triangle": 7, "diamond": 4, "rightArrow": 33,
               "leftArrow": 34, "upArrow": 35, "downArrow": 36, "homePlate": 51, "chevron": 52, "cloud": 179,
               "flowChartProcess": 61, "flowChartDecision": 63, "flowChartTerminator": 69}


# ---------------------------------------------------------------- 草稿读取：不开 PowerPoint 的读法
#
# 透明加密下 python 直接读 .pptx 是密文，但 `cmd /c type` 的输出是明文（路径必须是反斜杠，正斜杠返回 0 字节）。
# 读出来的 XML 整理成和 DRAFT_PS 同样的结构，后面 normalize_draft 一份代码两条路共用。
# 做不到的：每页渲染图；文字没写死颜色时从版式/形状样式继承的颜色（按“无颜色”处理，所以只认直接设成红色的字）。
# 字号没写死时按母版文字样式和演示文稿默认样式补，版式里单独改过的占位符字号不跟。

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
NS_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
EMU_PER_PT = 12700
ESAFENET_MAGIC = b"\xe0\xa8\x91\xe7\xd8\xf2\x05\xac"
PH_TYPES = {"title": 1, "body": 2, "ctrTitle": 3, "subTitle": 4}
PRESET_COLORS = {"red": "FF0000", "darkRed": "8B0000", "black": "000000", "white": "FFFFFF"}


def read_pptx_bytes(pptx):
    data = Path(pptx).read_bytes()
    if data[:4] == b"PK\x03\x04":
        return data
    r = subprocess.run(["cmd.exe", "/d", "/c", "type", str(Path(pptx).resolve())], capture_output=True, timeout=120)
    if r.stdout[:4] == b"PK\x03\x04":
        return r.stdout
    details = {"exit": r.returncode, "bytes": len(r.stdout), "head": r.stdout[:8].hex(),
               "stderr": r.stderr.decode("mbcs", "replace")[-500:]}
    if r.returncode == 0 and r.stdout and r.stdout[:8] != ESAFENET_MAGIC:
        raise CliError("E_VALIDATION", "不是 .pptx 文件（解密后的文件头不是 zip）", details=details,
                       suggestion="老格式 .ppt 先用 PowerPoint 另存为 .pptx")
    raise CliError("E_EXTERNAL_TOOL", "读不出草稿的明文内容", details=details,
                   suggestion="确认文件是 .pptx 而不是 .ppt；或装 PowerPoint 后用 --via powerpoint")


class PptxPackage:
    def __init__(self, data):
        self.zip = zipfile.ZipFile(io.BytesIO(data))
        self._xml = {}

    def xml(self, part):
        if part not in self._xml:
            self._xml[part] = ET.fromstring(self.zip.read(part))
        return self._xml[part]

    def rels(self, part):
        d, name = part.rsplit("/", 1)
        rel_part = f"{d}/_rels/{name}.rels"
        if rel_part not in self.zip.namelist():
            return []
        out = []
        for rel in self.xml(rel_part).iter(NS_REL + "Relationship"):
            target = rel.get("Target", "")
            if rel.get("TargetMode") == "External":
                continue
            parts = (target.lstrip("/").split("/") if target.startswith("/") else d.split("/") + target.split("/"))
            norm = []
            for p in parts:
                if p == "..":
                    norm.pop()
                elif p and p != ".":
                    norm.append(p)
            out.append((rel.get("Id"), rel.get("Type", "").rsplit("/", 1)[-1], "/".join(norm)))
        return out

    def rel_by_type(self, part, kind):
        return next((t for _, k, t in self.rels(part) if k == kind), None)


class ColorContext:
    def __init__(self, pkg, master):
        self.scheme, self.clrmap = {}, {}
        if master is None:
            return
        cm = next(pkg.xml(master).iter(NS_P + "clrMap"), None)
        if cm is not None:
            self.clrmap = dict(cm.attrib)
        theme = pkg.rel_by_type(master, "theme")
        if theme:
            cs = pkg.xml(theme).find(f".//{NS_A}clrScheme")
            for c in list(cs) if cs is not None else []:
                v = c[0] if len(c) else None
                if v is not None:
                    self.scheme[c.tag.replace(NS_A, "")] = v.get("lastClr") or v.get("val")

    def resolve(self, holder):
        """holder 是 solidFill / fillRef / lnRef 这类“里面装一个颜色”的元素，返回 PowerPoint COM 同款整数（R + G<<8 + B<<16）。"""
        if holder is None:
            return None
        for c in holder:
            tag = c.tag.replace(NS_A, "")
            if tag == "srgbClr":
                hexv = c.get("val")
            elif tag == "sysClr":
                hexv = c.get("lastClr")
            elif tag == "prstClr":
                hexv = PRESET_COLORS.get(c.get("val"))
            elif tag == "schemeClr":
                name = c.get("val")
                hexv = self.scheme.get(self.clrmap.get(name, name))
            else:
                continue
            if not hexv or len(hexv) != 6:
                return None
            r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (0, 2, 4))
            mods = {m.tag.replace(NS_A, ""): int(m.get("val", "0")) / 100000 for m in c}
            if "lumMod" in mods or "lumOff" in mods:
                h, l, s = colorsys.rgb_to_hls(r, g, b)
                l = min(1.0, max(0.0, l * mods.get("lumMod", 1.0) + mods.get("lumOff", 0.0)))
                r, g, b = colorsys.hls_to_rgb(h, l, s)
            r, g, b = (int(round(v * 255)) for v in (r, g, b))
            return r | (g << 8) | (b << 16)
        return None


def _local(el):
    return el.tag.rsplit("}", 1)[-1]


def _xfrm_box(xfrm):
    if xfrm is None:
        return None
    off, ext = xfrm.find(NS_A + "off"), xfrm.find(NS_A + "ext")
    if off is None or ext is None:
        return None
    return [int(off.get("x", 0)), int(off.get("y", 0)), int(ext.get("cx", 0)), int(ext.get("cy", 0))]


def _placeholder_boxes(pkg, part):
    """版式/母版里每个占位符的位置，给没写位置、从上层继承的占位符用。"""
    by_idx, by_type = {}, {}
    if part is None:
        return by_idx, by_type
    for sp in pkg.xml(part).iter(NS_P + "sp"):
        ph = sp.find(f"{NS_P}nvSpPr/{NS_P}nvPr/{NS_P}ph")
        box = _xfrm_box(sp.find(f"{NS_P}spPr/{NS_A}xfrm"))
        if ph is None or box is None:
            continue
        if ph.get("idx"):
            by_idx.setdefault(ph.get("idx"), box)
        by_type.setdefault(ph.get("type", "body"), box)
    return by_idx, by_type


def _level_sizes(style_el):
    """<a:lvl1pPr><a:defRPr sz=".."> 这类层级样式 → {层级: 字号pt}。"""
    out = {}
    if style_el is None:
        return out
    for n in range(1, 10):
        d = style_el.find(f"{NS_A}lvl{n}pPr/{NS_A}defRPr")
        if d is not None and d.get("sz"):
            out[n] = int(d.get("sz")) / 100
    return out


def _paras(tx_body, colors, sizes=None):
    paras = []
    if tx_body is None:
        return paras
    own = _level_sizes(tx_body.find(NS_A + "lstStyle"))
    for p in tx_body.findall(NS_A + "p"):
        ppr = p.find(NS_A + "pPr")
        level = int(ppr.get("lvl", "0")) + 1 if ppr is not None else 1
        default_size = own.get(level) or (sizes or {}).get(level)
        runs = []
        for r in p:
            tag = _local(r)
            if tag in ("r", "fld"):
                rpr = r.find(NS_A + "rPr")
                rgb = colors.resolve(rpr.find(NS_A + "solidFill")) if rpr is not None else None
                size = int(rpr.get("sz")) / 100 if rpr is not None and rpr.get("sz") else default_size
                bold = -1 if rpr is not None and rpr.get("b") in ("1", "true") else 0
                runs.append({"text": "".join(t.text or "" for t in r.findall(NS_A + "t")), "rgb": rgb, "size": size, "bold": bold})
            elif tag == "br":
                runs.append({"text": "\n", "rgb": None, "size": None, "bold": 0})
        paras.append({"text": "".join(r["text"] for r in runs), "level": level, "runs": runs})
    while paras and not paras[-1]["text"].strip():
        paras.pop()
    return paras


def _fill_info(sp_pr, style, colors):
    for c in (list(sp_pr) if sp_pr is not None else []):
        tag = _local(c)
        if tag == "noFill":
            return {"visible": 0, "rgb": None}
        if tag == "solidFill":
            return {"visible": -1, "rgb": colors.resolve(c)}
        if tag in ("gradFill", "pattFill", "blipFill", "grpFill"):
            return {"visible": -1, "rgb": None}
    ref = style.find(NS_A + "fillRef") if style is not None else None
    if ref is not None and ref.get("idx", "0") != "0":
        return {"visible": -1, "rgb": colors.resolve(ref)}
    return {"visible": 0, "rgb": None}


def _line_info(sp_pr, style, colors):
    ln = sp_pr.find(NS_A + "ln") if sp_pr is not None else None
    visible, rgb = None, None
    if ln is not None:
        if ln.find(NS_A + "noFill") is not None:
            visible = 0
        elif ln.find(NS_A + "solidFill") is not None:
            visible, rgb = -1, colors.resolve(ln.find(NS_A + "solidFill"))
    if visible is None:
        ref = style.find(NS_A + "lnRef") if style is not None else None
        if ref is not None and ref.get("idx", "0") != "0":
            visible, rgb = -1, colors.resolve(ref)
        else:
            visible = 0
    dash_el = ln.find(NS_A + "prstDash") if ln is not None else None
    dash_val = dash_el.get("val", "solid") if dash_el is not None else "solid"
    dash = 1 if dash_val == "solid" else 3 if dash_val in ("dot", "sysDot") else 4

    def arrow(tag):
        el = ln.find(NS_A + tag) if ln is not None else None
        return 2 if el is not None and el.get("type", "none") != "none" else 1

    return {"visible": visible, "rgb": rgb, "dash": dash, "begin_arrow": arrow("headEnd"), "end_arrow": arrow("tailEnd")}


def _walk_tree(container, tf, parent, acc, ctx):
    """tf = (sx, sy, tx, ty)：把组合内部坐标换成页面坐标（EMU）。"""
    sx, sy, tx, ty = tf

    def to_slide(box):
        return [box[0] * sx + tx, box[1] * sy + ty, box[2] * sx, box[3] * sy]

    for el in container:
        tag = _local(el)
        if el.tag == NS_MC + "AlternateContent":
            branch = el.find(NS_MC + "Fallback")
            if branch is None:
                branch = el.find(NS_MC + "Choice")
            if branch is not None:
                _walk_tree(branch, tf, parent, acc, ctx)
            continue
        if tag not in ("sp", "cxnSp", "grpSp", "pic", "graphicFrame"):
            continue
        nv = next((c for c in el if _local(c).startswith("nv")), None)
        cnv = nv.find(NS_P + "cNvPr") if nv is not None else None
        sid = int(cnv.get("id", "0")) if cnv is not None else 0
        o = {"id": sid, "name": cnv.get("name") if cnv is not None else None, "parent": parent, "connector": 0}
        sp_pr = el.find(NS_P + "grpSpPr" if tag == "grpSp" else NS_P + "spPr")
        style = el.find(NS_P + "style")
        xfrm = el.find(NS_P + "xfrm") if tag == "graphicFrame" else (sp_pr.find(NS_A + "xfrm") if sp_pr is not None else None)
        box = _xfrm_box(xfrm)
        ph = nv.find(f"{NS_P}nvPr/{NS_P}ph") if nv is not None else None
        if ph is not None:
            o["placeholder"] = PH_TYPES.get(ph.get("type", "body"), 0)
            if box is None:
                box = ctx["ph_box"](ph)
        if box is None:
            box = [0, 0, 0, 0]
        slide_box = to_slide(box)
        o.update(dict(zip(("left", "top", "width", "height"), slide_box)))
        o["rotation"] = int(xfrm.get("rot", "0")) / 60000 if xfrm is not None else 0
        o["hflip"] = -1 if xfrm is not None and xfrm.get("flipH") in ("1", "true") else 0
        o["vflip"] = -1 if xfrm is not None and xfrm.get("flipV") in ("1", "true") else 0
        prst_el = sp_pr.find(NS_A + "prstGeom") if sp_pr is not None else None
        prst = prst_el.get("prst") if prst_el is not None else None
        colors = ctx["colors"]
        if tag == "grpSp":
            o["type"] = 6
        elif tag == "pic":
            o["type"] = 13
        elif tag == "graphicFrame":
            tbl = el.find(f".//{NS_A}tbl")
            o["type"] = 19 if tbl is not None else 0
            if tbl is not None:
                o["table"] = [["\n".join(p["text"] for p in _paras(tc.find(NS_A + "txBody"), colors)) for tc in tr.findall(NS_A + "tc")]
                              for tr in tbl.findall(NS_A + "tr")]
        elif tag == "cxnSp" or prst == "line":
            o["type"], o["connector"] = (1 if tag == "cxnSp" else 9), -1
            cnv_cxn = nv.find(NS_P + "cNvCxnSpPr") if nv is not None else None
            if cnv_cxn is not None:
                st, en = cnv_cxn.find(NS_A + "stCxn"), cnv_cxn.find(NS_A + "endCxn")
                if st is not None:
                    o["begin_shape"] = int(st.get("id"))
                if en is not None:
                    o["end_shape"] = int(en.get("id"))
        elif ph is not None:
            o["type"] = 14
        elif nv is not None and nv.find(NS_P + "cNvSpPr") is not None and nv.find(NS_P + "cNvSpPr").get("txBox") in ("1", "true"):
            o["type"] = 17
        else:
            o["type"] = 1
        if prst and tag in ("sp", "cxnSp"):
            o["autoshape"] = PRST_TO_MSO.get(prst, prst)
        if tag in ("sp", "cxnSp", "pic"):
            o["fill"] = _fill_info(sp_pr, style, colors) if tag == "sp" else {"visible": 0, "rgb": None}
            o["line"] = _line_info(sp_pr, style, colors)
        if ph is None:
            sizes = ctx["sizes"]["other"]
        else:
            sizes = ctx["sizes"]["title" if ph.get("type") in ("title", "ctrTitle") else "body"]
        o["paras"] = _paras(el.find(NS_P + "txBody"), colors, sizes)
        if o.get("table"):
            o["paras"] = [{"text": c, "level": 1, "runs": [{"text": c, "rgb": None, "size": sizes.get(1), "bold": 0}]}
                          for row in o["table"] for c in row if c.strip()]
        acc.append(o)
        if tag == "grpSp" and xfrm is not None:
            ch_off, ch_ext = xfrm.find(NS_A + "chOff"), xfrm.find(NS_A + "chExt")
            if ch_off is not None and ch_ext is not None:
                ccx, ccy = int(ch_ext.get("cx", 0)) or 1, int(ch_ext.get("cy", 0)) or 1
                kx, ky = box[2] / ccx, box[3] / ccy
                ntf = (sx * kx, sy * ky, sx * (box[0] - int(ch_off.get("x", 0)) * kx) + tx,
                       sy * (box[1] - int(ch_off.get("y", 0)) * ky) + ty)
            else:
                ntf = tf
            _walk_tree(el, ntf, sid, acc, ctx)


def read_draft_xml(pptx):
    data = read_pptx_bytes(pptx)
    try:
        return _read_draft_package(PptxPackage(data))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
        raise CliError("E_VALIDATION", f"不是有效的 .pptx：{type(e).__name__}: {e}",
                       suggestion="用 PowerPoint 打开另存一次再试") from e


def _read_draft_package(pkg):
    pres_part = "ppt/presentation.xml"
    pres = pkg.xml(pres_part)
    size = pres.find(NS_P + "sldSz")
    W, H = int(size.get("cx")) / EMU_PER_PT, int(size.get("cy")) / EMU_PER_PT
    targets = {rid: t for rid, _, t in pkg.rels(pres_part)}
    default_sizes = _level_sizes(pres.find(NS_P + "defaultTextStyle"))
    slides = []
    for idx, sid in enumerate(pres.iter(NS_P + "sldId"), 1):
        part = targets.get(sid.get(NS_R + "id"))
        if not part:
            continue
        root = pkg.xml(part)
        layout = pkg.rel_by_type(part, "slideLayout")
        master = pkg.rel_by_type(layout, "slideMaster") if layout else None
        lay_idx, lay_type = _placeholder_boxes(pkg, layout)
        _, mas_type = _placeholder_boxes(pkg, master)

        def ph_box(ph, lay_idx=lay_idx, lay_type=lay_type, mas_type=mas_type):
            t = ph.get("type", "body")
            generic = "title" if t in ("title", "ctrTitle") else "body"
            return (lay_idx.get(ph.get("idx")) or lay_type.get(t) or mas_type.get(t) or mas_type.get(generic))

        acc = []
        tree = root.find(f"{NS_P}cSld/{NS_P}spTree")
        tx_styles = pkg.xml(master).find(f"{NS_P}txStyles") if master else None
        sizes = {"other": default_sizes,
                 "title": _level_sizes(tx_styles.find(NS_P + "titleStyle")) if tx_styles is not None else {},
                 "body": _level_sizes(tx_styles.find(NS_P + "bodyStyle")) if tx_styles is not None else {}}
        ctx = {"colors": ColorContext(pkg, master), "ph_box": ph_box, "sizes": sizes}
        if tree is not None:
            _walk_tree(tree, (1 / EMU_PER_PT, 1 / EMU_PER_PT, 0, 0), None, acc, ctx)
        notes = ""
        notes_part = pkg.rel_by_type(part, "notesSlide")
        if notes_part:
            for sp in pkg.xml(notes_part).iter(NS_P + "sp"):
                ph = sp.find(f"{NS_P}nvSpPr/{NS_P}nvPr/{NS_P}ph")
                if ph is not None and ph.get("type") == "body":
                    notes = "\n".join(p["text"] for p in _paras(sp.find(NS_P + "txBody"), ctx["colors"]))
        slides.append({"index": idx, "shapes": acc, "notes": notes, "png": None, "hidden": 1 if root.get("show") in ("0", "false") else 0})
    return {"width": W, "height": H, "slides": slides}


def is_red(rgb):
    if rgb is None or rgb < 0:
        return False
    r, g, b = rgb & 0xFF, (rgb >> 8) & 0xFF, (rgb >> 16) & 0xFF
    return r >= 170 and g <= 110 and b <= 110 and r - max(g, b) >= 80


def hexcolor(rgb):
    if rgb is None or rgb < 0:
        return None
    return "#%02X%02X%02X" % (rgb & 0xFF, (rgb >> 8) & 0xFF, (rgb >> 16) & 0xFF)


def normalize_draft(raw):
    W, H = float(raw["width"]), float(raw["height"])
    slides_raw = raw["slides"]
    if isinstance(slides_raw, dict):
        slides_raw = [slides_raw]
    out = []
    for s in slides_raw:
        shapes = s.get("shapes") or []
        if isinstance(shapes, dict):
            shapes = [shapes]
        items = []
        for sh in shapes:
            x, y, w, h = sh["left"] / W, sh["top"] / H, sh["width"] / W, sh["height"] / H
            paras = sh.get("paras") or []
            if isinstance(paras, dict):
                paras = [paras]
            text_lines, directives, content_lines = [], [], []
            max_size = 0
            for p in paras:
                runs = p.get("runs") or []
                if isinstance(runs, dict):
                    runs = [runs]
                line_red = "".join((r.get("text") or "") for r in runs if is_red(r.get("rgb")))
                line_plain = "".join((r.get("text") or "") for r in runs if not is_red(r.get("rgb")))
                for r in runs:
                    try:
                        max_size = max(max_size, float(r.get("size") or 0))
                    except (TypeError, ValueError):
                        pass
                full = (p.get("text") or "").strip()
                if full:
                    text_lines.append(full)
                if line_red.strip():
                    directives.append(line_red.strip())
                if line_plain.strip():
                    content_lines.append(line_plain.strip())
            t = int(sh.get("type") or 0)
            line = sh.get("line") or {}
            fill = sh.get("fill") or {}
            is_conn = bool(sh.get("connector")) or t == 9
            if t == 6:
                kind = "group"
            elif is_conn:
                kind = "connector"
            elif t == 13 or t == 11:
                kind = "picture"
            elif sh.get("table"):
                kind = "table"
            elif t == 17 or (not fill.get("visible") and not line.get("visible")):
                kind = "text"
            else:
                kind = "box"
            item = {"id": sh["id"], "kind": kind, "name": sh.get("name"),
                    "box": [round(x, 3), round(y, 3), round(w, 3), round(h, 3)],
                    "text": "\n".join(content_lines), "directives": directives, "max_font": max_size or None,
                    "parent": sh.get("parent")}
            if kind == "box":
                item["shape"] = AUTOSHAPE_NAMES.get(sh.get("autoshape"), f"形状{sh.get('autoshape')}")
                item["fill"] = hexcolor(fill.get("rgb")) if fill.get("visible") else None
                item["dashed"] = bool(line.get("dash") and line.get("dash") > 1)
            if sh.get("placeholder") in (1, 3):
                item["role"] = "title"
            if kind == "table":
                item["table"] = sh["table"]
            if kind == "connector":
                x1, y1, x2, y2 = x, y, x + w, y + h
                if sh.get("hflip") and int(sh["hflip"]) != 0:
                    x1, x2 = x2, x1
                if sh.get("vflip") and int(sh["vflip"]) != 0:
                    y1, y2 = y2, y1
                ba, ea = int(line.get("begin_arrow") or 1), int(line.get("end_arrow") or 1)
                item.update({"from_pt": [round(x1, 3), round(y1, 3)], "to_pt": [round(x2, 3), round(y2, 3)],
                             "begin_shape": sh.get("begin_shape"), "end_shape": sh.get("end_shape"),
                             "arrow": "both" if ba > 1 and ea > 1 else "end" if ea > 1 else "begin" if ba > 1 else "none",
                             "dashed": bool(line.get("dash") and line.get("dash") > 1)})
            if text_lines and not content_lines and directives:
                item["role"] = "directive"
            items.append(item)

        targets = [i for i in items if i["kind"] in ("box", "text", "picture", "table", "group")]

        def hit(pt):
            tol = 0.025
            best, best_area = None, None
            for t_ in targets:
                bx, by, bw, bh = t_["box"]
                if bx - tol <= pt[0] <= bx + bw + tol and by - tol <= pt[1] <= by + bh + tol:
                    area = bw * bh
                    if best is None or area < best_area:
                        best, best_area = t_, area
            return best["id"] if best else None

        for it in items:
            if it["kind"] != "connector":
                continue
            if it.get("begin_shape") is None:
                it["begin_shape"] = hit(it["from_pt"])
                it["begin_inferred"] = it["begin_shape"] is not None
            if it.get("end_shape") is None:
                it["end_shape"] = hit(it["to_pt"])
                it["end_inferred"] = it["end_shape"] is not None
            src, dst = it["begin_shape"], it["end_shape"]
            if it["arrow"] == "begin":
                src, dst = dst, src
            it["from"], it["to"] = src, dst

        titles = [i for i in items if i.get("role") == "title" and i["text"]]
        if not titles:
            texts = [i for i in items if i["kind"] in ("text", "box") and i["text"] and i.get("role") != "directive" and i["box"][1] < 0.25]
            texts.sort(key=lambda i: (-(i["max_font"] or 0), i["box"][1]))
            if texts:
                texts[0]["role"] = "title"
                titles = [texts[0]]
        items.sort(key=lambda i: (round(i["box"][1] * 12), i["box"][0]))
        names = {i["id"]: (i["text"].splitlines()[0][:16] if i["text"] else f"#{i['id']}") for i in items}
        summary = []
        for it in items:
            if it["kind"] == "group":
                continue
            pos = f"({it['box'][0]:.0%},{it['box'][1]:.0%}) {it['box'][2]:.0%}×{it['box'][3]:.0%}"
            if it["kind"] == "connector":
                a = names.get(it.get("from"), "?")
                b = names.get(it.get("to"), "?")
                sym = {"end": "→", "begin": "→", "both": "↔", "none": "—"}[it["arrow"]]
                summary.append(f"[连线{' 虚线' if it.get('dashed') else ''}] {a} {sym} {b}")
            elif it.get("role") == "directive":
                summary.append(f"[指令] {' / '.join(it['directives'])}")
            else:
                label = {"box": it.get("shape", "框"), "text": "文字", "picture": "图片", "table": "表格"}.get(it["kind"], it["kind"])
                if it.get("role") == "title":
                    label = "标题"
                txt = it["text"].replace("\n", " / ") if it["text"] else ""
                summary.append(f"[{label}] {txt} @ {pos}")
                for d in it["directives"]:
                    summary.append(f"[指令] {d}（写在「{names[it['id']]}」里）")
        out.append({"index": s["index"], "hidden": bool(s.get("hidden")), "title": titles[0]["text"] if titles else "",
                    "notes": (s.get("notes") or "").strip(), "png": s.get("png"), "summary": summary, "shapes": items})
    return {"width_pt": W, "height_pt": H, "aspect": round(W / H, 3), "slides": out}


# ---------------------------------------------------------------- lint

GENERIC_TITLES = {"概述", "总结", "小结", "简介", "介绍", "背景", "结果", "目录", "问题", "方案", "现状", "细节", "说明",
                  "overview", "summary", "results", "agenda", "introduction", "background", "details"}
CJK = re.compile(r"[\u4e00-\u9fff]")
WORD = re.compile(r"[A-Za-z0-9_]+")


def split_slides(text):
    """按 Slidev 规则切页：顶层 --- 分隔，紧跟的 YAML 块是该页 frontmatter。"""
    lines = text.splitlines()
    slides, cur, fm, in_fence, i = [], [], None, False, 0
    if lines and lines[0].strip() == "---":
        j = 1
        while j < len(lines) and lines[j].strip() != "---":
            j += 1
        fm = "\n".join(lines[1:j])
        i = j + 1
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and ln.strip() == "---":
            slides.append({"fm": fm, "body": "\n".join(cur)})
            cur, fm = [], None
            j = i + 1
            if j < len(lines) and re.match(r"^[A-Za-z_][\w-]*\s*:", lines[j]):
                k = j
                while k < len(lines) and lines[k].strip() != "---":
                    k += 1
                if k < len(lines):
                    fm = "\n".join(lines[j:k])
                    i = k + 1
                    continue
            i += 1
            continue
        cur.append(ln)
        i += 1
    slides.append({"fm": fm, "body": "\n".join(cur)})
    return slides


def expand_slides(path, seen=None):
    seen = seen or set()
    path = path.resolve()
    if path in seen:
        return []
    seen.add(path)
    res = []
    for s in split_slides(path.read_text(encoding="utf-8")):
        m = re.search(r"^src:\s*(.+)$", s["fm"] or "", re.M)
        if m and not s["body"].strip():
            res.extend(expand_slides(path.parent / m.group(1).strip().strip("'\""), seen))
            continue
        if not s["body"].strip() and not s["fm"]:
            continue
        s["file"] = str(path)
        res.append(s)
    return res


def lint_slide(s):
    body = s["body"]
    fm = s["fm"] or ""
    layout = (re.search(r"^layout:\s*(\S+)", fm, re.M) or [None, "default"])[1]
    notes_removed = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    code_blocks = re.findall(r"```[^\n]*\n(.*?)```", notes_removed, flags=re.S)
    no_code = re.sub(r"```.*?```", "", notes_removed, flags=re.S)
    title_m = re.search(r"^#{1,2}\s+(.+)$", no_code, re.M)
    title = title_m.group(1).strip() if title_m else ""
    heading_m = re.search(r"^heading:\s*(.+)$", fm, re.M)
    if heading_m:
        title = heading_m.group(1).strip().strip("'\"")
    prose = re.sub(r"^#{1,2}\s+.+$", "", no_code, count=1, flags=re.M)
    prose = re.sub(r"<[^>]+>", " ", prose)
    prose = re.sub(r"::\w+::|\{[^}]*\}", " ", prose)
    chars = len(CJK.findall(prose)) + len(WORD.findall(prose))
    bullets = len(re.findall(r"^\s*(?:[-*+]|\d+\.)\s+", no_code, re.M))
    visual = bool(code_blocks) or bool(re.search(r"<(img|Diagram|svg|table)\b|class=\"[^\"]*sf-|```mermaid|^\|.+\|", notes_removed, re.M | re.I))
    issues = []
    if layout not in ("cover", "section", "statement", "end") :
        if not title:
            issues.append({"rule": "title-missing", "msg": "这页没有标题"})
        elif title.strip().lower() in GENERIC_TITLES:
            issues.append({"rule": "title-generic", "msg": f"标题「{title}」是标签不是结论，改成一句判断"})
        if not visual:
            issues.append({"rule": "no-visual", "msg": "这页只有文字，加图、代码或结构化元素"})
    if chars > 110:
        issues.append({"rule": "too-much-text", "msg": f"正文约 {chars} 字/词，超过 110，拆页或挪进讲稿"})
    if bullets > 6:
        issues.append({"rule": "too-many-bullets", "msg": f"{bullets} 条要点，超过 6 条"})
    for cb in code_blocks:
        n = len([l for l in cb.splitlines() if l.strip()])
        if n > 18:
            issues.append({"rule": "code-too-long", "msg": f"代码块 {n} 行，超过 18 行，截取关键段或分步高亮"})
    has_notes = "<!--" in body
    return {"title": title, "layout": layout, "chars": chars, "bullets": bullets, "code_blocks": len(code_blocks),
            "has_notes": has_notes, "issues": issues}


# ---------------------------------------------------------------- 子命令

def cmd_doctor(args):
    checks, missing = {}, []

    optional_missing = []

    def probe(name, fn, optional=False):
        try:
            checks[name] = {"ok": True, "detail": fn()}
        except CliError as e:
            checks[name] = {"ok": False, "detail": e.message, "optional": optional}
            (optional_missing if optional else missing).append({"tool": name, "fix": e.suggestion})

    probe("node", which_node)
    probe("slidev", lambda: str(slidev_entry()))
    probe("playwright-chromium", lambda: str(npm_root() / "playwright-chromium") if (npm_root() / "playwright-chromium").exists()
          else (_ for _ in ()).throw(CliError("E_EXTERNAL_TOOL", "没装 playwright-chromium", suggestion="npm i -g playwright-chromium")))
    probe("chrome", find_chrome)
    probe("d2", find_d2)
    probe("wavedrom", lambda: str(wavedrom_entry()))

    def ppt():
        code, out, err = run_ps("$a = New-Object -ComObject PowerPoint.Application; $v = $a.Version; if ($a.Presentations.Count -eq 0) { $a.Quit() }; $v", 120)
        if code != 0 or not out.strip():
            raise CliError("E_EXTERNAL_TOOL", "PowerPoint COM 不可用",
                           suggestion="可选：没有 PowerPoint 时 draft 自动改为直接读文件（没有每页图片），draft-template 用不了")
        return "PowerPoint " + out.strip()

    probe("powerpoint", ppt, optional=True)
    data = {"checks": checks, "missing": missing, "optional_missing": optional_missing, "all_ok": not missing}
    human = "\n".join(f"{'✓' if v['ok'] else ('-' if v.get('optional') else '✗')} {k}: {v['detail']}" + ("（可选）" if v.get("optional") else "")
                      for k, v in checks.items())
    return emit_ok(args, data, human)


def cmd_themes(args):
    cfg = load_user_config()
    if args.set_default:
        theme_meta(args.set_default)
        cfg["default_theme"] = args.set_default
        USER_CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    themes = list_themes()
    data = {"themes": themes, "default": cfg.get("default_theme", "instrument")}
    human = "\n".join(f"{'*' if t['name'] == data['default'] else ' '} {t['name']:<11} {t['label']}：{t['desc']}" for t in themes)
    return emit_ok(args, data, human)


def cmd_init(args):
    deck = Path(args.deck).resolve()
    title = read_text_arg(args.title, args.title_file, "title") or deck.name
    theme = args.theme or load_user_config().get("default_theme", "instrument")
    theme_meta(theme)
    if deck.exists() and any(deck.iterdir()) and not args.force:
        raise CliError("E_VALIDATION", f"{deck} 已存在且非空", suggestion="换个目录，或加 --force（只覆盖模板文件）")
    w = Writer(args.dry_run)
    build_deck(deck, theme, title, w)
    data = {"deck": str(deck), "theme": theme, "title": title, "files": w.planned, "dry_run": args.dry_run}
    return emit_ok(args, data, f"{'[预演] ' if args.dry_run else ''}已建工程 {deck}（主题 {theme}，{len(w.planned)} 个文件）")


def theme_color(deck, var, default):
    try:
        css = (deck / "styles" / "theme.css").read_text(encoding="utf-8")
    except OSError:
        return default
    m = re.search(re.escape(var) + r"\s*:\s*(#[0-9A-Fa-f]{6})", css)
    return m.group(1) if m else default


def recolor_wavedrom(path, ink):
    """WaveDrom 写死黑色、文字不设颜色；换成主题正文色和主题字体，深色主题上才看得见。"""
    svg = path.read_text(encoding="utf-8")
    svg = re.sub(r'stroke="(?:black|#000|#000000)"', f'stroke="{ink}"', svg)
    svg = re.sub(r'(stroke|fill):\s*(?:black|#000000|#000)\b', lambda m: f"{m.group(1)}:{ink}", svg)
    svg = svg.replace('font-family="sans-serif"', 'font-family="Microsoft YaHei UI, Microsoft YaHei, PingFang SC, sans-serif"')
    svg = re.sub(r'(<svg\b[^>]*?)>', lambda m: m.group(1) + f' fill="{ink}">' if "fill=" not in m.group(1) else m.group(0), svg, count=1)
    path.write_text(svg, encoding="utf-8")


def render_diagrams(deck, only=None):
    ddir, pdir = deck / "diagrams", deck / "public" / "diagrams"
    pdir.mkdir(parents=True, exist_ok=True)
    done, failed = [], []
    for src in sorted(ddir.glob("*")):
        if not src.is_file():
            continue
        name = src.name
        if only and not name.startswith(only):
            continue
        if name.endswith(".d2"):
            if name.startswith("_"):
                continue
            stem = name[:-3]
            dst = pdir / f"{stem}.svg"
            layout = "elk"
            head = src.read_text(encoding="utf-8")[:300]
            m = re.search(r"#\s*sf:\s*layout=(\w+)", head)
            if m:
                layout = m.group(1)
            body = src.read_text(encoding="utf-8")
            pre = []
            if (ddir / "_theme.d2").exists() and "@_theme" not in body:
                pre.append("...@_theme")
            pre += D2_PREAMBLE
            tmp = ddir / f".render-{stem}.d2"
            tmp.write_text("\n".join(pre) + "\n" + body, encoding="utf-8")
            try:
                r = subprocess.run([find_d2(), "--layout", layout, "--pad", "24", tmp.name, str(dst)], cwd=str(ddir),
                                   capture_output=True, text=True, encoding="utf-8", errors="replace")
            finally:
                tmp.unlink(missing_ok=True)
            if r.returncode == 0 and dst.exists():
                svg = dst.read_text(encoding="utf-8")
                svg = re.sub(r'(<rect[^>]*?)fill="#[0-9A-Fa-f]{6}" class=" fill-N7"', r'\1fill="none" class=""', svg, count=1)
                dst.write_text(svg, encoding="utf-8")
            err = (r.stderr or "").replace(tmp.name, name)
            (done if r.returncode == 0 else failed).append({"src": name, "out": str(dst), "tool": "d2",
                                                            **({} if r.returncode == 0 else {"exit": r.returncode, "stderr": err[-800:],
                                                                                            "note": f"报错行号比源文件多 {len(pre)} 行（前面拼了主题和字号前言）"})})
        elif name.endswith(".wavedrom.json"):
            stem = name[: -len(".wavedrom.json")]
            dst = pdir / f"{stem}.svg"
            r = subprocess.run([which_node(), str(wavedrom_entry()), "-i", str(src), "-s", str(dst)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            ok_ = r.returncode == 0 and dst.exists()
            if ok_:
                recolor_wavedrom(dst, theme_color(deck, "--sf-ink", "#1C231F"))
            (done if ok_ else failed).append({"src": name, "out": str(dst), "tool": "wavedrom",
                                              **({} if ok_ else {"exit": r.returncode, "stderr": (r.stderr or r.stdout)[-800:]})})
        elif name.endswith(".drawio.svg"):
            dst = pdir / name.replace(".drawio.svg", ".svg")
            dst.write_bytes(src.read_bytes())
            done.append({"src": name, "out": str(dst), "tool": "copy"})
    return done, failed


def cmd_diagrams(args):
    deck = require_deck(args.deck)
    done, failed = render_diagrams(deck, args.only)
    if failed:
        raise CliError("E_PARTIAL_FAILURE", f"{len(failed)} 张图渲染失败", details={"done": done, "failed": failed},
                       suggestion="按 failed[].stderr 改对应源文件再跑")
    return emit_ok(args, {"rendered": done}, "\n".join(f"✓ {d['src']} → {d['out']}" for d in done) or "diagrams/ 里没有要渲染的图")


def cmd_lint(args):
    deck = require_deck(args.deck)
    slides = expand_slides(deck / "slides.md")
    report, total_issues = [], 0
    for n, s in enumerate(slides, 1):
        r = lint_slide(s)
        r["n"] = n
        r["file"] = os.path.relpath(s["file"], deck)
        total_issues += len(r["issues"])
        report.append(r)
    data = {"slides": report, "total": len(report), "issues": total_issues}
    if args.strict and total_issues:
        raise CliError("E_VERIFICATION_FAILED", f"{total_issues} 处版面问题", details=data, suggestion="按 issues 改页面再跑")
    lines = [f"{r['n']:>3} {r['title'][:30]:<30} " + ("; ".join(i["msg"] for i in r["issues"]) or "✓") for r in report]
    return emit_ok(args, data, "\n".join(lines))


def cmd_qa(args):
    deck = require_deck(args.deck)
    slides = parse_slide_spec(args.slides)
    res = run_qa(deck, slides, not args.no_shots, args.port)
    total_issues = sum(len(s.get("issues") or []) for s in res["slides"])
    res["issues"] = total_issues
    (deck / "qa" / "report.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.strict and total_issues:
        raise CliError("E_VERIFICATION_FAILED", f"{total_issues} 处出界/裁切", details=res, suggestion="看每页 issues 与截图修页面")
    lines = [f"{s['n']:>3} {s.get('title', '')[:30]:<30} " + (f"{len(s['issues'])} 处问题" if s.get("issues") else "✓") + (f"  {s['shot']}" if s.get("shot") else "")
             for s in res["slides"]]
    return emit_ok(args, res, "\n".join(lines))


def cmd_preview(args):
    out = Path(args.outdir).resolve()
    names = [t.strip() for t in args.themes.split(",")] if args.themes else [t["name"] for t in list_themes()]
    previews = {}
    for name in names:
        meta = theme_meta(name)
        deck = out / name
        build_deck(deck, name, f"主题预览：{meta['label']}", Writer(False))
        render_diagrams(deck)
        res = run_qa(deck, None, True, None)
        previews[name] = {"label": meta["label"], "desc": meta["desc"], "shots": [s["shot"] for s in res["slides"]],
                          "issues": sum(len(s.get("issues") or []) for s in res["slides"])}
    human = "\n".join(f"{k}（{v['label']}）：{len(v['shots'])} 张 → {Path(v['shots'][0]).parent if v['shots'] else ''}" for k, v in previews.items())
    return emit_ok(args, {"outdir": str(out), "previews": previews}, human)


def cmd_draft(args):
    pptx = Path(args.pptx).resolve()
    if not pptx.exists():
        raise CliError("E_NOT_FOUND", f"{pptx} 不存在")
    out = Path(args.out).resolve() if args.out else pptx.parent / "read"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("draft-*.png"):
        old.unlink()
    raw, reader, fallback = None, None, None
    if args.via in ("auto", "powerpoint"):
        try:
            raw, reader = read_draft_powerpoint(pptx, out, not args.no_render), "powerpoint"
        except CliError as e:
            if args.via == "powerpoint":
                raise
            fallback = {"message": e.message, "stderr": (e.details or {}).get("stderr", "")[-300:]}
    if raw is None:
        try:
            raw, reader = read_draft_xml(pptx), "xml"
        except CliError as e:
            if fallback:
                e.details = dict(e.details or {}, powerpoint=fallback)
            raise
    draft = normalize_draft(raw)
    draft["source"] = str(pptx)
    draft["reader"] = reader
    (out / "draft.json").write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    brief = [{"index": s["index"], "title": s["title"], "notes": s["notes"], "png": s["png"], "summary": s["summary"]}
             for s in draft["slides"]]
    data = {"json": str(out / "draft.json"), "aspect": draft["aspect"], "reader": reader, "slides": brief}
    head = ""
    if reader == "xml":
        data["reader_note"] = "没开 PowerPoint，直接读的文件内容：没有每页图片；字号是按母版推的近似值；只认直接设成红色的字"
        if fallback:
            data["fallback_reason"] = fallback
        head = f"（{data['reader_note']}" + (f"；PowerPoint 那条路失败：{fallback['message']}" if fallback else "") + "）\n\n"
    human = head + "\n\n".join(f"草稿第 {s['index']} 页：{s['title']}\n  " + ("\n  ".join(s["summary"]) or "（空白页）") + (f"\n  备注：{s['notes']}" if s["notes"] else "")
                               for s in brief)
    return emit_ok(args, data, human)


def read_draft_powerpoint(pptx, out, render):
    script = (DRAFT_PS.replace("__PPTX__", str(pptx).replace("'", "''"))
              .replace("__OUT__", str(out).replace("'", "''"))
              .replace("__RENDER__", "$true" if render else "$false"))
    code, stdout, stderr = run_ps(script, timeout=600)
    if code != 0 or not stdout.strip():
        raise CliError("E_EXTERNAL_TOOL", "PowerPoint 读草稿失败", details={"exit": code, "stderr": stderr[-1500:]},
                       suggestion="确认草稿能用 PowerPoint 正常打开；关掉正在编辑它的窗口再试；或用 --via xml 不开 PowerPoint 读")
    return json.loads(stdout.strip().splitlines()[-1])


def cmd_draft_template(args):
    out = Path(args.pptx).resolve()
    if out.suffix.lower() != ".pptx":
        raise CliError("E_VALIDATION", "输出文件要以 .pptx 结尾")
    if out.exists() and not args.force:
        raise CliError("E_VALIDATION", f"{out} 已存在", suggestion="换个文件名，或加 --force 覆盖")
    if args.dry_run:
        return emit_ok(args, {"pptx": str(out), "dry_run": True}, f"[预演] 将生成草稿模板 {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    code, stdout, stderr = run_ps(DRAFT_TEMPLATE_PS.replace("__OUT__", str(out).replace("'", "''")), timeout=300)
    if code != 0 or not out.exists():
        raise CliError("E_EXTERNAL_TOOL", "PowerPoint 生成草稿模板失败", details={"exit": code, "stderr": stderr[-1500:]})
    return emit_ok(args, {"pptx": str(out), "dry_run": False}, f"已生成草稿模板 {out}")


def cmd_export(args):
    deck = require_deck(args.deck)
    out = Path(args.out).resolve() if args.out else deck / f"{deck.name}.pdf"
    r = subprocess.run([which_node(), str(slidev_entry()), "export", "slides.md", "--output", str(out),
                        "--executable-path", find_chrome(), "--timeout", "120000"],
                       cwd=str(deck), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, NODE_PATH=str(npm_root())), timeout=1800)
    if r.returncode != 0 or not out.exists():
        raise CliError("E_EXTERNAL_TOOL", "导出失败", details={"exit": r.returncode, "stderr": (r.stderr or r.stdout)[-1500:]})
    return emit_ok(args, {"pdf": str(out)}, f"已导出 {out}")


# ---------------------------------------------------------------- 入口

def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="输出 JSON 信封")
    common.add_argument("--format", choices=["json", "text"], default="text", help="--format json 等价 --json")
    p = Parser(prog="sf", description="slide-flow 幻灯片工具链。LLMs/agents: run 'sf.py --ai-help' for usage guidance.",
               parents=[common])
    sub = p.add_subparsers(dest="cmd", required=True, parser_class=Parser)
    sub.add_parser("doctor", parents=[common], help="检查依赖")
    t = sub.add_parser("themes", parents=[common], help="列出主题 / 设默认主题")
    t.add_argument("--set-default")
    i = sub.add_parser("init", parents=[common], help="从模板建工程")
    i.add_argument("deck")
    i.add_argument("--theme")
    i.add_argument("--title")
    i.add_argument("--title-file")
    i.add_argument("--force", action="store_true")
    i.add_argument("--dry-run", action="store_true")
    pv = sub.add_parser("preview-themes", parents=[common], help="每个主题出一份示例截图")
    pv.add_argument("outdir")
    pv.add_argument("--themes")
    d = sub.add_parser("draft", parents=[common], help="读 PowerPoint 草稿")
    d.add_argument("pptx")
    d.add_argument("--out")
    d.add_argument("--no-render", action="store_true")
    d.add_argument("--via", choices=["auto", "powerpoint", "xml"], default="auto")
    dt = sub.add_parser("draft-template", parents=[common], help="生成带画法示范的空白草稿")
    dt.add_argument("pptx")
    dt.add_argument("--force", action="store_true")
    dt.add_argument("--dry-run", action="store_true")
    dg = sub.add_parser("diagrams", parents=[common], help="渲染图")
    dg.add_argument("deck")
    dg.add_argument("--only")
    l = sub.add_parser("lint", parents=[common], help="版面规则检查")
    l.add_argument("deck")
    l.add_argument("--strict", action="store_true")
    q = sub.add_parser("qa", parents=[common], help="截图与出界检查")
    q.add_argument("deck")
    q.add_argument("--slides")
    q.add_argument("--no-shots", action="store_true")
    q.add_argument("--port", type=int)
    q.add_argument("--strict", action="store_true")
    e = sub.add_parser("export", parents=[common], help="导出 PDF")
    e.add_argument("deck")
    e.add_argument("--out")
    return p


HANDLERS = {"doctor": cmd_doctor, "themes": cmd_themes, "init": cmd_init, "preview-themes": cmd_preview,
            "draft": cmd_draft, "draft-template": cmd_draft_template, "diagrams": cmd_diagrams, "lint": cmd_lint, "qa": cmd_qa, "export": cmd_export}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    head = argv[: argv.index("--")] if "--" in argv else argv
    if "--ai-help" in head:
        sys.stdout.write(AI_HELP)
        return 0
    args = build_parser().parse_args(argv)
    if args.format == "json":
        args.json = True
    try:
        return HANDLERS[args.cmd](args)
    except KeyboardInterrupt as e:
        return emit_err(args.json, "E_INTERRUPTED", "被中断", exit_code=1)
    except CliError as e:
        return emit_err(args.json, e.code, e.message, e.details, e.suggestion, e.retryable,
                        exit_code=2 if e.code == "E_VALIDATION" else 1)
    except subprocess.TimeoutExpired as e:
        return emit_err(args.json, "E_EXTERNAL_TOOL", f"外部命令超时：{e.cmd[0] if e.cmd else ''}")
    except Exception as e:
        return emit_err(args.json, classify(e), f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    sys.exit(main())
