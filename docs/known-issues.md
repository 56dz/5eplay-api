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

## 🟢 低：`/matches/{id}/data` 的增量参数

实测传 `?state_ver=` / `?local_ver=` **响应体积不变**（都是全量 60–125 KB）。

但响应里有 `eplus_realtime_topic` 字段，说明官方用 WebSocket 推送增量。WS 协议未逆向。

对于手表这类流量敏感的设备，目前只能靠**本地缓存 + 降频轮询**。

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
