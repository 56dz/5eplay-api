#!/usr/bin/env python3
"""
5eplay CS2 API 命令行探针 / 示例客户端。

只依赖 Python 标准库（3.8+）。可直连，也可走代理。

用法：
    python probe.py matches --status 2 --limit 5
    python probe.py detail csgo_mc_2399921
    python probe.py rounds csgo_mc_2399921 --bout 1
    python probe.py tournament csgo_tt_8251
    python probe.py teams --limit 10
    python probe.py raw '/v1/api/csgo/matches?page=1&limit=1'

带代理：
    python probe.py --proxy socks5h://127.0.0.1:10808 matches --status 1
    （socks 需要 pip install pysocks；http 代理不需要额外依赖）
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Windows 控制台默认 GBK，中文会乱码。强制 UTF-8。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

DATA_BASE = "https://esports-data.5eplaycdn.com"
APP_BASE = "https://app.5eplay.com"

DEFAULT_UA = "5eplay-cs2-api/1.0 (+https://github.com/)"
MIN_INTERVAL = 1.0  # 秒；对别人服务器客气一点

_last_call = [0.0]


class ApiError(Exception):
    def __init__(self, message, code=None, body=None):
        super().__init__(message)
        self.code = code
        self.body = body


def _opener(proxy):
    if not proxy:
        return urllib.request.build_opener()
    handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    return urllib.request.build_opener(handler)


_openers = {}


def get(url, proxy=None, timeout=25, throttle=True):
    """GET 一个 URL，返回解析后的 JSON dict（原始信封，不是 data）。"""
    if throttle:
        gap = MIN_INTERVAL - (time.time() - _last_call[0])
        if gap > 0:
            time.sleep(gap)
        _last_call[0] = time.time()

    if proxy not in _openers:
        _openers[proxy] = _opener(proxy)
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA, "Accept": "application/json"})
    try:
        with _openers[proxy].open(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        raise ApiError("HTTP %s" % e.code, code=e.code, body=e.read()[:500])
    except urllib.error.URLError as e:
        raise ApiError("连接失败: %s（需要代理吗？试试 --proxy）" % e.reason)

    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ApiError("返回的不是 JSON，可能是 404 页面: %s" % text[:200])


def api(path, proxy=None, base=DATA_BASE):
    """调接口并拆掉信封，返回 data。失败抛 ApiError。"""
    url = base + path
    env = get(url, proxy=proxy)
    if not env.get("success", False):
        raise ApiError(env.get("message") or "接口返回失败", code=env.get("errcode"), body=env)
    return env.get("data")


# ---------------------------------------------------------------- commands


def cmd_matches(args, proxy):
    q = {"page": args.page, "limit": args.limit, "game_status": args.status}
    if args.tt:
        q["tt_ids"] = args.tt
    data = api("/v1/api/csgo/matches?" + urllib.parse.urlencode(q), proxy)

    rows = []
    for key, label in (("live_matches", "进行中"), ("matches", "列表")):
        for m in data.get(key) or []:
            mc = m.get("mc_info") or {}
            st = m.get("state") or {}
            tt = m.get("tt_info") or {}
            rows.append(
                {
                    "status": st.get("status"),
                    "time": _fmt_ts(mc.get("plan_ts")),
                    "match": "%s %s:%s %s"
                    % (
                        (mc.get("t1_info") or {}).get("disp_name", "?"),
                        st.get("t1_score") or "-",
                        st.get("t2_score") or "-",
                        (mc.get("t2_info") or {}).get("disp_name", "?"),
                    ),
                    "event": tt.get("disp_name") or "",
                    "round": mc.get("round_name") or "",
                    "id": mc.get("id"),
                    "src": key,
                }
            )

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    if not rows:
        print("（没有数据）")
        return
    for r in rows:
        print("[%s] %-16s %-40s | %s | %s | %s" % (r["status"], r["time"], r["match"], r["event"], r["round"], r["id"]))


def cmd_detail(args, proxy):
    data = api("/v1/api/csgo/matches/%s/data" % args.match_id, proxy)
    match = (data or {}).get("match") or {}
    if args.raw:
        print(json.dumps(match, ensure_ascii=False, indent=2))
        return

    mc = match.get("mc_info") or {}
    tt = match.get("tt_info") or {}
    t1 = (mc.get("t1_info") or {}).get("disp_name", "?")
    t2 = (mc.get("t2_info") or {}).get("disp_name", "?")
    print("赛事: %s  奖金: %s  地点: %s" % (tt.get("disp_name", ""), tt.get("bonus", ""), tt.get("city_name", "")))
    print("对阵: %s vs %s   赛制: BO%s   轮次: %s" % (t1, t2, mc.get("format", "?"), mc.get("round_name", "")))
    print()

    for b in match.get("bouts_state") or []:
        status = b.get("status")
        if status == "-1":
            print("  图%s %-10s 未开始" % (b.get("bout_num"), b.get("map_name")))
            continue
        s1 = (b.get("t1_stats") or {}).get("quick_score") or "?"
        s2 = (b.get("t2_stats") or {}).get("quick_score") or "?"
        flag = {"2": "已结束", "1": "进行中"}.get(status, status)
        print("  图%s %-10s %s:%s  [%s]  %s" % (b.get("bout_num"), b.get("map_name"), s1, s2, flag, b.get("bp_act") or ""))
        if args.players:
            for side, label in (("t1_pr_stats", t1), ("t2_pr_stats", t2)):
                print("    -- %s --" % label)
                for p in b.get(side) or []:
                    print(
                        "      %-12s %2s/%2s/%2s  rating %-5s adr %-5s kast %-6s hs %s"
                        % (
                            p.get("name", "?"),
                            p.get("kill", "-"),
                            p.get("death", "-"),
                            p.get("assist", "-"),
                            p.get("rating", "-"),
                            p.get("adr", "-"),
                            p.get("kast", "-"),
                            p.get("head_shot_percent") or p.get("head_shot_rate") or "-",
                        )
                    )


def cmd_rounds(args, proxy):
    path = "/v1/api/csgo/match/%s/event/log?update_version=0&limit=%d" % (args.match_id, args.limit)
    if args.bout:
        path += "&bout_id=%s_%s" % (args.match_id, args.bout)
    data = api(path, proxy)

    logs = []
    for item in (data or {}).get("list") or []:
        try:
            info = json.loads(item.get("log_info") or "{}")
        except json.JSONDecodeError:
            continue
        logs.append((item.get("bout_num"), item.get("map_name"), info))

    logs.reverse()  # 原接口倒序，翻转成时间正序

    if args.json:
        print(json.dumps([{"bout": a, "map": b, "info": c} for a, b, c in logs], ensure_ascii=False, indent=2))
        return

    for bout, mapname, info in logs:
        t = info.get("type")
        if t == "2":
            re_ = info.get("round_end") or {}
            print(
                "  图%s %-9s 回合结束  CT %-2s : %-2s T   %s (%s)"
                % (bout, mapname, re_.get("ct_score"), re_.get("t_score"), re_.get("winner"), re_.get("win_type"))
            )
        elif t == "1":
            rs = info.get("round_start") or {}
            print("  图%s %-9s 回合开始  #%s" % (bout, mapname, rs.get("round_num")))


def cmd_tournament(args, proxy):
    data = api("/v1/api/csgo/tournaments/%s/introduction" % args.tt_id, proxy)
    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    b = (data or {}).get("basic") or {}
    print("名称: %s" % b.get("name_zh"))
    print("英文: %s" % b.get("name_en"))
    print("时间: %s ~ %s" % (b.get("start_time"), b.get("end_time")))
    print("奖金: %s" % b.get("bonus"))
    print("地点: %s" % b.get("city_name"))
    print("等级: %s   状态: %s" % (b.get("grade"), b.get("status")))
    print("Logo: %s" % b.get("logo"))
    ranks = (data or {}).get("cur_team_rank") or []
    if ranks:
        print("\n排名/奖金分配 (%d 项):" % len(ranks))
        for r in ranks[:10]:
            print("  ", json.dumps(r, ensure_ascii=False)[:120])


def cmd_teams(args, proxy):
    data = api("/v1/api/csgo/teams?page=1&limit=%d" % args.limit, proxy)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    for t in (data or {}).get("items") or []:
        print("%-24s %-14s kd=%-6s maps=%-6s %s" % (t.get("id"), t.get("name"), t.get("kd"), t.get("map_count"), t.get("logo")))


def cmd_raw(args, proxy):
    base = APP_BASE if args.app else DATA_BASE
    env = get(base + args.path, proxy=proxy)
    print(json.dumps(env, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- helpers


def _fmt_ts(ts):
    if not ts:
        return "-"
    try:
        return time.strftime("%m-%d %H:%M", time.localtime(int(ts)))
    except (ValueError, TypeError, OSError):
        return str(ts)


# ---------------------------------------------------------------- main


def main():
    p = argparse.ArgumentParser(description="5eplay CS2 API 探针", formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--proxy", help="例如 socks5h://127.0.0.1:10808 或 http://127.0.0.1:8080")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("matches", help="比赛列表")
    m.add_argument("--status", default="2", choices=["0", "1", "2"], help="0未开始 1进行中 2已结束")
    m.add_argument("--page", type=int, default=1)
    m.add_argument("--limit", type=int, default=10)
    m.add_argument("--tt", help="按赛事 ID 过滤")
    m.add_argument("--json", action="store_true")
    m.set_defaults(func=cmd_matches)

    d = sub.add_parser("detail", help="比赛详情（每图比分 + 选手）")
    d.add_argument("match_id")
    d.add_argument("--players", action="store_true", help="同时打印选手数据")
    d.add_argument("--raw", action="store_true", help="输出原始 JSON")
    d.set_defaults(func=cmd_detail)

    r = sub.add_parser("rounds", help="逐回合流水")
    r.add_argument("match_id")
    r.add_argument("--bout", help="只看第几张图")
    r.add_argument("--limit", type=int, default=500)
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=cmd_rounds)

    t = sub.add_parser("tournament", help="赛事详情")
    t.add_argument("tt_id")
    t.add_argument("--raw", action="store_true")
    t.set_defaults(func=cmd_tournament)

    tm = sub.add_parser("teams", help="队伍列表")
    tm.add_argument("--limit", type=int, default=10)
    tm.add_argument("--json", action="store_true")
    tm.set_defaults(func=cmd_teams)

    raw = sub.add_parser("raw", help="直接打一个路径")
    raw.add_argument("path")
    raw.add_argument("--app", action="store_true", help="用 app.5eplay.com 作 base")
    raw.set_defaults(func=cmd_raw)

    args = p.parse_args()
    try:
        args.func(args, args.proxy)
    except ApiError as e:
        print("错误: %s" % e, file=sys.stderr)
        if e.body:
            print("详情: %s" % (e.body if isinstance(e.body, str) else json.dumps(e.body, ensure_ascii=False)[:400]), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
