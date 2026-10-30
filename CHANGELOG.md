# 更新日志

## 2026-10-31 新增第四源：Nyaa（需代理）

有了可用代理之后重测此前全部连不通的站，60+ 个里挑出 4 个代理下可用的，最终接入 **Nyaa**。

- **Nyaa（`nyaa.si`）**：番剧/日影向，**唯一支持中文关键词的源**（实测搜「进击的巨人」75 条、标题中文完整；apibay 完全搜不出中文）。直连实测 12 秒超时必死，代理下 2.2~2.4 秒。
  - 无可用 JSON API（`/api/v1/search` 404），只能解析 HTML，故在 `nyaa.cgi` 里转成 JSON 再给前端。
  - **必须用临时文件接 curl 输出**：中文页面 133768 字节，用 `HTML=$(curl ...)` 捕获后内容会丢（`${#HTML}` 报 133768 却为空），`curl -o 文件` 解析正常。多字节大响应用 shell 变量接是坑。
  - `--compressed` 收益明显：109612 → 14474 字节，8 秒级降到 2.2 秒。
- 其余代理下可用但未接入（响应慢或需跳转多次，收益低）：TorrentKitty（8.9s）、SolidTorrents→bitsearch.eu（7.2s）、LimeTorrents→limetorrents.fun（7.2s）。
- 大量站仍不可用：1337x/katcr（403 反爬）、btdig（429 限流）、knaben（503）、magnetdl/pirateiro（超时）、eztv（403）。
- `status.cgi` 扩到四源；Nyaa 只探代理（直连必死，探了白占 5 秒预算），代理没开时如实标灰。
- `deploy.sh` 自检清单加 `nyaa.cgi`；README / deploy.md 同步四源。

实测（K40，代理开）：

```
status:  btsow/tpb/yts/nyaa 全部 ok:true
nyaa 中文「进击的巨人」: 200 / 2.2s / 75 条
nyaa 英文 matrix:        200 / 2.4s / 75 条
代理关: nyaa 状态 timeout（灰）、搜索返回空不报错
```

## 2026-10-30 新增搜索历史与下载进度

**搜索历史**（纯前端，存在浏览器 localStorage）

- 点搜索框弹出最近 10 个关键词，点一下直接搜；右侧「清空」一键清掉
- 重复的词自动提到最前，不重复堆积；空白词不入库
- 只存关键词不存结果——结果是几万个字符，撑不起 localStorage 的 5MB 配额
- 内容经 `esc()` 转义后插入，避免历史里的特殊字符破坏页面

**下载进度**（新增 `src/cgi-bin/list.cgi` + 页面底部常驻细栏）

- 底部显示「↓ 2 个任务 · 41% · 3.9 MB/s」，点一下展开看每个任务的进度条与速度
- 没有任务时自动隐藏；刚下完会显示「✓ 2 个任务已完成」5 秒后收起，失败则显示红色「!」
- 有任务时 3 秒轮询一次，空闲时 15 秒一次，别让手机一直醒着
- 展开状态记在 localStorage，下次打开保持

**配套改动**

- 抽了 `src/lib/aria2.sh`：curl 定位、aria2 配置读取、补 token 调 RPC 的逻辑从 `add.cgi` 挪进来，`add.cgi` 和 `list.cgi` 共用。原来这段有 25 行，复制两份迟早改漏一边
- 这个库故意部署到 `www` 之外（`$TARGET/lib/`）：httpd 的根目录是 www，放里面浏览器就能直接把源码下载走
- `deploy.sh` 增加 lib 复制与自检项（`list.cgi`、`lib/aria2.sh` 缺一个就报错）
- `add.cgi` 改用公共库后行为不变，四种入参的返回与原来一致

验证方式与结果（本地模拟 httpd + 假 aria2，可在 downloading/done/error/empty 四种状态间切换）：

