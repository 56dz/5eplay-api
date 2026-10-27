# 字段速查表

只列写客户端真正会用到的字段。路径以 `data` 为根。

## 比赛列表项

来源：`GET /v1/api/csgo/matches`

| 用途 | 字段路径 | 示例值 | 备注 |
| --- | --- | --- | --- |
| 比赛 ID | `matches[].mc_info.id` | `csgo_mc_2399921` | 拉详情用 |
| 主队名 | `matches[].mc_info.t1_info.disp_name` | `Spirit` | |
| 主队 logo | `matches[].mc_info.t1_info.logo` | `https://oss.5eplay.com/...png` | 直接 `<img>` |
| 主队 ID | `matches[].mc_info.t1_info.id` | `csgo_tm_7020` | |
| 客队名 | `matches[].mc_info.t2_info.disp_name` | `MOUZ` | |
| 客队 logo | `matches[].mc_info.t2_info.logo` | `...` | |
| 大比分 | `matches[].state.t1_score` / `t2_score` | `"2"` / `"0"` | 局分 |
| 比赛状态 | `matches[].state.status` | `"0"/"1"/"2"` | 未开始/进行中/已结束 |
| 赛制 | `matches[].mc_info.format` | `"3"` | 3 = BO3 |
| 开始时间 | `matches[].mc_info.plan_ts` | `"1794315000"` | **秒**时间戳（字符串） |
| 轮次 | `matches[].mc_info.round_name` | `"决赛"` | |
| 阶段 | `matches[].mc_info.tt_stage` | `"淘汰赛"` | |
| 赛事名 | `matches[].tt_info.disp_name` | `"BLAST 对抗赛 2026 S2"` | |
| 赛事 logo | `matches[].tt_info.logo` | `...` | |
| 奖金 | `matches[].tt_info.bonus` | `"$1,000,000"` | |
| 赛事等级 | `matches[].tt_info.grade_label` | `"S级赛事"` | 直接显示 |
| 地点 | `matches[].tt_info.city_name` | `"中国香港赤鱲角"` | |
| 当前回合 | `matches[].state.round_num` | `"14"` | 直播时 |

> 进行中的比赛在 `data.live_matches[]`，结构与 `data.matches[]` 完全一致。

## 比赛详情 — 地图

来源：`GET /v1/api/csgo/matches/{id}/data` → `data.match.bouts_state[]`

| 用途 | 字段路径 | 示例值 |
| --- | --- | --- |
| 第几局 | `bouts_state[].bout_num` | `"1"` |
| 地图名 | `bouts_state[].map_name` | `"Ancient"` |
| 地图图标 | `bouts_state[].map_icon` | `https://...` |
| 地图状态 | `bouts_state[].status` | `"2"` 打完 / `"1"` 进行中 / `"-1"` 未开始 |
| 本图胜者 | `bouts_state[].result` | `"t1"` / `"t2"` / `""` |
| **本方比分** | `bouts_state[].t1_stats.quick_score` | `"13"` |
| **对方比分** | `bouts_state[].t2_stats.quick_score` | `"9"` |
| 上半场得分 | `bouts_state[].t1_stats.sh_score` | `"5"` |
| 上半场阵营 | `bouts_state[].t1_stats.sh_role` | `"T"` |
| 下半场得分 | `bouts_state[].t1_stats.fh_score` | `"8"` |
| 比分曲线 | `bouts_state[].t1_stats.sh_data` | `[0,2,2,2,...]` |
| 选图动作 | `bouts_state[].bp_act` | `"t2_pick"` |
| 回合数 | `bouts_state[].round_num` | `"22"` |

## 比赛详情 — 选手（单图）

来源：`bouts_state[].t1_pr_stats[]` / `t2_pr_stats[]`

| 用途 | 字段 | 示例 |
| --- | --- | --- |
| ID | `id` | `csgo_pl_18638` |
| 昵称 | `name` | `sk0R` |
| 头像 | `portrait` | `https://...png` |
| 国籍旗 | `country_logo` | `https://...png` |
| 击杀 | `kill` | `"28"` |
| 死亡 | `death` | `"27"` |
| 助攻 | `assist` | `"6"` |
| **Rating** | `rating` | `"1.07"` |
| Impact | `impact` | `"1.12"` |
| **ADR** | `adr` | `"81.3"` |
| **KAST** | `kast` | `"75.0%"` |
| K/D | `kdratio` | `"1.04"` |
| 爆头率 | `head_shot_rate` | `"17.6%"` |
| 首杀 | `first_blood_num` | `"3"` |
| 首杀率 | `first_blood_rate` | `"42.9%"` |
| MVP | `round_mvp` | `"4"` |
| 多杀 | `k2` `k3` `k4` `k5` | `"3"` `"1"` `"0"` `"0"` |

## 赛事

| 用途 | 字段路径 | 示例 |
| --- | --- | --- |
| 赛事 ID | `basic.tt_id` | `csgo_tt_8251` |
| 中文名 | `basic.name_zh` | `BLAST 对抗赛 2026 S2` |
| 英文名 | `basic.name_en` | `BLAST Rivals 2026 Season 2` |
| Logo | `basic.logo` | `https://...png` |
| 奖金 | `basic.bonus` | `$1,000,000` |
| 地点 | `basic.city_name` | `中国香港赤鱲角` |
| 开始 | `basic.start_time` | `2026-11-09 00:00:00` |
| 结束 | `basic.end_time` | `2026-11-15 23:59:59` |
| 等级 | `basic.grade` | `2`（见等级映射） |
| 状态 | `basic.status` | `upcoming` |

`grade` 映射：`1`=Major · `7`=S+ · `2`=S级 · `3`=A级

## 队伍

| 用途 | 字段路径 | 示例 |
| --- | --- | --- |
| ID | `items[].id` | `csgo_tm_7020` |
| 名 | `items[].name` | `Spirit` |
| Logo | `items[].logo` | `https://...png` |
| K/D | `items[].kd` | `1.07` |
| 地图数 | `items[].map_count` | `2073` |

---

## 解析注意事项

1. **几乎所有数值都是字符串**，包括 `"13"`、`"1.07"`、`"75.0%"`。解析前先 `strip("%")`。
2. **时间戳有两种格式**：
   - `plan_ts` = 秒级时间戳字符串（如 `"1794315000"`）
   - `start_time` / `end_time` = `"2026-11-09 00:00:00"`（本地时间，无时区标记，按 UTC+8 处理）
3. **`log_info` 是二次转义 JSON**，需要 `JSON.parse(JSON.parse(x).log_info)`。
4. **`graph` 也是 JSON 字符串**（在 `stages` 接口里）。
5. **`t1` / `t2` 的语义**：始终对应 `mc_info.t1_info` / `t2_info`，页面上"主队 vs 客队"的位置。CSS 上不一定真的在主队位置。
6. **`bouts_state` 里未开始的地图 `t1_stats` 可能是空对象**，判空再读 `quick_score`。
7. **`status` 都是字符串**，`"2"` 不是 `2`。腾讯系接口习惯。
