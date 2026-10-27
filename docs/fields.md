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

## 比赛详情 — ban/pick 序列

来源：`data.match.global_state.bp_map_item[]`（BO3 共 7 条，顺序即实际操作顺序）

| 用途 | 字段 | 示例值 |
| --- | --- | --- |
| 动作 | `bp_type` | `ban` / `pick` / `left` |
| 地图 | `map_name` | `"Ancient"` |
| 谁操作 | `team_side` | `t1` / `t2` / `""`（left 时为空） |
| 地图图标 | `map_icon` | `https://...` |
| 地图背景 | `map_logo` | `https://...` |

## 比赛详情 — 地图池对比

来源：`GET /v1/api/csgo/matches/{id}/analysis_v1` → `data.result.comparison.team_map_stats[]`

| 用途 | 字段 | 示例值 |
| --- | --- | --- |
| 地图英文 | `name` | `Ancient` |
| 地图中文 | `name_zh` | `远古遗迹` |
| 选图方 | `bp_type` | `t2_pick` |
| T1 选择率 | `t1_pick_rate` | `"8"`（%） |
| T1 ban 率 | `t1_ban_rate` | `"26"` |
| T1 胜场 | `t1_win_num` | `"15"` |
| T1 胜率 | `t1_rate` | `"60"` |

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

队伍详情（`/teams/{id}/overview` 的 `basic_info`）：

| 用途 | 字段 | 示例 |
| --- | --- | --- |
| ID / 名 / 简称 | `id` / `disp_name` / `disp_abbr` | `csgo_tm_9565` / `Vitality` / `Vitality` |
| Logo | `logo` | `https://...png` |
| 国家 / 国旗 | `country_name` / `country_logo` | `欧盟` / `https://...png` |
| 教练 | `coach` | `XTQZZZ` |
| 总奖金 | `bonus` | `$10,373,593` |
| 平均年龄 | `average_player_age` | `28` |

## 选手

| 用途 | 字段（`basic_info`） | 示例 |
| --- | --- | --- |
| ID / 名 | `id` / `name` | `csgo_pl_11893` / `ZywOo` |
| 头像 | `portrait` / `half_portrait` | `https://...png` |
| 国家 | `country_zh` / `country_en` / `country_logo` | `法国` / `France` / url |
| 生日 / 星座 | `birthday` / `constellation` | `2000-11-09` / url |
| 位置 | `positions[]` | `["步枪手","狙击手"]`（`position` 单值为空，用数组） |
| 队伍 | `team_id` / `team_name` / `team_logo` | `csgo_tm_9565` / `Vitality` |
| 总奖金 | `bonus` | `$1,893,960` |
| Top20 次数 | `top20_num` | `7` |

选手生涯数据（`player_data`，26 个键里常用的）：

| 用途 | 字段 | 示例 |
| --- | --- | --- |
| Rating | `rating` | `1.36` |
| K/D | `kd` | `1.41` |
| 每回合击杀/死亡 | `kpr` / `dpr` | `0.84` / `0.6` |
| ADR | `adr` | `87.3` |
| Impact | `impact` | `0.95` |
| KAST | `kast` | `76.3` |
| 爆头率 | `head_shot` | `41.2` |
| 地图数 / 回合数 | `maps_played` / `rounds_played` | `1727` / `43019` |
| 分图数据 | `maps[]` | `{name, rating, kd, use_num}` |
| 武器数据 | `weapons[]` | `{name, rate, logo}` |
| 外设 | `player_profile.player_config` | `mouse_config` / `monitor_config` |

## 世界排名

`POST /v1/api/csgo/new/rank/team_list` 的 `field_values`：

| 用途 | 字段 | 示例 |
| --- | --- | --- |
| 名次 | `rank` / `global_rank` | `1` |
| 积分 | `point` / `score` | `904`（两者相同，取 `point`） |
| 名次变化 | `rank_change` / `rank_diff` | `"-"`（字符串，无变化时是横杠） |
| 分区 | `region_name` | `欧洲` |
| 击杀差 | `kd_diff` | `11214` |

