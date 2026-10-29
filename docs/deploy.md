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
busybox httpd -p 8080 -h /data/adb/srv/magnet/www -c /data/adb/srv/magnet/www/httpd.conf -t 60
```

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

## 五、出问题了

### 页面打不开

```sh
ps | grep httpd                      # 进程在不在
netstat -tln | grep 8080             # 端口有没有占上
ls -l /data/adb/srv/magnet/www/      # 文件在不在
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

### 状态条一直是红的

对应 `status.cgi` 的探测结果。先直接请求看返回：

```sh
curl "http://127.0.0.1:8080/cgi-bin/status.cgi"
```

`code` 是 `timeout` 表示 8 秒内没连上，页面会把圆点显示成灰色（未知），不是红点；红点只在源站明确返回错误码时出现。这个只是显示，不影响实际搜索。

### 点「下载」没反应

```sh
curl -X POST -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"aria2.getVersion","params":[]}' http://127.0.0.1:6800/jsonrpc
```

- `Unauthorized` → aria2 配了 `rpc-secret`，但 `add.cgi` 没读到——检查配置文件路径，或设 `ARIA2_CONF`。
- 完全没返回 → aria2 没在跑，或端口不是 6800。

### 搜中文没结果

btsow 支持中文，apibay 中文基本搜不出来，属于正常现象。

### 源站打不开（DNS 污染 / 反爬）

手机端只能靠换网络环境解决（换 DNS、走代理）。本项目不做代理集成。

## 六、注意

- 这个页面**没有任何登录和权限校验**，同一局域网的人都能打开、都能往你的 aria2 里塞任务。别把端口映射到公网。
- 只在自己家里用。
