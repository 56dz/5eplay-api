# 逆向方法

记录我们是怎么从一个普通网页挖出这些接口的。方便你继续补全，或者把这套方法用到别的站点上。

## 1. 锁定目标页面

```
https://event.5eplay.com/csgo/matches
```

这是 5E 的 CS2 赛事列表页。先确认它是**服务端渲染还是客户端渲染**：

```bash
curl -s 'https://event.5eplay.com/csgo/matches' | wc -c
```

返回的 HTML 很小（几 KB），说明数据是前端 JS 拉取的 —— 那就得从 JS bundle 里找接口。

## 2. 扒 JS chunk

页面用 Next.js / webpack 打包，chunk 文件名带 hash。最省事的办法是**打开开发者工具 → Network → JS**，把所有 chunk 存下来。

也可以从 HTML 里的 `<script src>` 和 webpack runtime 的 `__webpack_require__.u` 映射里推。

我们最终拿到 51 个 chunk，总共 4.3 MB，存在本地目录（**不随仓库分发**，见 `.gitignore`）。

## 3. 在 chunk 里搜接口

不用真的读懂压缩后的代码，**正则搜字符串字面量就够了**：

```python
import re, pathlib

pat = re.compile(r'(?:url|apiUrl|baseURL)\s*:\s*["\'`]([^"\'`]{3,200})')
for f in pathlib.Path('chunks').glob('*.js'):
    src = f.read_text('utf-8', errors='replace')
    for m in pat.finditer(src):
        print(f.name, m.group(1))
```

再配合搜业务关键词：`csgo`、`matches`、`tournament`、`rank`、`mfilter`、`/v1/api`、`5eplaycdn`。

我们的收获：

```js
// 3902.js —— 比赛列表
url: "/v1/api/csgo/matches".concat((0,m.eA)(l))   // l = {tt_ids, game_status, limit, page}

// 5428.js —— 比赛详情 / 回合流水 / 战队对比
url: "/v1/api/csgo/matches/".concat(a,"/data")
url: "/v1/api/csgo/match/".concat(t,"/event/log?update_version=0&limit=500")
url: "/v1/api/csgo/matches/".concat(t,"/analysis_v1")

// 177.js —— 赛事
url: "/v1/api/csgo/tournaments/".concat(id,"/stages")
url: "/v1/api/csgo/tournaments/".concat(id,"/introduction")
url: "/v1/api/csgo/focus/tournaments".concat(qs)

// 4351.js —— 队伍
url: "/v1/api/csgo/teams/".concat(...)
url: "/v1/api/csgo/team_players/batch?team_ids="

// 5428.js —— app.5eplay.com 的补充接口
url: "/api/score/match_score_tab?match_id=".concat(t,"&game_type=1")
url: "/api/score/match_score_list?match_id=".concat(t,"&tab=").concat(a,"&game_type=1&team_id=").concat(l)
```

## 4. 找 base URL

接口路径是相对的，得找它挂在哪。搜 `5eplaycdn`、`apiUrl`、`axios.create`：

```js
apiUrl: "https://app.5eplay.com"
baseURL: "https://esports-data.5eplaycdn.com"
```

三个域名分工明确（见 README）。

## 5. 找参数

压缩后的代码里，查询参数通常被一个序列化函数处理，比如 `.concat((0,m.eA)(l))` —— `eA` 是 querystring 序列化，`l` 才是真正的参数对象。往上翻调用处：

```js
l = { tt_ids: t, game_status: n, limit: 20, page: 1 }
```

如果翻不到，就**按常见命名穷举**：`page` / `limit` / `status` / `type` / `game_status` / `grade` / `tt_ids` / `team_id`。每试一次看 `success` 和 `data` 是否变化。

参数错的典型报错：

```
{"success":false,"errcode":400,"message":"parsing field \"status\": strconv.ParseInt: parsing \"upcoming\": invalid syntax","data":null}
```

这条报错信息量很大：它告诉我们后端是 **Go**（`strconv.ParseInt`），并且 `status` 是枚举整数，不是字符串。换 `status=1` 就通了。

## 6. 验证 ID 关系

三个 ID 前缀，从返回里推断：

| 前缀 | 含义 | 例 |
| --- | --- | --- |
| `csgo_mc_` | match | `csgo_mc_2399921` |
| `csgo_tt_` | tournament | `csgo_tt_8251` |
| `csgo_tm_` | team | `csgo_tm_7020` |
| `csgo_pl_` | player | `csgo_pl_18638` |

交叉引用：列表里拿 `mc_info.id` → 拉详情；详情里拿 `t1_info.id` → 拉队伍。

## 7. 反查数据字段的含义

字段名大部分自解释（`kill`、`death`、`adr`）。不确定的对照网页 DOM：

1. 网页上打开一场已结束的比赛
2. 开发者工具里看渲染出的数字
3. 去 JSON 里搜同一个数字，就能确定是哪个字段

比如页面上 `13` 这个比分，在 JSON 里同时出现在 `quick_score`、`all_score`、`sh_score + fh_score` 的和 —— 有多个来源时优先用 `quick_score`（语义最直接）。

## 8. 判断"死路"

如果一个接口在所有参数组合下都返回同一结果，就记进 [known-issues.md](known-issues.md)，别反复试。

我们踩过的：

- 路径猜错 → `404 page not found`（Go 的默认 404 body，也印证了后端是 Go）
- 参数名猜错 → `参数错误`（业务层校验失败）
- 参数类型猜错 → `strconv.ParseInt` 报错
- 接口存在但不给数据 → `success:true, data:{items:[]}`

## 9. 工具

写了个 `tools/probe.py` 封装了上述流程，改 URL 就能复用到别的站点：

```bash
python tools/probe.py matches --status 1
python tools/probe.py detail csgo_mc_2399921 --raw
```

## 10. 合规提醒

- 只读公开接口，不做写操作
- 控制频率，建议 ≥1s/请求
- 不改 URL 参数去尝试越权访问
- 不确定的接口先小 `limit` 试探，别一上来 `limit=1000`
