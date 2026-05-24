# 语声 - 项目工作指引

## 项目概述

**语声**是一个跨平台语音输入法产品，帮助用户提高文本输入效率。目标用户为个人用户，优先保证易用性。

## 核心原则

- **易用性优先**：界面简洁直观，操作简单
- **分阶段开发**：MVP → 完整版 → 扩展版，逐步迭代
- **成本控制**：使用百度语音识别API（成本最低），配合本地Whisper离线模型
- **稳定推进**：每步验证后再进行下一步

## 技术栈

- UI框架：Flutter（跨平台）
- 核心逻辑：Python
- 语音识别：百度语音识别API + Whisper本地模型
- 版本控制：Git

## 标准文件路径指引

### 开发日志
- **目录**：`dev-logs/`
- **命名格式**：`YYYY-MM-DD.md`
- **内容**：每日完成事项和待办事项
- **自动记录**：每次开发会话结束时更新当天的开发日志

### 项目标准文档
- **开发需求文档**：[docs/requirements.md](docs/requirements.md) — 功能需求、非功能需求、优先级定义
- **技术设计规范**：[docs/technical-design.md](docs/technical-design.md) — 技术栈、系统架构、核心模块、数据流
- **设计规范**：[docs/design-spec.md](docs/design-spec.md) — 设计原则、色彩、字体、布局、组件、动画
- **执行步骤**：[docs/execution-plan.md](docs/execution-plan.md) — 分阶段实施计划、任务清单
- **API参考文档**：[docs/api-reference.md](docs/api-reference.md) — 百度API、Whisper模型、内部接口

### 源代码
- **Flutter UI**：`src/flutter_app/`
- **Python核心**：`src/python_core/`
- **资源文件**：`src/assets/`

### 测试
- **测试代码**：`tests/`

## 工作说明

### 开发前检查
1. 查看 `docs/execution-plan.md` 确认当前阶段任务
2. 查看当天的 `dev-logs/` 了解进度
3. 确认开发环境就绪（Flutter、Python、Git）

### 开发流程
1. 从执行计划中选择待完成的任务
2. 完成开发后更新对应代码
3. 记录变更到当天开发日志
4. 提交Git commit（有意义的变更时）

### 每天结束时
1. 更新 `dev-logs/YYYY-MM-DD.md`，记录：
   - 今日完成事项
   - 遇到的问题
   - 明日待办事项
2. 检查是否有需要更新的标准文档

### 决策参考
- 遇到技术选型问题，参考 `docs/technical-design.md`
- 遇到UI/UX问题，参考 `docs/design-spec.md`
- 遇到需求疑问，参考 `docs/requirements.md`
- 遇到API使用问题，参考 `docs/api-reference.md`

## 关键约束

- 开发周期：1-2个月（MVP）
- 目标平台：Windows、Mac、Linux
- 支持语言：初期中文，后续扩展
- 离线支持：MVP阶段提供基础离线能力
