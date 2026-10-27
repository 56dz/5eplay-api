# 接口总览

大多数接口是 `GET`，查询串放参数；但**所有「筛选/统计/榜单」类接口都是 `POST`**，参数放 JSON body。
返回统一 `application/json` 信封：

```json
{ "success": true, "errcode": 0, "message": "", "data": ... }
```

Base URL：

- 数据：`https://esports-data.5eplaycdn.com`
- 补充：`https://app.5eplay.com`
- 图片：`https://oss.5eplay.com`

> ⚠️ **最容易踩的坑：`POST` 接口用 `GET` 调用会返回 `404 page not found`**（不是 405）。
> 如果你照着路径拼 GET 却拿到 404，先怀疑方法写错了 —— `mfilter/*`、`new/rank/*`、`tournaments/team_data|player_data|map_data` 全是 POST。
> 反过来，`POST` 接口漏了 `Content-Type: application/json` 也会失败。

无需任何鉴权 header。`User-Agent` 随意（默认 curl UA 也能通）。

下文示例里的 ID 都是真实存在的：

| 类型 | ID | 说明 |
| --- | --- | --- |
| 比赛 | `csgo_mc_2399921` | 已结束 BO2 |
| 比赛 | `csgo_mc_2399893` | 直播中 BO3 |
| 比赛 | `csgo_mc_2399854` | 未开始 |
| 赛事 | `csgo_tt_8251` | BLAST 对抗赛 2026 S2 |
| 赛事 | `csgo_tt_9440` | 有完整赛事维度统计（126 名选手） |
| 队伍 | `csgo_tm_4494` | MOUZ（1613 场历史比赛） |
| 队伍 | `csgo_tm_7020` | Spirit |
| 选手 | `csgo_pl_11893` | ZywOo |

**参数速记**：

| 场景 | 正确写法 | 常见错法 |
| --- | --- | --- |
| 队伍近期比赛 | `?status=past` | ~~`?status=2`~~（静默返回空数组） |
| 赛事赛程（app） | `?tt_ids=csgo_tt_8251&limit=20` | ~~`?tt_id=22819`~~（不过滤） |
| 赛事赛果（app） | `?page_size=20&page_token=...` | ~~`?page=2&limit=20`~~（无效） |
| 选手近期比赛 | body 里 `"time_value":"<起点>_<终点>"` | ~~`~` 连接~~ / ~~留空~~（`time_value验证错误`） |
| 世界排名 | `POST` + `rank_type` 与 `sort_key` 同时改（`rank`=HLTV，`valve_rank`=VRS） | ~~只改 `sort_key`~~ |

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
| `quick_score` | **本图最终得分，直接用这个**（含加时） |
| `all_score` | 同上（通常相等） |
| `sh_score` / `sh_role` / `sh_data` | 上半场得分 / 我方阵营 / 每回合累计 |
| `fh_score` / `fh_role` / `fh_data` | 下半场得分 / 我方阵营 / 每回合累计 |
| `ot_score` / `ot_role` / `ot_data` | 加时得分 / （恒空）/ 每回合累计 |
| `flags` | 前端徽标标记，如 `["w10"]` |

`sh_data` 是**累计比分曲线**：索引 = 回合序号，值 = 该回合结束后的累计得分。可以直接拿去画走势图。

**加时赛（实测 19:16，`csgo_mc_2399119` Inferno）**

```json
{
  "quick_score": "19",
  "sh_score": "6", "sh_role": "CT", "sh_data": [0,1,1,1,1,1,0,0,4,0,0,0],
  "fh_score": "6", "fh_data": [0,3,2,3,0,0,0,0,2,0,3,2],
  "ot_score": "7", "ot_role": "",   "ot_data": [0,0,0,2,3,2,0,3,2,1,1,0],
  "all_score": "19",
  "flags": ["w10"]
}
```

- `sh_score + fh_score + ot_score == quick_score`（6+6+7=19 ✅）
- `ot_data` 长度 = 6 × 加时次数（两个 OT 为 12），双方互补
- 解析时把三段分开读即可

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

### 2.4 `global_state` — 全局状态（含 ban/pick 序列）

`global_state` 里有几个非常有用的字段：

| 字段 | 说明 |
| --- | --- |
| **`bp_map_item[]`** | **完整 ban/pick 序列**（见下） |
| `status` | 比赛状态 |
| `t1_score` / `t2_score` | 大比分 |
| `t1_quick_score` / `t2_quick_score` | 当前图比分 |
| `t1_odds` / `t2_odds` / `t1_odds_percent` / `t2_odds_percent` | 赔率 |
| `avg_player_stats` | 全队平均（字段同选手数据） |
| `max_player_stats` | 各项最佳（最高击杀、最高 ADR…） |
| `mvp_player_stats` | MVP 候选 |
| `bar_chart_player_stats` | 柱状图用的对比数据 |
| `milestones` | 里程碑 |
| `pr_stats` | 亮点对比 |
| `t1_player_stats` / `t2_player_stats` | 选手数据（同 `bouts_state`） |
| `t1_player_stats_ct` / `_t` | 分半场 |
| `is_general` / `is_show_diagram` / `ana_map_desc_flag` | 前端开关 |
| `disp_name` | `"地图总览"` |
| `live_status` / `log_text` | 直播状态文案 |
| `dark_horse` | 冷门提示 |

#### `bp_map_item[]` — 完整 ban/pick 序列 ★

**这就是你要的选图过程。** 已结束和进行中的比赛都有，7 条（BO3）：

```json
[
  { "bp_type": "ban",  "map_name": "Nuke",    "team_side": "t2", "map_icon": "https://...", "map_logo": "https://..." },
  { "bp_type": "ban",  "map_name": "Anubis",  "team_side": "t1", "map_icon": "...", "map_logo": "..." },
  { "bp_type": "pick", "map_name": "Ancient", "team_side": "t2", "map_icon": "...", "map_logo": "..." },
  { "bp_type": "pick", "map_name": "Dust2",   "team_side": "t1", "map_icon": "...", "map_logo": "..." },
  { "bp_type": "ban",  "map_name": "Cache",   "team_side": "t2", "map_icon": "...", "map_logo": "..." },
  { "bp_type": "ban",  "map_name": "Mirage",  "team_side": "t1", "map_icon": "...", "map_logo": "..." },
  { "bp_type": "left", "map_name": "Inferno", "team_side": "",   "map_icon": "...", "map_logo": "..." }
]
```

| 字段 | 值 |
| --- | --- |
| `bp_type` | `ban` 禁用 / `pick` 选图 / `left` 剩下的决胜图 |
| `map_name` | 地图名 |
| `team_side` | `t1` / `t2` / `""`（`left` 时为空） |
| `map_icon` / `map_logo` | 两种尺寸的图 |

数组顺序就是实际的 ban/pick 顺序。`left` 的那张是 decider。

> 注意：`bouts_state[].bp_act` 只是这张图"是谁选的"（`t1_pick` / `t2_pick`），要看完整序列用 `global_state.bp_map_item`。

### 2.5 增量 / 实时

`/data` 的响应顶层还有三个字段：

```json
{
  "data": {
    "state_ver": "00017930921572",
    "local_ver": 0,
    "eplus_realtime_topic": "csgo/product/eplus/csgo_mc_2399921_d1ffd54d445591d",
    "match": { ... }
  }
}
```

- `state_ver`：这场比赛数据的状态版本号
- `eplus_realtime_topic`：MQTT 推送的 topic 名，见下一节
- ⚠️ 实测传 `?state_ver=` / `?local_ver=` **不减少响应体积**（都是全量 60–125 KB）。`/data` 没有可用的增量参数，增量只能走 MQTT。

### 2.6 实时推送（MQTT over WSS）★ 已打通

`/data` 只能全量拉，真正的增量更新走**阿里云 MQTT over WebSocket**。全链路：

```
① 取临时凭证   POST https://www.5eplay.com/api/restrict/matchscore
                    body: {"topic": "<topic>", "client_id": "<任意字符串>"}
② 连 Broker    wss://post-cn-7mz2e5hc90i.mqtt.aliyuncs.com:443
③ 订阅 topic   用 ① 返回的 username / password 做 MQTT 认证
```

**① 取凭证**：

```bash
curl -s -X POST 'https://www.5eplay.com/api/restrict/matchscore' \
  -H 'Content-Type: application/json' \
  -d '{"topic":"csgo/product/detail/csgo_mc_2399893","client_id":"my-client-001"}'
```

```json
{
  "success": true,
  "errcode": 0,
  "message": null,
  "data": {
    "client_id": "GID_5EPLAY@@@my-client-001",
    "username": "Token|LTAI5t****（阿里云 AccessKeyId 前缀）|post-cn-7mz2e5hc90i",
    "password": "RW|LzMT+XLFl5s/YWJ/...（约 700 字符，一次性）"
  }
}
```

- `client_id` 服务端会加 `GID_5EPLAY@@@` 前缀回给你，**连接时必须用返回的这个值**，不是你传的那个。
- `password` 是一次性签名，每次请求都不同，别缓存。
- 无需登录态，无需 Referer/Origin（实测裸 curl 即可）。

**topic 命名**（`{mc_id}` = `csgo_mc_xxxxxxx`，`{tt_id}` = 赛事 ID）：

| topic | event_name | 用途 |
| --- | --- | --- |
| `csgo/product/detail/{mc_id}` | `csgo-detail` | 单场比赛全量快照 + 增量（结构同 `/data` 的 `match`） |
| `csgo/product/event/log/{mc_id}` | `csgo-event-log` | 逐回合流水增量（同 `/match/{id}/event/log`） |
| `csgo/product/agenda` | `csgo-agenda` | 全站赛程变化（`changed_matches[]`） |

**② ③ 订阅**（Python + `paho-mqtt`，这是唯一需要第三方库的地方）：

```python
import json, subprocess, time
import paho.mqtt.client as mqtt

topic = "csgo/product/detail/csgo_mc_2399893"
r = subprocess.run(['curl','-s','-X','POST','https://www.5eplay.com/api/restrict/matchscore',
    '-H','Content-Type: application/json',
    '-d', json.dumps({"topic": topic, "client_id": "my-client-001"})],
    capture_output=True, text=True)
cred = json.loads(r.stdout)['data']

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                client_id=cred['client_id'], transport='websockets')
c.username_pw_set(cred['username'], cred['password'])
c.tls_set()                       # 必须 TLS
c.on_connect = lambda cl, u, f, rc, p=None: cl.subscribe(topic)
c.on_message = lambda cl, u, msg: print(msg.payload.decode())
c.connect("post-cn-7mz2e5hc90i.mqtt.aliyuncs.com", 443, 30)
c.loop_start(); time.sleep(30); c.loop_stop()
```

**推送消息格式**（实测 `csgo-detail`，12 KB 一帧）：

```json
{
  "event_name": "csgo-detail",
  "data": {
    "from_ver": "00017930942673",
    "match": {
      "bouts_state": [ ... ],
      "global_state": { ... }
    }
  }
}
```

`csgo-event-log` / `csgo-agenda` 都带 `from_ver` + `to_ver`（19 位数字版本号，**不是** `/data` 里的 `state_ver`），可用来判断是否有跳帧：

```json
{"event_name":"csgo-event-log","data":{"info":{...},"from_ver":1793094307113620888,"to_ver":1793094312202663912}}
{"event_name":"csgo-agenda","data":{"changed_matches":[...],"from_ver":1793094317798594375,"this_ver":1793094342076788456}}
```

**实测记录**：对进行中的 `csgo_mc_2399893`（FlyQuest vs Rooster）订阅 `csgo/product/detail/` 立刻收到 1 帧 12128 字节的全量快照；`csgo/product/event/log/` 15 秒内收到 3 帧；`csgo/product/agenda` 20 秒内收到 2 帧。对**已结束**的 `csgo_mc_2399921` 订阅 12 秒收到 0 帧（连接成功但无推送），符合预期。