| 项目 | 结果 |
|---|---|
| `list.cgi` 四种状态 | active/waiting/stopped 数量与 status 均正确，三次 RPC 都带上了 `token:` |
| `add.cgi` 回归 | 合法 hash 成功；非法、长度错、空各自返回对应错误 |
| 底栏文案 | 下载中「2 个任务 · 41%」+「3.9 MB/s」+ 图标 ↓；完成「2 个任务已完成」✓ 绿色；失败「1 个任务失败」! 红色；空闲 display:none |
| 遮挡检查 | 底栏高 42px，body 底部留白 70px，滚到底时最后一条底边 729.5px < 底栏顶边 766px，不遮挡 |
| 历史逻辑 | 8 项全通过：空历史不弹窗、去重置顶、上限 10 条、空白不入库、内容转义、点击回填、自动收起、清空生效 |

## 2026-10-30 二次复核（本地模拟环境回归）

在 Windows 上重建 busybox httpd + aria2 RPC 的模拟环境，把三个源逐个跑了一遍，修掉 5 处：

- **`yts.cgi` 空关键词会返回整站列表**：`q=%20`、`q=+`、`q=%09` 这类纯空白输入，YTS 会当成"无过滤"返回 `movie_count` 78129 的首页数据，页面就会显示一堆与关键词无关的条目。现在另取一份解码后的副本 trim 判空（原值不动，仍按 URL 编码拼进 `query_term`）。
- **`status.cgi` 超时给得过长**：三个探测各给 8 秒，而 apibay 现在经常 28 秒以上不返回，实测状态接口整体要 **9.3 秒**，前端只等 10 秒，几乎每次都贴边。单个超时收紧到 5 秒，实测总耗时降到 **6.0 秒**，前端的 10 秒有了余量。慢到 5 秒不答就当"未知"（灰点），与事实一致。
- **`sortAll()` 增加按 hash 去重**：同一部片子的同一磁力可能被两个源同时返回（或翻页重复），列表会出现两条完全一样的条目。现在统一转大写后去重。
- **搜索按钮恢复时机提前**：原来要等 `Promise.all` 三个源全部返回才解除禁用，apibay 慢的时候用户要干等 28 秒才能重新搜索。现在只要任一源出结果就解锁。
- **`addUri()` 加 15 秒超时**：aria2 没起或端口不通时，原来会一直卡在"加入中"，且失败无提示。

另修一处非代码问题：`.gitignore` 末尾那行中文注释在 Windows 上被转码成 `U+FFFD` 替换字符（原文已不可逆丢失），重写为正常中文。

实测记录（本机直连，非手机网络）：

| 项目 | 结果 |
|---|---|
| btsow 搜索 | 2.1~3.2 秒，30 条 |
| YTS 搜索 | 2.6~3.9 秒，8 部电影展开 20 条 |
| apibay 搜索 | **28 秒超时，返回 0 条**（三次直连 60 秒仍拿不完整响应） |
| status.cgi | 6.0 秒，三源并行 |
| add.cgi 推送 | aria2 收到 `token:...` + `magnet:?xt=urn:btih:...`，非法 hash 正确拒绝 |

**apibay 的可用性问题不是代码能解决的**，它现在经常整分钟不返回。TPB 这一源实际上处于"偶尔能用"的状态。

## 2026-10-30 每日自动换节点（凌晨 3 点档）

在 K40 上部署并完整实测了订阅自动轮换：

- `scripts/node-update.sh`：拉 v2rayfree 当天 sing-box 订阅 → 提取 shadowsocks 节点（限 4 种标准 method）→ 批量 TCP 探活 → 可达前 8 台组成 urltest → **临时实例（10809）真实请求 gstatic 验证** → 才原子替换 config.json；代理开着时换完自动重启实例。任何一步失败原配置不动，日志 `update.log`，mkdir 锁防并发，支持 `--force` 手动跑。
- 订阅拉取方式：网站**按日期命名文件且历史文件不再变动**，故用 `date` 现算 URL（`uploads/<年>/<月不补零>/<年月日紧凑>.json`，另备补零形态）直接下载；目录不可枚举（列目录 403）。
- 调度：`node-scheduler.sh` 每小时醒一次调用它，脚本自门控——凌晨 3 点起每小时试，直到拿到当天订阅；处理完写 `update.flag` 当天收工。**（初版是"只在 03:xx 干、失败也写 flag"，缺陷：网站发布时间未知，若 3 点还没发布当天就彻底不换了。现已改为未发布不写 flag、留给下一小时；实测模拟未发布场景 flag 保持不变。）**
- `scripts/service.d-magpie-node.sh`：开机自启，独立新文件不动 srv.sh。
- 实测（当天）：解析 10 台 ss、TCP 可达 9 台、挑 8 台、验证 204、换后 apibay 经新节点 200 + 100 条、代理关闭端口正常释放。

