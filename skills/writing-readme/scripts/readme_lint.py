# 结构: vibe-scripts/standard
# 用途: README 去 AI 味检查器 —— 结构层 + 文体层双检,中英双语规则包,超阈值非零退出
# 用法: py -3 readme_lint.py check README.md
#       py -3 readme_lint.py diff README.md          # 只报这一版新引入的命中
#       py -3 readme_lint.py rules --lang zh
#       py -3 readme_lint.py selftest
# 原始需求: 写一个中英双语的 README 去 AI 味检查器,规则包 JSON,结构检查 + 文体检查,
#           超阈值非零退出,带 --diff 只报新增命中。市面 slopster/deslop/vale-llm-slop
#           只做英文文体、不碰文档结构;slop-gate 的中文包只打公文腔。此脚本补两个空:
#           中文技术写作指纹 + README 结构层。

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass, field

# ===== 1 配置/常量 =====

RULES_DIR = pathlib.Path(__file__).resolve().parent.parent / "rules"

# 默认只跑中文包。英文包要显式 --lang en(或 --lang both),因为绝大多数文档是单语的,
# 两个包一起跑等于把另一半规则空转一遍。跑错包会静默通过,所以下面有 lang_hint 兜底。
DEFAULT_LANG = "zh"

# 结构阈值。改这里就能整体收紧/放松,不必动检查函数。
CONFIG = {
    "evidence_within_lines": 45,   # 首个代码块/图片必须出现在前多少行内
    "max_preamble_lines": 15,      # 第一个代码块之前允许多少行正文
    "max_total_lines": 220,        # 超过就该往 docs/ 拆
    "max_bold_ratio": 0.12,        # 加粗数 / 正文行数
    "min_bold_hits": 5,            # 少于这么多处加粗就不看比例(短文档上比例噪声太大)
    "install_within_lines": 25,    # 装法直接摆在开头(无标题)也算数
    "max_tables": 4,               # 表格张数
    "max_paragraph_lines": 8,      # 单个自然段最长行数
    "install_before_ratio": 0.6,   # 安装段必须出现在全文前 60%
    "long_doc_needs_links": 150,   # 超过这么长却没有 docs/ 出口就报
}

CJK_RE = re.compile(r"[一-鿿]")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(|<img\s")
BOLD_RE = re.compile(r"\*\*[^*\n]+\*\*")
INSTALL_RE = re.compile(
    r"(?:install|installation|quick\s*start|getting\s*started|setup"
    r"|安装|快速开始|上手|开始使用|^#{1,6}\s*装\s*$)", re.I | re.M)
DOCS_LINK_RE = re.compile(r"\]\((?!https?://)[^)]*\.md[^)]*\)")

SEV_ORDER = {"error": 0, "warn": 1}
EXIT_OK, EXIT_FOUND, EXIT_ERROR = 0, 1, 2


# ===== 2 Port：接口定义 =====

class SourceReader:
    """取一份 README 文本的能力。工作区、git 版本、内存都是它的实现。"""

    def read(self, path: str) -> str:
        raise NotImplementedError


# ===== 3 Core：纯逻辑（不 open、不跑子进程、不 print）=====

@dataclass
class Finding:
    rule_id: str
    name: str
    sev: str
    count: int
    limit: int
    msg: str
    fix: str
    kind: str = "prose"
    lines: list[int] = field(default_factory=list)
    samples: list[str] = field(default_factory=list)

    @property
    def over(self) -> int:
        return self.count - self.limit


@dataclass
class Doc:
    path: str
    lines: list[str]        # 原始行
    prose: list[str]        # 掩码后行(代码/链接/行内码被抹成空格),行号与 lines 对齐


def mask_code(lines: list[str]) -> list[str]:
    """把代码块、行内码、URL、HTML 注释抹成空格,行号保持不变。

    文体规则只该扫人写的散文。终端输出里的 `——` 是工具自己打印的,算到作者头上是误报。
    """
    out: list[str] = []
    in_fence = False
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
            continue
        s = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), line)
        s = re.sub(r"https?://\S+", lambda m: " " * len(m.group(0)), s)
        s = re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), s)
        s = re.sub(r"\]\([^)]*\)", lambda m: " " * len(m.group(0)), s)
        out.append(s)
    return out


