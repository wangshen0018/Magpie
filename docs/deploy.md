# 部署与排障

## 一、环境准备

### 1. root + busybox

手机已 root（Magisk / KernelSU 都行），并且有 busybox。检查：

```sh
busybox | head -1
busybox httpd --help
```

如果 `httpd` 不在列表里，说明这个 busybox 没编进 httpd，换一个带完整功能的版本。

### 2. aria2 开 RPC

`aria2.conf` 里至少要有：

```
enable-rpc=true
rpc-listen-all=true
rpc-allow-origin-all=true
rpc-secret=你自己设的密钥
```

`add.cgi` 会自己去找配置文件（依次试 `/data/adb/srv/aria2.conf`、`/data/adb/aria2/aria2.conf`、`/data/adb/modules/aria2/aria2.conf`、`/sdcard/aria2/aria2.conf`、`~/.aria2/aria2.conf`），端口从 `rpc-listen-port` 读，没写就用 6800。配置文件在别处时，启动 httpd 前设个环境变量：

```sh
export ARIA2_CONF=/你的路径/aria2.conf
```

**不需要**把 rpc-secret 写进网页。

## 二、部署

```sh
sh scripts/deploy.sh /data/adb/srv/magnet
```

脚本会把 `src/` 和 `static/httpd.conf` 一起复制过去，最后自检一遍文件是否齐全，缺文件会直接报错。

## 三、启动

```sh
sh scripts/start-service.sh 8080 /data/adb/srv/magnet
```

参数：第一个是端口（默认 8080），第二个是部署目录（默认 `/data/adb/srv/magnet`）。

脚本会自己找 busybox（PATH → Magisk → KernelSU → `/system/xbin` → `/system/bin`），检查配置文件在不在，再启动。

手动启动等价写法：

```sh
busybox httpd -p 8080 -h /data/adb/srv/magnet/www -c /data/adb/srv/magnet/www/httpd.conf
```

> 不要加 `-t 60`。busybox httpd 没有超时选项，带了会 `invalid option -- t` 直接启动失败。

停掉：

```sh
pkill -f 'httpd -p 8080'
```

### 开机自启（可选）

在 `/data/adb/service.d/` 下放个 `magnet.sh`（路径换成你仓库的实际位置）：

```sh
#!/system/bin/sh
sleep 30
sh /data/local/magnet/scripts/start-service.sh 8080 /data/adb/srv/magnet
```

## 四、塞进 AriaNg（可选）

AriaNg 的 `index.html` 里 `</body>` 前加一行：

```html
<a href="javascript:void(0)" onclick="window.open('http://'+location.hostname+':8080/','_blank')" style="position:fixed;right:20px;bottom:20px;background:#007bff;color:#fff;padding:8px 12px;border-radius:4px;text-decoration:none;z-index:9999">搜索</a>
```

## 五、代理开关（可选，救被墙的源站）

apibay 从国内家庭网络经常直连不通（实测 20~35 秒超时）。页面右上角有个"代理"开关，点一下在 K40 后台拉起 sing-box，搜索请求自动走它；再点关掉，闲置 600 秒也会自动关。

### 前置：装 sing-box

```sh
# 下载 android/arm64 构建（Linux glibc 构建在安卓上跑不了）
# 官方校验值务必核对，第三方镜像下载的二进制不可盲信
sh scripts/proxy-setup.sh    # 建配置目录，默认生成 direct 透传
```

`proxy-setup.sh` 会把 sing-box 二进制放到 `/data/adb/srv/bin/sing-box`（需先自行下载放进去），配置放 `/data/adb/srv/magpie-proxy/`（权限 700，**在 web 根之外**，否则 config.json 里的节点密码会被 httpd 当静态文件下载走）。

### 接真实节点

默认配置是 direct 透传——**开关是空转的**：只多绕一跳、不解决封锁，实测 YTS 直连 1~2 秒、经 direct 透传反而 12.8 秒。所以页面上开着但没节点时会显示"代理:开(透传)"提醒你。

