# 5eplay CS2 API 逆向笔记

> 5E 对战平台（5eplay）CS2 赛事数据的**非官方**接口文档。
> 全部结论来自对 `https://event.5eplay.com` 前端 JS bundle 的静态分析 + 实际抓包验证。

**不需要 API Key，不需要登录，不需要 Cookie。** 三个域名均可直接匿名访问。

---

## 这是什么

[5E 对战平台](https://www.5eplay.com) 的赛事页 `https://event.5eplay.com/csgo/matches` 提供了相当完整的 CS2 赛事数据：

- 比赛列表（进行中 / 未开始 / 已结束，可按赛事筛选）
- **每张地图的详细比分**（13:11 这种，不是只有 2:1 的大比分）
- **每张地图的选手数据**（击杀 / 死亡 / 助攻 / Rating / ADR / KAST / 爆头率 / 首杀 …）
- **逐回合流水**（每回合谁赢、比分怎么走、击杀事件）
- 赛事信息（奖金、地点、等级、参赛队伍、赛程树）
- 队伍 / 选手资料

这些数据网页上都渲染了，只是没公开文档。本项目把接口整理出来，方便写客户端、做数据看板、喂给 AI agent。

## 快速开始

```bash
# 比赛列表（1 = 进行中，2 = 已结束，0 = 未开始）
curl -s 'https://esports-data.5eplaycdn.com/v1/api/csgo/matches?page=1&limit=20&game_status=2' \
  | python -m json.tool | head -60
```

```bash
# 某场比赛的完整数据（每图比分 + 选手数据）
curl -s 'https://esports-data.5eplaycdn.com/v1/api/csgo/matches/csgo_mc_2399921/data' \
  | python -m json.tool | head -100
```

所有接口返回统一信封：

```json
{ "success": true, "errcode": 0, "message": "", "data": { ... } }
```

失败时 `success:false`，`message` 里通常有中文错误（如 `参数错误`、`404 page not found`）。

## 三个域名

| 域名 | 用途 |
| --- | --- |
| `https://esports-data.5eplaycdn.com` | 主要数据接口（`/v1/api/csgo/...`） |
| `https://app.5eplay.com` | 补充接口（`/api/score/...`，整场选手汇总） |
| `https://oss.5eplay.com` | 静态资源：队伍 / 赛事 / 地图 / 选手头像 |

> 从中国大陆以外的网络访问时，`esports-data.5eplaycdn.com` 可能需要代理才能连通；`app.5eplay.com` 与 `oss.5eplay.com` 通常直连可达。实测在智能手表（Android 8.1）上三个域名均直连 200。

## 文档

| 文件 | 内容 |
| --- | --- |
| [docs/endpoints.md](docs/endpoints.md) | 全部已知接口，含参数、curl 示例、真实返回片段 |
| [docs/fields.md](docs/fields.md) | 字段速查表：比赛 / 地图 / 选手 / 赛事 / 队伍 |
| [docs/reverse-engineering.md](docs/reverse-engineering.md) | 怎么找到这些接口的（方法论，方便你继续挖） |
| [docs/known-issues.md](docs/known-issues.md) | 已知死路、未解之谜、待补参数 |

## 示例脚本

```bash
python tools/probe.py matches --status 1          # 列出进行中的比赛
python tools/probe.py detail csgo_mc_2399921      # 拉一场比赛的完整数据
python tools/probe.py rounds csgo_mc_2399921      # 逐回合流水
```

需要代理时：

```bash
python tools/probe.py --proxy socks5h://127.0.0.1:10808 matches --status 2
```

## 免责声明

- 这是**非官方**文档，接口随时可能变，不做任何稳定性保证。
- 所有数据版权归 5E 对战平台 / 相关赛事方所有，本项目只记录公开可访问的接口形态。
- 请**控制请求频率**，不要做压力测试或大规模爬取。建议单 IP 不低于 1 秒/请求。
- 不要用于商业用途或二次分发原始数据。
- 本项目不包含 5E 的前端代码，只包含我们自己写的文档与脚本。

## License

文档与脚本采用 [MIT](LICENSE)。接口与数据本身不属于本项目。
