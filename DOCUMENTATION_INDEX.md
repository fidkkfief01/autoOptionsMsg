# 📚 项目文档索引

本文档提供了 autoOptionsMsg 项目的完整文档导航。

## 📖 文档列表

### 1. **项目文档主体** 
   📄 [`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md)
   
   **内容**：
   - 项目概览和目标
   - 完整的目录结构说明
   - 核心模块功能介绍
   - 配置文件详细说明
   - 使用指南和示例
   - 常见问题解答
   
   **适合人群**：
   - 初次接触项目的用户
   - 需要快速了解项目功能的人
   - 寻求使用指南的用户

---

### 2. **技术架构深度分析**
   📄 [`TECHNICAL_ARCHITECTURE.md`](TECHNICAL_ARCHITECTURE.md)
   
   **内容**：
   - 系统分层架构设计
   - 完整的工作流程图
   - 数据模型关系图
   - 关键算法和逻辑说明
   - 期权符号标准化 (OCC)
   - 数据提供商接口设计
   - 安全性考虑
   - 性能优化策略
   - 日志系统说明
   - 测试策略
   - 扩展点文档
   - 生产部署建议
   
   **适合人群**：
   - 系统设计师
   - 后端开发工程师
   - 需要深入理解架构的人
   - 贡献代码的开发者

---

### 3. **API 参考和快速查询**
   📄 [`API_REFERENCE.md`](API_REFERENCE.md)
   
   **内容**：
   - 完整的模块 API 参考
   - 每个主要类和函数的使用示例
   - 命令行参数详解
   - 配置文件所有选项说明
   - 期权查询语法速查表
   - 消息格式示例
   - 常见错误代码和解决方案
   - 盈亏计算实例
   
   **适合人群**：
   - 开发人员
   - 需要集成 API 的用户
   - 寻求代码示例的人

---

### 4. **故障排查与部署指南**
   📄 [`TROUBLESHOOTING_DEPLOYMENT.md`](TROUBLESHOOTING_DEPLOYMENT.md)
   
   **内容**：
   - 完整的故障排查指南
   - 配置和启动常见问题
   - 环境变量问题诊断
   - API 连接问题排查
   - 轮询调度问题分析
   - Telegram 机器人常见问题
   - 生产部署方案 (4 种)
   - 监控和维护指南
   - 部署检查表
   
   **适合人群**：
   - 部署工程师
   - 运维人员
   - 遇到问题需要排查的用户
   - 生产环境维护人员

---

## 🗺 快速导航

### 按用户角色导航

#### 👤 **首次使用者**
1. 阅读 [`README.md`](README.md) - 快速开始
2. 阅读 [`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md) - 完整功能介绍
3. 参考 [`API_REFERENCE.md`](API_REFERENCE.md) - Telegram 机器人语法

#### 👨‍💻 **开发人员**
1. 了解 [`TECHNICAL_ARCHITECTURE.md`](TECHNICAL_ARCHITECTURE.md) - 系统架构
2. 查看 [`API_REFERENCE.md`](API_REFERENCE.md) - 模块 API
3. 需要时参考 [`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md) - 配置详情

#### 🔧 **运维/部署工程师**
1. 阅读 [`TROUBLESHOOTING_DEPLOYMENT.md`](TROUBLESHOOTING_DEPLOYMENT.md) - 部署指南
2. 查看 [`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md) - 配置管理
3. 参考 [`TECHNICAL_ARCHITECTURE.md`](TECHNICAL_ARCHITECTURE.md) - 性能优化

#### 🐛 **问题排查者**
1. 直接查阅 [`TROUBLESHOOTING_DEPLOYMENT.md`](TROUBLESHOOTING_DEPLOYMENT.md) - 故障诊断
2. 参考 [`API_REFERENCE.md`](API_REFERENCE.md) - 错误代码速查表
3. 检查日志并对比 [`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md) 配置

---

## 📚 按主题导航

### 配置管理
- [`PROJECT_DOCUMENTATION.md` - 配置说明](PROJECT_DOCUMENTATION.md#-配置说明)
- [`TROUBLESHOOTING_DEPLOYMENT.md` - 配置问题](TROUBLESHOOTING_DEPLOYMENT.md#1-配置和启动问题)
- [`API_REFERENCE.md` - 配置文件基本结构](API_REFERENCE.md#配置文件基本结构)

### 使用指南
- [`PROJECT_DOCUMENTATION.md` - 使用指南](PROJECT_DOCUMENTATION.md#-使用指南)
- [`API_REFERENCE.md` - 期权查询语法](API_REFERENCE.md#-期权查询语法速查表)

### API 文档
- [`API_REFERENCE.md` - 模块 API 参考](API_REFERENCE.md#-模块-api-参考)
- [`TECHNICAL_ARCHITECTURE.md` - 设计接口](TECHNICAL_ARCHITECTURE.md#-数据提供商接口设计)

### 部署指南
- [`TROUBLESHOOTING_DEPLOYMENT.md` - 部署方案](TROUBLESHOOTING_DEPLOYMENT.md#-生产部署指南)

### 架构设计
- [`TECHNICAL_ARCHITECTURE.md` - 系统架构](TECHNICAL_ARCHITECTURE.md#-系统设计架构)

### 问题排查
- [`TROUBLESHOOTING_DEPLOYMENT.md` - 故障排查](TROUBLESHOOTING_DEPLOYMENT.md#-故障排查-troubleshooting)
- [`API_REFERENCE.md` - 错误代码](API_REFERENCE.md#-常见错误代码和解决方案)

---

## 🎯 常见任务速查

### "我想快速上手"
→ [`README.md`](README.md) + [`PROJECT_DOCUMENTATION.md` - 使用指南章节](PROJECT_DOCUMENTATION.md#-使用指南)

### "我想了解系统如何工作"
→ [`TECHNICAL_ARCHITECTURE.md` - 工作流程](TECHNICAL_ARCHITECTURE.md#-核心工作流程)

### "我想学习如何编写查询命令"
→ [`API_REFERENCE.md` - 期权查询语法](API_REFERENCE.md#-期权查询语法速查表)

### "我想部署到生产环境"
→ [`TROUBLESHOOTING_DEPLOYMENT.md` - 生产部署指南](TROUBLESHOOTING_DEPLOYMENT.md#-生产部署指南)

### "应用出错了"
→ [`TROUBLESHOOTING_DEPLOYMENT.md` - 故障排查](TROUBLESHOOTING_DEPLOYMENT.md#-故障排查-troubleshooting)

### "我想修改代码或添加功能"
→ [`TECHNICAL_ARCHITECTURE.md` - 扩展点](TECHNICAL_ARCHITECTURE.md#-扩展点-extension-points)

### "我想了解成本和盈亏是如何计算的"
→ [`TECHNICAL_ARCHITECTURE.md` - 盈亏计算公式](TECHNICAL_ARCHITECTURE.md#1-盈亏计算公式-pnl-calculation) 或 [`API_REFERENCE.md` - 盈亏计算示例](API_REFERENCE.md#-盈亏计算示例)

### "我遇到了 API 错误"
→ [`API_REFERENCE.md` - 常见错误代码](API_REFERENCE.md#-常见错误代码和解决方案)

---

## 📖 文档阅读建议

### 第一阶段（入门）- 预计 30 分钟
1. [`README.md`](README.md) - 快速开始指南
2. [`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md) - 项目概览到使用指南