**对流量敏感客户端的建议**：先 `GET /data` 拿一次全量快照（拿到 `state_ver`），然后只连 MQTT 收增量，不要循环轮询 `/data`。MQTT 每帧 12 KB 左右，比每 5 秒重拉 125 KB 省得多。

---

## 2bis. 赛前分析 / 战队对比

```
GET /v1/api/csgo/matches/{mc_id}/analysis_v1
```

约 90 KB。给"赛前数据对比"页面用：

```json
{
  "data": {
    "state_ver": "...",
    "result": {
      "mc_info": { ... },
      "tt_info": { ... },
      "comparison": {
        "t1_stats": { "rating": "1.09", "kd": "1.04", "win_rate": "58", "f_rate": "43", "s_rate": "49" },
        "t2_stats": { ... },
        "t1_player_stats": [
          { "id": "csgo_pl_18638", "name": "sk0R", "Rating": "1.17", "adr": "81.5",
            "kast": "72.4", "kd": "1.14", "kpr": "0.74", "impact": "0",
            "mk_rating": "...", "swing": "...",
            "country_name": "蒙古", "country_logo": "https://...", "logo": "https://...", "half_logo": "https://..." }
        ],
        "t2_player_stats": [ ... ],
        "team_map_stats": [
          { "name": "Ancient", "name_zh": "远古遗迹", "bp_type": "t2_pick",
            "icon": "https://...", "bgm": "https://...",
            "t1_pick_rate": "8", "t1_ban_rate": "26", "t1_win_num": "15", "t1_rate": "60",
            "t2_pick_rate": "...", "t2_ban_rate": "...", "t2_win_num": "...", "t2_rate": "..." }
        ],
        "ana_map_desc_flag": true
      },
      "power_comparison": { "is_hide": "1", "t1_player_stats": [...], "t2_player_stats": [...] },
      "rec_vs_matches": { "matches": [], "t1_win_rate": "", "t2_win_rate": "" },
      "t1_rec_matches": { ... },
      "t2_rec_matches": { ... }
    }
  }
}
```

| 区块 | 用途 |
| --- | --- |
| `comparison.t1_stats` / `t2_stats` | 队伍整体系数：Rating / K/D / 胜率 / 首杀率 / 残局率 |
| `comparison.t1_player_stats[]` | 选手赛前数据（**注意字段名是 `Rating` 大写 R**，和 `/data` 里的 `rating` 不同） |
| `comparison.team_map_stats[]` | **每张图的双方 pick/ban 率与胜率** —— 做"地图池对比"用 |
| `power_comparison` | 选手能力雷达图数据，`is_hide:"1"` 表示当前不展示 |
| `rec_vs_matches` / `t1_rec_matches` / `t2_rec_matches` | 两队近期交手记录 —— ⚠️ 实测 `matches` 为空 |

> ⚠️ `analysis_v1` 的 `t1_player_stats[].Rating` 是**大写开头**，`kast` 是 `"72.4"`（不带 %），`/data` 里是 `kast: "75.0%"`。两个接口的格式不一致，别混用。

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

### 5.1 赛事列表 ★ 真正的批量接口（POST，走 app.5eplay.com）

**注意：不是** `GET /v1/api/csgo/tournaments`（那个永远空，见 known-issues）。真正的赛事列表是 `app.5eplay.com` 上的 **POST** 接口：

```
POST https://app.5eplay.com/api/csgo/tournament/csgo_event_list_v1
Content-Type: application/json
```

请求体所有筛选条件都塞在 `tournaments_options` 里：

```json
{
  "tournaments_options": {
    "cursor": "",
    "page_token": "",
    "time_type": null,
    "time_value": null,
    "grade": [],
    "tt_series": [],
    "tt_bonus": [],
    "team_id": "",
    "player_id": ""
  }
}
```

```bash
curl -s -X POST 'https://app.5eplay.com/api/csgo/tournament/csgo_event_list_v1' \
  -H 'Content-Type: application/json' \
  -d '{"tournaments_options":{"cursor":"","page_token":"","time_type":null,"time_value":null,
       "grade":[],"tt_series":[],"tt_bonus":[],"team_id":"","player_id":""}}'
```

实测一次返回 **21 条**（含 `live` / `upcoming` / `past` 三种状态混排）。

```json
{
  "success": true,
  "errcode": 0,
  "message": null,
  "data": {
    "items": [
      {
        "basic_info": {
          "id": "csgo_tt_9463",
          "disp_name": "ViderGG CTRL 第二季",
          "abbr_zh": "", "abbr_en": "",
          "logo": "https://oss.5eplay.com/cloudx/p/sport/csgo/tournament/d2plorkconkqbk3bnm00.png",
          "cover": "https://oss.5eplay.com/cloudx/p/gamedata/csgo/csgo_default_cover.png",
          "bonus": "$1,629",
          "city_name": "巴基斯坦-卡拉奇",
          "grade": "5",
          "grade_label": "C级赛事",
          "special_grade_label": "",
          "color": "7983a2",
          "special_color": "",
          "mode": "2",
          "start_time": "2026-10-25 00:00:00",
          "end_time": "2026-10-25 23:59:59",
          "status": "past"
        },
        "page_token": "2026-10-25 00:00:00,csgo_tt_9463",
        "recent_match": null,
        "teams": [
          { "id": "csgo_tm_10287", "name": "Legion", "abbr": "Legion", "logo": "..." },
          { "id": "hltv_team_14110", "name": "BadKids", "abbr": "", "logo": "..." }
        ],
        "win_team": { "id": "hltv_team_14110", "name": "BadKids", "abbr": "", "logo": "..." },
        "is_follow": 0
      }
    ],
    "stats": [],
    "api_go": true
  }
}
```

#### 参数

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `cursor` | string | 分页方向：`""` 首页 / `"next"` 向后 / `"prev"` 向前 |
| `page_token` | string | 分页锚点，取上一页最后一条的 `page_token`（格式 `开始时间,tt_id`） |
| `time_type` | string/null | `"self"` 用自定义区间、`"recent"` 最近、`null` 不限 |
| `time_value` | string/null | `"YYYY-MM-DD 00:00:00_YYYY-MM-DD 23:59:59"`，仅 `time_type="self"` 时生效 |
| `grade` | string[] | 赛事等级，见 5.5。`["2","7"]` = S级 + S+ |
| `tt_series` | string[] | 赛事系列：`major` / `blast` / `iem` / `esl` |
| `tt_bonus` | string[] | 奖金档位过滤（字符串，如 `"$1,000,000"`） |
| `team_id` | string | 只看某支队伍参加的赛事，如 `csgo_tm_4494` |
| `player_id` | string | 只看某个选手参加的赛事，如 `csgo_pl_11893` |

#### 分页（实测）

`cursor` 和 `page_token` **必须配对使用**，只传 `page_token` 不生效（会原样返回第一页）：

```python
# 第 1 页
d  = call({"cursor": "", "page_token": "", ...})
tok = d["data"]["items"][-1]["page_token"]        # "2026-11-09 00:00:00,csgo_tt_8251"

# 第 2 页（向后）
call({"cursor": "next", "page_token": tok, ...})   # → 2026-11-12 ~ 2027-01-27
call({"cursor": "next", "page_token": <新的最后一条>, ...})   # → 2027-02-08 ~ 2027-10-08

# 往前翻
call({"cursor": "prev", "page_token": "", ...})    # → 2027-11-22 ~ 2028-11-20
```

实测翻页结果：

| 请求 | 返回区间 |
| --- | --- |
| `cursor=""` 首页 | 2026-10-25 → 2026-11-09 |
| `cursor="next"` + 首页末条 token | 2026-11-12 → 2027-01-27 |
| 继续 `next` | 2027-02-08 → 2027-10-08 |
| `cursor="prev"` 空 token | 2027-11-22 → 2028-11-20 |

> 注意排序是按 `start_time` 升序（首页就从 2026-10 开始，往后是未来赛事）。要拿历史赛事请用 `time_type:"self"` 指定区间，实测 `2024-01-01_2024-12-31` 返回 20 条全部 `past`。

#### 筛选项实测

| 请求 | items | 说明 |
| --- | --- | --- |
| 裸请求 | 21 | 三种状态混排 |
| `tt_series:["iem"]` | 3 | IEM 系列 |
| `grade:["1"]` | 8 | Major |
| `grade:["2","7"]` | 21 | S级 + S+ |
| `time_type:"recent"` | 21 | 最近 |
| `time_type:"self"` + 2024 全年 | 20 | 全 `past` |
| `team_id:"csgo_tm_4494"` | 14 | MOUZ 参加的 |
| `player_id:"csgo_pl_11893"` | 2 | ZywOo 参加的 |

> `status` 不是请求参数，是返回字段（`live` / `upcoming` / `past`），客户端自己按它过滤。实测 `time_value` 为 `null` 时区间筛选会被忽略。

### 5.1bis 赛事搜索（轻量备选）

如果只想要名字做下拉框，这个更省流量（但也只有 name + id）：

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

> 只有 `name` + `tt_id`，**没有**封面、时间、奖金。要完整信息用 5.1 或对每个 `tt_id` 调 5.2。

### 5.1ter 赛事筛选项枚举

```
GET /v1/api/csgo/mfilter/tournaments/options
```

返回 `grade` / `main_tt` / `time` / `tt_bonus` / `tt_series` 五个数组，每项 `{name, value, type, default}`，直接喂给 5.1 的对应参数。`value` 为 `""` 且 `type:"all"` 的项表示「不限」。**筛选项全部由服务端下发、带 `default` 标记，前端照抄即可**，不用自己硬编码。

`grade`（12 项，与 5.5 一致）：

| `value` | 名称 |
| --- | --- |
| `""` | 不限等级（默认） |
| `1` | Major（默认选中） |
| `7` | S+ |
| `2` | S级 |
| `3` | A级 |
| `9` | 资格赛A级 |
| `8` | 表演赛 |
| `4` | B级 |
| `6` | 资格赛B级 |
| `5` | C级 |
| `10` | 资格赛C级 |
| `0` | 其他 |

`main_tt`（主赛事分组，只有 2 项，`name` 直接是图标 URL）：

| `value` | 含义 |
| --- | --- |
| `""` | 全部赛事 |
| `1,7,2,3,9` | 顶级赛事（Major / S+ / S / A / 资格赛A 的合集） |

`tt_bonus`（奖金区间，**值本身是 SQL 片段**，直接当查询值用）：

| `value` | 含义 |
| --- | --- |
| `""` | 不限奖金 |
| `<= 100000` | 10 万美元以下 |
| `BETWEEN 100000 AND 500000` | 10 万–50 万 |
| `BETWEEN 500000 AND 1000000` | 50 万–100 万 |
| `>= 1000000` | 100 万美元以上 |

`time`（15 项，`type` 决定配套传哪个 `time_type`）：

```json
[
  { "default": false, "name": "不限时间", "type": "all", "value": "" },
  { "default": false, "name": "自定义",   "type": "self", "value": "" },
  { "default": false, "name": "近一个月", "type": "recent", "value": "2026-09-27 00:00:00_2026-10-27 23:59:59" },
  { "default": true,  "name": "近三个月", "type": "recent", "value": "2026-07-27 00:00:00_2026-10-27 23:59:59" },
  { "default": false, "name": "近半年",   "type": "recent", "value": "2026-04-27 00:00:00_2026-10-27 23:59:59" },
  { "default": false, "name": "近一年",   "type": "recent", "value": "2025-10-27 00:00:00_2026-10-27 23:59:59" },
  { "default": false, "name": "2026年",   "type": "year",   "value": "2026-01-01 00:00:00_2026-12-31 23:59:59" }
]
```

