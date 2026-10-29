# Magpie

家里一台屏幕摔坏的旧手机（红米 K40）改的磁力搜索页。手机 root 后跑 busybox httpd + aria2，局域网里用浏览器打开搜资源，点一下就把磁力推给 aria2 下载。屏幕坏了不影响——只用它的 CPU 和网。

自用工具，没有别的目标，也不打算做成什么项目。

## 能干什么

- 同时搜两个站：**btsow**（中文资源多）、**apibay**（英文资源，带做种数）
- 页面顶部两个小圆点，显示两个站当前连不连得上，30 秒自动刷新
- 结果里「下载」直接进 aria2，「复制」拿磁力链接
- 手机浏览器适配，也能塞进 AriaNg 当浮动按钮

## 需要什么

- 一台能 root 的安卓手机（root 是为了跑 httpd 和 aria2），或任意 Linux 小机器
- busybox，要带 httpd 和 CGI
- aria2 已开启 RPC
- 设备能访问 `btsow.live` 和 `apibay.org`

## 部署

```sh
sh scripts/deploy.sh /data/adb/srv/magnet       # 复制文件到目标目录
sh scripts/start-service.sh 8080 /data/adb/srv/magnet   # 启动
```

手机浏览器打开 `http://手机IP:8080/` 就能用。

部署细节、aria2 配置、出问题怎么查，见 [docs/deploy.md](docs/deploy.md)。

## 目录

```
src/index.html          搜索页面（单文件，样式脚本都在这）
src/cgi-bin/search.cgi  apibay 搜索转发
src/cgi-bin/btsow.cgi   btsow 搜索转发
src/cgi-bin/add.cgi     推磁力给本机 aria2（rpc-secret 在服务端读，不进页面）
src/cgi-bin/status.cgi  探测两个站通不通（并行，约 8 秒出结果）
scripts/deploy.sh       部署
scripts/start-service.sh 启动
static/httpd.conf       busybox httpd 配置（只有一行：*.cgi 用 sh 执行）
docs/deploy.md          部署与排障
```

## 接口（给自己备忘）

| 地址 | 方法 | 入参 | 返回 |
|---|---|---|---|
| `/cgi-bin/search.cgi` | GET | `q=关键词`（URL 编码） | apibay 原始 JSON 数组 |
| `/cgi-bin/btsow.cgi` | POST | 正文为 UTF-8 原文关键词 | btsow 原始 JSON |
| `/cgi-bin/add.cgi` | GET | `h=info_hash`（32 或 40 位十六进制） | aria2 的 JSONRPC 响应 |
| `/cgi-bin/status.cgi` | GET | 无 | `{"btsow":{"ok":true,"code":"200"},"tpb":{...},"t":时间戳}` |

## 说明

- 代码是 AI 辅助写的，我不懂编程，只保证在自己手机上跑得动。
- 只在局域网里用，没做登录和权限，别往公网暴露。
- 下载什么内容自己负责，遵守当地法律。

MIT License，见 [LICENSE](LICENSE)。
