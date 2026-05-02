# AGENTS.md

## 项目标识
- 插件名在**两个地方**定义，必须保持一致：
  - `metadata.yaml` 第 1 行 `name:` 字段 — 遵循 `astrbot_plugin_<id>` 命名约定
  - `main.py` 第 5 行 `@register()` 第一个参数 — 仅用 `<id>`，不带前缀
- 目录名也应遵循 `astrbot_plugin_<id>` 以匹配 metadata。

## AstrBot 特有模式
- 命令处理器是**异步生成器** — 用 `yield event.plain_result(...)` 发送回复，**不要**用 `return`。
- 命令通过 `@filter.command("名称")` 装饰器注册。
- 生命周期：`__init__` → `initialize()`（自动调用）→ 处理器运行 → `terminate()`（卸载时）。

## 运行与测试
- 此插件**无法独立运行**，必须由 AstrBot 运行时加载执行。
- 未配置任何 lint、测试或构建工具。
- 插件开发文档：https://docs.astrbot.app/dev/star/plugin-new.html

## 依赖
- 唯一运行时依赖为 `astrbot`（在 AstrBot 环境中可用）。不存在 `requirements.txt` 或 `pyproject.toml` — 所有导入均来自 `astrbot.api.*`。
