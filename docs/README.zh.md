# 永久记忆

> **Mem-Forever · 跨会话 · 跨模型 · 跨工具**
> 基于 I-Lang 协议构建的 AI 持久记忆层。

[![License](https://img.shields.io/badge/license-MIT-d4a858?style=flat-square)](../LICENSE)
[![Protocol](https://img.shields.io/badge/protocol-I--Lang_v4.0-d4a858?style=flat-square)](https://ilang.ai)
[![Tools](https://img.shields.io/badge/works_with-Claude_·_Cursor_·_Codex_·_Copilot_·_Gemini-d4a858?style=flat-square)]()

[English](../README.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md) | [Русский](README.ru.md)

---

## 摘要

所有AI工具都会在会话结束后忘记你。你关掉窗口，偏好、决策、教训全部消失。下次打开，从零开始。

**Mem-Forever** 是一个基于Git的记忆层，让任何AI工具永久记住你。记忆以 I-Lang 结构化格式存储在你自己的私有仓库中。人类可读，机器可解析，跨工具通用。

上下文窗口会遗忘，**Mem-Forever 不会**。

---

## 为什么

| | |
|---|---|
| **持久** | 一份记忆，跨越每次会话、每次模型切换。 |
| **便携** | `.ilang/` 目录里的纯文本，`git diff` 可追踪，零厂商锁定。 |
| **自动** | AI从对话中自动建立你的画像，你不需要填任何表格。 |
| **私密** | 你的仓库，你的数据。没有服务器，没有账号，没有遥测。 |

---

## 速览

```
.ilang/
  soul.md      ← 你是谁（从对话中自动生成）
  memory.md    ← 你做了什么决定、学了什么（自动追加）
```

```ilang
::DNA{user}
::CORE{
  ::CONTEXT{role:全栈开发|experience:10yr}
  ::GENE{style|conf:confirmed}
    T:先说结论
    T:简洁输出|when:简单任务
    A:无信号的冗长⇒浪费
}
::LESSONS{
  ::LESSON{id:serverless不能共享状态|conf:confirmed}
}
```

每一条偏好都是**可寻址的**、**有作用域的**、**有版本的**、**可证伪的**。

---

## 设置（几秒钟）

**第一步** &ensp; 点击 **"Use this template"** → **Create a new repository** → 设为 **Private**。

**第二步** &ensp; 没有第二步。

用任何AI工具打开这个仓库。它会读取指令文件，问你几个问题，建立你的画像。从此，它记住你。

---

## 适配所有工具

| 工具 | 自动读取 | 方式 |
|---|---|---|
| Claude Code | `CLAUDE.md` | 打开仓库，直接工作 |
| Cursor | `.cursorrules` | 打开仓库，直接工作 |
| Codex | `AGENTS.md` | 打开仓库，直接工作 |
| Copilot | `.github/copilot-instructions.md` | 打开仓库，直接工作 |
| Gemini CLI | `GEMINI.md` | 打开仓库，直接工作 |
| ChatGPT | 项目知识 | 上传 `soul.md` |
| Claude.ai | 项目知识 | 上传 `soul.md` |
| Gemini网页版 | Google云端硬盘 | 同步 `soul.md` 到云端硬盘 |

### 在其他项目里工作？

一句话恢复完整上下文：

> *我的记忆仓库在 `https://github.com/你的用户名/mem-forever`。PAT: `ghp_xxx`。去clone它，读 `.ilang/soul.md` 和 `.ilang/memory.md`，然后回来继续这个项目。*

### 多个项目？

再用一次模板。`mem-forever-work`、`mem-forever-research`、`mem-forever-client-x`。每个仓库是独立的记忆。同一个引擎，不同的上下文。

---

## 对比

| | Mem-Forever | Nowledge Mem | Mem0 |
|---|---|---|---|
| 安装 | 用模板 | 下载应用+配置 | pip install+API key |
| 配置 | 无 | MCP+插件+LLM | SDK集成 |
| 存储 | 你的GitHub仓库 | 本地SQLite | 云端向量库 |
| 跨工具 | 任何能读文件的工具 | 每个工具装插件 | 每个工具接API |
| 价格 | 永久免费 | 免费/付费 | 免费/付费 |
| 数据归属 | 你 | 你 | 他们 |
| 迁移 | `git clone` | 导出 | API调用 |

---

## 底层原理

指令文件包含用 [I-Lang v4.0](https://ilang.ai) 编写的行为规则，AI模型能原生解析。它们告诉AI如何提取偏好、格式化记忆、处理冲突、随时间演进你的画像。

你不需要了解I-Lang。你只管和AI对话，它会越来越懂你。

---

## 许可证

MIT

---

<sub>由 <a href="https://ilang.ai">I-Lang Protocol</a> 构建 · 人工智能的原生语言</sub>
