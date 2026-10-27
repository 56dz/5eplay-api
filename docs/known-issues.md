# 已知问题 / 未解之谜

按「影响程度」排序。欢迎 PR 补全。

> **2026-10 大更新**：原来这里的 4 条主要待办**全部解决**了。
> 结论见下面「✅ 已解决」各节；真正还没搞定的放在最后的「🟡 仍未解」。

---

## ✅ 已解决：赛事列表的批量接口（原 🔴 高）

**结论：`GET /v1/api/csgo/tournaments` 是死路，真正的列表接口在 `app.5eplay.com`，而且是 POST。**

```
POST https://app.5eplay.com/api/csgo/tournament/csgo_event_list_v1
Content-Type: application/json
```

```bash
curl -s -X POST 'https://app.5eplay.com/api/csgo/tournament/csgo_event_list_v1' \
  -H 'Content-Type: application/json' \
  -d '{"tournaments_options":{"cursor":"","page_token":"","time_type":null,"time_value":null,
       "grade":[],"tt_series":[],"tt_bonus":[],"team_id":"","player_id":""}}'
```

实测一次返回 **21 条**，`live` / `upcoming` / `past` 三种状态混排，每条带完整 `basic_info`（封面、奖金、地点、`grade_label`、`start_time`/`end_time`）+ `teams[]` + `win_team`。

翻页要 `cursor` + `page_token` **配对**：`cursor` 取 `"next"` / `"prev"`，`page_token` 取上一页最后一条的 `page_token`（格式 `"2026-10-25 00:00:00,csgo_tt_9463"`）。只传 `page_token` 不起来作用（会原样返回第一页）。

