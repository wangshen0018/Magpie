# 更新日志

## 2026-10-29 新增第三源：YTS

在 K40 上实测了 60+ 个"国内可直连"的磁力站候选，结论：

- 唯一值得接入的是 **YTS**（`yts.gg/api/v2/list_movies.json`，官方 JSON API，实测 1~2 秒返回，含 hash/seeds/peers/size_bytes/quality）。它只有英文电影，与 apibay 内容重叠，价值主要在冗余——而实测发现 **apibay 的可达性随时段剧烈波动**（同一会话内早先 12 秒返回 100 条、晚间直连 35 秒超时），YTS 正好补位。
- 其余候选全军覆没，且失败原因不是 DNS 污染：curl 都能解析到真实公网 IP，是 IP/SNI 层被阻断，换 doh/分流救不回来，别在这上面花时间。追镜像名单是跑步机（域名更换以周计，博客清单必然过期）。
- 假阳性提醒：`mztf`/`magent`/`gp5` 返回 200 实为域名停放页；`91sou`/`jizhi` 返回 200 是同名无关站；`pirateproxy` 返回 200 是广告 HTML。只认 HTTP 200 会写出三个死源。

代码改动：

- 新增 `src/cgi-bin/yts.cgi`：转发 YTS 搜索。官方已宣布 API base 迁往 `movies-api.accel.li`（sunset 2026-04-10），`yts.gg` 目前仍在服务，所以脚本内置**域名回退**（依次尝试，校验返回是闭合且 `"status":"ok"` 的完整 JSON 才采用），避免单域名失效变死源。
- 前端加 `srcYTS()`：一部电影展开多个清晰度版本；**注意 `size` 字段是 `"487.87 MB"` 字符串，必须取 `size_bytes`**。页面加 YTS 标签与绿色徽标。
- `status.cgi` 并行探测扩到三个源，返回体加 `yts` 字段；顺带清掉遗留的 `cat=0`（与 search.cgi 的修复保持一致）。
- `sortAll()` 改为按"有无做种数"分组（TPB/YTS 有做种数排前，BTSOW 按更新时间排后），不再按源名硬编码。
- `deploy.sh` 自检清单加入 `yts.cgi`。
- README / CHANGELOG 同步为三源。

## 2026-10-29 K40 实机部署验证

在红米 K40（root + busybox 1.36.1 + aria2 RPC）上部署跑通，过程中修掉 4 个问题：

- **`start-service.sh` 启动即失败**：busybox httpd 没有 `-t` 选项，带上会 `invalid option -- t` 直接退出码 1。去掉该参数，`httpd.conf` 与 `docs/deploy.md` 里的相应说明一并订正。
- **`search.cgi` 恒定搜不到东西**：apibay 已把 `cat=0` 当成一个真实分类，实测 `q=inception&cat=0` 稳定返回 `No results returned`（239 字节占位）；去掉 `cat` 参数才走全站搜索（实测 28582 字节、100 条结果）。
- **apibay 超时给得太紧**：实测成功请求耗时 2.7~22.5 秒抖动，5 次里 2 次几十秒不返回。后端 `--max-time` 从 12 秒放到 28 秒，前端 `srcTPB` 从 14 秒放到 30 秒。
- **状态条误报红点**：curl 连不上时 `%{http_code}` 输出 `000`，前端只把 `timeout` 当"未知"，`000` 会落到非 200 分支标红；实测 apibay 慢的时候必现。`status.cgi` 现在把 `000` 归一化成 `timeout` 显示灰点。
- **前端两处加固**：`doSearch` 改为渐进渲染，两个源谁先回来先显示（btsow 实测 1.3 秒、apibay 常需 10 秒以上，原 `Promise.all` 齐了才出结果，白等）；源站返回的 hash 一律先校验 32/40 位十六进制再插入 `onclick`，避免畸形值拼出脚本。
- **`deploy.sh` 同步维护根目录 `httpd.conf`**：开机自启读 `$TARGET/httpd.conf`，`start-service.sh` 读 `$TARGET/www/httpd.conf`，原来只写后者，改一份容易两边不一致。