> ⚠️ **时间区间的值是「两个时间用下划线连起来」** —— `"起点_终点"`，不是 `~`、不是两个字段。
> `type` 的取值只有 `all` / `self` / `recent` / `year` 四种，`self` 表示用户自选时间。
> 这些值随「今天」浮动（服务端按请求时间算），**不要缓存超过一天**。

`tt_series`（赛事系列）：`""` 不限 / `major` / `blast` / `iem` / `esl`。

### 5.1quater 赛事奖金分配（`team_rank`）

赛事详情（5.2）里的 `cur_team_rank` / `team_rank` 就是奖金分配表，**两个字段内容基本一样**：

| 字段 | 含义 | 实测差异 |
| --- | --- | --- |
| `cur_team_rank` | 当前已确定的名次 | 只列已经打进/已结束的名次 |
| `team_rank` | 完整名次表 | 未开赛也有全部名次（队伍为 `TBD`） |

`csgo_tt_8251`（BLAST 2026 S2，未开赛）：`cur_team_rank` 6 条、`team_rank` 8 条。
`csgo_tt_9463`（已结束小组赛）：两者都是 2 条。

每项结构：

```json
{
  "rank": "3-4",
  "bonus": "$40,000 + Club $90,000",
  "point": "",
  "point_type": "BLAST积分",
  "metal_info": "",
  "cup_info": "",
  "team": { "id": "", "name": "TBD", "logo": "" }
}
```

- `rank` **是字符串**，可能是区间（`"3-4"` / `"5-8"`），不能直接转 int。
- `bonus` 是**原始展示串**，含 `+`（并列奖金 + 俱乐部奖金）。要数值得自己正则抽第一个数字。
- `point` / `point_type` 是积分制赛事才有（如 BLAST 积分）。
- `metal_info` / `cup_info` 是奖牌/奖杯图，普通赛事为空串。
- `team` 未确定时是 `{"id":"","name":"TBD"}`。

> 队伍自己的「拿过多少奖金」在 `team_rank[].bonus`；队伍生涯总奖金走 `overview` 的
> `total_earnings`（6.5）。两者口径不同（前者是单届名次奖金）。

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

### 5.3 赛事赛程 / 对阵图 ★ 可解析

```
GET /v1/api/csgo/tournaments/{tt_id}/stages
```

**这是拿完整赛程树（对阵图）的接口。** 返回 `data[]`，每个元素是一个 stage：

```
data[] = [
  {
    "stageInfo": { ... },          // 阶段元信息
    "groups": [
      {
        "id": "5587",
        "name": "淘汰赛",
        "stageId": "4081",
        "legend_config": { ... },
        "graph": "<JSON 字符串>"    // ← 对阵图本体，需再 parse 一次
      }
    ]
  }
]
```

`graph` 解析后：

```json
{
  "id": "5585",
  "name": "淘汰赛",
  "stageId": "4081",
  "dEB": {
    "lanes": [
      { "lowerRound": "0", "upperRound": "0" },
      { "lowerRound": "-1", "upperRound": "1" }
    ],
    "upperEB": {
      "basic": { "name": "胜者组" },
      "layout": { "ebWidth": 5890, "ebHeight": 208, "nodeSpace": 30, "nodeWidth": 190, "nodeHeight": 52, "roundSpace": 30 },
      "rounds": [
        {
          "rect": { "width": 190, "height": 26 },
          "basic": { "name": "首轮", "start_ts": "", "end_ts": "" },
          "matches": [
            {
              "absId": "csgo_mc_2399851",
              "format": "3",
              "planTs": "2026-11-11 11:00:00",
              "status": "upcoming",
              "result": "draw",
              "t1Score": "0",
              "t2Score": "0",
              "roundNum": 0,
              "isManual": "0",
              "graphId": "...",
              "t1": { "TBD": false, "absId": "hltv_team_12468", "abbrEn": "Legacy", "abbrZh": "", "nameEn": "", "nameZh": "", "logo": "https://...", "fromMatchId": "", "fromDesc": "", "rect": {...} },
              "t2": { "TBD": true,  "absId": "",                "abbrEn": "",       "abbrZh": "", "nameEn": "", "nameZh": "", "logo": "",                "fromMatchId": "", "fromDesc": "", "rect": {...} },
              "rect": { "top": 56, "width": 190, "height": 52, "headLine": {...} }
            }
          ],
          "winners": [...],
          "stackIndex": ...,
          "byeRoundLines": [...]
        }
      ]
    },
    "lowerEB": { ... }    // 败者组，结构同上；单败淘汰赛没有这个键
  }
}
```

**关键：`matches[].absId` 就是 `csgo_mc_xxx` 比赛 ID**，可以直接拿去拉 `/matches/{id}/data`。

对阵图解析要点：

| 字段 | 说明 |
| --- | --- |
| `dEB.upperEB` / `dEB.lowerEB` | 胜者组 / 败者组（单败赛制只有 `upperEB`） |
| `rounds[]` | 每一轮（首轮、四强、决赛…），`basic.name` 是轮次名 |
| `rounds[].matches[]` | 该轮的比赛节点 |
| `matches[].absId` | 比赛 ID，空字符串 = 还没排定 |
| `matches[].t1` / `t2` | 参赛队伍，`TBD:true` 表示未定 |
| `matches[].t1.absId` | 队伍 ID（**注意是 `hltv_team_xxx` 前缀，不是 `csgo_tm_`**） |
| `matches[].t1.abbrEn` / `nameZh` | 队名（页面上显示的那个） |
| `matches[].t1.fromMatchId` | 如果队伍来自上一轮某场比赛，这里是那场的 ID |
| `matches[].t1.fromDesc` | 如 `"胜者组决赛胜者"` |
| `matches[].planTs` | 比赛时间，`"2026-11-11 11:00:00"` 格式 |
| `matches[].status` | `upcoming` / `ongoing` / `finished` |
| `matches[].result` | `"draw"` 未打 / 其他值见下 |
| `matches[].t1Score` / `t2Score` | 大比分 |
| `matches[].rect` | **布局坐标**（top/left/width/height），画对阵图时直接用，不用自己算 |

> `rect` 是服务端算好的绝对坐标，`ebWidth: 5890` / `ebHeight: 208` 是整个图布的画布尺寸。要做对阵图 UI，直接按这些坐标摆节点即可。

> ⚠️ 队伍 ID 有两种前缀：比赛详情里是 `csgo_tm_xxx`，对阵图里是 `hltv_team_xxx`。两者不能混用，跨接口查队伍时要留意。

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

同一个接口 `GET /v1/api/csgo/mfilter/tournaments/options` 里的 `grade` 数组，完整枚举见 5.1ter 的表。

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

`grade` 映射：`1`=Major，`7`=S+，`2`=S级，`3`=A级，`9`=资格赛A级，`8`=表演赛，
`4`=B级，`6`=资格赛B级，`5`=C级，`10`=资格赛C级，`0`=其他。

### 5.6 赛事赛程 / 赛果（app.5eplay.com）

赛事详情页的「赛程」「赛果」两个 tab 走的是 **app 域名**，不是 CDN 域名：

```
GET https://app.5eplay.com/api/tournament/session_list?game_type=1&limit=20&page=1
GET https://app.5eplay.com/api/tournament/session_result_list?game_type=1&page_size=20
```

```bash
curl -s 'https://app.5eplay.com/api/tournament/session_list?game_type=1&tt_ids=csgo_tt_8251&limit=20'
```

⚠️ **两个接口的参数名不一样，别套用**：

| 接口 | 条数参数 | 翻页 | 赛事过滤 |
| --- | --- | --- | --- |
| `session_list` | `limit`（1–50） | `page` | **`tt_ids=csgo_tt_8251`**（可逗号多个）✅ |
| `session_result_list` | `page_size`（1–50） | `page_token`（见下） | ❌ 传 `tt_id` / `tt_ids` 都**不过滤**（实测 `tt_id=999999` 照样返回同一批） |

**`session_list` 是全局赛程流，必须显式传 `tt_ids` 才是「这个赛事的赛程」**：

| 请求 | 返回条数 | 说明 |
| --- | --- | --- |
| 不传 `tt_ids`，`limit=50` | 50 | 全站赛程，混着 8 个赛事 |
| `tt_ids=csgo_tt_8251&limit=50` | 4 | 只剩该赛事 |
| `tt_ids=csgo_tt_9440&limit=50` | 47 | 同上 |
| `tt_ids=csgo_tt_8251,csgo_tt_8245&limit=50` | 12 | 多个赛事 |

`tt_id=22819`（纯数字）**不生效**，还是要用 `csgo_tt_*`。

`session_result_list` 翻页用 `page_token`，格式是 **`"YYYY-MM-DD HH:mm:ss,id1,id2"`** ——
时间取上一页最后一条的 `mc_info.plan_ts` 转成 UTC 字符串，后面跟同一时刻的所有 `mc_id`（同一时刻可能有多场）。
`page` / `limit` 对它无效（`page=2&limit=3` 还是返回同一批 10 条）。

```bash
# 第一页 20 条，取最后一条的 plan_ts 和 id
curl -s 'https://app.5eplay.com/api/tournament/session_result_list?game_type=1&order_by=asc&page_size=20'
# 假设最后一条是 2026-10-27 09:00:00 / csgo_mc_2399120
curl -s 'https://app.5eplay.com/api/tournament/session_result_list?game_type=1&order_by=asc&page_size=20&page_token=2026-10-27%2009%3A00%3A00%2Ccsgo_mc_2399120'
```

`order_by=asc` 表示按时间正序，不传是倒序。`plan_ts` 是**秒级时间戳**（不是毫秒）。

> 想拿「某赛事的全部比赛」别用这个，直接用 **9.4 的 `tournaments/match_list?tt_ids=`**，一次给全且带比分。

```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "mc_info": {
          "id": "csgo_mc_2399854",
          "t1_info": { "disp_name": "MOUZ", "...": "..." },
          "t2_info": { "disp_name": "G2", "...": "..." },
          "plan_ts": 1794393000,
          "round_name": "首轮",
          "tt_stage": "淘汰赛"
        },
        "tt_info": { "id": "csgo_tt_8251" },
        "state": { "status": "0", "...": "..." }
      }
    ]
  }
}
```

| 接口 | 用途 | `data` 额外键 |
| --- | --- | --- |
| `session_list` | 赛程（未开赛 + 进行中） | `matches` / `state_ver` |
| `session_result_list` | 赛果（已结束） | `matches` / `state_ver` / `state_ver_v1` / `today_mc_total` |

- `game_type=1` 是 CS2，省略也行（该域名下只服务 CS2）。
- `stage_id` 传了不生效（实测 `stage_id=4081` 结果不变），**要按赛段筛得自己按 `round_name` / `tt_stage_desc` 分组**。
- 元素结构和第 1 章比赛列表**完全一致**，`mc_info` 可直接复用同一套解析代码。

> `event_session_list`（chunk 里见过）是 DOTA2 专用，CS2 传 `game_type=2` 返回空，别用。

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

### 6.3 队伍近期比赛 ★ 已解（`status` 是字符串枚举）

```
GET /v1/api/csgo/team/matches_v1/{team_id}?page=1&limit=20&status=past
```

**关键：`status` 不是 0/1/2 的数字，是字符串 `past` / `upcoming`。** 之前一直传数字所以 `matches` 恒空。

```bash
# 历史比赛（MOUZ，共 1613 场）
curl -s \
  'https://esports-data.5eplaycdn.com/v1/api/csgo/team/matches_v1/csgo_tm_4494?page=1&limit=5&status=past'

# 未来赛程
curl -s \
  'https://esports-data.5eplaycdn.com/v1/api/csgo/team/matches_v1/csgo_tm_4494?page=1&limit=5&status=upcoming'
```

