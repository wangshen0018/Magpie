# 开发指南

## 项目架构

### 技术栈
- **前端**: 纯 HTML + CSS + JavaScript (无框架依赖)
- **后端**: Shell CGI 脚本
- **服务器**: busybox httpd (轻量级 HTTP 服务器)
- **部署**: Shell 脚本自动化

### 目录结构
```
src/
├── index.html         # 主页面
└── cgi-bin/           # 后端脚本
    ├── search.cgi     # apibay 代理
    ├── btsow.cgi      # btsow 代理
    ├── add.cgi        # aria2 RPC 代理
    └── status.cgi     # 状态探测

scripts/
├── deploy.sh          # 部署脚本
├── start-service.sh   # 服务启动脚本
└── test-deploy.sh    # 测试脚本
```

## 开发环境搭建

### 1. 克隆项目
```bash
git clone <repository-url>
cd magnet-github
```

### 2. 安装依赖
```bash
# 需要的工具
which curl node python3
```

### 3. 本地测试
```bash
# 启动本地 HTTP 服务器
python3 -m http.server 8080
# 或者使用 busybox
busybox httpd -p 8080 -h src/
```

## 代码规范

### JavaScript 代码规范
- 使用 ES6+ 语法
- 函数命名使用驼峰命名法
- 变量命名使用语义化名称
- 添加必要的注释

### Shell 脚本规范
- 使用 bash 语法
- 添加 shebang (`#!/bin/bash`)
- 错误处理 (`set -e`)
- 变量使用大写命名

### HTML/CSS 规范
- 语义化 HTML5 标签
- 响应式设计
- 移动端优先

## 测试

### 单元测试
```bash
# 测试 CGI 脚本
curl -s "http://localhost:8080/cgi-bin/status.cgi" | python3 -m json.tool
```

### 集成测试
```bash
# 运行部署测试
./scripts/test-deploy.sh
```

### 浏览器测试
- Chrome
- Firefox
- Safari (iOS)
- 移动端浏览器

## 贡献流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 发布流程

1. 更新版本号
2. 更新 CHANGELOG.md
3. 创建标签
4. 推送到 GitHub

## 常见问题

### Q: 为什么使用 CGI 而不是现代框架？
A: 为了保持轻量级，避免在资源受限的设备上运行 Node.js/Python 等。

### Q: 如何添加新的搜索源？
A: 在 `src/cgi-bin/` 添加新的 CGI 脚本，然后在 `index.html` 中添加相应的搜索函数。

### Q: 如何优化移动端体验？
A: 使用响应式设计，触摸友好的按钮，避免复杂的交互。