详见 [endpoints.md 5.1](endpoints.md#51-赛事列表--真正的批量接口post走-app5eplaycom)。

**另外补到的**：`GET /v1/api/csgo/tournaments/match_list?tt_ids=csgo_tt_8050` 一次返回该赛事全部 **41 场**比赛，结构与比赛列表页完全一致。

---

## ✅ 已解决：队伍近期比赛恒为空（原 🔴 高）

**结论：`status` 不是数字，是字符串 `past` / `upcoming`。** 传数字不报错、`success` 仍为 `true`，只是 `matches` 静默为空 —— 这就是一直被误导的原因。

```bash
curl -s \
  'https://esports-data.5eplaycdn.com/v1/api/csgo/team/matches_v1/csgo_tm_4494?page=1&limit=5&status=past'
```

对 `csgo_tm_4494`（MOUZ）实测：

| `status` | `matches` | `total_rows` |
| --- | --- | --- |
| `past` | 5 | **1613** |
| `upcoming` | 3 | 3 |
| `live` | 0 | 0 |
| `0` / `1` / `2` | 0 | 0 |
| 省略 | 5 | 1613（默认 `past`） |

`limit` 没有硬上限，实测 200 也照常返回（建议 ≤ 50）。

详见 [endpoints.md 6.3](endpoints.md#63-队伍近期比赛--已解status-是字符串枚举)。

---

## ✅ 已解决：世界排名 / VRS 找不到（原 🟡 中）—— 且它不是「5E 榜」

**结论：路径没变，是 `/v1/api/csgo/new/rank/team_list`，但必须 `POST`。`GET` 一律 `404 page not found`。**

```bash
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/new/rank/team_list' \
  -H 'Content-Type: application/json' \
  -d '{"sort_value":"desc","rank_type":"rank","sort_key":"rank","region":"",
       "team_options":{"tt_ids":[],"time_value":"","grade":[],"team_id":"",
       "time_type":"","tt_series":[],"maps":[],"page":1}}'
```

两套榜，`rank_type` 和 `sort_key` 必须同时改：

| `rank_type` | `sort_key` | 榜 | `total_rows` |
| --- | --- | --- | --- |
| `rank` | `rank` | **HLTV 世界排名**（积分榜，不是 5E 榜） | **328** |
| `valve_rank` | `valve_rank` | Valve VRS | **377** |

> 更正：早先这里写的「5E 世界排名」是错的。5E 不发布排名，`rank` 就是 HLTV 积分榜。
> item 里 `rank`/`point` 与 `valve_rank`/`valve_point` 并列存在，取值要和 `rank_type` 对上。

`region` 传**中文**（`""` 全球 328 / `欧洲` 182 / `亚洲` 35 / `美洲` 69 / `中国` 0 / `大洋洲` 0）。20 条/页。

前端默认值是一串乱码 `ȫ������`（GBK 被当 latin1 解出来的「全部地区」），实测等价于空字符串 —— 别照抄。

详见 [endpoints.md 8](endpoints.md#8-世界排名--vrs--必须-post)。

---

## ✅ 已解决：`/matches/{id}/data` 的增量参数（原 🟢 低）

**结论：不存在增量参数。** `?state_ver=` / `?local_ver=` / `?from_ver=` 传了都一样，响应体积不变（恒为全量 60–125 KB）。

增量只能走 **MQTT over WSS**：

- `/matches/{id}/data` 响应里的 `eplus_realtime_topic` 就是订阅 topic
- 官方前端根本不做轮询，比赛进行中全靠推送

已完整打通链路（握手 / topic / 消息结构），详见 [endpoints.md 2.6](endpoints.md#26-实时推送mqtt-over-wss-已打通)。

对流量敏感的设备（比如手表），推荐：**首次全量 → 之后只订阅 MQTT → 断线再全量重拉**。

---

## ✅ 已解决：完整 ban/pick 序列

在 `GET /matches/{id}/data` 的 `data.match.global_state.bp_map_item[]` 里，7 条（BO3），`bp_type` 为 `ban` / `pick` / `left`。已结束和进行中的比赛都有。详见 [endpoints.md 2.4](endpoints.md#24-global_state--全局状态含-banpick-序列)。

---

## ✅ 已解决：加时赛结构（19:16 实测）

用 `csgo_mc_2399119` 的 Inferno（19:16，两次加时）实测：

```json
"quick_score": "19",   // 最终总分，含加时
"sh_score":   "6",     // 上半场
"sh_role":    "CT",
"sh_data":    [0,1,1,1,1,1,0,0,4,0,0,0],   // 12 个分段（每 3 回合一段）
"fh_score":   "6",     // 下半场
"fh_data":    [0,3,2,3,0,0,0,0,2,0,3,2],
"ot_score":   "7",     // 加时得分 = 19 - 6 - 6
"ot_role":    "",
"ot_data":    [0,0,0,2,3,2,0,3,2,1,1,0],
"all_score":  "19",
"flags":      ["w10"]
```

结论：

- `sh_score + fh_score + ot_score == quick_score`（6+6+7=19 ✅）
- `ot_data` 是逐步累加序列，长度为 **6 × 2 = 12**（两个 OT 各 6 回合），两边 `ot_data` 互补（t1 赢的分 = t2 没赢的分）
- `ot_role` 为空字符串，不用管
- `flags` 是给前端画棋子/徽标用的标记（`w10` = 10 连胜？），非核心

所以解析时：**上半场 `sh_score` / 下半场 `fh_score` / 加时 `ot_score`** 三段分开读，`quick_score` 为总分。

---

## 🟡 仍未解

### 1. `mfilter/player/list` 只有两个排序维度

`POST /v1/api/csgo/mfilter/player/list` 的 `dimension` + `sort_key` 实测只有两组合法：

| `dimension` | `sort_key` | 含义 |
| --- | --- | --- |
| `top` | `rating` | Rating 榜（1218 人） |
| `earning` | `total_earnings` | 总奖金榜（1503 人） |

试过 `sort_key` = `kpr` / `adr` / `impact` / `kast` / `swing` / `kd` / `kddiff` / `mvp` / `map_count` → 全部 `参数排序错误`。`dimension` 空 → `维度不能为空`；`sort_key` 空 → `排序字段不能为空`。

**绕过办法（已验证）**：要按 ADR/KAST/KPR/Impact/KD 排序，用 **7.10 的 `mfilter/player/multidimension/list`**，那个接口 `sort_key` 支持全套指标。

```bash
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/mfilter/player/multidimension/list' \
  -H 'Content-Type: application/json' \
  -d '{"player_options":{"player_id":"","time_type":"recent",
       "time_value":"2026-07-27 00:00:00_2026-10-27 23:59:59","tt_ids":[],"maps":[],
       "recent_match":"","grade":[],"page":1,"team_id":""},
       "dimension":"","sort_key":"adr","sort_value":"DESC"}'
```

> **仍未解**：`player/list` 本身为什么只认这两种，chunk 里也只出现 `top` / `earning` 两个值。但功能上已被 7.10 完全覆盖，不影响写客户端。

### 2. `player_data` 里几个字段恒为 0

`GET /v1/api/csgo/players/{id}` → `data.player_data`：

- `assists_round` = `"0"`
- `saved_by_teammate_round` = `"0"`
- `saved_teammates_round` = `"0"`
- `rating_chart` = `[]`

换了几个选手都一样。**未验证**是真没数据还是需要额外参数（比如 `?time_type=`）。需要用助攻数的话，走 `mfilter/player/stats` 的 `player_data.total_assist`（有值）。

### 3. `team/data/details` 的选手区块是空的

`POST /v1/api/csgo/mfilter/team/data/details` 返回 `player_basics_display: false`、`player_basics_data: []`，即使传了合法 `time_type`/`time_value` 也不填。

**推测**：队伍页的选手数据本来就走 `team_players/batch`（6.2）+ `player/stats`，这个字段是残留。**未验证**有没有能激活它的参数。

### 4. 三个赛事维度统计接口的 `total_rows` 不可信

`POST /v1/api/csgo/tournaments/player_data` 能正常返回 **81 名选手**的完整 78 字段，但 `data.total_rows` 恒为 `0`、`total_page` 也异常。`team_data` 和 `map_data` 同样如此。

**结论**：这三个接口**不做分页**，一次全给你，**不要信 `total_rows`**，直接用 `len(items)`。`page` 参数传了对结果也没影响（未逐页验证）。

同类问题还有 **7.10 `multidimension/list`**：`total_rows` 在 `page=1` 时返回 `"19"`、`page=2` 时 `"20"`、
翻到 `page=50` 才变成真实值 `"627"`。判断还有没有下一页只能看 `items` 是否为空。

### 5. `hltv_team_*` 与 `csgo_tm_*` 两套队伍 ID（已查清，无需转换）

比赛详情、`matches` 列表里常见 `csgo_tm_xxx`；对阵图（`stages` 的 `graph`）和部分队伍用 `hltv_team_xxx`。

**结论：不需要转换接口。两套 ID 在所有队伍端点上都通用**，实测全部 `success:true`：

| 端点 | `hltv_team_12394` |
| --- | --- |
| `GET /v1/api/csgo/teams/{id}/overview` | ✅ |
| `GET /v1/api/csgo/teams/{id}/honors` | ✅ |
| `GET /v1/api/csgo/team/tt/{id}` | ✅ |
| `GET /v1/api/csgo/team/matches_v1/{id}?status=past` | ✅ |
| `GET /v1/api/csgo/matches?...&team_ids={id}` | ✅ |

而且**同一个队只会有一种前缀**：`teams?name=BB` 只返回 `hltv_team_12394` / `hltv_team_13996`，
`teams?name=Spirit` 返回 `csgo_tm_7020` / `csgo_tm_7900` / `hltv_team_13012`。
`mfilter/team/list` 的第一页 20 条里也是混着的（15 个 `csgo_tm_` + 5 个 `hltv_team_`）。

> 写客户端：**拿到什么 ID 就存什么 ID**，两种都能直接当主键用；别试图拼一个转换函数。
> 唯一要注意的是**别对 ID 做前缀假设**（比如 `id.replace('csgo_tm_','')` 这种会崩）。

### 6. `/datacenter-web-api/` 系列 —— 确认是死路

chunk 里见过 `/datacenter-web-api/api/rank/batch/5epl` 和 `.../ladder`（5EPL 排位 / 天梯）。

实测四个域名：

| 域名 | 结果 |
| --- | --- |
| `esports-data.5eplaycdn.com` | `404` |
| `app.5eplay.com` | `404` |
| `www.5eplay.com` | `404` |
| `event.5eplay.com` | `200`，但返回的是 **SPA 的 index.html**（`<title>5EPlay-赛事数据中心</title>`），不是 JSON |

**结论**：这个 series 挂在另一个我们没找到的后端上，或者需要登录态。不属于「赛事数据」范畴
（5EPL 是天梯排位，不是比赛），**不再投入**。

### 7. 视频回放 / 直播源只在部分比赛上有

选手近期比赛（7.9）的 `mc_info.high_lights_cfg_list[]` 与 `live_cfg_list[]` 是回放/直播地址，
但**不是每场都有**（老比赛基本空）。未验证是否存在「按比赛 ID 单独取回放」的接口 —— chunk 里没找到。

---

## 已确认的死路（不用再试）

| 请求 | 结果 |
| --- | --- |
| `GET /v1/api/csgo/matches/{id}`（不带 `/data`） | 404 |
| `GET /v1/api/csgo/match/{id}` | 404 |
| `GET /v1/api/csgo/teams/{team_id}` | 404 |
| `GET /v1/api/csgo/tournaments?page=&limit=&grade=&status=` | 空数组（参数怎么试都空） |
| **`GET`** `/v1/api/csgo/mfilter/team/list` | 404（是 POST） |
| **`GET`** `/v1/api/csgo/mfilter/player/list` | 404（是 POST） |
| **`GET`** `/v1/api/csgo/mfilter/team/data/details` | 404（是 POST） |
| **`GET`** `/v1/api/csgo/mfilter/player/{stats,map/stats,camp/stats,weapon/stats,final/list}` | 404（都是 POST） |
| **`GET`** `/v1/api/csgo/new/rank/team_list` | 404（是 POST） |
| **`GET`** `/v1/api/csgo/tournaments/{team,player,map}_data` | 404（都是 POST） |
| `POST /v1/api/csgo/mfilter/team/search` | 404（队伍搜索用 `GET /v1/api/csgo/teams?name=`） |
| `POST /v1/api/csgo/mfilter/player/search` | 404（选手搜索用 `GET /v1/api/csgo/players?name=`） |
| `POST /v1/api/csgo/mfilter/tournament/search` | 404（是 **GET**，`?name=&page=`） |
| `/v1/api/csgo/mfilter/team/data/maps`、`.../team/data/players` | 404（地图总览是 `.../team/data/map/all`，见 6.9） |
| `/v1/api/csgo/map/list` | 404（地图列表没有独立接口） |
| **`GET`** `/v1/api/csgo/mfilter/player/match/list` | 404（是 POST，且 body 里 `time_value` 不能为空，否则 `time_value验证错误`） |
| `/datacenter-web-api/api/rank/batch/{5epl,ladder}` | 前三个域名 404，`event.5eplay.com` 返回 HTML |
| `app.5eplay.com/api/tournament/event_session_list?game_type=2`（CS2） | `matches: []`（那是 DOTA2 的，CS2 用 `session_list`，见 5.6） |
| `session_result_list` 传 `tt_id=22819` / `tt_ids=csgo_tt_8251` | **不过滤**，实测 `tt_id=999999` 也返回同一批。赛果只能拿全站流再按 `tt_info.id` 自己分组 |
| `session_list` 传 `tt_id=22819`（纯数字） | **不过滤**，要 `tt_ids=csgo_tt_8251`（带前缀） |
| `session_result_list` 传 `page` / `limit` | 无效（恒返回 10 条），它只认 `page_size` + `page_token` |
| `match_score_list` 的 `tab` 传 `0/1/2/3/match_map/match_data/map/bout/match_score/match_detail` | 全部 `参数错误`（只认 `match_player` 且要带 `team_id`） |

> ⚠️ **`POST` 接口用 `GET` 调会返回 `404 page not found`，不是 405。** 这是本项目最大的坑 —— 看到 404 先怀疑方法错了，不要以为路径不存在。
> 反过来，`POST` 漏了 `Content-Type: application/json` 也会失败。

---

## 报告问题

发现了错误或者补齐了某项，欢迎提 issue / PR。
请附上**可复现的 curl + 真实返回**（敏感字段可以打码，但 ID 和时间请保留）。