def make_doc(path: str, text: str) -> Doc:
    lines = text.splitlines()
    return Doc(path=path, lines=lines, prose=mask_code(lines))


def detect_langs(doc: Doc) -> list[str]:
    """按正文里的汉字占比决定跑哪些语言包。双语文档两包都跑。"""
    body = "\n".join(doc.prose)
    cjk = len(CJK_RE.findall(body))
    letters = len(re.findall(r"[A-Za-z]", body))
    langs = []
    if cjk >= 20:
        langs.append("zh")
    if letters >= 200 and (cjk == 0 or letters > cjk * 2):
        langs.append("en")
    return langs or ["zh", "en"]


@dataclass
class Block:
    """一个自然段:掩码后连续非空行拼成一串,附字符偏移→行号的对照。

    必须按段扫而不是按行扫,因为文档是硬折行的,「not just X, but Y」和
    「不是X，是Y」经常跨行,按行扫会整条漏掉。
    """
    text: str
    marks: list[tuple[int, int]]        # (段内字符偏移, 原文行号)

    def lineno(self, pos: int) -> int:
        no = self.marks[0][1]
        for off, n in self.marks:
            if off > pos:
                break
            no = n
        return no


def build_blocks(prose: list[str]) -> list[Block]:
    blocks: list[Block] = []
    buf: list[str] = []
    marks: list[tuple[int, int]] = []
    off = 0

    def flush():
        nonlocal buf, marks, off
        if buf:
            blocks.append(Block(" ".join(buf), marks))
        buf, marks, off = [], [], 0

    for no, line in enumerate(prose, 1):
        s = line.strip()
        if not s:
            flush()
            continue
        marks.append((off, no))
        buf.append(s)
        off += len(s) + 1
    flush()
    return blocks


def compile_rule(rule: dict, pack: dict) -> re.Pattern:
    flags = 0
    for ch in str(rule.get("flags", pack.get("flags", ""))):
        flags |= {"i": re.I, "m": re.M, "s": re.S}.get(ch, 0)
    try:
        return re.compile(rule["pattern"], flags)
    except re.error as exc:                           # 规则包写坏了要说清是哪条
        raise ValueError(f"规则 {rule['id']} 的正则无法编译: {exc}") from exc


def lang_hint(doc: Doc, langs: list[str]) -> str | None:
    """跑的包和文档语言对不上时给一句话。

    这是默认单包最危险的地方:拿中文包扫英文文档,一条都不命中,报「干净」。
    静默通过比报错难发现,所以宁可多说一句。
    """
    detected = detect_langs(doc)
    missing = [d for d in detected if d not in langs]
    if not missing:
        return None
    names = {"zh": "中文", "en": "英文"}
    return ("这篇看着有{0}内容,但没跑{0}包 —— 那部分规则一条都没查。加 --lang {1}"
            .format("/".join(names[m] for m in missing), missing[0]))


def check_prose(doc: Doc, pack: dict) -> list[Finding]:
    """按一个语言包扫全文。每条规则汇总成一个 Finding(带命中次数和样例行)。

    scope=line 的规则按行扫(用于 ^ 锚定的);其余按自然段扫,以跨过硬折行。
    """
    found: list[Finding] = []
    blocks = build_blocks(doc.prose)
    for rule in pack["rules"]:
        pat = compile_rule(rule, pack)
        hits: list[tuple[int, str]] = []
        if rule.get("scope") == "line":
            for no, line in enumerate(doc.prose, 1):
                for m in pat.finditer(line):
                    hits.append((no, m.group(0).strip()))
        else:
            for blk in blocks:
                for m in pat.finditer(blk.text):
                    hits.append((blk.lineno(m.start()), m.group(0).strip()))
        limit = int(rule.get("max", 0))
        if len(hits) > limit:
            found.append(Finding(
                rule_id=rule["id"], name=rule["name"], sev=rule.get("sev", "warn"),
                count=len(hits), limit=limit, msg=rule["msg"], fix=rule["fix"],
                kind="prose",
                lines=[n for n, _ in hits[:6]],
                samples=[(t[:58] + "…") if len(t) > 58 else t for _, t in hits[:3]],
            ))
    return found


