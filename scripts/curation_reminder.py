#!/usr/bin/env python3
"""curating-memory 的久未整理提醒 hook(SessionStart)。纯 stdlib、只提醒不自动整理。

盯的对象随体制走:
  - 装了 hub(`~/.hub/config.toml` 指得到金库) → 只看金库 `<vault>/shared/memory/.curated`,
    因为金库才是记忆的唯一活源;
  - 没装 hub → 回退旧行为,扫 `~/.claude/projects/*/memory/.curated`。
两种情况都是「没有戳 = 没基线 → 静默」,只提醒、绝不自动整理。
"""
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


def vault_from_config(cfg_path):
    """从 ~/.hub/config.toml 读金库路径。读不到/没配 → None(不是错误,是没装 hub)。"""
    try:
        raw = Path(cfg_path).read_text(encoding="utf-8")
    except Exception:
        return None
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("["):
            break             # 进了别的 table:vault 只认根表里的那个
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        if key.strip() != "vault":
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        return val or None
    return None


def stores_to_check(cfg_path, projects_root):
    """返回 [(标签, memory 目录)]。金库在 → 只查金库;否则回退旧扫描。"""
    vault = vault_from_config(cfg_path)
    if vault:
        shared = Path(vault) / "shared" / "memory"
        if shared.is_dir():
            return [("金库 shared/memory", str(shared))]
    return [(Path(m).parent.name, m) for m in glob.glob(os.path.join(projects_root, "*", "memory"))]


def stale_entries(cfg_path, projects_root, today, stale_days=STALE_DAYS):
    out = []
    for label, mem in stores_to_check(cfg_path, projects_root):
        stamp = os.path.join(mem, STAMP)
        if not os.path.isfile(stamp):
            continue  # 无基线 → 静默
        d = _parse_stamp(stamp)
        if d is None:
            continue
        days = (today - d).days
        if days > stale_days:
            out.append((label, days))
    return out


def _hub_config():
    return str(Path.home() / ".hub" / "config.toml")


def _projects_root():
    return str(Path.home() / ".claude" / "projects")


def main(argv):
    if len(argv) > 1 and argv[1] == "selftest":
        return _selftest()
    try:
        json.load(sys.stdin)   # 读入 SessionStart 负载,内容可忽略
    except Exception:
        pass
    stale = stale_entries(_hub_config(), _projects_root(), date.today())
    if not stale:
        return 0  # 静默
    names = ", ".join(f"{label}({days}天)" for label, days in stale)
    ctx = (f"[记忆整理提醒] 距上次整理已超 {STALE_DAYS} 天:{names}。"
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
        projects = os.path.join(root, "projects")
        os.makedirs(projects)

        def mk_project(name, stamp_date):
            mem = os.path.join(projects, name, "memory")
            os.makedirs(mem)
            if stamp_date is not None:
                Path(os.path.join(mem, STAMP)).write_text(stamp_date.isoformat(), encoding="utf-8")

        def mk_vault(name, stamp_date):
            shared = os.path.join(root, name, "shared", "memory")
            os.makedirs(shared)
            if stamp_date is not None:
                Path(os.path.join(shared, STAMP)).write_text(stamp_date.isoformat(), encoding="utf-8")
            cfg = os.path.join(root, f"config-{name}.toml")
            Path(cfg).write_text(
                f'vault = "{os.path.join(root, name).replace(os.sep, "/")}"\n'
                f'host = "testbox"\n', encoding="utf-8")
            return cfg

        mk_project("fresh", today - timedelta(days=29))    # 未超期
        mk_project("stale", today - timedelta(days=31))    # 超期
        mk_project("nostamp", None)                        # 无基线 → 静默

        missing_cfg = os.path.join(root, "no-such-config.toml")

        # 1) 没装 hub → 回退旧扫描,只报超期那个项目
        res = {lab for lab, _ in stale_entries(missing_cfg, projects, today)}
        assert res == {"stale"}, f"legacy fallback got {res}"

        # 2) 金库超期 → 只报金库,**不再**报收件箱(避免对着已降级的库催)
        cfg = mk_vault("vault-stale", today - timedelta(days=45))
        res = stale_entries(cfg, projects, today)
        assert res == [("金库 shared/memory", 45)], f"vault stale got {res}"

        # 3) 金库新鲜 → 全静默(哪怕收件箱的戳很旧)
        cfg = mk_vault("vault-fresh", today - timedelta(days=3))
        assert stale_entries(cfg, projects, today) == [], "fresh vault should be silent"

        # 4) 金库无戳 → 无基线,静默(不因"从没整理过"天天喊)
        cfg = mk_vault("vault-nostamp", None)
        assert stale_entries(cfg, projects, today) == [], "no baseline should be silent"

        # 5) config 里 vault 指向不存在的目录 → 回退旧扫描,不崩
        bad = os.path.join(root, "config-bad.toml")
        Path(bad).write_text('vault = "%s"\n' % os.path.join(root, "nowhere").replace(os.sep, "/"),
                             encoding="utf-8")
        res = {lab for lab, _ in stale_entries(bad, projects, today)}
        assert res == {"stale"}, f"bad vault path got {res}"

        # 6) config 存在但没有 vault 键 → 同样回退
        novault = os.path.join(root, "config-novault.toml")
        Path(novault).write_text('host = "testbox"\n[other]\nvault = "ignored"\n', encoding="utf-8")
        res = {lab for lab, _ in stale_entries(novault, projects, today)}
        assert res == {"stale"}, f"no vault key got {res}"

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
