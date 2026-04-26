# mem-forever

**所有AI工具都会忘记你。用这个仓库，它们再也不会。**

[English](../README.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md) | [Русский](README.ru.md)

---

你关掉对话。刚才讨论的一切都消失了。下次打开，从零开始。重新解释你是谁。重新说明你的偏好。看着AI犯你已经纠正过的错误。

这个仓库就是解决方案。你的AI会记住你是谁、你做了什么决定、你学到了什么、你讨厌什么。跨工具。跨会话。永远。

## 原理

```
.ilang/
  soul.md      ← 你是谁（AI自动生成，不是你填的）
  memory.md    ← 你做了什么决定、学了什么、建了什么（AI自动追加）
```

你的AI在每次会话开始时读取这些文件，结束时更新它们，然后commit并push。下次会话、换个工具、下个月、明年：完整上下文，零重复。

## 设置（10秒）

**第一步**：点击 **"Use this template"** → **Create a new repository** → 设为 **Private**。

**第二步**：没有第二步。

用任何AI工具打开这个仓库。它会读取指令文件，问你几个问题，然后开始建立你的档案。从那以后，它就记住你了。

## 配合任何AI工具使用

### Claude Code / Codex / Cursor / Copilot / Gemini CLI

用你的工具打开这个仓库。指令文件已经就位：

| 工具 | 自动读取 |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex | `AGENTS.md` |
| Cursor | `.cursorrules` |
| Copilot | `.github/copilot-instructions.md` |
| Gemini CLI | `GEMINI.md` |

### 在其他项目里工作？

告诉你的AI：

> 我的记忆仓库在 `https://github.com/你的用户名/mem-forever`。PAT: `ghp_xxx`。去clone它，读 `.ilang/soul.md` 和 `.ilang/memory.md`，然后回来继续这个项目。

就这样。一句话。完整上下文恢复。

### ChatGPT / Claude.ai / Gemini网页版

把 `.ilang/soul.md` 上传到：

| 平台 | 上传到哪里 |
|---|---|
| ChatGPT | 项目知识文件 |
| Claude.ai | 项目知识 |
| Gemini | Google云端硬盘 → Gemini自动读取 |

记忆更新后重新上传。或者直接把内容贴在对话开头。

## 记住什么

你的AI自动生成并维护两个文件：

**soul.md** 是你的画像。从对话中建立，不是填表。包含你的角色、工作方式、偏好、反模式和教训。每次会话通过突变和衰减规则变得更精准。

**memory.md** 是你的日志。做过的决定、学到的教训、发现的事实、追踪的进展。只追加不覆盖。Git历史保留一切。

你永远不需要手写这些文件。你的AI来写。你随时可以查看和编辑。它们是你私有仓库里的纯文本。归你所有。

## 多个项目？

再用一次模板。创建 `mem-forever-work`、`mem-forever-side-project`、`mem-forever-research`。每个仓库是独立的记忆。同一个引擎，不同的上下文。

## 上游更新

新功能和改进每周一通过GitHub Action自动同步。只更新引擎文件。你的 `.ilang/` 数据永远不会被碰。

## 隐私

你的记忆存储在你自己的私有GitHub仓库中。没有服务器。没有账号。没有数据离开你的仓库。删掉仓库就没了。

## 对比

| | mem-forever | Nowledge Mem | Mem0 |
|---|---|---|---|
| 安装 | 用模板 | 下载应用+配置 | pip install+API key |
| 配置 | 无 | MCP+插件+LLM设置 | SDK集成 |
| 存储 | 你的GitHub仓库 | 本地SQLite | 云端向量库 |
| 跨工具 | 任何能读文件的工具 | 每个工具装插件 | 每个工具接API |
| 价格 | 免费 | 免费/付费 | 免费/付费 |
| 数据归属 | 你 | 你 | 他们 |
| 迁移 | `git clone` | 导出 | API调用 |

## 底层原理

指令文件（`CLAUDE.md`、`.cursorrules`、`AGENTS.md`、`GEMINI.md`）包含用 [I-Lang v3.0](https://ilang.ai) 编写的行为规则，这是一种AI模型能原生解析的结构化协议。这些规则告诉AI如何提取偏好、格式化记忆、处理冲突、随时间演进你的画像。

你不需要了解I-Lang。你不需要读指令文件。你只管和AI对话，它会越来越懂你。

## 许可证

MIT

---

由 [I-Lang Protocol](https://ilang.ai) 构建。人工智能的原生语言。