#### `status` 枚举实测

对 `csgo_tm_4494`（MOUZ）逐一试：

| `status` | `matches` | `total_rows` | 说明 |
| --- | --- | --- | --- |
| `past` | **5** | **1613** | 历史比赛 ✅ |
| `upcoming` | **3** | **3** | 未来赛程 ✅ |
| `live` | 0 | 0 | 无进行中 |
| `0` / `1` / `2` | 0 | 0 | ❌ 数字不认，静默返回空 |
| 省略（空） | 5 | 1613 | 默认等同 `past` |

> 数字 `status` 不报错、`success` 仍为 `true`，只是 `matches` 空 —— 这就是之前一直被误导的原因。**只有 `past` / `upcoming` 两个合法值。**

#### 返回结构

> ⚠️ **注意：这个接口的 `mc_info` 跟第 1 章比赛列表的 `mc_info` 结构不一样！**
> 它没有 `t1_info` / `t2_info`，而是 `home_info` / `opponent_info`。
> **`home_info` 恒为被查询的那支队伍**（不是主队），`opponent_info` 是它的对手。

```json
{
  "success": true,
  "errcode": 0,
  "message": "",
  "data": {
    "items": {
      "game_played": "",
      "game_played_desc": "",
      "matches": [
        {
          "mc_info": {
            "id": "csgo_mc_2398757",
            "ts": "1791730800",
            "status": "past",
            "match_status": "2",
            "result": "opponent_win",
            "format": "3",
            "grade": "2",
            "home_info":      { "id": "csgo_tm_4494", "disp_name": "MOUZ",     "logo": "...", "rank": "", "v_rank": null },
            "opponent_info":  { "id": "csgo_tm_9565", "disp_name": "Vitality", "logo": "...", "rank": "", "v_rank": null },
            "home_score": "0",
            "opponent_score": "3",
            "home_quick_score": "0",
            "opponent_quick_score": "3",
            "t1_score": "3",
            "t2_score": "0",
            "bouts_result": ["away", "away", "away"],
            "dark_horse": "0",
            "tt_stage": "淘汰赛",
            "tt_stage_desc": "淘汰赛 决赛",
            "t1_odds": "1.85", "t1_odds_percent": "54",
            "t2_odds": "2.05", "t2_odds_percent": "46",
            "high_lights_cfg_list": [ ... ],
            "live_cfg_list": [ ... ]
          },
          "tt_info": { "id": "csgo_tt_...", "disp_name": "...", "...": "..." }
        }
      ],
      "win_rate": "72.0",
      "win_rate_desc": "近三个月胜率72.0%",
      "wins_streak": "0"
    },
    "total_page": "323",
    "total_rows": "1613"
  }
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| **`home_info`** | **被查询的那支队伍**，恒在同一侧。跨队伍查（MOUZ / Vitality / Spirit）都验证过 |
| `opponent_info` | 对手 |
| `home_score` / `opponent_score` | ⭐ **用这两个算胜负**，跟 `home_info` 严格对应 |
| `home_quick_score` / `opponent_quick_score` | 同上，历史场次恒等于 `home_score` |
| `t1_score` / `t2_score` | ⚠️ **别用**。这是比赛本身的 t1/t2 视角，而响应里**没有** `t1_info`/`t2_info`，无法对应到队伍。实测同一场 `csgo_mc_2398757`：`home_score=0`、`opponent_score=3`，但 `t1_score=3`、`t2_score=0`（因为比赛侧 t1 是 Vitality，不是 MOUZ） |
| `result` | `"home_win"` / `"opponent_win"` / `"draw"`（未开始也是 `draw`） |
| `status` | `"past"` / `"upcoming"` / `"live"`，跟请求参数一致 |
| `match_status` | 数字状态：`"0"` 未开始 / `"1"` 进行中 / `"2"` 已结束 |
| `ts` | 比赛时间戳（秒）。**这个接口没有 `plan_ts`** |
| `tt_stage` / `tt_stage_desc` | 阶段名 / 阶段全称（`"小组赛"` / `"小组赛 胜者组 首轮"`） |
| `t1_odds` / `t1_odds_percent` | 赛前赔率与胜率预测（百分比字符串） |
| `items.win_rate` | 近三个月胜率（百分数字符串），**不受 `status` 影响**，永远有值 |
| `items.win_rate_desc` | 胜率的中文描述，可直接展示 |
| `items.wins_streak` | 连胜/连败数 |
| `total_rows` / `total_page` | 总场次 / 总页数 |
| `mc_info.bouts_result[]` | 每张图谁赢：`"home"` / `"away"` / `""`（未打） |
| `mc_info.high_lights_cfg_list[]` | 录像回放链接（`url` 是 5E 的 iframe 包装页，需解 base64 `video` 参数） |
| `mc_info.live_cfg_list[]` | 直播源（斗鱼 / 虎牙 / B 站），`third_url` 是原始地址 |
| `mc_info.dark_horse` | 是否「以弱胜强」标记 |
| `mc_info.home_info.v_rank` | VRS 排名（这个接口里恒为 `null`；要 VRS 用第 8 章） |

> 要拿这场比赛的全部细节（每图比分 / 选手数据 / ban-pick），用 `mc_info.id` 去调第 2 章的 `/matches/{id}/data`。

#### `limit` 上限

实测 `limit=200` 也照常返回 200 条，**没有硬上限**（与 `/v1/api/csgo/matches` 的 100 上限不同）。但为了对方服务器，建议 ≤ 50。

> 分页：`page` 从 1 开始，配 `total_page` 翻页。

### 6.4 队伍参加过的赛事

```
GET /v1/api/csgo/team/tt/{team_id}
```

```json
{
  "data": {
    "items": [
      {
        "id": "csgo_tt_8251",
        "disp_name": "BLAST 对抗赛 2026 S2",
        "abbr_zh": "BLAST对抗赛 2026 S2",
        "abbr_en": "BLAST Rivals 2026 S2",
        "bonus": "$1,000,000",
        "grade": "2",
        "grade_label": "S级赛事",
        "city_name": "中国香港赤鱲角",
        "start_time": "...", "end_time": "2026-11-15 23:59:59",
        "logo": "https://oss.5eplay.com/...", "cover": "https://oss.5eplay.com/..."
      }
    ]
  }
}
```

> 返回的是精简版赛事对象（字段同 5.1 的 `basic_info`），不含赛程。要赛程用 5.3。

### 6.5 队伍详情页接口

队伍详情页 `https://event.5eplay.com/csgo/team/{team_id}` 用到以下接口：

| 接口 | 说明 |
| --- | --- |
| `GET /v1/api/csgo/teams/{id}/overview?time_type=1` | 队伍概览（成员、近况、地图池） |
| `GET /v1/api/csgo/teams/{id}/honors` | 队伍荣誉（冠军/亚军记录） |
| `GET /v1/api/csgo/teams/{id}/matches?page=1&limit=20` | 近期比赛（**另一个接口**，`data.rec_matches.matches[]`，条数少，推荐用 6.3） |
| `GET /v1/api/csgo/team_players/batch?team_ids=a,b` | 批量取成员（见 6.2） |
| `GET /v1/api/csgo/team/tt/{id}` | 参加过的赛事（见 6.4） |
| `GET /v1/api/csgo/team/matches_v1/{id}?status=past` | 历史比赛（见 6.3） |

`teams/{id}/matches` 与 `matches_v1` 的差别：前者返回 `data.rec_matches.matches[]`（只有 2 条，用于首页卡片），`total_rows` / `win_rate` 在 `data` 顶层；后者是完整可翻页列表。**写客户端一律用 `matches_v1`。**

### 6.6 队伍榜单（POST，可排序）

```
POST /v1/api/csgo/mfilter/team/list
Content-Type: application/json
```

```json
{
  "dimension": "top",
  "sort_value": "desc",
  "sort_key": "rating",
  "team_options": {
    "tt_ids": [], "time_value": "", "grade": [], "team_id": "",
    "time_type": "", "tt_series": [], "maps": [], "page": 1
  }
}
```

```bash
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/team/list' \
  -H 'Content-Type: application/json' \
  -d '{"dimension":"top","sort_value":"desc","sort_key":"rating",
       "team_options":{"tt_ids":[],"time_value":"","grade":[],"team_id":"",
       "time_type":"","tt_series":[],"maps":[],"page":1}}'
```

实测返回 **20 条/页，`total_rows: 7764`**（全量队伍）。每条：

```json
{
  "country_logo": "",
  "field_values": {
    "avg_kill": "81.0", "avg_death": "35.0", "avg_round": "17.5",
    "ct_win_rate": "100.0%", "t_win_rate": "...",
    "first_kill": "0", "first_death_num": "0",
    "kd": "...", "map_count": "...", "rating": "...", "global_rank": "..."
  },
  "team_id": "csgo_tm_...", "team_name": "...", "team_logo": "https://..."
}
```

`field_values` 的键跟 `tournaments/team_data` 的 **40 个字段同名同义**（见第 9 章），可以复用同一套渲染逻辑。

### 6.7 队伍数据统计（`team_overview` + 地图池）

```
POST /v1/api/csgo/mfilter/team/data/details
Content-Type: application/json
```

```json
{
  "team_options": {
    "team_id": "csgo_tm_9565",
    "time_type": "recent",
    "time_value": "2026-07-27 00:00:00_2026-10-27 23:59:59"
  }
}
```

```bash
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/team/data/details' \
  -H 'Content-Type: application/json' \
  -d '{"team_options":{"team_id":"csgo_tm_9565","time_type":"recent",
       "time_value":"2026-07-27 00:00:00_2026-10-27 23:59:59"}}'
```

`data` 有四个键：`team_overview` / `map_data` / `player_basics_data` / `player_basics_display`。

`team_overview`（近三个月，实测 Vitality）：

```json
{
  "map_count": "61", "map_per_round": "20.6",
  "total_kill": "4333", "total_death": "3849", "total_assist": "1624",
  "kd": "1.13", "rating": "1.17", "win_rate": "76.0%",
  "ct_win_rate": "62.6%", "t_win_rate": "51.8%",
  "ct_first_win_rate": "44.3%", "t_first_win_rate": "63.9%",
  "pistol_win_rate": "54.1%",
  "first_kill_win_rate": "32.9%", "first_death_win_rating": "73.9%",
  "first_five_win_rate": "68.9%", "first_ten_win_rate": "67.2%"
}
```

| 字段 | 说明 |
| --- | --- |
| `rating` / `kd` / `win_rate` | 队伍整体三围 |
| `ct_win_rate` / `t_win_rate` | 防守/进攻方回合胜率 |
| `ct_first_win_rate` / `t_first_win_rate` | 手枪局胜率（CT/T 分开） |
| `pistol_win_rate` | 手枪局总胜率 |
| `first_kill_win_rate` | 拿到首杀后的回合胜率 |
| `first_death_win_rating` | 丢掉首杀后仍赢下回合的比例（残局能力） |
| `first_five_win_rate` / `first_ten_win_rate` | 前 5 / 前 10 回合领先率 |
| `map_per_round` | 场均回合数 |

`map_data[]`（每张图一行，实测 11 张）：

```json
{
  "map_name": "Dust2",
  "map_icon": "https://...", "map_logo": "https://...",
  "relative_win": "12", "relative_lose": "3", "relative_total": "15",
  "win_rate": "80.0%",
  "ct_win_rate": "64.1%", "t_win_rate": "58.8%",
  "round_win_rate": "0.6%"
}
```

> `relative_*` 是「自己选这张图时」的战绩，`win_rate` 是全部场次。