### 第二阶段（实践）- 预计 1 小时
1. 运行 `python main.py -c config.yaml --once --dry-run`
2. 查看 [`API_REFERENCE.md`](API_REFERENCE.md) 尝试 Telegram 查询

### 第三阶段（深入）- 预计 2-3 小时
1. 阅读 [`TECHNICAL_ARCHITECTURE.md`](TECHNICAL_ARCHITECTURE.md) 理解系统设计
2. 查阅源代码实现细节
3. 考虑扩展或优化

### 第四阶段（部署）- 按需阅读
1. 选择合适的部署方案
2. 参考 [`TROUBLESHOOTING_DEPLOYMENT.md`](TROUBLESHOOTING_DEPLOYMENT.md) 进行部署

---

## 🔗 外部资源参考

### 美股期权
- [OCC 期权符号标准](https://www.theocc.com/)
- [期权基础知识](https://www.investopedia.com/terms/o/option.asp)

### 数据源
- [Alpaca 官方文档](https://docs.alpaca.markets/)
- [Yahoo Finance API](https://pypi.org/project/yfinance/)

### Telegram
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [BotFather 教程](https://core.telegram.org/bots#botfather)

### Python 框架
- [Pydantic 文档](https://docs.pydantic.dev/)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)
- [HTTPX 文档](https://www.python-httpx.org/)

---

## 📝 文档版本和更新

| 文档 | 版本 | 更新时间 | 备注 |
|------|------|---------|------|
| PROJECT_DOCUMENTATION.md | 1.0 | 2026-05-28 | 初版 |
| TECHNICAL_ARCHITECTURE.md | 1.0 | 2026-05-28 | 初版 |
| API_REFERENCE.md | 1.0 | 2026-05-28 | 初版 |
| TROUBLESHOOTING_DEPLOYMENT.md | 1.0 | 2026-05-28 | 初版 |

---

## ✅ 检查清单

在开始使用项目前，请确认已完成以下步骤：

```
准备阶段
- [ ] 已阅读 README.md
- [ ] 已理解项目目的和功能
- [ ] 已准备好 API 密钥和 Telegram 信息

配置阶段
- [ ] 复制了 config.example.yaml 到 config.yaml
- [ ] 编辑了 config.yaml 填入真实数据
- [ ] 创建了 .env 文件并设置环境变量
- [ ] 验证了环境变量加载正确

测试阶段
- [ ] 运行干运行测试成功
- [ ] 验证了 Telegram 消息发送
- [ ] 查看了日志无错误

部署阶段（如需要）
- [ ] 选择了合适的部署方案
- [ ] 完成了部署检查清单
- [ ] 配置了监控和告警
- [ ] 保存了文档和联系信息
```

---

## 💬 快速帮助

**问题**: 我不确定从哪个文档开始读？
**答案**: 根据你的角色在 [按用户角色导航](#按用户角色导航) 部分找到推荐路径。

**问题**: 我想查找某个特定功能的文档？
**答案**: 使用 [按主题导航](#-按主题导航) 或 [常见任务速查](#-常见任务速查) 来定位。

**问题**: 文档和代码不一致怎么办？
**答案**: 优先参考源代码实现，然后更新文档。在 GitHub 提交 Issue。

**问题**: 我想为文档做出贡献？
**答案**: 欢迎提交 Pull Request 或创建 Issue 报告文档缺陷。

---

## 📞 联系和反馈

- 报告 bug：检查 [`TROUBLESHOOTING_DEPLOYMENT.md`](TROUBLESHOOTING_DEPLOYMENT.md)
- 建议改进：提交 Issue 或 PR
- 一般咨询：查阅相应文档或通过 GitHub Discussions

---

**文档生成日期**: 2026 年 5 月 28 日  
**项目名称**: autoOptionsMsg  
**文档版本**: 1.0

