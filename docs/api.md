# API 接口说明

## 接口概览

所有接口都运行在 8080 端口，路径以 `/cgi-bin/` 开头。

## 1. 搜索接口

### apibay 搜索
```
GET /cgi-bin/search.cgi?q=<关键词>
```

**参数：**
- `q`: 搜索关键词（URL 编码）

**返回：**
```json
[
  {
    "info_hash": "...",
    "name": "文件名",
    "size": 文件大小（字节）,
    "seeders": 做种数,
    "leechers": 下载人数
  }
]
```

**示例：**
```bash
curl "http://localhost:8080/cgi-bin/search.cgi?q=inception"
```

### btsow 搜索
```
POST /cgi-bin/btsow.cgi
Content-Type: text/plain; charset=utf-8
```

**请求体：**
- 原始 UTF-8 搜索关键词

**返回：**
```json
[
  {
    "hash": "info_hash",
    "name": "文件名",
    "size": 文件大小（字节）,
    "lastUpdateTime": 时间戳
  }
]
```

**示例：**
```bash
curl -X POST -H "Content-Type: text/plain; charset=utf-8" --data "流浪地球" "http://localhost:8080/cgi-bin/btsow.cgi"
```

## 2. 下载接口

### 添加到 aria2
```
POST /cgi-bin/add.cgi
Content-Type: application/json
```

**请求体：**
```json
{
  "uri": "magnet:?xt=urn:btih:info_hash"
}
```

**返回：**
```json
{"id":"任务ID","jsonrpc":"2.0","result":"OK"}
```

## 3. 状态查询接口

### 源状态检测
```
GET /cgi-bin/status.cgi
```

**返回：**
```json
{
  "btsow": {
    "ok": true,
    "code": "200"
  },
  "tpb": {
    "ok": true,
    "code": "200"
  },
  "t": 1234567890
}
```

**字段说明：**
- `ok`: 源是否可用
- `code`: HTTP 状态码
- `t`: 时间戳

## 4. 前端接口

### 搜索页面
```
GET /
```

返回完整的搜索页面，包含：
- 搜索框
- 状态条
- 结果展示区域

### 页面功能
- 支持双源搜索（btsow + apibay）
- 实时状态显示
- 结果排序（TPB 按做种数，BTSOW 按更新时间）
- 一键下载和复制磁力链接

## 错误处理

### HTTP 状态码
- 200: 成功
- 400: 请求参数错误
- 404: 接口不存在
- 500: 服务器内部错误

### 错误响应格式
```json
{
  "error": "错误信息",
  "code": 错误代码
}
```

### 常见错误
1. **超时错误**
   - 原因：源站点响应慢
   - 处理：自动重试或返回空结果

2. **网络错误**
   - 原因：源站点不可达
   - 处理：显示状态为不可用

3. **解析错误**
   - 原因：返回数据格式异常
   - 处理：返回空结果列表

## 安全说明

1. **CORS 支持**
   - 所有接口都设置 `Access-Control-Allow-Origin: *`
   - 支持跨域请求

2. **输入过滤**
   - 关键词进行 HTML 转义
   - 防止 XSS 攻击

3. **权限控制**
   - aria2 RPC 密钥不暴露在前端
   - 所有下载操作通过代理进行