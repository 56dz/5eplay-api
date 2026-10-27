# 接口总览

所有接口均为 `GET`，返回 `application/json`，统一信封：

```json
{ "success": true, "errcode": 0, "message": "", "data": ... }
```

Base URL：

- 数据：`https://esports-data.5eplaycdn.com`
- 补充：`https://app.5eplay.com`
- 图片：`https://oss.5eplay.com`

无需任何鉴权 header。`User-Agent` 随意（默认 curl UA 也能通）。

下文示例里的 ID 都是真实存在的：

| 类型 | ID | 说明 |
| --- | --- | --- |
| 比赛 | `csgo_mc_2399921` | 已结束 BO2 |
| 比赛 | `csgo_mc_2399893` | 直播中 BO3 |
| 比赛 | `csgo_mc_2399854` | 未开始 |
| 赛事 | `csgo_tt_8251` | BLAST 对抗赛 2026 S2 |
| 队伍 | `csgo_tm_4494` | MOUZ |
| 队伍 | `csgo_tm_7020` | Spirit |

---

## 1. 比赛列表

```
GET /v1/api/csgo/matches?page=1&limit=20&game_status=<0|1|2>[&tt_ids=<赛事ID>]
```

| 参数 | 说明 |
| --- | --- |
| `page` | 从 1 开始 |
| `limit` | 每页条数，实测最大 100 |
| `game_status` | `0` 未开始/近期，`1` 进行中，`2` 已结束 |
| `tt_ids` | 可选，按赛事过滤 |

返回：

- `game_status=1` → 数据在 `data.live_matches[]`
- 其他 → 数据在 `data.matches[]`

**两个数组始终存在**，只是不匹配的那个是空数组。

```bash
curl -s 'https://esports-data.5eplaycdn.com/v1/api/csgo/matches?page=1&limit=2&game_status=2' \
  | python -m json.tool | head -80
```

```json
{
  "success": true,
  "errcode": 0,
  "message": "",
  "data": {
    "live_matches": [],
    "matches": [
      {
        "mc_info": {
          "id": "csgo_mc_2399921",
          "plan_ts": "1794315000",
          "format": "2",
          "round_name": "决赛",
          "tt_stage": "淘汰赛",
          "tt_stage_desc": "淘汰赛 决赛",
          "grade": "2",
          "star": "3",
          "group_id": 5591,
          "t1_info": {
            "id": "csgo_tm_7020",
            "disp_name": "Spirit",
            "logo": "https://oss.5eplay.com/sport/csgo/team/merge_cgchcqhll806h1bg2lt0.png",
            "country": "",
            "rank": "",
            "v_rank": null
          },
          "t2_info": { "id": "csgo_tm_4494", "disp_name": "MOUZ", "logo": "...", "..." : "..." }
        },
        "state": {
          "status": "2",
          "t1_score": "2",
          "t2_score": "0",
          "t1_quick_score": "",
          "t2_quick_score": "",
          "round_num": "",
          "bout_states": [],
          "t1_odds": "1.54",
          "t2_odds": "2.42",
          "t1_odds_percent": "61",
          "t2_odds_percent": "39",
          "video_status": "2",
          "live_status": "",
          "dark_horse": "2"
        },
        "tt_info": {
          "id": "csgo_tt_8251",
          "disp_name": "BLAST 对抗赛 2026 S2",
          "abbr_zh": "BLAST对抗赛 2026 S2",
          "abbr_en": "BLAST Rivals 2026 S2",
          "logo": "https://oss.5eplay.com/sport/csgo/event/7556.png",
          "bonus": "$1,000,000",
          "city_name": "中国香港赤鱲角",
          "grade": "2",
          "grade_label": "S级赛事",
          "special_grade_label": "S级赛事",
          "color": "663dea",
          "special_color": "663dea",
          "mode": "2",
          "start_time": "2026-11-09 00:00:00",
          "end_time": "2026-11-15 23:59:59",
          "status": "upcoming"
        }
      }
    ]
  }
}
```

`state.status`：`0` 未开始 / `1` 进行中 / `2` 已结束。
`mc_info.format`：`1` BO1、`2` BO2、`3` BO3、`5` BO5。
`mc_info.plan_ts`：排期时间戳（**秒**，字符串）。