两个实测坑（已写进脚本）：订阅 URL 错误也返回 HTTP 200 + HTML 提示页，必须验内容不能信状态码；bash 风格 `/dev/tcp` 探测在 mksh 里因 stderr/stdin 继承全军覆没，改 busybox `nc -z` + `</dev/null`。调度没走 crond：设备唯一的 crond 是 GGAT_10007 模块自带的、crontab 目录在人家模块目录里，模块更新可能被清；改用 battguard 同款 nohup 循环（该模式已稳定跑 13 天）。

## 2026-10-30 代理开关（sing-box）

页面右上角加"代理"开关：点一下 K40 后台拉起 sing-box，搜索请求自动走它；再点关掉，闲置 600 秒看门狗自动关。动机是 apibay 从国内家庭网络经常直连不通。

- 新增 `src/cgi-bin/proxy.cgi`：开关只接受 `status|on|off|touch` 四个固定动作，其余拒绝；状态汇报前先和真实进程核对（state 说 on 但进程没了就就地校正）。
- 新增 `scripts/proxy-setup.sh`（建配置目录）、`scripts/proxy-lib.sh`（各搜索 CGI source 它，决定是否注入 `--proxy`）、`scripts/watchdog.sh`（闲置自动关）。
- 配置目录 `/data/adb/srv/magpie-proxy/`（700）在 **web 根之外**；实测三个探测 URL 全 404，`config.json` 里的节点密码不会被 httpd 当静态文件下载走。
- 只有 apibay / YTS / status 走代理。**btsow 故意不接**（直连 1~2 秒且从未失败，绕境外只会更慢）；**add.cgi 不接**（连本机 aria2 RPC，走代理直接坏）。

K40 实测踩到的坑（都修了）：

- **单次请求 15 秒**：早先版本探测进程存活靠遍历 `/proc/*/cmdline`，这台设备 920 个进程、每个 fork 一次 `tr`，一次 status 就 fork 上千次，前端点开关根本没反应。改成 `sb.pid` + 读 `/proc/<pid>/comm`（shell 内建，零 fork）后降到 **0.14 秒**，之前的"偶发空响应"也随之消失（真凶就是慢）。
- **`proxy.cgi` 误报 direct**：`grep '"type": "direct"'` 全文匹配，配置末尾那条备用 direct 出站被误命中，urltest 主配置显示成"透传"。改成只看 outbounds 数组第一个 `type`（默认出站），与 proxy-lib.sh 判据统一，四种配置来回切换实测一致。
- **direct 透传反而更慢**：没节点时开关是空转，实测 YTS 直连 1~2 秒、经 direct 透传 12.8 秒。页面因此显示"代理:开(透传)"，不做静默处理。
- `$PROXY_OPT` 使用处**不能加引号**：加引号时空值会留下一个空参数，curl 报 `option : blank argument`（实测过）。空值靠词分割自然消失才对。
- `dns.servers[].address` 不存在（sing-box 1.14 报 unknown field），且 `"type":"proxy"` 不是合法类型名。
- 后台进程必须 `< /dev/null`，否则继承 httpd 给 CGI 的 stdin 把响应卡住。
- 不记录、不 kill watchdog 的 PID：setsid 会 fork，`$!` 不是 watchdog 本体，那个号被回收后照它 kill 就是杀错无关进程。只靠 `state` 文件，watchdog 每 30 秒读一次、见 off 自退。

订阅验证：v2rayfree.org 每日更新（445 个节点）里**大部分是死的**，但 `shadowsocks aes-256-gcm` 那簇（202.50.253.x:19999）复现验证有效——apibay 从"直连 000 超时 20 秒"变成"经代理 200、3~4 秒、100 条结果"。结论：可当应急备胎，不适合当稳定依赖（每天换订阅、说没就没）。

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
