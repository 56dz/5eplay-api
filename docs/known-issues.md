# 已知问题 / 未解之谜

按「影响程度」排序。欢迎 PR 补全。

## 🔴 高：赛事列表没有正确的批量接口

`/v1/api/csgo/tournaments` 无论怎么传参数都返回空：

```bash
curl -s 'https://esports-data.5eplaycdn.com/v1/api/csgo/tournaments?page=1&limit=3'
# {"success":true,"errcode":0,"message":"","data":{"items":[]}}
```

试过 `status=1` / `status=0` / `grade=2` / `page=1&limit=5&grade=2`，全部空。

**目前唯一能用的赛事列表**是 `/v1/api/csgo/mfilter/tournament/search`，但只返回 `name` + `tt_id`，没有封面/时间/奖金。

**临时方案**：先 search 拿到一批 `tt_id`，再用 `/v1/api/csgo/focus/tournaments?tt_ids=a,b,c,d` **批量**补全详情（这个接口支持逗号分隔多 ID，一次最多实测 5 个稳定）。

**待解**：`/tournaments` 到底该传什么。可能参数名不是 `status` 而是 `tt_status` / `time_range` / `start_ts`，也可能需要先传 `game_id`。

---

## 🔴 高：队伍近期比赛恒为空

```bash
curl -s 'https://esports-data.5eplaycdn.com/v1/api/csgo/team/matches_v1/csgo_tm_4494?page=1&limit=20&status=2'
# matches: [], total_rows: "0"
```

`status` 试了 `0` `1` `2` `3` `4`，`matches` 永远是空数组。但 `win_rate: "72.0"` 有值，说明这场队确实有数据。

**待解**：`status` 的真实枚举，或者应该用另一个路径（`/v1/api/csgo/teams/{id}/matches` 之类）。

---

## 🟡 中：世界排名 / VRS 积分接口未找到

`/v1/api/csgo/new/rank/team_list` → 404。

网页上应该有「世界排名」页签，但接口没定位到。可能路径在 `/datacenter-web-api/` 下（chunk 里见过 `/datacenter-web-api/api/rank/batch/5epl`，但那是 5EPL 排位，不是 CS2 世界排名）。

---

## 🟡 中：`bouts_state[].bp_act` 只有单值

只看到 `"t2_pick"`，没有完整的 ban/pick 序列（谁先 ban、ban 了什么图）。

完整序列可能在：
- `global_state` 里的某个字段
- `stages` 接口的 `graph` 里
- `/matches/{id}/analysis_v1`（未验证）

---

## 🟡 中：加时赛结构未验证

`t1_stats.ot_data` / `ot_score` / `ot_role` 字段存在，但没找到一场加时的比赛来验证结构。

手上已知比赛的比分都是常规时间结束。

---

## 🟢 低：`/matches/{id}/data` 是否支持增量

试过 `?update_version=0` 之类的参数，没看出差别。每次都是全量 60–120 KB。

对于手表这类流量敏感的设备是个负担。**待解**：有没有 `?since=` / `?ver=` 这类增量参数。

---

## 🟢 低：`global_state` 未逐字段梳理

里面字段很多（`avg_player_stats`、`ana_map_desc_flag`、各种 map 描述），目前只确认了 `avg_player_stats` 是全队平均。

---

## 已确认的死路（不用再试）

| 请求 | 结果 |
| --- | --- |
| `GET /v1/api/csgo/matches/{id}`（不带 `/data`） | 404 |
| `GET /v1/api/csgo/match/{id}` | 404 |
| `GET /v1/api/csgo/teams/{team_id}` | 404 |
| `GET /v1/api/csgo/mfilter/team/list` | 404 |
| `GET /v1/api/csgo/new/rank/team_list` | 404 |
| `GET /v1/api/csgo/tournaments?page=&limit=&grade=&status=` | 空数组 |
| `match_score_list` 的 `tab` 传 `0/1/2/3/match_map/match_data/map/bout/match_score/match_detail` | 全部 `参数错误` |

---

## 报告问题

发现了错误或者补齐了某项，欢迎提 issue / PR。
请附上**可复现的 curl + 真实返回**（敏感字段可以打码，但 ID 和时间请保留）。
