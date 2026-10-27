# 5eplay CS2 API 逆向

> 5E 对战平台（5eplay）CS2 赛事数据的**非官方**接口文档。
> 全部结论来自对 `https://event.5eplay.com` 前端 JS bundle 的静态分析 + 实际抓包验证。

**不需要 API Key，不需要登录，不需要 Cookie。** 三个域名均可直接匿名访问。

## 为什么有这份文档

想看 CS2 比赛的详细数据，官方的赛事页有，但没有任何 API 文档 —— 数据都在前端异步拉，想知道怎么拿只能自己去读打包后的 JS。

这份笔记就是干这个的：把 `event.5eplay.com` 四个菜单背后的接口一个个挖出来，**每个都亲手 curl 过**，把请求参数、真实返回、字段含义、以及踩过的坑一起记下来。目标是你看完之后能直接写出一个能跑的数据客户端，而不用再重复一遍逆向的过程。

文档里凡是标「实测」的都有可复现命令，标「未验证」的是从代码里读到但没打出返回的 —— 请自己再确认。

---

## 这是什么

[5E 对战平台](https://www.5eplay.com) 的赛事页 `https://event.5eplay.com/csgo/*` 提供了相当完整的 CS2 赛事数据。本项目覆盖它的**四个主菜单**：

| 菜单 | 能拿到什么 |
| --- | --- |
| `/csgo/matches` 比赛 | 比赛列表（未开始/直播/已结束）、**每图详细比分**（19:16 含两次加时）、**每图每队 5 名选手完整数据**（kill/death/rating/adr/kast/…）、**逐回合流水**、**完整 ban/pick 序列**、赛前分析、实时推送（MQTT） |
| `/csgo/events` 赛事 | 赛事列表（可翻页）、赛事详情、**赛程对阵图**（含服务端算好的节点坐标）、**奖金分配**、赛程/赛果列表（可翻页）、参赛队伍 / 选手 / 地图三套维度统计（78 个选手字段） |
| `/csgo/teams` 队伍 | 队伍搜索、队伍榜单（20+ 统计字段可排序）、队伍详情、荣誉墙、**近期比赛**（`status=past`）、地图池与地图三块总览、选手名单 |
| `/csgo/player` 选手 | 选手搜索、Rating 榜 / 总奖金榜、**任意指标排序的自定义榜**、选手详情（生涯 + 外设配置）、地图/武器/残局三套统计、**近期比赛（可翻页+按赛事/地图/等级筛）**、同位置百分位对比 |
| 世界排名 | **5E 世界排名**（328 队）与 **Valve VRS**（377 队），支持按地区筛选 |

这些数据网页上都渲染了，只是没公开文档。本项目把接口整理出来，方便写客户端、做数据看板、喂给 AI agent。

## 快速开始

```bash
# 比赛列表（1 = 进行中，2 = 已结束，0 = 未开始）
curl -s 'https://esports-data.5eplaycdn.com/v1/api/csgo/matches?page=1&limit=20&game_status=2' \
  | python -m json.tool | head -60
```

```bash
# 某场比赛的完整数据（每图比分 + 选手数据 + ban/pick）
curl -s 'https://esports-data.5eplaycdn.com/v1/api/csgo/matches/csgo_mc_2399921/data' \
  | python -m json.tool | head -100
```

```bash
# 赛事列表（注意：POST 到 app.5eplay.com，不是 GET 到 esports-data）
curl -s -X POST 'https://app.5eplay.com/api/csgo/tournament/csgo_event_list_v1' \
  -H 'Content-Type: application/json' \
  -d '{"tournaments_options":{"cursor":"","page_token":"","grade":[],"tt_series":[],"tt_bonus":[]}}'
```

```bash
# 世界排名（必须 POST，GET 会 404）
curl -s -X POST 'https://esports-data.5eplaycdn.com/v1/api/csgo/new/rank/team_list' \
  -H 'Content-Type: application/json' \
  -d '{"sort_value":"desc","rank_type":"rank","sort_key":"rank","region":"",
       "team_options":{"page":1}}'
```

所有接口返回统一信封：

```json
{ "success": true, "errcode": 0, "message": "", "data": { ... } }
```

失败时 `success:false`，`message` 里通常有中文错误（如 `参数错误`、`404 page not found`）。

> ⚠️ **两个必读的坑**
> 1. `mfilter/*`、`new/rank/*`、`tournaments/{team,player,map}_data` 这些**全是 POST**。用 GET 调会返回 `404 page not found`（不是 405），很容易误判成路径不存在。
> 2. `POST` 必须带 `Content-Type: application/json`，body 是 JSON 字符串，否则静默失败。

## 三个域名

| 域名 | 用途 |
| --- | --- |
| `https://esports-data.5eplaycdn.com` | 主要数据接口（`/v1/api/csgo/...`），含比赛、队伍、选手、排名、统计 |
| `https://app.5eplay.com` | 补充接口：**赛事列表**（`/api/csgo/tournament/csgo_event_list_v1`）与整场选手汇总（`/api/score/...`） |
| `https://oss.5eplay.com` | 静态资源：队伍 / 赛事 / 地图 / 选手头像 |

> 从中国大陆以外的网络访问时，`esports-data.5eplaycdn.com` 可能需要代理才能连通；`app.5eplay.com` 与 `oss.5eplay.com` 通常直连可达。实测在智能手表（Android 8.1）上三个域名均直连 200。

## 文档

| 文件 | 内容 |
| --- | --- |
| [docs/endpoints.md](docs/endpoints.md) | 全部已知接口（2400+ 行），含参数、curl 示例、真实返回片段 |
| [docs/fields.md](docs/fields.md) | 字段速查表：比赛 / 地图 / 选手 / 赛事 / 队伍 / 排名 |
| [docs/reverse-engineering.md](docs/reverse-engineering.md) | 怎么找到这些接口的（方法论，方便你继续挖） |
| [docs/known-issues.md](docs/known-issues.md) | 已知死路、未解之谜、待补参数 |

### 按页面找接口

`docs/endpoints.md` 第 10 章有「四个菜单 → 接口」的完整对照表，直接按你想做的页面查。

| 你想做… | 看这一节 |
| --- | --- |
| 比赛列表页 | [1. 比赛列表](docs/endpoints.md#1-比赛列表) |
| 比赛详情 / 比分板 | [2. 比赛详情](docs/endpoints.md#2-比赛详情--核心) |
| 实时比分（比赛进行中） | [2.6 MQTT over WSS](docs/endpoints.md#26-实时推送mqtt-over-wss-已打通) |
| 逐回合回放 | [3. 逐回合流水](docs/endpoints.md#3-逐回合流水) |
| 赛事列表页 | [5.1 赛事列表](docs/endpoints.md#51-赛事列表--真正的批量接口post走-app5eplaycom) |
| 赛事详情 / 对阵图 | [5.2 赛事详情](docs/endpoints.md#52-赛事详情) / [5.3 赛程对阵图](docs/endpoints.md#53-赛事赛程--对阵图--可解析) |
| 赛事奖金分配 | [5.1quater 奖金分配](docs/endpoints.md#51quater-赛事奖金分配team_rank) |
| 赛事赛程 / 赛果列表 | [5.6 赛程与赛果](docs/endpoints.md#56-赛事赛程--赛果app5eplaycom) |
| 队伍详情页 | [6.5 队伍详情页](docs/endpoints.md#65-队伍详情页接口) / [6.7 队伍数据统计](docs/endpoints.md#67-队伍数据统计team_overview--地图池) |
| 队伍近期比赛 | [6.3 队伍近期比赛](docs/endpoints.md#63-队伍近期比赛--已解status-是字符串枚举) |
| 队伍地图总览 | [6.9 队伍地图总览](docs/endpoints.md#69-队伍地图总览一次拿三块地图数据) |
| 选手详情页 | [7.3 选手详情](docs/endpoints.md#73-选手详情--一个接口拿全) |
| 选手数据 tab | [7.4 选手统计](docs/endpoints.md#74-选手统计带同位置对比区间) |
| 选手近期比赛 | [7.9 选手近期比赛](docs/endpoints.md#79-选手近期比赛--可翻页可筛选) |
| 自定义指标排行（按 ADR/KAST 等排序） | [7.10 选手多维对比](docs/endpoints.md#710-选手多维对比--自定义排序榜) |
| 世界排名 / VRS | [8. 世界排名 / VRS](docs/endpoints.md#8-世界排名--vrs--必须-post) |
| 赛事内队/选手/地图统计 | [9. 赛事维度统计](docs/endpoints.md#9-赛事维度统计队--选手--地图) |

## 示例脚本

```bash
# —— 比赛 ——
python tools/probe.py matches --status 1              # 列出进行中的比赛
python tools/probe.py detail csgo_mc_2399921          # 一场比赛的完整数据
python tools/probe.py rounds csgo_mc_2399921          # 逐回合流水

# —— 赛事 ——
python tools/probe.py events                          # 赛事列表（POST app.5eplay.com）
python tools/probe.py tournament csgo_tt_8251         # 赛事详情
python tools/probe.py tt-prize csgo_tt_8251           # 奖金分配
python tools/probe.py sessions csgo_tt_8251         # 赛程（加 --result 看赛果）
python tools/probe.py tt-data csgo_tt_9440            # 赛事内队/选手/地图统计
python tools/probe.py tt-stats csgo_tt_8050           # 同上，走 mfilter 的完整版

# —— 队伍 ——
python tools/probe.py team csgo_tm_9565               # 队伍详情
python tools/probe.py team-matches csgo_tm_4494       # 队伍近期比赛
python tools/probe.py team-stats csgo_tm_9565         # 队伍数据统计
python tools/probe.py team-map csgo_tm_9565           # 地图池 + 三块地图总览
python tools/probe.py teams --limit 10                # 队伍榜单

# —— 选手 ——
python tools/probe.py player csgo_pl_11893            # 选手详情
python tools/probe.py player-matches csgo_pl_11893    # 选手近期比赛
python tools/probe.py player-top --sort-key adr       # 任意指标排行

# —— 排名 ——
python tools/probe.py rank                            # 5E 世界排名
python tools/probe.py vrs                             # Valve VRS 榜
```

需要代理时：

```bash
python tools/probe.py --proxy socks5h://127.0.0.1:10808 matches --status 2
```

## 免责声明

本项目是一份**非官方的技术笔记**，与 5E 对战平台（5eplay）及其运营方**没有任何关系**，未经其授权、认可或背书。

- **接口随时可能变**。不保证任何稳定性、可用性或正确性，也不承诺维护。
- **数据版权归 5E 对战平台及相应赛事主办方所有**。本仓库只记录公开可访问的接口形态（URL、参数、字段名），**不包含任何抓取下来的数据副本**，也不包含 5E 的前端代码。
- **请克制使用**。建议单 IP 不低于 1 秒/请求，不要并发轰炸、不要做压力测试、不要大规模爬取。被投诉或被封禁是你自己的事。
- **不要商用**，不要二次分发原始数据，不要拿去搭建对外提供的镜像服务。
- 文档里的 curl 示例仅用于说明接口形态。是否使用、如何使用，以及由此产生的任何后果，由使用者自行承担。
- 如果 5E 官方认为本仓库有不妥之处，提 issue 或邮件联系，会立即配合处理（下架相关内容或删除仓库）。
- 文中出现的队伍名、选手名、赛事名、商标均归各自所有者。

> 简言之：**这是给想学逆向和数据接口的人看的技术资料，不是给爬虫用的工具包。** 请把它当文档读，而不是当枪使。

## License

文档与脚本采用 [GPL-3.0](LICENSE)。接口与数据本身不属于本项目，也不受本许可证约束。