# --- 结构检查：每个都是「读 Doc 出 Finding」的纯函数,注册在下面的表里 ---

def _first_evidence_line(doc: Doc) -> int | None:
    for no, line in enumerate(doc.lines, 1):
        if FENCE_RE.match(line) or IMAGE_RE.search(line):
            return no
    return None


def _prose_line_count(doc: Doc) -> int:
    return sum(1 for s in doc.prose if s.strip() and not HEADING_RE.match(s))


def chk_evidence_first(doc: Doc) -> list[Finding]:
    at = _first_evidence_line(doc)
    limit = CONFIG["evidence_within_lines"]
    if at is not None and at <= limit:
        return []
    where = "全文都没有" if at is None else f"第 {at} 行才出现"
    return [Finding(
        "struct-evidence-first", "首屏没有可看的证据", "error",
        at or 999, limit, kind="structure",
        msg=f"代码块/截图/终端输出{where}。读者判断要不要用一个工具,靠的是看见它跑起来的样子。",
        fix="把一段真实输出、一张截图或一条能直接抄的命令提到前 45 行以内",
    )]


def chk_preamble(doc: Doc) -> list[Finding]:
    at = _first_evidence_line(doc)
    if at is None:
        return []
    n = sum(1 for s in doc.prose[:at - 1] if s.strip() and not HEADING_RE.match(s))
    limit = CONFIG["max_preamble_lines"]
    if n <= limit:
        return []
    return [Finding(
        "struct-preamble", "说理跑在使用前面", "error", n, limit, kind="structure",
        msg=f"第一个代码块之前有 {n} 行正文。读者还没跑过一次,就先读了 {n} 行设计论证。",
        fix="先给能抄的东西,理由压到后面;超过三行的「为什么这样设计」搬去 docs/",
    )]


def chk_total_length(doc: Doc) -> list[Finding]:
    n = len(doc.lines)
    limit = CONFIG["max_total_lines"]
    if n <= limit:
        return []
    return [Finding(
        "struct-length", "README 吃下了整本手册", "warn", n, limit, kind="structure",
        msg=f"全文 {n} 行。排错、回滚、卸载、并发语义这类内容属于手册,不属于 README。",
        fix="按读者流失率切:README 只留「装上、跑起来、凭什么用它」,其余进 docs/",
    )]


def chk_bold_density(doc: Doc) -> list[Finding]:
    bold = sum(len(BOLD_RE.findall(s)) for s in doc.prose)
    body = _prose_line_count(doc)
    if body == 0:
        return []
    ratio = bold / body
    limit = CONFIG["max_bold_ratio"]
    if ratio <= limit or bold < CONFIG["min_bold_hits"]:
        return []
    return [Finding(
        "struct-bold", "加粗当标点用", "error", bold, int(limit * body), kind="structure",
        msg=f"{body} 行正文里有 {bold} 处加粗(每 {body / bold:.1f} 行一处)。全都强调等于都不强调,"
            f"而且这是中文 LLM 写作最容易被认出的排版特征。",
        fix="每节最多留一处加粗,只用于术语首次出现",
    )]


def chk_table_count(doc: Doc) -> list[Finding]:
    n = sum(1 for s in doc.lines if TABLE_SEP_RE.match(s) and "|" in s)
    limit = CONFIG["max_tables"]
    if n <= limit:
        return []
    return [Finding(
        "struct-tables", "表格代替叙事", "warn", n, limit, kind="structure",
        msg=f"{n} 张表。表格是给人查的(安装方式、参数对照),不是用来讲道理的;"
            f"用表格组织论证是模型压缩信息的习惯,不是人的。",
        fix="留下真正供查阅的那几张,讲道理的改回句子",
    )]