---

## 2. 比赛详情 ★ 核心

```
GET /v1/api/csgo/matches/{mc_id}/data
```

这是最有价值的接口：**每张地图的比分 + 每张地图的选手数据**都在这里。

体积：已结束的比赛约 120 KB，直播中约 60 KB。建议客户端缓存，不要频繁拉。

```bash
curl -s 'https://esports-data.5eplaycdn.com/v1/api/csgo/matches/csgo_mc_2399921/data' \
  | python -m json.tool > match.json
```

顶层结构：

```
data.match
  ├── mc_info        比赛基本信息（同列表里的 mc_info）
  ├── tt_info        赛事信息（同列表里的 tt_info）
  ├── global_state   全局状态 + 全队平均数据
  └── bouts_state[]  每张地图（按顺序，一个元素 = 一张图）
```

### 2.1 `bouts_state[]` — 每张地图

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `bout_num` | string | 第几局，`"1"` `"2"` `"3"` |
| `map_name` | string | 地图名，`"Ancient"` / `"Dust2"` / `"Inferno"` / `"Nuke"` / `"Mirage"` / `"Anubis"` / `"Vertigo"` / `"Overpass"` / `"Train"` |
| `map_icon` | string | 地图图标 URL |
| `map_bgm` | string | 地图背景视频 URL（演示用） |
| `status` | string | `2` 已打完 / `1` 进行中 / `-1` 未开始 |
| `result` | string | `"t1"` / `"t2"` / `""`（本图胜者） |
| `disp_name` | string | 在页面上的显示名，如 `"第一局"` |
| `bp_act` | string | 选图动作，如 `"t2_pick"`；decider 图可能为空 |
| `round_num` | string | 本图打了多少回合 |
| `curr_round_num` | string | 直播时：当前第几回合 |
| `curr_bout_stage` | string | 直播时：当前半场（CT / T） |
| `t1_stats` / `t2_stats` | object | 本图比分，见 2.2 |
| `t1_pr_stats` / `t2_pr_stats` | array | 本图选手数据，见 2.3 |
| `t1_pr_stats_ct` / `t1_pr_stats_t` | array | 分 CT / T 两个半场的选手数据 |
| `pr_stats` | object | 本图亮点对比（首杀王、最高 ADR 等） |
| `milestones` | array | 里程碑事件 |
| `event_log` | object | 最后一个事件，如 `{"log":{...},"text":"比赛已结束"}` |
| `start_time` / `end_time` | string | 秒级时间戳 |

### 2.2 `t1_stats` / `t2_stats` — 地图比分

```json
{
  "quick_score": "13",
  "all_score": "13",
  "sh_score": "5",
  "sh_role": "T",
  "sh_data": [0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0],
  "fh_score": "8",
  "fh_role": "CT",
  "fh_data": [0, 0, 1, 1, 4, 4, 1, 0, 4, 5, 0, 1],
  "ot_score": "",
  "ot_role": "",
  "ot_data": []
}
```

| 字段 | 说明 |
| --- | --- |
| `quick_score` | **本图最终得分，直接用这个** |
| `all_score` | 同上（通常相等） |
| `sh_score` / `sh_role` / `sh_data` | 上半场得分 / 我方阵营 / 每回合累计 |
| `fh_score` / `fh_role` / `fh_data` | 下半场得分 / 我方阵营 / 每回合累计 |
| `ot_score` / `ot_role` / `ot_data` | 加时（需要有加时的比赛才有值，未实测到样例） |

`sh_data` 是**累计比分曲线**：索引 = 回合序号，值 = 该回合结束后的累计得分。可以直接拿去画走势图。

> `t1_stats` 对应 `mc_info.t1_info`（即主队），`t2_stats` 对应 `t2_info`。

### 2.3 `t1_pr_stats[]` / `t2_pr_stats[]` — 选手数据

每张图、每队 5 名选手。字段：

**基础**
`id`, `name`（游戏 ID）, `portrait`, `half_portrait`, `country_logo`, `weapon`, `weapon_logo`

