# 贡献

欢迎补全 [known-issues.md](docs/known-issues.md) 里的任何一项。

## 提 PR 前

1. **每个结论都要有可复现的命令**
   ```bash
   curl -s 'https://esports-data.5eplaycdn.com/v1/api/csgo/...' | python -m json.tool | head -40
   ```
   把真实返回（截断到 200 字内）贴进文档。

2. **区分「实测」和「推测」**
   - 实测：有 curl + 返回 → 正常写
   - 推测：字段名看起来像/从 chunk 里读到但没验证 → 标注 `> 未验证：…`

3. **清理敏感信息**
   抓包结果里如果带了 cookie、token、手机号，删掉。ID、时间戳、比分都保留（这些是公开数据）。

4. **不要把 5E 的前端代码提交进来**
   `docs/reverse-engineering.md` 里可以引用**几行**路径字符串作为证据，不要贴整段混淆代码。

5. **控制请求频率**
   探测时用 `--limit 1` 起步，不要写循环猛刷。

## 补全某一项时

- 在 `docs/endpoints.md` 对应章节追加接口
- 在 `docs/fields.md` 追加字段
- 把 `docs/known-issues.md` 里对应条目删掉或改成「已解决（PR #n）」

## 代码风格

- `tools/probe.py` 只用标准库，不要引入 `requests` / `httpx`
- 命令行输出默认人要能读，`--json` 给机器
- 错误信息要能指导下一步（比如提示「需要代理吗」）

## 分工建议

如果你只想补一小块，按这个顺序最容易出成果：

| 优先级 | 任务 | 难度 |
| --- | --- | --- |
| P0 | 找出 `/v1/api/csgo/tournaments` 的正确参数 | 中 |
| P0 | 找出 `team/matches_v1` 的 status 枚举 | 中 |
| P1 | 定位世界排名接口 | 中 |
| P1 | 完整 ban/pick 序列在哪 | 中 |
| P2 | 加时赛数据样例 | 容易（找到一场加时比赛即可） |
| P2 | `/data` 增量参数 | 难 |

起点是 `docs/reverse-engineering.md` —— 那套方法可以原样套用。
