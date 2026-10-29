# 部署指南

## 环境要求

### 硬件要求
- K40 手机或其他安卓设备（root 权限）
- 至少 100MB 可用空间
- 网络连接（需能访问 btsow.live 和 apibay.org）

### 软件要求
- busybox（包含 httpd 和 CGI 支持）
- aria2c（用于下载）
- curl（用于测试）

## 部署步骤

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd magnet-github
```

### 2. 一键部署
```bash
./scripts/deploy.sh /data/adb/srv/magnet
```

### 3. 手动启动服务
```bash
busybox httpd -p 8080 -h /data/adb/srv/magnet/www
```

### 4. 开机自启（可选）
在开机脚本中添加：
```bash
# 添加到 /data/adb/service.d/srv.sh
busybox httpd -p 8080 -h /data/adb/srv/magnet/www &
```

## 配置说明

### httpd 配置
创建 `httpd.conf` 文件：
```
*.cgi:/system/bin/sh
```

### aria2 配置
确保 aria2 配置包含：
```
enable-rpc=true
rpc-listen-all=true
rpc-allow-origin-all=true
```

## 验证部署

### 1. 测试页面访问
```bash
curl -I http://localhost:8080/
```

### 2. 测试搜索接口
```bash
curl -s "http://localhost:8080/cgi-bin/search?q=test"
curl -s -X POST -H "Content-Type: text/plain" --data "test" "http://localhost:8080/cgi-bin/btsow.cgi"
```

### 3. 测试状态接口
```bash
curl -s "http://localhost:8080/cgi-bin/status.cgi"
```

## 故障排除

### 1. 端口占用
```bash
netstat -tlnp | grep 8080
# 更换端口
busybox httpd -p 8880 -h /data/adb/srv/magnet/www
```

### 2. 权限问题
```bash
chmod +x /data/adb/srv/magnet/www/cgi-bin/*.cgi
chown -R root:root /data/adb/srv/magnet
```

### 3. 网络问题
确保能访问：
```bash
curl -I https://btsow.live/
curl -I https://apibay.org/
```

## 性能优化

### 1. 超时设置
- search.cgi: 12 秒超时
- btsow.cgi: 8 秒超时
- status.cgi: 1.5 秒超时

### 2. 并发处理
busybox httpd 默认单进程处理，适合轻量级使用。

### 3. 资源占用
- 内存：约 1-2MB
- CPU：空闲时几乎为 0
- 磁盘：约 10KB