**核心数据**
| 字段 | 示例 | 说明 |
| --- | --- | --- |
| `kill` | `"28"` | 击杀 |
| `death` | `"27"` | 死亡 |
| `assist` | `"6"` | 助攻 |
| `rating` | `"1.07"` | HLTV 式 Rating |
| `mk_rating` | | 5E 自有评分 |
| `impact` | `"1.12"` | Impact |
| `adr` | `"81.3"` | 每回合平均伤害 |
| `kast` | `"75.0%"` | KAST 百分比（字符串，带 %） |
| `kpr` | `"0.78"` | 每回合击杀 |
| `dpr` | `"0.75"` | 每回合死亡 |
| `kdratio` | `"1.04"` | K/D |
| `kd_diff` | `"1"` | 击杀减死亡 |
| `fkdiff` | `"2"` | 首杀减首死 |
| `headshot` | `"5"` | 爆头数 |
| `head_shot_rate` | `"17.6%"` | 爆头率 |
| `first_blood_num` | `"3"` | 首杀数 |
| `first_blood_rate` | `"42.9%"` | 首杀率 |
| `first_death_num` | `"1"` | 首死数 |
| `round_mvp` | `"4"` | 回合 MVP 次数 |
| `k2` `k3` `k4` `k5` | | 双杀 / 三杀 / 四杀 / 五杀次数 |
| `more_kill` | | 多杀总数 |
| `traded_death` | | 被换掉的死亡 |

**对位统计**
`counter_kills`, `first_kills`（数组）, `counter_kill_map`, `first_kill_map`

**经济 / 状态（直播时）**
`money`, `hp`, `alive`, `helmet`, `kevlar`, `has_defusekit`, `v1`~`v5`（道具）

**目标**
`unpack_num`（下包）, `subpackage_num`（拆包）, `cl_win_num`（残局胜利）, `final_victory_num`

**其他**
`swing`（状态起伏）

> ⚠️ 大部分数值字段是**字符串**，带 `%` 的也是字符串，解析时要自己 `strip('%')`。

### 2.4 `global_state`

包含全队平均数据 `avg_player_stats`（字段同选手数据，但值是全队平均）、地图描述开关 `ana_map_desc_flag` 等。结构尚未逐字段梳理完。

---

## 3. 逐回合流水

```
GET /v1/api/csgo/match/{mc_id}/event/log?update_version=0&limit=500[&bout_id={mc_id}_{n}]
```

| 参数 | 说明 |
| --- | --- |
| `update_version` | 增量游标，首次传 0 |
| `limit` | 一次取多少条，实测 500 够一场 BO3 |
| `bout_id` | 可选，只看第 n 张图，格式 `csgo_mc_xxx_2` |

返回 `data.list[]`，**倒序**（最后一条最新）：

```json
{
  "from_ver": "0",
  "to_ver": "512",
  "not_more": "1",
  "list": [
    {
      "bout_id": "csgo_mc_2399921_1",
      "bout_num": "1",
      "map_name": "Ancient",
      "update_version": "12",
      "log_info": "{\"type\":\"2\",\"round_end\":{\"ct_score\":\"13\",\"t_score\":\"9\",\"winner\":\"CT\",\"win_type\":\"Bomb_Defused\",\"win_type_app\":4},\"round_start\":{\"round_num\":\"\",\"map\":\"\",\"bout_num\":\"\"}}"
    }
  ]
}
```

⚠️ `log_info` 是**二次转义的 JSON 字符串**，要再 parse 一次。

`log_info.type`：

| type | 含义 | 有效字段 |
| --- | --- | --- |
| `1` | 回合开始 | `round_start.round_num` |
| `2` | 回合结束 | `round_end.ct_score`, `round_end.t_score`, `round_end.winner`, `round_end.win_type` |
| `3` `4` `6` `8` `10` | 击杀 / 经济 / 中场等 | 击杀类带 `killer_nick`, `victim_nick`, `weapon` |

`win_type` 示例：`Bomb_Defused`、`Target_Bombed`、`Target_Saved`、`CT_Win`、`T_Win`。

`not_more: "1"` 表示没有更多了。增量拉取：把上次的 `to_ver` 传给 `update_version`。

---

## 4. 整场选手汇总（app.5eplay.com）