`player_basics_display` 实测为 `false`、`player_basics_data` 为空数组 —— 队伍页的选手数据走 `team_players/batch`（6.2），不要指望这个字段。

### 6.8 队伍筛选项枚举（下拉框数据源）

```
GET /v1/api/csgo/mfilter/team/options?team_id={team_id}&page_source={任意串}
GET /v1/api/csgo/mfilter/team_player/options
```

```bash
curl -s \
  'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/team/options?team_id=csgo_tm_9565&page_source=team'
```

两个接口返回同一套结构（`{name, value, type, default}` 数组），`team/options` 用于**队伍榜单页**（6.6），
`team_player/options` 用于**队内选手榜**（比前者多一个 `grade`）：

| 键 | `team/options` | `team_player/options` | 说明 |
| --- | --- | --- | --- |
| `maps` | 12 | 12 | 地图下拉 |
| `time` | 15 | 17 | 时间下拉 |
| `recent_match` | 6 | — | 只取近 N 场 |
| `tt_series` | 5 | 5 | 赛事系列 |
| `grade` | — | 12 | 赛事等级 |

`maps` 的全部值（顺序固定）：

```
'' mirage nuke overpass vertigo ancient anubis inferno cache cobblestone dust2 train
```

`recent_match`：`""`(不限) / `10` / `20` / `30` / `50` / `100` —— 直接对应 6.6 body 里的
`team_options.recent_match`。

`tt_series`：`""` / `major` / `blast` / `iem` / `esl`。

`time` 每项带 `type`，取值 `all` / `self` / `recent` / `year`，
`value` 是 `"起点_终点"` 的下划线格式（说明见 5.1ter）。**默认选中项是 `default:true` 的那条
—— 对 `team/options` 是「近三个月」**，这就是为什么 6.6/6.7 不传时间时拿到的是近三个月数据。

> `page_source` 传什么都行（实测 `test` / `x` / `team` 结果相同），像是埋点参数。

### 6.9 队伍地图总览（一次拿三块地图数据）

```
POST /v1/api/csgo/mfilter/team/data/map/all
Content-Type: application/json
```

```bash
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/team/data/map/all' \
  -H 'Content-Type: application/json' \
  -d '{"team_options":{"time_value":"2026-07-27 00:00:00_2026-10-27 23:59:59",
       "team_id":"csgo_tm_9565","time_type":"recent","tt_series":[],"tt_ids":[],
       "maps":[],"grade":[],"page":1},"sort_key":""}'
```

和 6.7 的 `map_data` 是**互补**关系：6.7 是「该队各图战绩一览」，这个是把三张地图维度的表一次给全。
`data` 固定三个键，**每个都是 6 条（只返回该队打过的图）**：

```json
{
  "relative_data": [
    { "map_name": "Nuke",
      "map_logo": "https://oss.5eplay.com/cloudx/p/sport/csgo/map/xxx.png",
      "bout_win": "77", "bout_lose": "77",
      "relative_win": "4", "relative_lose": "3" }
  ],
  "win_data": [
    { "map_name": "Nuke",
      "pistol_round": "14", "pistol_round_win_rate": "64.3%",
      "first_kill_win_rate": "71.0%", "first_death_win_rate": "34.3%" }
  ],
  "win_rate_data": [
    { "map_name": "Cache",
      "map_icon": "https://...", "map_logo": "https://...",
      "map_win_rate": "90.0%",
      "ct_win_rate": "67.0%", "t_win_rate": "...",
      "relative_win": "", "relative_lose": "", "relative_total": "" }
  ]
}
```

| 块 | 字段 | 含义 |
| --- | --- | --- |
| `relative_data` | `bout_win` / `bout_lose` | 这张图上的回合赢/输数（不是场次！） |
| | `relative_win` / `relative_lose` | **自己主动选**这张图时的场次战绩 |
| `win_data` | `pistol_round` | 打过的图数/手枪局数 |
| | `pistol_round_win_rate` | 手枪局胜率 |
| | `first_kill_win_rate` / `first_death_win_rate` | 首杀后/丢首杀后的回合胜率 |
| `win_rate_data` | `map_win_rate` | 该图总胜率 |
| | `ct_win_rate` / `t_win_rate` | 分阵营回合胜率 |

> **三块里同名图的顺序不一定一致**，要按 `map_name` 对齐，不能按下标 zip。
> `win_rate_data` 里 `relative_*` 全是空串，别指望从这块拿「自选图」数据。

---
## 7. 选手（Player）

### 7.1 选手搜索

```
GET /v1/api/csgo/players?name=zywoo&page=1&limit=5
```

```bash
curl -s \
  'https://esports-data.5eplaycdn.com/v1/api/csgo/players?name=zywoo&page=1&limit=5'
```

```json
{
  "data": {
    "items": [
      {
        "id": "csgo_pl_11893",
        "name": "ZywOo",
        "highlight_name": "<SF-HL>ZywOo</SF-HL>",
        "Portrait": "https://oss.5eplay.com/...png",
        "country_logo": "https://oss.5eplay.com/...jpg",
        "kd": "0", "map_count": "1734"
      }
    ],
    "total_rows": 1, "total_page": 1
  }
}
```

> `highlight_name` 里的 `<SF-HL>` 是搜索关键词高亮标记，展示前要剥掉或转成 `<mark>`。

`limit` 省略时默认 20。这个接口只返回精简对象，要完整资料用 7.3。

### 7.2 选手榜单（POST，两套榜）

```
POST /v1/api/csgo/mfilter/player/list
```

**坑：`dimension` 和 `sort_key` 必须成对，且只有两组合法组合。**

| `dimension` | `sort_key` | 含义 | `total_rows` |
| --- | --- | --- | --- |
| `top` | `rating` | 选手 Rating 榜 | **1218** |
| `earning` | `total_earnings` | 总奖金榜 | **1503** |

```bash
# Rating 榜
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/player/list' \
  -H 'Content-Type: application/json' \
  -d '{"dimension":"top","sort_value":"desc","sort_key":"rating",
       "player_options":{"tt_ids":[],"time_value":"","grade":[],"player_id":"",
       "time_type":"","tt_series":[],"maps":[],"page":1}}'

# 总奖金榜
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/player/list' \
  -H 'Content-Type: application/json' \
  -d '{"dimension":"earning","sort_value":"desc","sort_key":"total_earnings",
       "player_options":{"tt_ids":[],"time_value":"","grade":[],"player_id":"",
       "time_type":"","tt_series":[],"maps":[],"page":1}}'
```

实测的报错信息（很直白，`success:false`）：

| 传法 | 返回 `message` |
| --- | --- |
| `dimension` 空 | `维度不能为空` |
| `sort_key` 空 | `排序字段不能为空` |
| `dimension=top` + `sort_key=kpr/adr/impact/kast/swing/kd/kddiff/mvp/map_count` | `参数排序错误` |
| `dimension=earning` + `sort_key=prize` | `参数排序错误` |

返回：

```json
// dimension=top
{ "player_id": "csgo_pl_11893", "player_name": "ZywOo",
  "portrait": "https://...", "team_logo": "https://...", "country_logo": "https://...",
  "field_values": { "rating": "1.33" } }

// dimension=earning
{ "player_id": "csgo_pl_7322", "player_name": "apEX", "...": "...",
  "field_values": { "total_earnings": "$2,375,287", "match_num": "1321", "map_count": "2040" } }
```

> ⚠️ 两个榜的 `field_values` 只有上面这几个键，**不是**完整选手资料。要详情再按 `player_id` 调 7.3。

### 7.3 选手详情 ★ 一个接口拿全

```
GET /v1/api/csgo/players/{player_id}
```

```bash
curl -s \
  'https://esports-data.5eplaycdn.com/v1/api/csgo/players/csgo_pl_11893'
```

`data` 三个顶层键：`basic_info` / `player_data` / `player_profile`。

#### `basic_info`

```json
{
  "id": "csgo_pl_11893", "name": "ZywOo",
  "portrait": "https://...png", "half_portrait": "https://...png",
  "country_zh": "法国", "country_en": "France",
  "country_logo": "https://...jpg",
  "birthday": "2000-11-09", "constellation": "https://.../tianxie.png",
  "positions": ["步枪手", "狙击手"], "position": "",
  "team_id": "csgo_tm_9565", "team_name": "Vitality", "team_logo": "https://...png",
  "bonus": "$1,893,960", "top20_num": "7", "is_conduct": ""
}
```

| 字段 | 说明 |
| --- | --- |
| `positions` | 位置数组（步枪手/狙击手/指挥…），`position` 单值字段实测为空，**用 `positions`** |
| `bonus` | 职业生涯总奖金（字符串，带 `$`） |
| `top20_num` | HLTV Top20 上榜次数 |
| `birthday` + `constellation` | 生日直接给，星座是图标 URL |

#### `player_data`（生涯累计，26 个键）

| 字段 | 示例 | 说明 |
| --- | --- | --- |
| `rating` | `"1.36"` | HLTV 2.0 Rating |
| `kd` | `"1.41"` | K/D |
| `kill` / `death` | `"36261"` / `"25785"` | 总击杀/死亡 |
| `kpr` / `dpr` | `"0.84"` / `"0.6"` | 每回合击杀/死亡 |
| `adr` / `damage_round` | `"87.3"` / `"87.35"` | 每回合伤害 |
| `impact` | `"0.95"` | Impact |
| `kast` | `"76.3"` | KAST |
| `head_shot` | `"41.2"` | 爆头率（%） |
| `maps_played` | `"1727"` | 地图数 |
| `rounds_played` | `"43019"` | 回合数 |
| `kills_round` / `deaths_round` | `"0.84"` / `"0.6"` | 同 kpr/dpr |
| `assists_round` | `"0"` | 每回合助攻（实测为 0，暂不可信） |
| `saved_by_teammate_round` / `saved_teammates_round` | `"0"` | 同上，实测 0 |

数组字段：

| 字段 | 长度 | 结构 |
| --- | --- | --- |
| `maps[]` | 13 | `{ "name": "Inferno", "rating": "1.35", "kd": "1.43", "use_num": "277" }` |
| `weapons[]` | 82 | `{ "name": "AWP", "rate": "35.60", "logo": "" }` |
| `weapon_cate[]` | 4 | `{ "weapon_cate": "步枪击杀", "total_kills": "14211", "rate": "39%", "weapons": [...] }` |
| `round_data[]` | 6 | `{ "kill_type": "0杀回合", "num": "20003" }` |
| `final_phase_data[]` | 5 | `{ "data_type": "1V1", "num": "327" }` |
| `players[]` | 4 | 队友精简对象（含 `birthday` / `half_portrait`） |
| `rating_chart[]` | 0 | 实测为空，给前端画折线用，暂不可用 |

#### `player_profile`

| 字段 | 说明 |
| --- | --- |
| `history_honor[]` | 生涯荣誉，实测 109 条：`{ "rank": "1", "rank_desc": "冠军", "team_ranking": "1st", "history_tt": { "id", "name", "bonus", "grade", "start_time", "team_name", "team_logo" } }` |
| `milestones[]` / `milestone_display` | 里程碑卡片（同队伍 6.5） |
| `player_config` | **外设与设置**：`mouse_config`（DPI 400 / eDPI 800 / 1000Hz / 灵敏度 2 / ZOWIE EC2-CW / raw_input 1）、`monitor_config`（1280x960 / 4:3 / Stretched / Computer Monitor） |

### 7.4 选手统计（带同位置对比区间）

```
POST /v1/api/csgo/mfilter/player/stats
```

```bash
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/player/stats' \
  -H 'Content-Type: application/json' \
  -d '{"player_options":{"player_id":"csgo_pl_11893","time_type":"","time_value":"",
       "tt_ids":[],"maps":[],"grade":[],"page":1}}'
```