def chk_wall_of_text(doc: Doc) -> list[Finding]:
    limit = CONFIG["max_paragraph_lines"]
    walls, run, start = [], 0, 0
    for no, s in enumerate(doc.prose, 1):
        if s.strip() and not HEADING_RE.match(s) and not s.lstrip().startswith(("-", "*", "|", ">")):
            if run == 0:
                start = no
            run += 1
        else:
            if run > limit:
                walls.append(start)
            run = 0
    if run > limit:
        walls.append(start)
    if not walls:
        return []
    return [Finding(
        "struct-wall", "长段落", "warn", len(walls), 0, kind="structure",
        lines=walls[:6],
        msg=f"{len(walls)} 个自然段超过 {limit} 行。屏幕上的长段落读者会整段跳过。",
        fix="拆段,或把其中的枚举改成列表",
    )]


def chk_install_position(doc: Doc) -> list[Finding]:
    """看装法第一次出现在哪。标题、正文、代码块里的 pip/npm/plugin install 都算数——
    读者不在乎它挂在什么标题下,只在乎翻多久能找到。"""
    total = len(doc.lines) or 1
    for no, s in enumerate(doc.lines, 1):
        if not INSTALL_RE.search(s):
            continue
        ratio = no / total
        if no <= CONFIG["install_within_lines"] or ratio <= CONFIG["install_before_ratio"]:
            return []
        return [Finding(
            "struct-install-pos", "安装段埋太深", "warn",
            int(ratio * 100), int(CONFIG["install_before_ratio"] * 100),
            kind="structure", lines=[no],
            msg=f"装法到全文 {ratio:.0%} 处才出现。想用的人要先翻过大半篇才找得到怎么装。",
            fix="提到前 60% 以内,最好紧跟在证据块后面",
        )]
    return [Finding(
        "struct-install-pos", "没有安装段", "warn", 0, 1, kind="structure",
        msg="全文找不到装法(安装/快速开始/pip/npm/plugin install)。",
        fix="加一节,给出能直接粘贴的两行命令",
    )]


def chk_docs_exit(doc: Doc) -> list[Finding]:
    if len(doc.lines) <= CONFIG["long_doc_needs_links"]:
        return []
    if any(DOCS_LINK_RE.search(s) for s in doc.lines):
        return []
    return [Finding(
        "struct-no-exit", "没有出口", "warn", len(doc.lines),
        CONFIG["long_doc_needs_links"], kind="structure",
        msg="长文档里一条指向 docs/ 的相对链接都没有,说明细节全堆在正文。",
        fix="给每个模块留一个「细节见 docs/xxx.md」的出口",
    )]


STRUCTURE_CHECKS = {
    "evidence-first": chk_evidence_first,
    "preamble": chk_preamble,
    "length": chk_total_length,
    "bold": chk_bold_density,
    "tables": chk_table_count,
    "wall": chk_wall_of_text,
    "install-pos": chk_install_position,
    "docs-exit": chk_docs_exit,
}


def analyze(doc: Doc, packs: list[dict], skip: set[str] | None = None) -> list[Finding]:
    skip = skip or set()
    out: list[Finding] = []
    for name, fn in STRUCTURE_CHECKS.items():
        if name not in skip:
            out.extend(fn(doc))
    for pack in packs:
        out.extend(check_prose(doc, pack))
    out.sort(key=lambda f: (SEV_ORDER.get(f.sev, 9), -f.over))
    return out


def new_findings(old: list[Finding], new: list[Finding]) -> list[Finding]:
    """只留这一版新引入的量(借 slop-diff 的思路:忽略行号漂移,按规则比次数)。"""
    before = {f.rule_id: f.count for f in old}
    out = []
    for f in new:
        was = before.get(f.rule_id, 0)
        if f.count > was:
            g = Finding(**{**f.__dict__})
            g.limit = was
            out.append(g)
    return out