`/matches/{id}/data` 里是**单图**数据。要看**整场（跨图合计）**，走这两个接口：

### 4.1 拿队伍 tab

```
GET https://app.5eplay.com/api/score/match_score_tab?match_id={mc_id}&game_type=1
```

```json
{
  "success": true,
  "data": [
    { "tab": "match_player", "id": "csgo_tm_7020", "name": "Spirit", "logo": "https://...", "is_selected": true },
    { "tab": "match_player", "id": "csgo_tm_4494", "name": "MOUZ",  "logo": "https://...", "is_selected": false }
  ]
}
```

> ⚠️ **未开赛的比赛返回 `data: []`**。`id` 是**队伍 ID**，要传给下一个接口。

### 4.2 拿该队整场选手数据

```
GET https://app.5eplay.com/api/score/match_score_list?match_id={mc_id}&tab=match_player&game_type=1&team_id={team_id}
```

```json
{
  "success": true,
  "data": [
    {
      "tab": "match_player",
      "card_content_tab": "player",
      "id": "csgo_pl_18638",
      "name": "sk0R",
      "rating": "1.07",
      "kill": "28",
      "death": "27",
      "kast": "75.0%",
      "adr": "81.3",
      "positions": ["步枪手"],
      "is_mvp_player": false,
      "is_coach_player": false,
      "logo": "https://...",
      "country_logo": "https://..."
    }
  ]
}
```

> ⚠️ `tab` **只认 `match_player`**，且**必须带 `team_id`**，否则返回 `参数错误`。

---

## 5. 赛事（Tournament）

### 5.1 赛事搜索 / 列表

```
GET /v1/api/csgo/mfilter/tournament/search?page=1&limit=20
```

```json
{
  "data": {
    "items": [
      { "name": "MESA Pro 2026 万圣节杯", "tt_id": "csgo_tt_9462" },
      { "name": "Stake 排位赛 第5季", "tt_id": "csgo_tt_9257" }
    ],
    "total_page": "24",
    "total_rows": "470"
  }
}
```

> 只有 `name` + `tt_id`，**没有**封面、时间、奖金。要拿到完整信息，得对每个 `tt_id` 再调 5.2。

### 5.2 赛事详情

```
GET /v1/api/csgo/tournaments/{tt_id}/introduction
```

```json
{
  "data": {
    "basic": {
      "tt_id": "csgo_tt_8251",
      "id": "22819",
      "name_zh": "BLAST 对抗赛 2026 S2",
      "name_en": "BLAST Rivals 2026 Season 2",
      "abbr_zh": "BLAST对抗赛 2026 S2",
      "abbr_en": "BLAST Rivals 2026 S2",
      "logo": "https://oss.5eplay.com/sport/csgo/event/7556.png",
      "bonus": "$1,000,000",
      "city_name": "中国香港赤鱲角",
      "start_time": "2026-11-09 00:00:00",
      "end_time": "2026-11-15 23:59:59",
      "grade": "2",
      "status": "upcoming",
      "current_stage_id": "4081",
      "tt_name_show": "BLAST 对抗赛 2026 S2",
      "character": ""
    },
    "cur_team_rank": [
      { "bonus": "$125,000 + Club $125,000", "cup_info": "", "metal_info": "", "point": "", "..." : "..." }
    ],
    "team_rank": []
  }
}
```

### 5.3 赛事赛程 / 对阵图

```
GET /v1/api/csgo/tournaments/{tt_id}/stages
```

`data[]` 每个元素是一个 stage，内含 `groups[]`，每个 group 有 `graph` —— 一个**超长 JSON 字符串**，是赛程树/对阵图的布局数据：

```json
{
  "id": "5585",
  "dEB": {
    "lanes": [{ "lowerRound": "0", "upperRound": "0" }, { "lowerRound": "-1", "upperRound": "1" }],
    "lowerEB": {
      "basic": { "name": "败者组" },
      "layout": { "ebWidth": 5890, "ebHeight": 208, "nodeSpace": 30, "nodeWidth": 190, "nodeHeight": 52, "roundSpace": 30 },
      "rounds": [
        {
          "rect": { "width": 190, "height": 26 },
          "basic": { "id": "", "desc": "", "name": "决赛", "end_ts": "", "start_ts": "", "match_days": null },
          "matches": [
            { "t1": { "TBD": true, "desc": "", "logo": "", "rect": "..." }, "t2": { "..." : "..." } }
          ]
        }
      ]
    }
  }
}
```

