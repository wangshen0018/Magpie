# 更新日志

所有重要的版本更新都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

## [Unreleased]

### 计划中
- [ ] 添加更多磁力源支持
- [ ] 实现搜索结果缓存
- [ ] 添加用户认证功能
- [ ] 支持多语言界面
- [ ] 优化移动端用户体验

## [1.0.0] - 2026-10-29

### 新增
- ✅ 初始版本发布
- ✅ 双源聚合搜索（btsow + apibay）
- ✅ 实时源状态显示
- ✅ 集成到 AriaNg 浮动按钮
- ✅ 响应式设计，支持移动端
- ✅ 硬超时保护机制
- ✅ 一键部署脚本
- ✅ 完整的文档和示例

### 功能特性
- **双源搜索**: 
  - BTSOW: 中文资源丰富，支持中文搜索
  - APIBay: 英文资源，有做种数统计
- **状态监测**: 实时显示源连通性，30秒自动刷新
- **零新增常驻**: 复用现有 aria2/AriaNg，不增加后台服务
- **资源优化**: 仅需 1-2MB 内存，空闲时 CPU 几乎为 0
- **中文友好**: 针对中文用户的使用习惯优化
- **移动端适配**: 专为手机浏览器设计，支持触摸操作

### 技术实现
- **前端**: 纯 HTML/CSS/JavaScript，无框架依赖
- **后端**: Shell CGI 脚本，轻量级
- **服务**: 支持 busybox httpd，单文件部署
- **网络**: HTTP/HTTPS，支持 CORS 跨域

### 部署要求
- Linux 设备（支持 busybox httpd）
- 已有 aria2c 服务
- 网络可访问 btsow.live 和 apibay.org
- 移动端：支持现代浏览器的手机

### 文档
- 📖 [快速开始](README.md)
- 📖 [部署指南](docs/deploy.md)
- 📖 [API 文档](docs/api.md)
- 📖 [故障排除](docs/troubleshooting.md)
- 📖 [贡献指南](CONTRIBUTING.md)

### 许可证
- [MIT License](LICENSE)

---

## 版本说明

### 版本号规则
- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 更新频率
- 重大版本：每 6-12 个月
- 功能版本：根据需求情况
- 修正版本：问题修复后立即发布

### 贡献
欢迎通过 [GitHub Issues](https://github.com/你的用户名/magnet-github/issues) 和 Pull Request 参与项目开发！