`data` 五个键：`map_stats` / `match_stats` / `player_data` / `player_performance` / `player_power_list`。

```json
{
  "map_stats":   { "total": 1728, "win": 1114, "loss": 614, "draw": 0,
                   "win_rate": "64.5%", "mvp_count": 573 },
  "match_stats": { "total": 830, "win": 563, "loss": 264, "draw": 3,
                   "win_rate": "67.8%", "mvp_count": 370 },
  "player_data": { "rating": "...", "kd": 1.41, "kddiff": 10484,
                   "total_kills": 36290, "total_death": 25806, "total_assist": 8505,
                   "hs": 14950, "hs_rate": "41.2%",
                   "ct_win_rate": "56.2%", "t_win_rate": "52.1%",
                   "map_count": 1728, "map_win": 1114, "map_loss": 614,
                   "map_mvp": 573, "map_win_rate": "64.5%" }
}
```

> 注意 `map_stats` / `match_stats` 里数值是**数字**，`player_data` 里 `kd` 也是**数字** 1.41 —— 跟其它接口全是字符串不同，别写死 `strip("%")`。

`player_performance` 是**同位置百分位评分**，每项结构一致：

```json
"adr": {
  "value": "87.3",
  "avg_value": "73.9",
  "lower_better": false,
  "range": {
    "bad":    { "start": "72.5", "end": "64.0" },
    "middle": { "start": "80.7", "end": "72.6" },
    "good":   { "start": "88.5", "end": "80.8" }
  }
}
```

七个维度：`adr` / `dpr` / `impact` / `kast` / `kpr` / `rating` / `swing`。

| 字段 | 说明 |
| --- | --- |
| `value` | 该选手的值 |
| `avg_value` | 同位置平均水平 |
| `lower_better` | `dpr` 为 `true`（越低越好），其余 `false` |
| `range.bad/middle/good` | 三档区间，**注意 `start` > `end`**（左闭右开反着写的），判断时用 `end <= v <= start` |

`player_power_list` 实测为 `[]`（空数组），别依赖。

### 7.5 选手地图统计

```
POST /v1/api/csgo/mfilter/player/map/stats
```

body 与 7.4 完全相同。返回 `data.bout_data[]`，实测 12 张图：

```json
{
  "map_name": "Inferno",
  "map_logo": "https://...png",
  "bout":  { "win": "213", "loss": "109" },
  "round": { "win_round": "4397", "loss_round": "3590" }
}
```

`bout` = 地图胜负场次，`round` = 回合胜负数。客户端要算回合胜率用 `win_round / (win_round + loss_round)`。

### 7.6 选手武器统计

```
POST /v1/api/csgo/mfilter/player/weapon/stats
```

body 同 7.4。`data.player_data_weapon` 五个键：

| 键 | 结构 |
| --- | --- |
| `weapon_rank[]` | 每把枪一行：`{ "weapon": "AWP", "weapon_type": "狙击枪", "kills_num": "11071", "kills_rate": "36.1%", "hs_rate": "11.4%", "rate": "36.1", "weapon_logo": "https://...", "player_id": "..." }` |
| `weapon_cate[]` | 按大类聚合：`{ "cate_name": "步枪", "kills_num": "12140", "kills_rate": "39.6%", "rate": "100.0", "weapons": [] }`（`weapons` 实测为空，要明细看 `weapon_rank`） |
| `weapon_rate[]` | 画饼图用：`{ "weapon": "AWP", "kills_rate": "36.1%", "rate": "36.1" }` |
| `knifes[]` | 刀杀：第一条 `knife_name: "总击杀"` 是**总数**（144），不是刀杀，别算错 |
| `throw_weapon` | 投掷物：`flash_grenade` 27579（投出数）/ `flash_grenade_assist` 7.05（每回合闪光助攻）/ `flash_grenade_success_rate` 69.92（致盲成功率 %）/ `flash_grenade_time` `"8.41S"`（致盲时长）/ `molotov_cocktail` / `grenade_kills` / `grenade_round_damage` |

### 7.7 选手残局（clutch）统计

```
POST /v1/api/csgo/mfilter/player/camp/stats
```

body 同 7.4。`data` 四个键：

```json
{
  "base_data": { "total_kills": 34710, "total_death": 24732, "total_assist": 8037,
                 "kd": "1.40", "kddiff": 9978, "hs": 14426, "hs_rate": "41.6%" },
  "final_data": [
    { "final_type": "1v1", "round_count": 652, "round_win": 454,
      "round_lose": 198, "round_win_rate": "69",
      "logo": "https://static.5eplay.com/images/app/final/1v1.png" }
  ]
}
```

`final_data` 固定 5 条：`1v1` / `1v2` / `1v3` / `1v4` / `1v5`。
`round_win_rate` 是**不带 `%` 的字符串**（`"69"` 表示 69%）。

另有 `first_data`（首杀相关）与 `round_data`（每回合击杀分布），结构同 `player_data.round_data`。

### 7.8 选手残局逐局列表

```
POST /v1/api/csgo/mfilter/player/final/list
```

```json
{
  "final_type": "1",
  "player_options": { "player_id": "csgo_pl_11893", "time_type": "", "time_value": "",
                      "tt_ids": [], "maps": [], "grade": [], "page": 1 }
}
```

`final_type` 是**独立的顶层字段**（不在 `player_options` 里）：

| `final_type` | 含义 | 实测 `total_rows` |
| --- | --- | --- |
| `"1"` | 1v1 | **652** |
| `"2"` | 1v2 | **1047** |

```json
{
  "match_id": "csgo_mc_2398757", "bout_num": "1", "bout_id": "",
  "map_name": "Cache", "map_background": "https://...png",
  "match_time": "2026/10/11", "round_num": 21, "round_result": "win",
  "t1_info": { "id": "csgo_tm_9565", "abbr_en": "Vitality" }
}
```

> 每条记录指向一个具体回合（`match_id` + `bout_num` + `round_num`），要回放细节得再调比赛详情 / 逐回合流水。`t1_info` 固定是该选手所在队。

### 7.9 选手近期比赛 ★ 可翻页、可筛选

```
POST /v1/api/csgo/mfilter/player/match/list
Content-Type: application/json
```

```bash
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/player/match/list' \
  -H 'Content-Type: application/json' \
  -d '{"player_options":{"player_id":"csgo_pl_11893","time_type":"recent",
       "time_value":"2026-07-27 00:00:00_2026-10-27 23:59:59",
       "tt_ids":[],"maps":[],"grade":[],"page":1}}'
```

选手详情页「比赛记录」列表用的就是它。**`time_value` 必填**，传空会返回
`{"success":false,"message":"time_value验证错误"}`；要「全部时间」得把
`time_type` 也一起置空（`"time_type":"","time_value":""`，实测 830 场）。

`data.total_rows` / `data.total_page` 正常可翻页（10 条/页，`page_size` **无效**，
传 50 仍然给 10 条）。

`data.items` 是**对象**不是数组：

```json
{
  "items": {
    "game_played": "25",
    "game_played_desc": "25场次",
    "win_rate": "76.0%",
    "win_rate_desc": "76.0%胜率",
    "wins_streak": "",
    "matches": [ /* 每条 { mc_info, tt_info } */ ]
  },
  "total_page": "3",
  "total_rows": "25"
}
```

`items.matches[]` 每项 `{ mc_info, tt_info }`，**没有 `state`/`maps`**（恒为 `null`，
要比分细节还得回 `/matches/{id}/data`）。`mc_info` 里对客户端有用的：

| 字段 | 说明 |
| --- | --- |
| `id` | `csgo_mc_xxx` |
| `status` / `match_status` | `past` / `"2"` |
| `result` | `home_win` / `opponent_win` / `draw`（**以该选手所在队为 home**） |
| `home_score` / `opponent_score` | 大比分 |
| `home_quick_score` / `opponent_quick_score` | 逐图比分（逗号分隔） |
| `bouts_result` | 每图胜负 `["home","opponent","opponent"]` |
| `ts` | unix 秒 |
| `format` | `"3"` = BO3 |
| `home_info` / `opponent_info` | `{ id, disp_name, logo, rank, v_rank }` |
| `high_lights_cfg_list[]` | **回放地址**（含 `url` 与 `origin_video` iframe），有就用 |
| `live_cfg_list[]` | 直播源（`name` / `player_type` / `native_link`） |
| `t1_odds` / `t1_odds_percent` / `t2_odds` / `t2_odds_percent` | 赔率 |
| `tt_stage` / `tt_stage_desc` | 赛段 |
| `dark_horse` | `"1"` 表示爆冷 |

筛选实测（`csgo_pl_11893`，近三个月）：

| 参数 | 结果 |
| --- | --- |
| 不传（近三个月） | 25 场 |
| `time_type:"" , time_value:""` | **830 场** |
| `tt_ids:["csgo_tt_8050"]` | 3 场（该赛事内） |
| `maps:["mirage"]` | 12 场 |
| `grade:["2"]` | 19 场（只算 S 级赛事） |

> `maps` 传地图**英文名小写**（`mirage` / `inferno` / `nuke`…），`grade` 传赛事等级码（见 5.5）。

### 7.10 选手多维对比 / 自定义排序榜

```
POST /v1/api/csgo/mfilter/player/multidimension/list
```

```bash
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/player/multidimension/list' \
  -H 'Content-Type: application/json' \
  -d '{"player_options":{"player_id":"","time_type":"recent",
       "time_value":"2026-07-27 00:00:00_2026-10-27 23:59:59","tt_ids":[],"maps":[],
       "recent_match":"","grade":[],"page":1,"team_id":""},
       "dimension":"","sort_key":"rating","sort_value":"DESC"}'
```

这是 **7.2 的加强版**：7.2 只支持 `rating` / `total_earnings` 两种排序，
而这个接口 `sort_key` 支持 7.4 里那套全部指标，可以自己造榜。

`sort_key` 实测全部可用（不再报「参数排序错误」）：
`rating` / `kpr` / `kast` / `swing` / `adr` / `dpr` / `impact` / `kd`。

```json
{
  "items": [
    {
      "player_id": "csgo_pl_11893",
      "player_name": "ZywOo",
      "portrait": "https://...png",
      "team_logo": "https://...png",
      "team_name": "",
      "country_logo": "https://...jpg",
      "field_values": {
        "rating": "1.44", "kd": "1.49", "kddiff": "+348", "kpr": "0.85",
        "dpr": "0.57", "adr": "87.79", "kast": "77.4", "swing": "4.19",
        "impact": "0.00", "hs_rate": "42.3%", "win_rate": "70.49",
        "map_count": "61", "first_blood": "173", "first_death": "100",
        "kill4": "26", "kill5": "2", "v4": "1", "v5": "0", "dagger": "2"
      }
    }
  ],
  "total_page": "1",
  "total_rows": "627"
}
```

- **`total_rows` 不可信**：第 1 页返回 `"19"`、第 2 页返回 `"20"`、翻到 `page=50`
  才稳定成 `"627"`。判断还有没有下一页要看 `items` 是否为空，别信 `total_rows`/`total_page`。
- `player_id` 传具体选手 → 只返回 1 条（当「单人属性查询」用，但字段齐全、比 7.3 轻）。
- `team_id` 传某队 → 只返回该队成员。
- `dimension` 传什么都一样（`""` / `"top"` / `"all"` 结果相同），不用传。

### 7.11 选手参加过的赛事

```
GET /v1/api/csgo/player/tt/{player_id}
```

```bash
curl -s \
  'https://esports-data.5eplaycdn.com/v1/api/csgo/player/tt/csgo_pl_11893'
```

实测 ZywOo → **190 条**。`data.items[]` 每项与 5.1 的赛事条目同构：

