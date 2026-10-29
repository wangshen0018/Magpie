磁力搜索增强版 - Magpie
=======================

## 📱 项目背景

这个项目是我为了个人使用而开发的磁力搜索工具。最初是为了解决我的红米 K40 设备的离线下载需求，后来发现对其他用户也可能有用，所以开源分享。

## 📱 项目背景

这个项目是我为了个人使用而开发的磁力搜索工具。最初是为了解决我的红米 K40 设备的离线下载需求，后来发现对其他用户也可能有用，所以开源分享。

> 💡 **AI 开发声明**: 本项目由 AI 辅助开发，确保代码质量和功能完整性，所有内容均为原创。

### 开发动机

- **个人需求**: 我需要一个简单的磁力搜索工具来配合现有的下载服务
- **设备利用**: 将闲置设备改造成实用的下载工具
- **网络环境**: 解决国内访问某些磁力站点的问题
- **使用便利**: 不想安装复杂的软件，希望有一个轻量级的解决方案

### 通用设计理念

这个项目不仅适用于 K40，更广泛适用于各种**资源受限的设备**，在保证功能的前提下：
- ✅ **零新增常驻进程**: 复用现有 aria2/AriaNg，不增加后台服务
- ✅ **极低资源占用**: 仅需 1-2MB 内存，空闲时 CPU 几乎为 0
- ✅ **网络友好**: 只在搜索时活跃，平时保持静默
- ✅ **中文优化**: 针对中文用户的使用习惯和资源需求

### 🎯 核心特性
- ✅ **双源聚合**: btsow（中文资源丰富）+ apibay（英文资源，有做种数）
- ✅ **实时状态显示**: 源连通性实时监测，30 秒自动刷新
- ✅ **零新增常驻**: 复用现有 aria2/AriaNg，不增加后台服务
- ✅ **中文友好**: btsow 中文资源丰富，支持中文搜索
- ✅ **硬超时保护**: 防止慢请求阻塞整个页面
- ✅ **移动端优化**: 响应式设计，适配手机浏览器操作

### 🖥️ 适用范围

这个工具主要适用于需要磁力搜索功能的个人用户，特别是那些已经拥有下载服务（如 aria2、Transmission 等）的用户。

#### 支持的设备
- **Android 设备**: 红米 K40、其他已 root 的安卓手机
- **Linux 设备**: 树莓派、Ubuntu 服务器等
- **其他**: 任何支持 busybox httpd 的 Linux 环境

#### 基本要求
- **操作系统**: Linux/Android
- **内存**: 最少 64MB
- **存储**: 最少 50MB 空间
- **网络**: 能够访问目标磁力站点

#### 典型使用场景
- 个人离线下载
- 家庭文件共享
- 媒体资源收集
- 学习资料整理

### 🌐 源站说明

本集成了两个在国内网络环境下**无需翻墙即可直接访问**的磁力搜索站：

#### 1. BTSOW (btsow.live)
- **特点**: 中文资源极其丰富，新电影、剧集、动漫等一应俱全
- **优势**: 搜索中文片名效果极佳，如"流浪地球"、"狂飙"等
- **局限**: 无做种数显示（按最后更新时间排序）
- **状态**: 实时监测连通性

#### 2. APIBay (apibay.org)
- **特点**: Pirate Bay 官方 JSON API，英文资源丰富
- **优势**: 有准确的做种数、下载人数统计
- **局限**: 中文搜索效果较差
- **状态**: 实时监测连通性

> 💡 **提示**: 两个源互为补充，中文内容优先使用 BTSOW，英文内容使用 APIBay

## 📖 文档

- [部署指南](docs/deploy.md)
- [API 说明](docs/api.md)
- [故障排除](docs/troubleshooting.md)
- [贡献指南](CONTRIBUTING.md)

