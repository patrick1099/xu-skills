#!/usr/bin/env python3
"""curating-memory 的久未整理提醒 hook(SessionStart)。纯 stdlib、只提醒不自动整理。"""
import sys, json, glob, os
from datetime import date
from pathlib import Path

STALE_DAYS = 30
STAMP = ".curated"

def _parse_stamp(p):
    try:
        txt = Path(p).read_text(encoding="utf-8").strip().splitlines()[0].strip()
        y, m, d = (int(x) for x in txt.split("-"))
        return date(y, m, d)
    except Exception:
        return None

def stale_stores(root, today, stale_days=STALE_DAYS):
    out = []
    for mem in glob.glob(os.path.join(root, "*", "memory")):
        stamp = os.path.join(mem, STAMP)
        if not os.path.isfile(stamp):
            continue  # 无基线 → 静默
        d = _parse_stamp(stamp)
        if d is None:
            continue
        days = (today - d).days
        if days > stale_days:
            out.append((mem, days))
    return out

def _projects_root():
    return str(Path.home() / ".claude" / "projects")

def main(argv):
    if len(argv) > 1 and argv[1] == "selftest":
        return _selftest()
    try:
        json.load(sys.stdin)   # 读入 SessionStart 负载,内容可忽略
    except Exception:
        pass
    stale = stale_stores(_projects_root(), date.today())
    if not stale:
        return 0  # 静默
    names = ", ".join(f"{Path(m).parent.name}({days}天)" for m, days in stale)
    ctx = (f"[记忆整理提醒] 有记忆库距上次整理已超 {STALE_DAYS} 天:{names}。"
           f"需要时可用 curating-memory skill 整理(会先出计划、逐批批准,不自动改)。")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": ctx}}))
    return 0

def _selftest():
    import tempfile, shutil
    from datetime import timedelta
    root = tempfile.mkdtemp()
    try:
        today = date(2026, 7, 2)
        def mk(name, stamp_date):
            mem = os.path.join(root, name, "memory")
            os.makedirs(mem)
            if stamp_date is not None:
                Path(os.path.join(mem, STAMP)).write_text(stamp_date.isoformat(), encoding="utf-8")
        mk("fresh", today - timedelta(days=29))    # 未超期
        mk("stale", today - timedelta(days=31))    # 超期
        mk("nostamp", None)                        # 无基线 → 静默
        res = {Path(m).parent.name for m, _ in stale_stores(root, today)}
        assert res == {"stale"}, f"got {res}"

        payload = {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                          "additionalContext": "记忆整理提醒:测试"}}
        s = json.dumps(payload)   # 必须与 main() 用同一种调用:不传 ensure_ascii=False
        s.encode("ascii")         # ensure_ascii=True 下应为纯 ASCII;抛异常即回归
        assert "\\u" in s, "中文应被转义"

        print("selftest OK"); return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
