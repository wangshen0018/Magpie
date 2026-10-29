# 更新日志

## 2026-10-29 整理

修掉的问题（全部在本机模拟部署后实测过）：

**部署链路**

- `deploy.sh` 没有把 `httpd.conf` 复制到部署目录，照着文档启动会读不到配置；现在一起复制，并在部署后自检文件是否齐全，缺文件直接报错
- `deploy.sh` 原来用相对路径 `cp src/...`，只能在仓库根目录执行；改用脚本自身位置推算仓库路径
- `httpd.conf` 里混了 `Timeout` / `MaxClients` / `DirectoryIndex` 等 Apache 写法，busybox httpd 不认；只保留 `*.cgi` 映射，超时改由启动参数 `-t 60` 给
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