## 🚀 快速部署

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd magnet-github
```

### 2. 一键部署
```bash
./scripts/deploy.sh /data/adb/srv/magnet  # K40 部署路径
```

### 3. 启动服务
```bash
busybox httpd -p 8080 -h /data/adb/srv/magnet/www
```

### 4. 访问服务
- 直接访问: http://你的IP:8080/
- 集成到 AriaNg: 添加浮动按钮

## 📋 详细文档

- [📖 部署指南](docs/deploy.md) - 详细的环境配置和部署步骤
- [🔌 API 说明](docs/api.md) - 所有 CGI 接口文档
- [🔧 故障排除](docs/troubleshooting.md) - 常见问题解决方案
- [📝 更新日志](CHANGELOG.md) - 版本更新历史

## 🚀 未来计划

### 📅 近期计划
- **增加更多源网站**: 扩展可访问的磁力源，提高搜索成功率
- **性能优化**: 改进搜索速度和稳定性
- **界面改进**: 优化移动端使用体验

### 🔮 远期计划
- **代理支持**: 解决网络访问限制，支持自动代理
- **功能扩展**: 添加搜索历史、收藏等实用功能
- **多设备支持**: 支持更多类型的设备和部署方式

### 🎯 项目目标

这个工具旨在提供一个简单易用的磁力搜索功能：

- ✅ **简单**: 一键部署，开箱即用
- ✅ **稳定**: 多源聚合，自动容错
- ✅ **隐私**: 本地运行，数据不外泄
- ✅ **实用**: 支持常用功能和扩展

### 🤝 参与贡献

欢迎贡献者参与未来计划：
- 📝 提交功能建议和改进意见
- 💻 提交代码实现和 bug 修复
- 🧪 测试新功能和性能优化
- 📚 完善文档和用户指南

## 🏗️ 项目结构

```
magnet-github/
├── README.md              # 项目说明和快速开始
├── LICENSE                 # MIT 开源许可证
├── CONTRIBUTING.md         # 贡献指南
├── CHANGELOG.md            # 版本更新日志
├── SECURITY.md             # 安全政策
├── .gitignore              # Git 忽略文件
├── FUNDING.yml            # 赞助支持
├── src/                   # 源代码
│   ├── index.html         # 搜索页面（双源、状态显示）
│   └── cgi-bin/           # 后端代理脚本
│       ├── search.cgi     # apibay 搜索代理
│       ├── btsow.cgi      # btsow 搜索代理
│       ├── add.cgi        # aria2 RPC 代理
│       └── status.cgi     # 源状态探测
├── scripts/               # 部署脚本
│   ├── deploy.sh          # 一键部署脚本
│   ├── start-service.sh   # 服务启动脚本
│   └── test-deploy.sh    # 测试部署脚本
├── docs/                  # 详细文档
│   ├── deploy.md          # 部署指南
│   ├── api.md            # API 接口说明
│   └── troubleshooting.md # 故障排除
├── static/               # 配置文件
│   └── httpd.conf        # busybox httpd 配置
└── .github/               # GitHub 配置
    ├── ISSUE_TEMPLATE/   # Issue 模板
    ├── PULL_REQUEST_TEMPLATE.md # PR 模板
    └── FUNDING.yml       # 赞助配置
```

## 🔧 集成到 AriaNg

在 AriaNg 的 index.html 最后 `</body>` 前添加：

```html
<a href="javascript:void(0)" onclick="window.open('http://'+location.hostname+':8080/','_blank')" style="position:fixed;right:20px;bottom:20px;background:#007bff;color:#fff;padding:8px 12px;border-radius:4px;text-decoration:none;z-index:9999">🔍 磁力搜索</a>
```

## 📱 界面功能

搜索页面包含：
- 🔍 搜索框（支持中文片名）
- 🟢/🔴 实时状态条（BTSOW/TPB 连通性）
- 📋 双源标签切换（全部/BTSOW/TPB）
- 📄 结果列表（显示大小、做种数、更新时间）
- ⬇️ 一键下载（直接推送到 aria2）
- 📋 一键复制磁力链接

## 🤝 贡献指南

欢迎贡献代码！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 开发环境设置
```bash
git clone <your-repo-url>
cd magnet-github
# 测试部署
./scripts/test-deploy.sh /tmp/test-deploy
# 启动测试服务
./scripts/start-service.sh 8080 /tmp/test-deploy
```

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式化
- refactor: 重构
- test: 测试
- chore: 构建/工具变动

## ⭐ Star History

如果这个项目对你有帮助，请给它一个 Star！🌟

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [btsow.live](https://btsow.live) - 提供丰富的中文磁力资源
- [apibay.org](https://apibay.org) - 提供英文磁力资源
- [aria2](https://aria2.github.io/) - 优秀的下载工具
- [AriaNg](https://github.com/mayswind/AriaNg) - 精美的 Web 界面

## 📞 联系方式

- 提交 Issue: [GitHub Issues](../../issues)
- 讨论: [GitHub Discussions](../../discussions)
- 邮箱: [your-email@example.com]