> 其余 `avg_kill` / `rating` / `ct_win_rate` 等字段在默认 body 下**全是空字符串**，只有加 `time_type`/`time_value` 过滤才会填。别当 0 排序。

## 赛事维度统计（`tournaments/{team,player,map}_data`）

三个接口共用 `field_values` 扁平结构，字段数：

| 接口 | 条数示例 | `field_values` 字段数 |
| --- | --- | --- |
| `team_data`（`csgo_tt_8050`） | 16 支队伍 | **40** |
| `player_data`（`csgo_tt_8050`） | 81 名选手 | **78** |
| `map_data`（`csgo_tt_8050`） | 7 张地图 | 17 |

常用：

| 用途 | 字段 | 所在 |
| --- | --- | --- |
| 半场胜率 | `sh_rate` / `fh_rate` | team |
| 手枪局胜率 | `sh_pistol_win_rate` / `fh_pistol_win_rate` / `pistol_win_rate` | team |
| 先到 5/10 分胜率 | `flag5_win_rate` / `flag10_win_rate` | team |
| 落后翻盘 | `inferior_position_win` / `inferior_position_max_core` | team |
| 0~5 杀回合 | `zero_kill_round` ~ `five_kill_round` + `*_rate` | player |
| 残局 | `one_vs_one_kills` ~ `one_vs_five_kills` + `*_win_rate` | player |
| 单场极值 | `max_adr` / `max_rating` / `min_rating` … | player |
| 被选率 / 被 ban | `pick_rate` / `ban_count` | map |
| 加时率 | `ot_rate` / `total_ot` | map |
| **地图最强队** | `fortissimo_team_id` / `fortissimo_team_win_rate` | map |

---

## 解析注意事项

1. **几乎所有数值都是字符串**，包括 `"13"`、`"1.07"`、`"75.0%"`。解析前先 `strip("%")`。
2. **时间戳有两种格式**：
   - `plan_ts` = 秒级时间戳字符串（如 `"1794315000"`）
   - `start_time` / `end_time` = `"2026-11-09 00:00:00"`（本地时间，无时区标记，按 UTC+8 处理）
   - ⚠️ `team/matches_v1` 用的是 `ts`，**不是 `plan_ts`**
3. **`log_info` 是二次转义 JSON**，需要 `JSON.parse(JSON.parse(x).log_info)`。
4. **`graph` 也是 JSON 字符串**（在 `stages` 接口里）。
5. **`t1` / `t2` 的语义**：在 `/matches` 与 `/matches/{id}/data` 里始终对应 `mc_info.t1_info` / `t2_info`，页面上"主队 vs 客队"的位置。
   ⚠️ **但 `team/matches_v1` 是例外**：它用 `home_info` / `opponent_info`，`home_info` 恒为被查询队伍，且没有 `t1_info`/`t2_info`。那里的 `t1_score`/`t2_score` 与 `home_score`/`opponent_score` **不保证对应**，一律用 `home_*` / `opponent_*`。
6. **`bouts_state` 里未开始的地图 `t1_stats` 可能是空对象**，判空再读 `quick_score`。
7. **`status` 都是字符串**，`"2"` 不是 `2`。腾讯系接口习惯。
8. **`mfilter/*`、`new/rank/*`、`tournaments/{team,player,map}_data` 全是 POST**。用 GET 打会返回 `404 page not found`（不是 405），别误判成路径不存在。
9. **`tournaments/{team,player,map}_data` 的 `total_rows` 恒为 0**，不分页，一次全给。用 `len(items)`。
10. **`player/stats` 里数值类型混杂**：`map_stats.total` 是数字、`player_data.kd` 也是数字，但别处都是字符串。别统一当字符串处理。
11. **`player_performance` 的 `range` 是反的**：`start` > `end`，判断用 `end <= v <= start`。
12. **搜索结果的 `highlight_name` 带 `<SF-HL>` 高亮标签**，展示前要剥掉。