## 2026-10-29 整理

修掉的问题（全部在本机模拟部署后实测过）：

**部署链路**

- `deploy.sh` 没有把 `httpd.conf` 复制到部署目录，照着文档启动会读不到配置；现在一起复制，并在部署后自检文件是否齐全，缺文件直接报错
- `deploy.sh` 原来用相对路径 `cp src/...`，只能在仓库根目录执行；改用脚本自身位置推算仓库路径
- `httpd.conf` 里混了 `Timeout` / `MaxClients` / `DirectoryIndex` 等 Apache 写法，busybox httpd 不认；只保留 `*.cgi` 映射
- `start-service.sh` 每次启动都重写一遍配置（会覆盖部署好的文件），且 busybox 路径写死 `/data/adb/magisk/busybox`；改为自动查找 busybox、校验配置存在后直接启动
- 删除 `test-deploy.sh`（其中硬编码了 `/var/minis/workspace/...` 绝对路径，检查逻辑已并入 `deploy.sh`）

**接口行为**

- `status.cgi` 原为串行探测、单个 1.5 秒超时：最坏 3 秒返回，而前端 2.5 秒就放弃，状态条必然全红。改为并行探测、单个 8 秒，前端等 10 秒
- `add.cgi` 对 info_hash 不做任何校验；现在只接受 32/40 位十六进制
- `add.cgi` 未配 `rpc-secret` 时仍发送 `token:` 前缀，aria2 必然鉴权失败；现在无密钥时不带该参数
- `add.cgi` 把 aria2 配置路径与端口写死；改为读 `ARIA2_CONF` 环境变量并依次尝试常见路径、从 `rpc-listen-port` 读端口
- `add.cgi` 在 aria2 返回非 JSON 文本时原样透传，前端解析报错；现在统一返回 `{"error":...}`
- `search.cgi` 在 apibay 搜不到时，会把一条 `info_hash` 全 0 的 `No results returned` 占位记录当正常结果返回；现在直接过滤为空
- `search.cgi` / `btsow.cgi` 在 curl 超时时会把**半截 JSON** 原样输出，前端 `JSON.parse` 必报错；现在校验首尾是否闭合，不完整就降级为空结果
- `btsow.cgi` 收到纯空格时不判空，btsow 会返回整站最新列表；现在先 trim 再判空，并限制 200 字节
- 各 CGI 的 `curl` 路径写死 `/system/bin/curl`；改为先查 PATH 再退回该路径
- 去掉 CGI 的 `Access-Control-Allow-Origin: *`（同源用不到，留着等于对任意网页开放代理）

**前端**

- `srcTPB` 的超时（6 秒）短于后端（12 秒），后端还没返回前端就放弃了；改为 14 秒 / 17 秒，与后端超时对齐
- 做种数缺失时排序产生 `NaN`；改为 `(+x.seeders || 0)`
- 状态探测超时原来一律标红，网络抖动会误报源站故障；现在超时标灰（未知），只有源站明确返回非 200 才标红，失败后 10 秒重试
- 两个源都没结果时，提示改为区分"网络不通或源站不可用"，不再只说"没有结果"

**文档**

- `README.md` 重写：只说明这是什么、怎么部署、怎么用，去掉愿景、路线图、成功指标
- 删除 `ROADMAP.md`、`docs/ROADMAP.md`、`MAINTENANCE.md`、`CONTRIBUTING.md`、`SECURITY.md`、`AI-STATEMENT.md`、`docs/DEVELOPMENT.md`、`docs/SIMPLE_README.md`
- 删除 `.github/` 下的 Issue / PR 模板与 FUNDING 配置
- `docs/api.md`、`docs/troubleshooting.md` 合并进 `docs/deploy.md`
- `.gitignore` 精简，去掉与本项目无关的 Node / Python / IDE 条目

## 1.0.0 - 2026-10-29

初版：双源搜索（btsow + apibay）、源站状态显示、一键推送 aria2、移动端适配。