```json
{
  "id": "csgo_tt_8047", "disp_name": "PGL 克卢日纳波卡 2026",
  "abbr_zh": "", "abbr_en": "",
  "bonus": "$1,250,000", "grade": "2", "grade_label": "S级赛事",
  "city_name": "罗马尼亚，克卢日-纳波卡",
  "start_time": "...", "end_time": "2026-02-23 23:59:59",
  "status": "past", "logo": "https://...png", "cover": "https://...png",
  "color": "663dea", "mode": "", "special_color": "", "special_grade_label": ""
}
```

同结构的还有 `GET /v1/api/csgo/team/tt/{team_id}`（见 6.4）。**这两个是「下拉框筛选项」接口**，
前端拿它填「按赛事筛选」的下拉，所以字段和列表页一致、不含战绩。

### 7.12 武器分类枚举

```
GET /v1/api/csgo/mfilter/player/weapon/cate
```

```json
{
  "data": {
    "weapon_cates": [
      { "cate_id": "全部类型", "cate_name": "", "list": [] },
      { "cate_id": "步枪", "cate_name": "步枪", "list": [] },
      { "cate_id": "狙击枪", "cate_name": "狙击枪", "list": [] },
      { "cate_id": "冲锋枪", "cate_name": "冲锋枪", "list": [] },
      { "cate_id": "霰弹枪", "cate_name": "霰弹枪", "list": [] },
      { "cate_id": "机枪", "cate_name": "机枪", "list": [] },
      { "cate_id": "手枪", "cate_name": "手枪", "list": [] }
    ]
  }
}
```

7 个分类固定不变，`cate_id` 直接当 7.6 `weapon/stats` 的分类筛选值传。`list` 恒为空数组
（**未验证**是不是需要额外参数才填具体枪械）。

### 7.13 残局汇总（轻量版）

```
POST /v1/api/csgo/mfilter/player/final/stats
```

body 同 7.4（`player_options`，不需要 `page`）。返回比 7.7 `camp/stats` **小得多**，
只要残局胜负、不要基础数据时用它：

```json
{
  "data": {
    "items": [
      { "final_type": "1v1", "round_count": 17, "round_win": 12, "round_lose": 5,
        "round_win_rate": "70",
        "logo": "https://static.5eplay.com/images/app/final/1v1.png" },
      { "final_type": "1v2", "round_count": 32, "round_win": 8,  "round_lose": 24,
        "round_win_rate": "25", "logo": "..." }
    ]
  }
}
```

固定 5 条（`1v1` / `1v2` / `1v3` / `1v4` / `1v5`），`round_win_rate` **不带 `%`**。
与 7.7 的差别：7.7 的 `final_data` 是**生涯累计**，这个接口吃 `player_options` 的时间/赛事/地图筛选。

---
## 8. 世界排名（HLTV 积分榜 / Valve VRS）★ 必须 POST

**`GET` 这个路径一律 `404 page not found`** —— 这就是之前一直找不到的原因。

```
POST /v1/api/csgo/new/rank/team_list
Content-Type: application/json
```

```json
{
  "sort_value": "desc",
  "rank_type": "rank",
  "sort_key": "rank",
  "region": "",
  "team_options": {
    "tt_ids": [], "time_value": "", "grade": [], "team_id": "",
    "time_type": "", "tt_series": [], "maps": [], "page": 1
  }
}
```

```bash
# HLTV 世界排名（积分榜）
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/new/rank/team_list' \
  -H 'Content-Type: application/json' \
  -d '{"sort_value":"desc","rank_type":"rank","sort_key":"rank","region":"",
       "team_options":{"tt_ids":[],"time_value":"","grade":[],"team_id":"",
       "time_type":"","tt_series":[],"maps":[],"page":1}}'

# Valve VRS 榜
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/new/rank/team_list' \
  -H 'Content-Type: application/json' \
  -d '{"sort_value":"desc","rank_type":"valve_rank","sort_key":"valve_rank","region":"",
       "team_options":{"tt_ids":[],"time_value":"","grade":[],"team_id":"",
       "time_type":"","tt_series":[],"maps":[],"page":1}}'
```

### 两套榜（都不是 5E 自己的榜）

| `rank_type` | `sort_key` | 榜 | 实测 `total_rows` |
| --- | --- | --- | --- |
| `rank` | `rank` | **HLTV 世界排名**（积分榜） | **328** |
| `valve_rank` | `valve_rank` | **Valve VRS**（官方地区积分） | **377** |

两者**必须同时改**，只改一个会返回另一套榜或空。20 条/页，`total_page` 分别是 17 / 19。

> ⚠️ **`rank` 不是「5E 世界排名」** —— 5E 平台本身不发布排名。`rank_type: "rank"` 拿到的
> 就是 **HLTV 世界排名积分**（`point`），和 5E 无关。前端顶部切换器写的是
> 「V社排名 / HLTV排名」（见 `1299.js`），从来不是「5E榜」。
>
> 同一个 item 里两套榜的字段是**并列**的：`rank` / `point` 属于 HLTV，
> `valve_rank` / `valve_point` 属于 VRS。服务端按你传的 `sort_key` 排序，但
> **显示的序号和积分必须取对应的那一对字段**，否则 VRS 榜会拿 HLTV 的名次去渲染，
> 出现「1 2 3 4 5」的顺序却配着乱序的分数。实测 page=1：
> `rank_type:"rank"` → Spirit 904 / Vitality 898 / FURIA 691；
> `rank_type:"valve_rank"` → Vitality 1990 / MOUZ 1940 / Spirit 1927。

### `region` 枚举（实测）

| `region` | `total_rows` |
| --- | --- |
| `""`（空，全球） | 328 |
| `"欧洲"` | 182 |
| `"亚洲"` | 35 |
| `"美洲"` | 69 |
| `"中国"` | **0**（无该分区） |
| `"大洋洲"` | **0** |

> 注意 `region` 传**中文**。传 `"全部地区"` 这种「选项文案」会返回空 —— 前端默认值其实是乱码 `ȫ������`（GBK 被当 latin1 解），实测该乱码值等价于空字符串。

### 返回结构

```json
{
  "country_logo": "https://oss.5eplay.com/...jpg",
  "team_id": "csgo_tm_...",
  "team_name": "...",
  "team_logo": "https://...",
  "field_values": {
    "rank": "1", "global_rank": "1",
    "rank_change": "-", "rank_diff": "-",
    "point": "904", "score": "904",
    "region_name": "欧洲",
    "kd_diff": "11214",
    "avg_kill": "", "avg_death": "", "avg_assist": "", "avg_round": "",
    "rating": "", "kd": "", "kd_rate": "",
    "map_num": "", "map_win_loss": "", "map_win_rate": "",
    "ct_win_rate": "", "t_win_rate": "",
    "first_kill": "", "first_kill_rate": "", "first_death_num": "", "first_death_rate": "",
    "first_five_win_num": "", "first_five_win_rate": "",
    "first_ten_win_num": "", "first_ten_win_rate": "",
    "ct_first_win_rate": "", "ct_first_win_round": "",
    "t_first_win_rate": "", "t_first_win_round": "",
    "game_played": "", "global_bonus": ""
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `rank` / `global_rank` | 当前名次（`global_rank` 是跨区总名次） |
| `point` / `score` | 积分，**两个值实测相同**，取 `point` 即可 |
| `rank_change` / `rank_diff` | 名次变化，无变化时是 `"-"`（字符串），要判空再转数字 |
| `region_name` | 所属分区中文名 |
| `kd_diff` | 击杀差 |
| 其余 `""` 字段 | **在默认 body 下全是空字符串** —— 只有加了 `time_type`/`time_value`/`tt_ids` 过滤才会填上。只做排名榜的话忽略即可 |

> ⚠️ 别把空字符串当 0 排序，会把空数据排到前面。

---
## 9. 赛事维度统计（队 / 选手 / 地图）

三个接口都是 **POST**，body 结构一致：外层键名不同，内层放 `tt_ids` **数组**（不是 `tt_id` 字符串）。

| 接口 | 外层键 |
| --- | --- |
| `POST /v1/api/csgo/tournaments/team_data` | `team_options` |
| `POST /v1/api/csgo/tournaments/player_data` | `player_options` |
| `POST /v1/api/csgo/tournaments/map_data` | `map_options` |

```bash
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/tournaments/team_data' \
  -H 'Content-Type: application/json' \
  -d '{"team_options":{"tt_ids":["csgo_tt_8050"],"page":1}}'