要真正翻墙，把 `/data/adb/srv/magpie-proxy/config.json` 换成含真实节点的配置（保留 `inbounds` 里那个 `127.0.0.1:10808` 的 mixed 端口，`outbounds` 第一个填节点），然后：

```sh
/data/adb/srv/bin/sing-box check -c /data/adb/srv/magpie-proxy/config.json
```

check 通过再在页面点开关。check 不通过点开关会直接报 `config invalid`，不会拉起半死进程。

sing-box 合法出站类型名：`shadowsocks` / `vmess` / `trojan` / `vless` / `hysteria2` / `wireguard` / `tuic` / `urltest`（多节点自动选优）。注意 `proxy` 不是合法类型名，写了 check 会报 unknown outbound type。

### 只有这些源走代理

- **走**：`search.cgi`（apibay）、`yts.cgi`（YTS）、`status.cgi`（探测要跟着走，否则状态点会误报红）
- **不走**：`btsow.cgi`（实测国内直连 1~2 秒且从未失败，绕境外只会更慢）、`add.cgi`（连的是本机 aria2 RPC，走代理直接坏）

### 闲置自动关

`/data/adb/srv/magpie-proxy/idle` 里的数字是秒数（默认 600）。搜索请求会 touch `lastuse` 续命，停止搜索 600 秒后 watchdog 关掉 sing-box。改这个文件即可调整。

### 免费节点订阅能不能用

实测过 v2rayfree.org 每日更新（2026-10-29 那批，445 个节点）：**能用，但可用率很低，且高度集中在个别簇**。复现验证：`shadowsocks aes-256-gcm` 那几个（同密码簇，202.50.253.x:19999）确实把 apibay 从"直连 000 超时"救成"经代理 200 + 100 条 hash"。但绝大多数节点是死的。结论：适合当备胎应急，不适合当稳定依赖，每天换订阅、可用节点说没就没。

### 每日自动换节点（凌晨 3 点档）

设备里装了自动轮换，逻辑全在 `/data/adb/srv/magpie-proxy/node-update.sh`：

- 触发：`node-scheduler.sh` 每小时醒一次调它；脚本自己判断只在 **03:00–03:59** 干实事，当天干过（`update.flag`）就退出，所以实际每天一轮。
- 流程：拉当天订阅（URL 规律 `uploads/<年>/<月不补零>/<年月日紧凑>.json`，两种月份形态都试）→ 只提取 shadowsocks 节点（限 4 种标准 method）→ `nc -z` 批量 TCP 探活 → 可达的前 8 台组成 urltest 组 → **临时实例（10809 端口）发真实请求验证 gstatic 通了才换** → 原子替换 `config.json`；若代理正开着，自动用新配置重启实例。
- 失败保命：订阅拉不到/解析 0 台/全不可达/新配置 `check` 不过/验证不通过——任何一步失败**原配置原状态不动**，日志写 `update.log`。
- 开机自启：`/data/adb/service.d/magpie-node.sh`（独立新文件，没动 srv.sh）。
- 手动强制跑一轮：`su -c 'sh /data/adb/srv/magpie-proxy/node-update.sh --force'`。

实测两个坑（脚本已防）：①订阅 URL 写错也返回 **HTTP 200 + HTML 提示页**，必须校验内容（`{` 开头且含 `outbounds`），不能信状态码；②bash 风格 `echo >/dev/tcp/...` 探测在 mksh 里因 stderr 继承和 stdin 问题会全军覆没误判"0 可达"，改用 `busybox nc -z` + `</dev/null`。urltest 组自带 10 分钟选优，8 台里死几台不用等夜里。

## 六、出问题了

### 页面打不开

```sh
ps | grep httpd                      # 进程在不在
netstat -tln | grep 8080             # 端口有没有占上
ls -l /data/adb/srv/magnet/www/      # 页面与 CGI 在不在
ls -l /data/adb/srv/magnet/lib/      # 公共库在不在（缺了所有推送/进度都会报错）
```

文件权限掉了就重跑一次 `deploy.sh`。

