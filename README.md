# Magpie

这是用白嫖的token为我一台屏幕损坏的红米 K40做的磁力搜索工具。手机 root 后跑 alist + aria2，在家作为轻nas和软路由使用。为了方便使用主力手机添加Aria离线下载，这个工具设计为聚合能在国内直连的磁力站点，局域网里用浏览器打开搜资源，点一下就把磁力推给 aria2 下载。

自用工具，未来计划添加更多源网站，同时尝试与v2ray联动，使用时自动挂代理，闲置一段时间后自动关代理。

## 能干什么

- 目前可以搜索三个站：**btsow**（中文资源多）、**apibay**（英文资源，带做种数）、**YTS**（英文电影，画质分版本）
- 页面顶部三个小圆点，显示各站当前连不连得上，30 秒自动刷新
- 结果里「下载」直接进 aria2，「复制」拿磁力链接
- **搜索历史**：点搜索框弹出最近 10 个关键词，点一下直接搜，可一键清空
- **下载进度**：屏幕底部一条常驻细栏，显示任务数、总进度、当前速度；点一下展开看每个任务的进度条。没有任务时自动隐藏
- 手机浏览器适配，也能塞进 AriaNg 当浮动按钮

## 需要什么

- 一台能 root 的安卓手机（root 是为了跑 httpd 和 aria2），或任意 Linux 小机器
- busybox，要带 httpd 和 CGI
- aria2 已开启 RPC
- 设备网络能访问 `btsow.live`、`apibay.org`、`yts.gg`

## 部署

```sh
sh scripts/deploy.sh /data/adb/srv/magnet       # 复制文件到目标目录
sh scripts/start-service.sh 8080 /data/adb/srv/magnet   # 启动
```

手机浏览器打开 `http://运行的设备IP:8080/` 就能用。

部署细节、aria2 配置、出问题怎么查，见 [docs/deploy.md](docs/deploy.md)。

## 目录

```
src/index.html          搜索页面（单文件，样式脚本都在这）
src/cgi-bin/search.cgi  apibay 搜索转发
src/cgi-bin/btsow.cgi   btsow 搜索转发
src/cgi-bin/yts.cgi     YTS 搜索转发（英文电影，带域名回退）
src/cgi-bin/add.cgi     推磁力给本机 aria2（rpc-secret 在服务端读，不进页面）
src/cgi-bin/list.cgi    查 aria2 当前下载情况（底部进度条用）
src/cgi-bin/status.cgi  探测三个站通不通（并行，约 6 秒出结果）
src/lib/aria2.sh        aria2 配置读取与 RPC 调用的公共库（部署到 www 之外）
scripts/deploy.sh       部署
scripts/start-service.sh 启动
static/httpd.conf       busybox httpd 配置（只有一行：*.cgi 用 sh 执行）
docs/deploy.md          部署与排障
```

部署后的目录结构：

```
/data/adb/srv/magnet/
  httpd.conf            开机自启读这份
  lib/aria2.sh          公共库，在 www 外面，浏览器访问不到
  www/                  这是 httpd 的根目录
    index.html
    httpd.conf          手动启动读这份
    cgi-bin/*.cgi
```

## 接口（给自己备忘）

| 地址 | 方法 | 入参 | 返回 |
|---|---|---|---|
| `/cgi-bin/search.cgi` | GET | `q=关键词`（URL 编码） | apibay 原始 JSON 数组 |
| `/cgi-bin/btsow.cgi` | POST | 正文为 UTF-8 原文关键词 | btsow 原始 JSON |
| `/cgi-bin/yts.cgi` | GET | `q=关键词`（URL 编码） | YTS 原始 JSON（`data.movies[].torrents[]`） |
| `/cgi-bin/add.cgi` | GET | `h=info_hash`（32 或 40 位十六进制） | aria2 的 JSONRPC 响应 |
| `/cgi-bin/list.cgi` | GET | 无 | `{"active":{...},"waiting":{...},"stopped":{...}}`，三个字段都是 aria2 原始响应 |
| `/cgi-bin/status.cgi` | GET | 无 | `{"btsow":{"ok":true,"code":"200"},"tpb":{...},"yts":{...},"t":时间戳}` |

## 说明

- 代码是 AI 辅助写的，我不懂编程，只保证在自己手机上跑得动。
- 只在局域网里用，没做登录和权限，别往公网暴露。
- 下载什么内容自己负责，遵守当地法律。

MIT License，见 [LICENSE](LICENSE)。