```

**坑：内层必须叫 `tt_ids` 且是数组。** 传 `"tt_id":"csgo_tt_8050"` 会报：

| 传法 | 报错 |
| --- | --- |
| `{"team_options":{"tt_id":"csgo_tt_8050"}}` | `success:false, message:""`（空消息，静默失败） |
| `{"player_options":{"tt_id":"..."}}` | `请传赛事id` |
| `{"map_options":{"tt_id":"..."}}` | `tt_id不能为空` |

### 9.1 队伍维度 `team_data`

实测 `csgo_tt_8050` → **16 支队伍**，每条 `{ team_id, team_name, team_logo, country_logo, field_values }`，`field_values` 共 **40 个字段**：

```
team_id team_name team_logo country_logo tt_id
rank global_rank win lose win_rate match_win_rate
map_count map_per_round
kd kddiff rating
total_kills total_death total_assist
avg_kill avg_death avg_assist
ct_win_rate t_win_rate
sh_rate fh_rate sh_pistol_win sh_pistol_win_rate fh_pistol_win fh_pistol_win_rate
pistol_win_rate
ot_win ot_win_rate
flag5_win flag5_win_rate flag10_win flag10_win_rate
max_diff_score inferior_position_win inferior_position_max_core
```

常用字段示例：

```json
{
  "rank": "1", "global_rank": "1",
  "win": "?", "lose": "3", "win_rate": "66.7%", "match_win_rate": "66.7%",
  "map_count": "8", "map_per_round": "21",
  "kd": "1.09", "kddiff": "+45", "rating": "1.08",
  "avg_kill": "71.38", "avg_death": "65.75", "avg_assist": "21.88",
  "ct_win_rate": "62.07%", "t_win_rate": "44.44%",
  "sh_rate": "50.00%", "fh_rate": "37.50%",
  "pistol_win_rate": "43.75%", "ot_win_rate": "0.0%",
  "flag5_win_rate": "83.3%", "flag10_win_rate": "100.0%",
  "max_diff_score": "10",
  "inferior_position_win": "1", "inferior_position_max_core": "2"
}
```

| 字段 | 说明 |
| --- | --- |
| `sh_rate` / `fh_rate` | 上半场 / 下半场胜率 |
| `sh_pistol_win_rate` / `fh_pistol_win_rate` | 上/下半场手枪局胜率 |
| `flag5_win` / `flag10_win` | 先到 5 / 10 分的场次数；`*_win_rate` 对应领先后的胜率 |
| `inferior_position_*` | 落后局面（inferior position）翻盘统计 |
| `max_diff_score` | 最大分差 |

### 9.2 选手维度 `player_data`

实测 `csgo_tt_8050` → **81 名选手**，`field_values` 共 **78 个字段**（最全的一份选手数据）。

```
adr apr dpr impact kast kd kddiff kpr rating swing bp bd
avg_kills avg_death avg_assist
avg_awp_kills avg_pistol_kills avg_rifle_kills avg_smg_kills avg_knife_kills
avg_blinding_teammate blinding_teammate flash_assist
total_kills total_death total_assist total_hs total_round
total_awp_kills total_pistol_kills total_rifle_kills total_smg_kills
total_knife_kills total_property_damage_taken
hs_rate mk_rating
rank map_count
zero_kill_round zero_kill_round_rate
one_kill_round one_kill_round_rate
two_kill_round two_kill_round_rate
three_kill_round three_kill_round_rate
four_kill_round four_kill_round_rate
five_kill_round five_kill_round_rate
more_kills more_kills_round_rate
first_kills first_kills_su_rate first_death
end_game end_game_win end_game_win_rate
one_vs_one_kills one_vs_one_win_rate
one_vs_two_kills one_vs_two_win_rate
one_vs_three_kills one_vs_three_win_rate
one_vs_four_kills one_vs_four_win_rate
one_vs_five_kills one_vs_five_win_rate
max_adr max_apr max_dpr max_impact max_kast max_kpr max_rating max_swing
min_dpr min_rating
```

示例：

```json
{
  "player_id": "...", "player_name": "...", "portrait": "https://...",
  "team_name": "...", "team_logo": "https://...", "country_logo": "https://...",
  "field_values": {
    "rating": "?", "adr": "71.2", "apr": "0.14", "dpr": "0.55",
    "kast": "?", "impact": "?", "kpr": "?",
    "avg_kills": "15.00", "avg_death": "11.62", "avg_assist": "3.00",
    "avg_awp_kills": "7.38", "avg_rifle_kills": "5.12", "avg_pistol_kills": "1.75",
    "avg_knife_kills": "0.00", "avg_smg_kills": "0.75",
    "avg_blinding_teammate": "8.00",
    "first_kills": "14", "first_death": "7",
    "end_game": "2", "end_game_win": "0", "end_game_win_rate": "0.00%"
  }
}
```

| 字段族 | 说明 |
| --- | --- |
| `zero_kill_round` ~ `five_kill_round` | 0~5 杀回合数，`*_rate` 是占比 |
| `more_kills` | 多杀回合数 |
| `first_kills` / `first_death` | 首杀 / 首死次数，`first_kills_su_rate` 是首杀成功率 |
| `end_game*` | 残局（clutch）统计 |
| `one_vs_one_kills` ~ `one_vs_five_kills` | 1v1~1v5 残局次数，`*_win_rate` 胜率 |
| `max_*` / `min_*` | 单场最高/最低值（给「极限值」卡片） |
| `bp` / `bd` | 拆包 / 下包次数 |

### 9.3 地图维度 `map_data`

实测 `csgo_tt_8050` → **7 张地图**（Mirage / Ancient / Nuke / Dust2 / Inferno / Anubis / Cache），每条：

```json
{
  "map_name": "Mirage",
  "map_logo": "https://oss.5eplay.com/...png",
  "field_values": {
    "map_count": "11",
    "pick_rate": "20.0%", "ban_count": "7",
    "total_round": "273", "avg_round": "24.82", "max_round": "36",
    "ct_win_rate": "57.1%", "t_win_rate": "42.9%",
    "pistol_ct_win_rate": "50.0%", "pistol_t_win_rate": "50.0%",
    "ot_rate": "27.0%", "total_ot": "3",
    "fortissimo_team_id": "csgo_tm_9565", "fortissimo_team_use": "2",
    "fortissimo_team_win_rate": "100.0%",
    "team_name": "Vitality", "team_logo": "https://..."
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `pick_rate` / `ban_count` | 该图被选率 / 被 ban 次数 |
| `ct_win_rate` / `t_win_rate` | 该图 CT/T 方胜率 |
| `pistol_ct_win_rate` / `pistol_t_win_rate` | 手枪局 CT/T 胜率 |
| `ot_rate` / `total_ot` | 进加时的比例 / 场次 |
| `fortissimo_team_*` | **该图最强队伍**（`fortissimo` = 最强音）及其使用次数/胜率 —— 可直接做「地图之王」卡片 |

> `map_data` 只返回**该赛事打过的图**，没打的地图不出现（所以是 7 而不是 9）。

---
### 9.4 赛事比赛列表（`match_list`）

```
GET /v1/api/csgo/tournaments/match_list?tt_ids=csgo_tt_8050
```

```bash
curl -s \
  'https://esports-data.5eplaycdn.com/v1/api/csgo/tournaments/match_list?tt_ids=csgo_tt_8050'
```

实测 `csgo_tt_8050` → **41 场**。`data.matches[]`，每项 `{ mc_info, state, tt_info }`，结构与第 1 章比赛列表项**完全一致**（`mc_info.t1_info` / `t2_info` / `grade` / `plan_ts` / `round_name` 都在）。

> 这是「一次拿完整个赛事的赛程」最快的方式，不用翻 `/matches?tt_ids=`。多个赛事用逗号分隔 `tt_ids=a,b,c`。

### 9.5 赛事数据的轻量版（`/data?type=`，GET 一次一个 tab）

```
GET /v1/api/csgo/tournaments/{tt_id}/data?type={1|2|3}
```

```bash
curl -s \
  'https://esports-data.5eplaycdn.com/v1/api/csgo/tournaments/csgo_tt_9440/data?type=2'
```

这是第 9 章那三个 POST 接口的 **GET 简版**，同一个赛事、同一批数据，但**字段少很多**、且一次只返回一个 tab：

| `type` | 等价 tab | 返回键 | 字段数 | 实测条数（`csgo_tt_9440`） |
| --- | --- | --- | --- | --- |
| `1` | 选手 | `player_data` | 16 | 126 |
| `2` | 队伍 | `team_data` | 10 | 23 |
| `3` | 地图 | `map_data` | 4 | 7 |

好消息是：**响应里三个键总在**，只有对应的那个有值，另外两个是空数组 —— 好判断。

`type=1` 的 `player_data[]`（16 字段）：

```json
{
  "id": "csgo_pl_11893", "name": "ZywOo",
  "logo": "https://...png",
  "country_name": "法国", "country_logo": "https://...png",
  "rank": "1", "positions": "狙击手",
  "map_count": "61",
  "kill": "1203", "death": "806", "kd": "1.49", "kd_diff": "+397",
  "adr": "87.79", "kast": "77.4", "rating": "1.44"
}
```

`type=2` 的 `team_data[]`（10 字段）：`id` / `name` / `logo` / `rank` / `map_count` /
`kill` / `death` / `kd` / `kd_diff` / `rating`。

`type=3` 的 `map_data[]`（4 字段）：`name`（地图名）/ `num`（打的场次）/ `logo` / `url`（详情链接）。

**什么时候用哪个：**

| 需求 | 用这个 | 用第 9 章 POST |
| --- | --- | --- |
| 做赛事页三个榜单（只要名字+分数） | ✅ 轻、一次一个 tab | 太重 |
| 要 `ct_win_rate` / `first_kill` 等细项 | ❌ 没有 | ✅ |
| 要一次拿全三个 tab | ❌ 得请求 3 次 | ✅ |
| 未开赛赛事 | 两边都空 | 两边都空 |

> `type` 传 0 或 4 不报错，但三个键都是空数组（等于没查）。**未开赛赛事（`status:upcoming`）三个 tab 全空**，别误判成接口坏了。

---

## 10. 按页面索引（四个菜单）

`https://event.5eplay.com/csgo/*` 四个主菜单对应的接口：

### `/csgo/matches`（比赛）

| 子区 | 接口 | 章节 |
| --- | --- | --- |
| 比赛列表（未开始/直播/已结束） | `GET /v1/api/csgo/matches` | 1 |
| 比赛详情 | `GET /v1/api/csgo/matches/{id}/data` | 2 |
| 赛前分析 | `GET /v1/api/csgo/matches/{id}/analysis_v1` | 2bis |
| 逐回合流水 | `GET /v1/api/csgo/match/{id}/event/log` | 3 |
| 整场选手汇总 | `app.5eplay.com/api/score/match_score_*` | 4 |
| 实时推送 | MQTT over WSS | 2.6 |

### `/csgo/events`（赛事）

| 子区 | 接口 | 章节 |
| --- | --- | --- |
| 赛事列表（首屏） | `POST app.5eplay.com/api/csgo/tournament/csgo_event_list_v1` | 5.1 |
| 赛事搜索框 | `GET /v1/api/csgo/mfilter/tournament/search` | 5.1bis |
| 筛选项枚举（等级/时间/奖金/系列/主赛事） | `GET /v1/api/csgo/mfilter/tournaments/options` | 5.1ter、5.5 |
| 赛事详情 | `GET /v1/api/csgo/tournaments/{tt}/introduction` | 5.2 |
| 赛事奖金分配 | `introduction` 的 `team_rank[]` | 5.1quater |
| 赛程 / 对阵图 | `GET /v1/api/csgo/tournaments/{tt}/stages` | 5.3 |
| 赛程 / 赛果列表（可翻页） | `GET app.5eplay.com/api/tournament/session_list` / `session_result_list` | 5.6 |
| 赛事比赛列表 | `GET /v1/api/csgo/tournaments/match_list?tt_ids=` | 9.4 |
| 赛事摘要批量补全 | `GET /v1/api/csgo/focus/tournaments?tt_ids=` | 5.4 |
| 「赛事数据」队/选手/地图三 tab | `POST /v1/api/csgo/tournaments/{team,player,map}_data` | 9 |
| 「世界排名」页签 | `POST /v1/api/csgo/new/rank/team_list` | 8 |

### `/csgo/teams`（队伍）

| 子区 | 接口 | 章节 |
| --- | --- | --- |
| 队伍列表 / 搜索 | `GET /v1/api/csgo/teams` | 6.1 |
| 队伍榜单（可按维度排序） | `POST /v1/api/csgo/mfilter/team/list` | 6.6 |
| 队伍榜单筛选项 | `GET /v1/api/csgo/mfilter/team/options` | 6.8 |
| 队伍详情 - 概览 | `GET /v1/api/csgo/teams/{id}/overview` | 6.5 |
| 队伍详情 - 荣誉墙 | `GET /v1/api/csgo/teams/{id}/honors` | 6.5 |
| 队伍详情 - 近期比赛 | `GET /v1/api/csgo/team/matches_v1/{id}?status=past` | 6.3 |
| 队伍详情 - 参加赛事 | `GET /v1/api/csgo/team/tt/{id}` | 6.4 |
| 队伍详情 - 数据 tab | `POST /v1/api/csgo/mfilter/team/data/details` | 6.7 |
| 队伍详情 - 地图总览（三块） | `POST /v1/api/csgo/mfilter/team/data/map/all` | 6.9 |
| 批量取成员 | `GET /v1/api/csgo/team_players/batch` | 6.2 |

### `/csgo/player`（选手）

| 子区 | 接口 | 章节 |
| --- | --- | --- |
| 选手搜索 | `GET /v1/api/csgo/players` | 7.1 |
| 选手排名 / 总奖金排名 | `POST /v1/api/csgo/mfilter/player/list` | 7.2 |
| 选手详情 | `GET /v1/api/csgo/players/{id}` | 7.3 |
| 选手数据 tab | `POST /v1/api/csgo/mfilter/player/stats` | 7.4 |
| 地图数据 | `POST /v1/api/csgo/mfilter/player/map/stats` | 7.5 |
| 武器数据 | `POST /v1/api/csgo/mfilter/player/weapon/stats` | 7.6 |
| 武器分类枚举 | `GET /v1/api/csgo/mfilter/player/weapon/cate` | 7.12 |
| 残局统计 | `POST /v1/api/csgo/mfilter/player/camp/stats` | 7.7 |
| 残局明细列表 | `POST /v1/api/csgo/mfilter/player/final/list` | 7.8 |
| 残局汇总（轻量） | `POST /v1/api/csgo/mfilter/player/final/stats` | 7.13 |
| 选手近期比赛（可翻页筛选） | `POST /v1/api/csgo/mfilter/player/match/list` | 7.9 |
| 选手多维排行（任意指标排序） | `POST /v1/api/csgo/mfilter/player/multidimension/list` | 7.10 |
| 选手参加过的赛事 | `GET /v1/api/csgo/player/tt/{id}` | 7.11 |
