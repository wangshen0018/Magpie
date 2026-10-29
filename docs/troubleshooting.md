# 故障排除指南

## 常见问题

### 1. 搜索页面无法访问

**问题：** 打开 `http://localhost:8080/` 显示连接错误

**排查步骤：**
1. 检查服务是否启动
   ```bash
   ps | grep httpd
   ```

2. 检查端口是否占用
   ```bash
   netstat -tlnp | grep 8080
   ```

3. 检查文件权限
   ```bash
   ls -la /data/adb/srv/magnet/www/
   chmod +x /data/adb/srv/magnet/www/cgi-bin/*.cgi
   ```

### 2. 搜索结果为空

**问题：** 搜索后没有结果，但页面显示"搜索中..."

**排查步骤：**
1. 手动测试搜索接口
   ```bash
   curl "http://localhost:8080/cgi-bin/search.cgi?q=test"
   curl -X POST -H "Content-Type: text/plain" --data "test" "http://localhost:8080/cgi-bin/btsow.cgi"
   ```

2. 检查网络连通性
   ```bash
   curl -I https://btsow.live/
   curl -I https://apibay.org/
   ```

3. 查看服务日志
   ```bash
   # busybox httpd 通常没有详细日志
   # 可以在 CGI 中添加调试输出
   ```

### 3. 状态条显示不可用

**问题：** 状态条一直显示红色

**排查步骤：**
1. 测试状态接口
   ```bash
   curl "http://localhost:8080/cgi-bin/status.cgi"
   ```

2. 检查探测词是否被反爬
   - 尝试更换关键词（如 "movie"）
   - 检查 User-Agent 是否正确

3. 手动测试源站点
   ```bash
   curl -I https://btsow.live/bts/data/api/search
   curl -I https://apibay.org/q.php?q=test
   ```

### 4. 下载失败

**问题：** 点击下载后任务没有进入 aria2

**排查步骤：**
1. 测试下载接口
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"uri":"magnet:?xt=urn:btih:dummyhash"}' \
     "http://localhost:8080/cgi-bin/add.cgi"
   ```

2. 检查 aria2 状态
   ```bash
   ps | grep aria2c
   curl "http://localhost:6800/jsonrpc" -d '{"jsonrpc":"2.0","method":"system.listMethods","id":1}'
   ```

3. 检查 RPC 密钥
   ```bash
   cat /data/adb/srv/aria2.conf | grep rpc-secret
   ```

## 性能问题

### 1. 搜索响应慢

**问题：** 搜索需要很长时间

**可能原因：**
- 源站点响应慢
- 网络延迟高
- CGI 脚本执行慢

**解决方案：**
1. 调整超时时间
   ```bash
   # 在 CGI 中修改 --max-time 参数
   search.cgi: 12秒 -> 8秒
   btsow.cgi: 8秒 -> 6秒
   ```

2. 使用更快的探测词
   ```bash
   # status.cgi 中使用 "inception" 而不是 "test"
   ```

### 2. 页面卡死

**问题：** 搜索后页面无响应

**可能原因：**
- busybox httpd 单进程阻塞
- 浏览器标签页被污染

**解决方案：**
1. 重启服务
   ```bash
   pkill httpd
   busybox httpd -p 8080 -h /data/adb/srv/magnet/www
   ```

2. 使用新标签页
   - 关闭当前标签页
   - 重新打开搜索页面

## 网络问题

### 1. DNS 污染

**问题：** 无法访问 btsow.live 或 apibay.org

**排查步骤：**
1. 检查 DNS 解析
   ```bash
   nslookup btsow.live
   nslookup apibay.org
   ```

2. 使用 DoH 解析
   ```bash
   curl -H "Host: btsow.live" 104.244.43.248
   ```

3. 使用代理或 VPN

### 2. 反爬检测

**问题：** 源站点返回 403 或 404

**解决方案：**
1. 更换 User-Agent
   ```bash
   # 在 CGI 中修改 UA 字符串
   UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
   ```

2. 使用代理 IP
   ```bash
   # 在 curl 中添加 -x 代理地址
   curl -x http://proxy:port ...
   ```

## 部署问题

### 1. busybox httpd 不支持 CGI

**问题：** CGI 脚本无法执行

**解决方案：**
1. 检查 busybox 版本
   ```bash
   busybox --help | grep httpd
   ```

2. 创建 httpd.conf
   ```
   *.cgi:/system/bin/sh
   ```

3. 手动测试 CGI
   ```bash
   echo "Content-Type: text/plain\n\nHello" | /system/bin/sh /path/to/script.cgi
   ```

### 2. Android 权限问题

**问题：** 无法创建文件或目录

**解决方案：**
1. 使用 root 权限
   ```bash
   su -c 'mkdir -p /data/adb/srv/magnet'
   ```

2. 检查 SELinux 状态
   ```bash
   getenforce
   # 如果是 enforcing，需要调整策略
   ```

## 日志和调试

### 1. 开启调试模式

在 CGI 脚本中添加调试输出：
```bash
echo "Content-Type: text/plain"
echo ""
echo "Debug: $QUERY_STRING"
echo "Debug: $(cat)"
```

### 2. 监控服务状态

```bash
# 监控 httpd 进程
watch -n 1 "ps | grep httpd"

# 监控端口使用
watch -n 1 "netstat -tlnp | grep 8080"
```

### 3. 性能分析

```bash
# 分析 CGI 执行时间
time curl -s "http://localhost:8080/cgi-bin/search?q=test"

# 分析内存使用
ps -o pid,ppid,cmd,%mem,%cpu -C httpd
```

## 联系支持

如果问题仍然存在，请提供以下信息：
1. 操作系统版本
2. busybox 版本
3. 错误日志
4. 网络环境描述
5. 复现步骤