含 `matches[]`，每个有 `t1` / `t2` / `start_ts` / `end_ts`，可以解析出完整对阵图。

### 5.4 赛事摘要（含等级标签）

```
GET /v1/api/csgo/focus/tournaments?tt_ids=csgo_tt_8251,csgo_tt_9257
```

```json
{
  "data": {
    "items": [
      {
        "basic_info": {
          "id": "csgo_tt_8251",
          "disp_name": "BLAST 对抗赛 2026 S2",
          "abbr_zh": "BLAST对抗赛 2026 S2",
          "logo": "https://oss.5eplay.com/sport/csgo/event/7556.png",
          "bonus": "$1,000,000",
          "city_name": "中国香港赤鱲角",
          "color": "663dea",
          "grade": "2",
          "grade_label": "S级赛事",
          "start_time": "2026-11-09 00:00:00",
          "end_time": "2026-11-15 23:59:59",
          "status": "upcoming",
          "mode": "2",
          "cover": "https://oss.5eplay.com/cloudx/p/gamedata/csgo/csgo_default_cover.png"
        },
        "page_token": "22819"
      }
    ]
  }
}
```

> 支持逗号分隔多个 `tt_ids` 批量查 —— 这是**批量补全赛事信息的最省事方式**。

### 5.5 赛事等级枚举

```
GET /v1/api/csgo/mfilter/tournaments/options
```

```json
{
  "data": {
    "grade": [
      { "default": true,  "name": "不限等级", "type": "all", "value": ""  },
      { "default": false, "name": "Major",   "type": "",    "value": "1" },
      { "default": false, "name": "S+",      "type": "",    "value": "7" },
      { "default": false, "name": "S级",     "type": "",    "value": "2" },
      { "default": false, "name": "A级",     "type": "",    "value": "3" }
    ]
  }
}
```

`grade` 映射：`1`=Major，`7`=S+，`2`=S级，`3`=A级。

---

## 6. 队伍 / 选手

### 6.1 队伍列表

```
GET /v1/api/csgo/teams?page=1&limit=20
```

```json
{
  "data": {
    "items": [
      {
        "id": "csgo_tm_7020",
        "name": "Spirit",
        "highlight_name": "Spirit",
        "logo": "https://oss.5eplay.com/sport/csgo/team/merge_cgchcqhll806h1bg2lt0.png",
        "kd": "1.07",
        "kd_diff": "11214",
        "map_count": "2073",
        "players": [ { "name": "...", "player_id": "...", "country_logo": "...", "..." : "..." } ]
      }
    ]
  }
}
```

### 6.2 批量取队伍成员

```
GET /v1/api/csgo/team_players/batch?team_ids=csgo_tm_4494,csgo_tm_7020
```

```json
{
  "data": {
    "items": [
      {
        "id": "csgo_tm_4494",
        "name": "MOUZ",
        "logo": "https://oss.5eplay.com/sport/csgo/team/hz/cec3pf74nfq43340unp0.png",
        "players": [
          { "name": "torzsi", "player_id": "csgo_pl_18072", "portrait": "https://oss.5eplay.com/cloudx/p/sport/csgo/player/d6tkvpkconkpudhr3otg.png" }
        ]
      }
    ]
  }
}
```

### 6.3 队伍近期比赛

```
GET /v1/api/csgo/team/matches_v1/{team_id}?page=1&limit=20&status={0|1|2|3|4}
```

```json
{
  "data": {
    "items": {
      "game_played": "",
      "game_played_desc": "",
      "matches": [],
      "win_rate": "72.0",
      "win_rate_desc": "近三个月胜率72.0%",
      "wins_streak": "0"
    },
    "total_page": "0",
    "total_rows": "0"
  }
}
```

> ⚠️ **`matches` 实测恒为空**，`status` 的枚举没试出来。胜率字段有值，比赛列表不可用。见 [known-issues.md](known-issues.md)。