def summarize(findings: list[Finding]) -> dict:
    return {
        "error": sum(1 for f in findings if f.sev == "error"),
        "warn": sum(1 for f in findings if f.sev == "warn"),
        "structure": sum(1 for f in findings if f.kind == "structure"),
        "prose": sum(1 for f in findings if f.kind == "prose"),
    }


# ===== 4 Adapter：实现 + 注册 =====

class FileReader(SourceReader):
    def read(self, path: str) -> str:
        return pathlib.Path(path).read_text(encoding="utf-8")


class GitHeadReader(SourceReader):
    """读该文件在 HEAD 里的版本,用于 diff。仓库里还没有这个文件时返回空串。"""

    def __init__(self, rev: str = "HEAD"):
        self.rev = rev

    def read(self, path: str) -> str:
        p = pathlib.Path(path).resolve()
        r = subprocess.run(["git", "-C", str(p.parent), "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"不在 git 仓库里: {p}")
        root = pathlib.Path(r.stdout.strip())
        rel = p.relative_to(root).as_posix()
        r = subprocess.run(["git", "-C", str(root), "show", f"{self.rev}:{rel}"],
                           capture_output=True)
        if r.returncode != 0:
            return ""
        return r.stdout.decode("utf-8", errors="replace")


class MemoryReader(SourceReader):
    """mock:直接吃字符串,给 selftest 用。"""

    def __init__(self, text: str = ""):
        self.text = text

    def read(self, path: str) -> str:
        return self.text


READERS = {"file": FileReader, "git": GitHeadReader, "memory": MemoryReader}


def load_packs(langs: list[str]) -> list[dict]:
    packs = []
    for lang in langs:
        f = RULES_DIR / f"{lang}.json"
        if not f.exists():
            raise FileNotFoundError(f"找不到规则包: {f}")
        packs.append(json.loads(f.read_text(encoding="utf-8")))
    return packs


# ===== 5 App：命令表 + CLI 入口（只有这一层负责打印和退出码）=====

def _print_findings(findings: list[Finding], title: str) -> None:
    if not findings:
        print(f"{title}: 干净,没有超阈值的命中。")
        return
    print(f"\n{title}")
    print("=" * 74)
    for f in findings:
        mark = "!!" if f.sev == "error" else " ·"
        where = ""
        if f.lines:
            where = "  行 " + ", ".join(str(n) for n in f.lines)
            if f.count > len(f.lines):
                where += " …"
        if f.kind == "structure":
            head = f"{mark} [{f.rule_id}] {f.name}"
        else:
            head = f"{mark} [{f.rule_id}] {f.name}  {f.count} 次(允许 {f.limit}){where}"
        print(head)
        print(f"     {f.msg}")
        if f.samples:
            print(f"     例: " + " / ".join(repr(s) for s in f.samples))
        print(f"     改法: {f.fix}")
    s = summarize(findings)
    print("-" * 74)
    print(f"合计 error {s['error']} · warn {s['warn']}   "
          f"(结构 {s['structure']} · 文体 {s['prose']})")


def _exit_code(findings: list[Finding], strict: bool) -> int:
    if any(f.sev == "error" for f in findings):
        return EXIT_FOUND
    if strict and findings:
        return EXIT_FOUND
    return EXIT_OK


def _prepare(args) -> tuple[Doc, list[dict]]:
    reader = READERS[args.source]()
    doc = make_doc(args.path, reader.read(args.path))
    langs = ["zh", "en"] if args.lang == "both" else [args.lang or DEFAULT_LANG]
    return doc, load_packs(langs)


def cmd_check(args) -> int:
    doc, packs = _prepare(args)
    findings = analyze(doc, packs, skip=set(args.skip or []))
    langs = ", ".join(p["display"] for p in packs)
    _print_findings(findings, f"{args.path}  ({len(doc.lines)} 行, 规则包: {langs})")
    hint = lang_hint(doc, [p["lang"] for p in packs])
    if hint:
        print(f"\n提示: {hint}")
    return _exit_code(findings, args.strict)


def cmd_diff(args) -> int:
    doc, packs = _prepare(args)
    old_text = GitHeadReader(args.rev).read(args.path)
    if not old_text:
        print(f"{args.rev} 里没有这个文件,按全量检查处理。")
        return cmd_check(args)
    skip = set(args.skip or [])
    old = analyze(make_doc(args.path, old_text), packs, skip=skip)
    new = analyze(doc, packs, skip=skip)
    delta = new_findings(old, new)
    _print_findings(delta, f"{args.path}  相对 {args.rev} 新增的 AI 味")
    if not delta:
        print(f"(存量 {len(old)} 项未计入;要看全部跑 check)")
    return _exit_code(delta, args.strict)


def cmd_rules(args) -> int:
    for pack in load_packs([args.lang] if args.lang else ["zh", "en"]):
        print(f"\n== {pack['display']} ({pack['lang']}) — {len(pack['rules'])} 条")
        print(f"   {pack['note']}")
        for r in pack["rules"]:
            print(f"   [{r['sev']:5}] {r['id']:24} 允许 {r.get('max', 0)}  {r['name']}")
    print(f"\n== 结构检查 — {len(STRUCTURE_CHECKS)} 条(与语言无关)")
    for name, fn in STRUCTURE_CHECKS.items():
        print(f"   {name:16} {(fn.__doc__ or fn.__name__)}")
    print(f"\n阈值: {json.dumps(CONFIG, ensure_ascii=False)}")
    return EXIT_OK


def cmd_selftest(args) -> int:
    """只跑 Core 的纯函数,不碰磁盘。"""
    bad = ("# 工具\n\n本项目是一个用于处理数据的工具——它不仅是一个解析器,更是一个框架。\n"
           "值得注意的是,这不是简单的封装,而是完整的方案——为此做了三层抽象。\n"
           "让我们从安装开始——先装依赖,再跑起来——然后看输出。\n"
           + "说明文字。\n" * 20)
    good = ("# 工具\n\n把串口日志转成 CSV。\n\n```bash\npy -3 t.py log.txt\n```\n\n"
            "## 安装\n\n```bash\npip install t\n```\n\n细节见 [用法](docs/usage.md)。\n")
    packs = load_packs(["zh"])
    cases = []

    d = make_doc("bad.md", bad)
    ids = {f.rule_id for f in analyze(d, packs)}
    for want in ("zh-emdash", "zh-not-just", "zh-definition-opener",
                 "struct-evidence-first"):
        cases.append((f"脏样本命中 {want}", want in ids))

    d2 = make_doc("good.md", good)
    f2 = analyze(d2, packs)
    cases.append(("干净样本无 error", not any(f.sev == "error" for f in f2)))

    masked = mask_code(["文本 ——", "```", "输出里的 —— 不算", "```", "又一个 ——"])
    cases.append(("代码块被掩码", masked[2].strip() == ""))
    cases.append(("掩码不改行号", len(masked) == 5))

    inline = mask_code(["用 `a——b` 举例"])
    cases.append(("行内码被掩码", "——" not in inline[0]))

    old = [Finding("x", "x", "warn", 3, 0, "", "")]
    new = [Finding("x", "x", "warn", 5, 0, "", ""), Finding("y", "y", "warn", 1, 0, "", "")]
    delta = {f.rule_id for f in new_findings(old, new)}
    cases.append(("diff 只报新增", delta == {"x", "y"}))
    cases.append(("diff 不报持平", not new_findings(new, new)))

    cases.append(("语言探测 zh", "zh" in detect_langs(make_doc("a", "中文" * 30))))
    cases.append(("语言探测 en", "en" in detect_langs(make_doc("a", "word " * 60))))

    # 硬折行:命中跨越换行,按行扫会漏
    wrapped = make_doc("w.md", "# t\n\n这套东西不是一个封装,\n而是完整的方案。这里不是终点,\n而是起点。\n")
    ids_w = {f.rule_id for f in check_prose(wrapped, packs[0])}
    cases.append(("跨行也能命中", "zh-negation-pivot" in ids_w))
    blk = build_blocks(["第一行", "第二行", "", "第四段"])
    cases.append(("段落切分", len(blk) == 2 and blk[0].lineno(4) == 2))

    # 短文档上少量加粗不该报(比例在小分母上噪声太大)
    tiny = make_doc("t.md", "# t\n\n一句**强调**的话。\n再一句**强调**。\n")
    cases.append(("短文档少量加粗不报",
                  not any(f.rule_id == "struct-bold" for f in chk_bold_density(tiny))))
    # 装法直接摆在开头(没有标题)是最好的位置,不该报
    top = make_doc("i.md", "# t\n\n```\npip install t\n```\n\n## 用法\n\n跑起来。\n")
    cases.append(("开头就给装法不报",
                  not chk_install_position(top)))
    # 装法在代码块里、标题叫什么都不该影响判定
    heading = make_doc("h.md", "# t\n\n介绍。\n\n## 装\n\n```\npip install t\n```\n" + "正文。\n" * 30)
    cases.append(("装法在非常规标题下也认",
                  not chk_install_position(heading)))
    deep = make_doc("d.md", "# t\n\n" + "正文。\n" * 60 + "\n## 安装\n\npip install t\n")
    cases.append(("装法埋太深要报",
                  any(f.rule_id == "struct-install-pos" for f in chk_install_position(deep))))

    # 默认单包最危险的失败:拿中文包扫英文文档,一条不命中,报「干净」
    en_doc = make_doc("e.md", "# t\n\n" + "This tool is a comprehensive solution. " * 20)
    cases.append(("英文文档用 zh 包会提醒", bool(lang_hint(en_doc, ["zh"]))))
    zh_doc = make_doc("z.md", "# t\n\n" + "这是一段中文说明文字。" * 20)
    cases.append(("中文文档用 zh 包不啰嗦", lang_hint(zh_doc, ["zh"]) is None))

    en = load_packs(["en"])[0]
    up = make_doc("u.md", "# t\n\nLet's dive in. Whether you're new or old, In conclusion it works.\n")
    ids_u = {f.rule_id for f in check_prose(up, en)}
    cases.append(("英文大小写不敏感",
                  {"en-lets-dive", "en-whether-youre", "en-conclusion"} <= ids_u))

    ok = 0
    for name, passed in cases:
        print(f"  {'PASS' if passed else 'FAIL'}  {name}")
        ok += bool(passed)
    print(f"\n{ok}/{len(cases)} 通过")
    return EXIT_OK if ok == len(cases) else EXIT_FOUND


COMMANDS = {
    "check": cmd_check,
    "diff": cmd_diff,
    "rules": cmd_rules,
    "selftest": cmd_selftest,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="README 去 AI 味检查器:结构层 + 文体层,中英双语。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="退出码: 0 通过 / 1 有超阈值命中 / 2 出错")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("path", help="README 路径")
        sp.add_argument("--lang", choices=["zh", "en", "both"],
                        help=f"跑哪个语言包(默认 {DEFAULT_LANG};英文文档要显式给 en)")
        sp.add_argument("--strict", action="store_true", help="warn 也算不通过")
        sp.add_argument("--skip", nargs="*", metavar="CHECK",
                        help=f"跳过结构检查: {' '.join(STRUCTURE_CHECKS)}")
        sp.add_argument("--source", choices=list(READERS), default="file",
                        help=argparse.SUPPRESS)

    common(sub.add_parser("check", help="全量检查"))
    d = sub.add_parser("diff", help="只报相对 git 版本新增的命中")
    common(d)
    d.add_argument("--rev", default="HEAD", help="比对基准(默认 HEAD)")
    r = sub.add_parser("rules", help="列出规则包与阈值")
    r.add_argument("--lang", choices=["zh", "en"])
    sub.add_parser("selftest", help="跑 Core 纯函数自检")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.cmd](args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"出错: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
