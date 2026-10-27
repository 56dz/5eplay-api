#!/usr/bin/env python3
"""
5eplay CS2 API 命令行探针 / 示例客户端。

只依赖 Python 标准库（3.8+）。可直连，也可走代理。

用法：
    python probe.py matches --status 2 --limit 5
    python probe.py detail csgo_mc_2399921
    python probe.py rounds csgo_mc_2399921 --bout 1
    python probe.py events                      # 赛事列表（POST app.5eplay.com）
    python probe.py tournament csgo_tt_8251
    python probe.py team-matches csgo_tm_4494 --status past
    python probe.py teams --limit 10
    python probe.py search team Vitality
    python probe.py team csgo_tm_9565
    python probe.py team-stats csgo_tm_9565
    python probe.py player csgo_pl_11893
    python probe.py tt-stats csgo_tt_8050
    python probe.py rank --region 欧洲
    python probe.py vrs
    python probe.py raw '/v1/api/csgo/matches?page=1&limit=1'
    python probe.py raw --app --body '{"tournaments_options":{}}' /api/csgo/tournament/csgo_event_list_v1

带代理：
    python probe.py --proxy socks5h://127.0.0.1:10808 matches --status 1
    （socks 需要 pip install pysocks；http 代理不需要额外依赖）

注意：mfilter/* 、new/rank/* 、tournaments/{team,player,map}_data 这些都是 POST。
用 GET 打会返回 404 page not found（不是 405），别误判成路径不存在。
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


def _throttle():
    gap = MIN_INTERVAL - (time.time() - _last_call[0])
    if gap > 0:
        time.sleep(gap)
    _last_call[0] = time.time()


def _do(req, proxy, timeout):
    if proxy not in _openers:
        _openers[proxy] = _opener(proxy)
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


def get(url, proxy=None, timeout=25, throttle=True):
    """GET 一个 URL，返回解析后的 JSON dict（原始信封，不是 data）。"""
    if throttle:
        _throttle()
    req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_UA, "Accept": "application/json"})
    return _do(req, proxy, timeout)


def post(url, body, proxy=None, timeout=25, throttle=True):
    """POST 一个 JSON body，返回原始信封。

    注意：这些接口一律要 Content-Type: application/json，否则静默失败。
    """
    if throttle:
        _throttle()
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "User-Agent": DEFAULT_UA,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    return _do(req, proxy, timeout)


def api(path, proxy=None, base=DATA_BASE):
    """GET 接口并拆掉信封，返回 data。失败抛 ApiError。"""
    env = get(base + path, proxy=proxy)
    if not env.get("success", False):
        raise ApiError(env.get("message") or "接口返回失败", code=env.get("errcode"), body=env)
    return env.get("data")


def api_post(path, body, proxy=None, base=DATA_BASE):
    """POST 接口并拆掉信封，返回 data。失败抛 ApiError。"""
    env = post(base + path, body, proxy=proxy)
    if not env.get("success", False):
        raise ApiError(env.get("message") or "接口返回失败", code=env.get("errcode"), body=env)
    return env.get("data")


def _blank_options():
    """mfilter 系列接口通用的空白 options 内层。"""
    return {
        "tt_ids": [],
        "time_value": "",
        "grade": [],
        "team_id": "",
        "time_type": "",
        "tt_series": [],
        "maps": [],
        "page": 1,
    }


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


def cmd_events(args, proxy):
    body = {
        "tournaments_options": {
            "cursor": args.cursor or "",
            "page_token": args.page_token or "",
            "time_type": None,
            "time_value": None,
            "grade": [],
            "tt_series": [],
            "tt_bonus": [],
            "team_id": "",
            "player_id": "",
        }
    }
    data = api_post("/api/csgo/tournament/csgo_event_list_v1", body, proxy, base=APP_BASE)
    items = data if isinstance(data, list) else (data.get("items") or data.get("list") or [])
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return
    if not items:
        print("（没有数据）")
        print("原始 data: %s" % json.dumps(data, ensure_ascii=False)[:300])
        return
    for it in items:
        b = it.get("basic_info") or it
        print(
            "%-14s %-10s ~ %-10s %-40s %s"
            % (
                it.get("status") or b.get("status") or "",
                (b.get("start_time") or "")[:10],
                (b.get("end_time") or "")[:10],
                (b.get("name") or b.get("name_zh") or "")[:40],
                b.get("id") or b.get("tt_id") or "",
            )
        )
    print("\n共 %d 条。下一页: --cursor next --page-token '<page_token>'" % len(items))


def cmd_team_matches(args, proxy):
    path = "/v1/api/csgo/team/matches_v1/%s?page=%d&limit=%d" % (args.team_id, args.page, args.limit)
    if args.status:
        path += "&status=" + args.status
    data = api(path, proxy)
    it = (data or {}).get("items") or {}
    rows = it.get("matches") or []
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print(
        "总场次: %s   总页数: %s   %s"
        % ((data or {}).get("total_rows"), (data or {}).get("total_page"), it.get("win_rate_desc") or "")
    )
    if not rows:
        print("（matches 为空 —— 检查 --status 是否是 past/upcoming/live）")
        return
    for m in rows:
        mc = m.get("mc_info") or {}
        t1 = (mc.get("home_info") or {}).get("disp_name", "?")
        t2 = (mc.get("opponent_info") or {}).get("disp_name", "?")
        print(
            "%-16s %-18s %s:%s %-18s %-13s | %s"
            % (
                _fmt_ts(mc.get("ts")),
                t1[:18],
                mc.get("home_score") or "-",
                mc.get("opponent_score") or "-",
                t2[:18],
                mc.get("result") or "",
                mc.get("id"),
            )
        )


def cmd_rank(args, proxy, valve=False):
    rank_type = "valve_rank" if valve else "rank"
    body = {
        "sort_value": "desc",
        "rank_type": rank_type,
        "sort_key": rank_type,
        "region": args.region or "",
        "team_options": _blank_options(),
    }
    body["team_options"]["page"] = args.page
    data = api_post("/v1/api/csgo/new/rank/team_list", body, proxy)
    rows = (data or {}).get("items") or (data if isinstance(data, list) else [])
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print("榜单: %s   region=%r   总队伍: %s" % (rank_type, body["region"], (data or {}).get("total_rows")))
    for r in rows:
        f = r.get("field_values") or {}
        print(
            "%-5s %-28s %-8s %-6s %s"
            % (
                f.get("rank") or f.get("global_rank") or "",
                (r.get("team_name") or "")[:28],
                f.get("point") or "",
                f.get("region_name") or "",
                r.get("team_id") or "",
            )
        )


def cmd_player(args, proxy):
    data = api("/v1/api/csgo/players/%s" % args.player_id, proxy)
    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    b = (data or {}).get("basic_info") or {}
    pd = (data or {}).get("player_data") or {}
    print("选手: %s (%s)" % (b.get("name"), b.get("id")))
    print("国家: %s   生日: %s" % (b.get("country_zh"), b.get("birthday")))
    print("位置: %s" % ", ".join(b.get("positions") or []))
    print("队伍: %s (%s)" % (b.get("team_name"), b.get("team_id")))
    print("总奖金: %s   Top20: %s" % (b.get("bonus"), b.get("top20_num")))
    print()
    for k in ("rating", "kd", "kpr", "dpr", "adr", "impact", "kast", "head_shot", "maps_played"):
        if k in pd:
            print("  %-14s %s" % (k, pd.get(k)))
    maps = pd.get("maps") or []
    if maps:
        print("\n地图 (%d):" % len(maps))
        for mm in maps[:12]:
            print("  %-10s rating %-6s kd %-6s 场次 %s" % (mm.get("name"), mm.get("rating"), mm.get("kd"), mm.get("use_num")))
    hist = ((data or {}).get("player_profile") or {}).get("history_honor") or []
    if hist:
        print("\n荣誉 %d 条，最近 5 条:" % len(hist))
        for h in hist[:5]:
            tt = h.get("history_tt") or {}
            print("  %-6s %-30s %s" % (h.get("team_ranking"), (tt.get("name") or "")[:30], tt.get("bonus") or ""))


def cmd_team(args, proxy):
    data = api("/v1/api/csgo/teams/%s/overview" % args.team_id, proxy)
    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    b = (data or {}).get("basic_info") or (data or {}).get("team_info") or {}
    print(json.dumps(b, ensure_ascii=False, indent=2)[:1200])
    print("\n顶层键: %s" % ", ".join((data or {}).keys()))


def cmd_team_stats(args, proxy):
    body = {
        "team_options": {
            "team_id": args.team_id,
            "time_type": args.time_type or "recent",
            "time_value": args.time_value or "",
        }
    }
    data = api_post("/v1/api/csgo/mfilter/team/data/details", body, proxy)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    ov = (data or {}).get("team_overview") or {}
    print("== 队伍概览 ==")
    for k, v in ov.items():
        print("  %-24s %s" % (k, v))
    maps = (data or {}).get("map_data") or []
    if maps:
        print("\n== 地图池 (%d) ==" % len(maps))
        for m in maps:
            print(
                "  %-10s %-6s 胜率 %-7s CT %-7s T %-7s 场次 %s"
                % (
                    m.get("map_name"),
                    "",
                    m.get("win_rate"),
                    m.get("ct_win_rate"),
                    m.get("t_win_rate"),
                    m.get("relative_total"),
                )
            )


def cmd_tt_stats(args, proxy):
    out = {}
    for kind in ("team", "player", "map"):
        body = {"%s_options" % kind: {"tt_ids": [args.tt_id], "page": 1}}
        out[kind] = api_post("/v1/api/csgo/tournaments/%s_data" % kind, body, proxy)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    for kind, data in out.items():
        items = (data or {}).get("items") or []
        print("== %s: %d 条 ==" % (kind, len(items)))
        for it in items[:10]:
            name = it.get("team_name") or it.get("player_name") or it.get("map_name")
            f = it.get("field_values") or {}
            print("   %-28s %s" % (name, json.dumps(f, ensure_ascii=False)[:110]))


def cmd_player_matches(args, proxy):
    """选手近期比赛（POST mfilter/player/match/list）。"""
    body = {
        "player_options": {
            "player_id": args.player_id,
            "time_type": args.time_type,
            "time_value": args.time_value,
            "tt_ids": [args.tt] if args.tt else [],
            "maps": [args.map] if args.map else [],
            "grade": [args.grade] if args.grade else [],
            "page": args.page,
        }
    }
    data = api_post("/v1/api/csgo/mfilter/player/match/list", body, proxy)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    it = (data or {}).get("items") or {}
    ms = it.get("matches") or []
    print(
        "共 %s 场 / %s 页 | 场次 %s 胜率 %s"
        % (data.get("total_rows"), data.get("total_page"), it.get("game_played"), it.get("win_rate"))
    )
    for m in ms:
        mc = m.get("mc_info") or {}
        t1 = (mc.get("home_info") or {}).get("disp_name") or "?"
        t2 = (mc.get("opponent_info") or {}).get("disp_name") or "?"
        print(
            "  %-20s %s %s:%s %s  %s"
            % (
                mc.get("id"),
                t1,
                mc.get("home_score"),
                mc.get("opponent_score"),
                t2,
                mc.get("result"),
            )
        )


def cmd_player_top(args, proxy):
    """按任意指标给选手排序（POST multidimension/list）。"""
    body = {
        "player_options": {
            "player_id": args.player_id or "",
            "time_type": args.time_type,
            "time_value": args.time_value,
            "tt_ids": [],
            "maps": [],
            "recent_match": "",
            "grade": [],
            "page": args.page,
            "team_id": args.team_id or "",
        },
        "dimension": "",
        "sort_key": args.sort_key,
        "sort_value": args.sort_value,
    }
    data = api_post("/v1/api/csgo/mfilter/player/multidimension/list", body, proxy)
    items = (data or {}).get("items") or []
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print("第 %d 页 %d 条（total_rows=%s 不可信）" % (args.page, len(items), data.get("total_rows")))
    for i, p in enumerate(items, 1):
        f = p.get("field_values") or {}
        print(
            "  %2d. %-22s %-8s %s=%s"
            % (i, p.get("player_name"), p.get("team_name") or "-", args.sort_key, f.get(args.sort_key))
        )


def cmd_team_map(args, proxy):
    """队伍地图三块总览（POST mfilter/team/data/map/all）。"""
    body = {
        "team_options": {
            "time_value": args.time_value,
            "team_id": args.team_id,
            "time_type": args.time_type,
            "tt_series": [],
            "tt_ids": [],
            "maps": [],
            "grade": [],
            "page": 1,
        },
        "sort_key": "",
    }
    data = api_post("/v1/api/csgo/mfilter/team/data/map/all", body, proxy)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    for block in ("relative_data", "win_data", "win_rate_data"):
        rows = (data or {}).get(block) or []
        print("== %s (%d) ==" % (block, len(rows)))
        for r in rows:
            rest = {k: v for k, v in r.items() if k not in ("map_name", "map_logo", "map_icon")}
            print("  %-12s %s" % (r.get("map_name"), json.dumps(rest, ensure_ascii=False)[:130]))


def cmd_tt_data(args, proxy):
    """赛事轻量统计（GET tournaments/{tt}/data?type=1|2|3）。"""
    out = {}
    for t in (1, 2, 3):
        d = api("/v1/api/csgo/tournaments/%s/data?type=%d" % (args.tt_id, t), proxy) or {}
        for k, v in d.items():
            if v:
                out[(t, k)] = v
    if args.json:
        print(json.dumps({k[1]: v for k, v in out.items()}, ensure_ascii=False, indent=2))
        return
    for (t, k), rows in out.items():
        print("== type=%d / %s: %d 条 ==" % (t, k, len(rows)))
        for r in rows[: args.limit]:
            name = r.get("name") or "?"
            rest = {kk: vv for kk, vv in r.items() if kk not in ("name", "logo", "url", "map_icon")}
            print("  %-24s %s" % (name, json.dumps(rest, ensure_ascii=False)[:130]))


def cmd_tt_prize(args, proxy):
    """赛事奖金分配（introduction 的 cur_team_rank / team_rank）。"""
    data = api("/v1/api/csgo/tournaments/%s/introduction" % args.tt_id, proxy) or {}
    basic = data.get("basic") or {}
    if args.json:
        print(json.dumps({"cur_team_rank": data.get("cur_team_rank"), "team_rank": data.get("team_rank")}, ensure_ascii=False, indent=2))
        return
    print("%s | 总奖金 %s | 状态 %s" % (basic.get("name_zh"), basic.get("bonus"), basic.get("status")))
    for key in ("cur_team_rank", "team_rank"):
        rows = data.get(key) or []
        print("== %s (%d) ==" % (key, len(rows)))
        for r in rows:
            team = (r.get("team") or {}).get("name") or "-"
            print("  %-8s %-28s %s" % (r.get("rank"), team, r.get("bonus")))


def cmd_sessions(args, proxy):
    """赛事赛程 / 赛果（app.5eplay.com）。

    两个接口参数名不同，别套用：
      session_list        : tt_ids=<csgo_tt_*>  limit=<1-50>  page=<n>
      session_result_list : 不支持按赛事过滤，page_size=<1-50>，翻页用 page_token
                            page_token 格式 "YYYY-MM-DD HH:mm:ss,id1,id2"（UTC）
    """
    if args.result:
        q = {"game_type": 1, "page_size": args.limit}
        if args.order_by:
            q["order_by"] = args.order_by
        if args.page_token:
            q["page_token"] = args.page_token
        url = "%s/api/tournament/session_result_list?%s" % (
            APP_BASE,
            urllib.parse.urlencode(q),
        )
    else:
        q = {"game_type": 1, "limit": args.limit, "page": args.page}
        # 不传 tt_ids 时这是全站赛程流，会混着好几个赛事。
        if args.tt_id:
            q["tt_ids"] = args.tt_id
        url = "%s/api/tournament/session_list?%s" % (APP_BASE, urllib.parse.urlencode(q))

    env = get(url, proxy=proxy)
    data = env.get("data") or {}
    ms = data.get("matches") or []
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print("%s | %d 条" % (url, len(ms)))
    for m in ms:
        mc = m.get("mc_info") or {}
        t1 = (mc.get("t1_info") or {}).get("disp_name") or "?"
        t2 = (mc.get("t2_info") or {}).get("disp_name") or "?"
        st = (m.get("state") or {}).get("status")
        tt = (m.get("tt_info") or {}).get("id") or "-"
        print(
            "  %-20s %-14s %s vs %s  status=%s  %s"
            % (mc.get("id"), tt, t1, t2, st, _fmt_ts(mc.get("plan_ts")))
        )
    # 方便翻页：打印本页最后一条的 page_token 写法。
    if args.result or args.page_token:
        last = (ms[-1].get("mc_info") or {}) if ms else {}
        if last:
            ts = int(last.get("plan_ts") or 0)
            same = [x["mc_info"]["id"] for x in ms if int(x["mc_info"].get("plan_ts") or 0) == ts]
            stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(ts))
            print("\n下一页 page_token=%s" % ("%s,%s" % (stamp, ",".join(same))))


def cmd_search(args, proxy):
    if args.kind == "team":
        data = api("/v1/api/csgo/teams?name=%s&page=1&limit=%d" % (urllib.parse.quote(args.q), args.limit), proxy)
    elif args.kind == "player":
        data = api("/v1/api/csgo/players?name=%s&page=1&limit=%d" % (urllib.parse.quote(args.q), args.limit), proxy)
    else:
        data = api("/v1/api/csgo/mfilter/tournament/search?name=%s&page=1&limit=%d" % (urllib.parse.quote(args.q), args.limit), proxy)
    items = (data or {}).get("items") or []
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    print("命中 %s 条" % (data or {}).get("total_rows"))
    for it in items:
        print(
            "  %-24s %-32s %s"
            % (
                it.get("id") or it.get("tt_id") or "",
                it.get("name") or it.get("tt_name") or "",
                it.get("Portrait") or it.get("logo") or "",
            )
        )


def _fix_path(path):
    """修 Windows/MSYS 把 "/v1/api/..." 当路径改写成 "C:/.../v1/api/..." 的问题。

    Git Bash 会自动转换以 / 开头的参数，导致 path 变成 Windows 绝对路径。
    这里把它还原成 /v1/... 或 /api/...
    """
    if not path.startswith("/"):
        m = None
        for prefix in ("/v1/", "/api/", "/datacenter-web-api/"):
            idx = path.find(prefix.replace("/", "/"))
            if idx != -1:
                m = path[idx:]
                break
        if m is None:
            # 兜底：找 /v1 之类
            for prefix in ("/v1/", "/api/"):
                idx = path.find(prefix)
                if idx != -1:
                    m = path[idx:]
                    break
        if m is not None:
            print(
                "提示: 检测到路径被 Git Bash 转换了，已还原为 %r\n"
                "      （以后可以用 MSYS_NO_PATHCONV=1 或改用 Windows 原生命令行）" % m,
                file=sys.stderr,
            )
            return m
    return path


def cmd_raw(args, proxy):
    base = APP_BASE if args.app else DATA_BASE
    path = _fix_path(args.path)
    if args.body:
        env = post(base + path, json.loads(args.body), proxy=proxy)
    else:
        env = get(base + path, proxy=proxy)
    print(json.dumps(env, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- helpers


def _fmt_ts(ts):
    if not ts:
        return "-"
    try:
        return time.strftime("%m-%d %H:%M", time.localtime(int(ts)))
    except (ValueError, TypeError, OSError):
        return str(ts)


def _default_range():
    """默认时间区间：近三个月，格式为 "起点_终点"（下划线连接，不是 ~）。"""
    now = time.localtime()
    y, m, d = now.tm_year, now.tm_mon - 3, now.tm_mday
    if m <= 0:
        y, m = y - 1, m + 12
    start = time.strftime("%Y-%m-%d 00:00:00", (y, m, d, 0, 0, 0, 0, 0, -1))
    end = time.strftime("%Y-%m-%d 23:59:59", now)
    return "%s_%s" % (start, end)


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

    ev = sub.add_parser("events", help="赛事列表（POST app.5eplay.com）")
    ev.add_argument("--cursor", default="", help="翻页方向：next / prev")
    ev.add_argument("--page-token", dest="page_token", default="", help="上一页最后一条的 page_token")
    ev.add_argument("--json", action="store_true")
    ev.set_defaults(func=cmd_events)

    utm = sub.add_parser("team-matches", help="队伍近期比赛")
    utm.add_argument("team_id")
    utm.add_argument("--status", default="past", choices=["past", "upcoming", "live"], help="注意是字符串！")
    utm.add_argument("--page", type=int, default=1)
    utm.add_argument("--limit", type=int, default=10)
    utm.add_argument("--json", action="store_true")
    utm.set_defaults(func=cmd_team_matches)

    rk = sub.add_parser("rank", help="5E 世界排名（POST）")
    rk.add_argument("--region", default="", help="欧洲 / 亚洲 / 美洲，留空为全球")
    rk.add_argument("--page", type=int, default=1)
    rk.add_argument("--json", action="store_true")
    rk.set_defaults(func=lambda a, p: cmd_rank(a, p, valve=False))

    vr = sub.add_parser("vrs", help="Valve VRS 榜（POST）")
    vr.add_argument("--region", default="")
    vr.add_argument("--page", type=int, default=1)
    vr.add_argument("--json", action="store_true")
    vr.set_defaults(func=lambda a, p: cmd_rank(a, p, valve=True))

    pl = sub.add_parser("player", help="选手详情")
    pl.add_argument("player_id")
    pl.add_argument("--raw", action="store_true")
    pl.set_defaults(func=cmd_player)

    tb = sub.add_parser("team", help="队伍详情")
    tb.add_argument("team_id")
    tb.add_argument("--raw", action="store_true")
    tb.set_defaults(func=cmd_team)

    ts = sub.add_parser("team-stats", help="队伍数据统计（POST）")
    ts.add_argument("team_id")
    ts.add_argument("--time-type", dest="time_type", default="recent", help="recent / self / all")
    ts.add_argument("--time-value", dest="time_value", default="", help='"2026-07-27 00:00:00_2026-10-27 23:59:59"')
    ts.add_argument("--json", action="store_true")
    ts.set_defaults(func=cmd_team_stats)

    tt = sub.add_parser("tt-stats", help="赛事维度统计（队/选手/地图，POST）")
    tt.add_argument("tt_id")
    tt.add_argument("--json", action="store_true")
    tt.set_defaults(func=cmd_tt_stats)

    pm = sub.add_parser("player-matches", help="选手近期比赛（POST，可翻页筛选）")
    pm.add_argument("player_id")
    pm.add_argument("--time-type", dest="time_type", default="recent", help="recent / self / all")
    pm.add_argument("--time-value", dest="time_value", default=None, help='默认近三个月；格式 "起点_终点"')
    pm.add_argument("--tt", help="按赛事 ID 过滤")
    pm.add_argument("--map", help="按地图过滤，英文小写，如 mirage")
    pm.add_argument("--grade", help="按赛事等级过滤，如 2")
    pm.add_argument("--page", type=int, default=1)
    pm.add_argument("--json", action="store_true")
    pm.set_defaults(func=cmd_player_matches)

    pt = sub.add_parser("player-top", help="按任意指标给选手排序（POST multidimension）")
    pt.add_argument("--sort-key", dest="sort_key", default="rating", help="rating/kpr/kast/swing/adr/dpr/impact/kd")
    pt.add_argument("--sort-value", dest="sort_value", default="DESC", choices=["DESC", "ASC"])
    pt.add_argument("--player-id", dest="player_id", help="只查某个人")
    pt.add_argument("--team-id", dest="team_id", help="只查某队成员")
    pt.add_argument("--time-type", dest="time_type", default="recent")
    pt.add_argument("--time-value", dest="time_value", default=None)
    pt.add_argument("--page", type=int, default=1)
    pt.add_argument("--json", action="store_true")
    pt.set_defaults(func=cmd_player_top)

    tmap = sub.add_parser("team-map", help="队伍地图三块总览（POST map/all）")
    tmap.add_argument("team_id")
    tmap.add_argument("--time-type", dest="time_type", default="recent")
    tmap.add_argument("--time-value", dest="time_value", default=None)
    tmap.add_argument("--json", action="store_true")
    tmap.set_defaults(func=cmd_team_map)

    td = sub.add_parser("tt-data", help="赛事轻量统计（GET data?type=1|2|3）")
    td.add_argument("tt_id")
    td.add_argument("--limit", type=int, default=10)
    td.add_argument("--json", action="store_true")
    td.set_defaults(func=cmd_tt_data)

    tz = sub.add_parser("tt-prize", help="赛事奖金分配")
    tz.add_argument("tt_id")
    tz.add_argument("--json", action="store_true")
    tz.set_defaults(func=cmd_tt_prize)

    ss = sub.add_parser("sessions", help="赛事赛程 / 赛果（app.5eplay.com）")
    ss.add_argument("tt_id", nargs="?", default="", help="赛事 ID，如 csgo_tt_8251（赛果模式下会被忽略）")
    ss.add_argument("--result", action="store_true", help="看赛果（session_result_list），默认看赛程")
    ss.add_argument("--page", type=int, default=1, help="仅 session_list 用")
    ss.add_argument("--limit", type=int, default=20, help="条数，1-50")
    ss.add_argument("--order-by", dest="order_by", default="", help="仅赛果：asc / desc")
    ss.add_argument("--page-token", dest="page_token", default="", help='仅赛果：上一页末尾的 "YYYY-MM-DD HH:mm:ss,id1,id2"')
    ss.add_argument("--json", action="store_true")
    ss.set_defaults(func=cmd_sessions)

    se = sub.add_parser("search", help="搜队伍 / 选手 / 赛事")
    se.add_argument("kind", choices=["team", "player", "tournament"])
    se.add_argument("q")
    se.add_argument("--limit", type=int, default=5)
    se.add_argument("--json", action="store_true")
    se.set_defaults(func=cmd_search)

    raw = sub.add_parser("raw", help="直接打一个路径")
    raw.add_argument("path")
    raw.add_argument("--app", action="store_true", help="用 app.5eplay.com 作 base")
    raw.add_argument("--body", help="给了 JSON body 就用 POST，例如 '{\"a\":1}'")
    raw.set_defaults(func=cmd_raw)

    args = p.parse_args()
    # 几个接口的 time_value 默认值要按「今天」算，统一在这里补。
    if getattr(args, "time_value", "") is None:
        args.time_value = _default_range()
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