### 搜不到东西

先在手机命令行直接测接口，绕开浏览器：

```sh
curl "http://127.0.0.1:8080/cgi-bin/search.cgi?q=inception"
curl -X POST -H "Content-Type: text/plain" --data "流浪地球" "http://127.0.0.1:8080/cgi-bin/btsow.cgi"
```

- 返回 `[]` 或 `{"code":200,"data":[]}` → 是源站或网络问题，接着测源站：
  ```sh
  curl -I https://apibay.org/
  curl -I https://btsow.live/
  ```
- 返回 404 → `httpd.conf` 没生效或 CGI 没有执行权限，检查 `www/httpd.conf` 是否存在、`cgi-bin/*.cgi` 是否 755。
- 返回 `{"error":"lib/aria2.sh not found, redeploy needed"}` → 只复制了 www 下的文件，`lib/aria2.sh` 没跟上。重跑一次 `deploy.sh` 即可。

### 状态条一直是红的

对应 `status.cgi` 的探测结果。先直接请求看返回：

```sh
curl "http://127.0.0.1:8080/cgi-bin/status.cgi"
```

`code` 是 `timeout` 表示 5 秒内没连上，页面会把圆点显示成灰色（未知），不是红点；红点只在源站明确返回错误码时出现。这个只是显示，不影响实际搜索。

apibay 现在经常 28 秒以上不返回，所以 TPB 那个点长期是灰的属于正常现象，不是故障。

### 点「下载」没反应

```sh
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"aria2.getVersion","params":[]}' http://127.0.0.1:6800/jsonrpc
```

- `Unauthorized` → aria2 配了 `rpc-secret`，但 `add.cgi` 没读到——检查配置文件路径，或设 `ARIA2_CONF`。
- 完全没返回 → aria2 没在跑，或端口不是 6800。

### 搜中文没结果

btsow 支持中文，apibay 中文基本搜不出来，属于正常现象。

### TPB 源特别慢，状态条老变灰

K40 实测（2026-10-29）：apibay 走 Cloudflare，成功返回也要 **2.7~22.5 秒**，而且 5 次里有 2 次几十秒不响应；btsow 稳定 1~1.3 秒。所以：

- 后端 `search.cgi` 超时给到 28 秒，前端 `srcTPB` 给 30 秒，慢是正常的，不要往回收。
- 页面已改成渐进渲染：BTSOW 结果先出来，TPB 回来再补进去，不用干等。
- 状态条 TPB 圆点变灰（`timeout`）不代表坏了，是这个源本来就飘。只有明确返回非 200 才标红。

真嫌慢可以打开第五节的代理开关（走 sing-box），或者直接只用 BTSOW 标签页。

### apibay 搜不到任何东西（连英文都是空）

先确认 `search.cgi` 里**没有** `cat=0`。apibay 现在把 `cat=0` 当成一个真实分类，带上它实测稳定返回一条 `No results returned` 占位（239 字节），前端过滤后就是空数组——看起来像"网络不通"，其实是参数问题：

```sh
# 有结果（不带 cat）
curl -4 -s "https://apibay.org/q.php?q=inception" | head -c 200
# 稳定空结果（带 cat=0）
curl -4 -s "https://apibay.org/q.php?q=inception&cat=0" | head -c 200
```

### 启动报 `busybox: invalid option -- t`

busybox httpd 没有超时选项（v1.36.1 只认 `-i -f -v -p -u -r -h -c -e -d`）。启动命令里不要写 `-t 60`，`start-service.sh` 已去掉。CGI 耗时由脚本内部 `curl --max-time` 控制。

### 源站打不开（DNS 污染 / 反爬）

手机端可换网络环境解决（换 DNS），或用第五节的代理开关走 sing-box。apibay 这类被墙的站经代理已实测可通。

## 七、注意

- 这个页面**没有任何登录和权限校验**，同一局域网的人都能打开、都能往你的 aria2 里塞任务。别把端口映射到公网。
- 只在自己家里用。
