# 永久记忆

> **Mem-Forever · 跨会话 · 跨模型 · 跨工具**
> 基于 iLang 协议构建的 AI 持久记忆层。2.0 把记忆仓库做成一个可移植的大脑：画像、一文件一记忆、一张写着「做到哪了」的交接单，以及一个加密的钥匙包。

[![License](https://img.shields.io/badge/license-MIT-d4a858?style=flat-square)](../LICENSE)
[![Protocol](https://img.shields.io/badge/protocol-iLang_v5.0-d4a858?style=flat-square)](https://ilang.ai)
[![Tools](https://img.shields.io/badge/works_with-Claude_·_Cursor_·_Codex_·_Copilot_·_Gemini-d4a858?style=flat-square)]()

[English](../README.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md) | [Русский](README.ru.md)

---

## 摘要

所有 AI 工具都会在会话结束后忘记你。你关掉窗口，偏好、决策、教训全部消失。下次打开，从零开始。换台机器，连 Agent 干活要用的钥匙都没了。

**Mem-Forever** 是一个基于 Git 的记忆层，让任何 AI 工具永久记住你。记忆是一个个小 Markdown 文件，头部是 [OKF](OKF.md) frontmatter，正文可以带 iLang 声明，放在你自己的私有仓库里。人类可读，机器可解析，跨工具通用。2.0 补上了让新会话、新工具、新机器从上次停下的地方接着干的那几样东西。1.0 是为了让一段长对话续下去；2.0 保存的是记忆本身，并且让两个模型之间的交接可以审计：先判断再动手，先比对再合并。

上下文窗口会遗忘，**Mem-Forever 不会**。

---

## 为什么

| | |
|---|---|
| **持久** | 一份记忆，跨越每次会话、每次模型切换。 |
| **便携** | `soul/`、`memory/`、`handoff/` 里的纯文本 Markdown，`git diff` 可追踪，零厂商锁定。 |
| **自动** | AI 从对话中自动建立你的画像，你不需要填任何表格。 |
| **私密** | 你的仓库，你的数据。没有服务器，没有账号，没有遥测。 |
| **可续接** | `handoff/CURRENT.md` 写着做了什么、下一步是什么、哪些没验证。下一个会话，不管用哪个工具，从这里开始。 |
| **齐全** | `vault/` 带着你的钥匙，age 加密。一台新机器三十分钟能干活。 |

---

## 速览

```
BRAIN.md              ← 先读我；也是你贴进网页聊天工具的那段文字
handoff/CURRENT.md    ← 停在哪：done / next / unverified
soul/soul.md          ← 你是谁（从对话中自动生成）
memory/MEMORY.md      ← 索引，一行一条记忆
memory/*.md           ← 一文件一记忆，带 `type` frontmatter
vault/keys-*.age      ← 你的钥匙，用你自己的公钥加密
docs/PASTE.md         ← 第三条路：没有工具的对话 AI
tools/brain.py        ← 可选：check、migrate、vault、install、handoff review、paste
```

```ilang
::STATE{@OWNER, kind:人, role:全栈开发, alias:对话里的我}
::GENE{style|conf:confirmed|scope:global}
T:先说结论
T:简洁输出|when:简单任务
A:无信号的冗长⇒浪费
::FACT{key:preferred_stack|value:react, node|conf:confirmed}
```

```ilang
::STATE{@TASK, name:发 v1.2, repo:my-app, branch:main, owner:@OWNER}
::PROGRESS{date:2026-11-04|done:§1 测试全绿|next:打 tag 发版|unverified:文档构建}
::BOUNDARY{never:对 main 强推|scope:project}
```

每一条偏好都是**可寻址的**、**有作用域的**、**有版本的**、**可证伪的**。每一张交接单就四个字段，任何工具都读得懂：date、done、next、unverified。记法就是 iLang 正典，模板里每个文件都过它的语法校验器，0 错 0 警。

---

## 设置（几秒钟）

**第一步** &ensp; 点击 **"Use this template"** → **Create a new repository** → 设为 **Private**。

**第二步** &ensp; 没有第二步。

用任何 AI 工具打开这个仓库。它读指令文件，读交接单，问你几个问题，建立你的画像。从此，它记住你。

**可选的加速器。** `tools/brain.py` 是一个 Python 文件，只用标准库，Python 3.10 以上：

```
python -X utf8 tools/brain.py check        # frontmatter 合规、无密钥形态的文本，每次推送前跑
python -X utf8 tools/brain.py migrate-cc   # 把 Claude Code 的自动记忆文件迁进 memory/
python -X utf8 tools/brain.py vault pack   # 把钥匙加密进 vault/（见 docs/VAULT.md）
python -X utf8 tools/brain.py install      # 把这个仓库接进本机的 Claude Code
python -X utf8 tools/brain.py paste        # 给没有工具的对话 AI 的那一条消息：速查卡加交接单（docs/PASTE.md）
python -X utf8 tools/brain.py handoff review returned.md   # 别的模型写回来的交接单，合并前先和你的比对
```

---

## 适配所有工具

| 工具 | 自动读取 | 方式 |
|---|---|---|
| Claude Code | `CLAUDE.md` | 打开仓库，直接工作。`brain.py install` 还会把它的自动记忆目录接到 `memory/`。 |
| Cursor | `.cursorrules` | 打开仓库，直接工作 |
| Codex | `AGENTS.md` | 打开仓库，直接工作 |
| Copilot | `.github/copilot-instructions.md` | 打开仓库，直接工作 |
| Gemini CLI | `GEMINI.md` | 打开仓库，直接工作 |
| ChatGPT | 自定义指令 + 连接器 | 贴 `BRAIN.md`；用 GitHub 连接器连仓库，或连 Drive 镜像 |
| Claude.ai | 项目说明 + 连接器 | 贴 `BRAIN.md`；用 GitHub 连接器连仓库 |
| Gemini 网页版 | Gem 指令 + Drive | 贴 `BRAIN.md`；把仓库镜像到 Drive |
| 任何没有工具的对话 AI | 贴一条消息 | `brain.py paste` 拼出来：速查卡加交接单。它把变更按块放在代码围栏里贴回来 |

写不了 git 的网页端把变更按块放在代码围栏里贴回来，能写 git 的端先跑 `brain.py handoff review` 比对，过了才落库。`BRAIN.md` 用 400 token 左右把这些都说清了；[docs/PASTE.md](PASTE.md) 里有五个检查问题，看得出模型是读懂了记法还是在猜。

### 在其他项目里工作？

一句话恢复完整上下文：

> *我的大脑仓库在 `https://github.com/你的用户名/brain`。去读那里的 `BRAIN.md`，然后回来继续这个项目。*

用 Agent 自己的连接器（GitHub 应用、Drive）或本地 clone 给它访问权限。不要把任何 token 贴进提示词；钥匙走 `vault/`，见 [docs/VAULT.md](VAULT.md)。

### 多个项目？

再用一次模板。`brain-work`、`brain-research`、`brain-client-x`。每个仓库是独立的记忆。同一个引擎，不同的上下文。

---

## 2.0 新在哪

- **布局。** `soul/`（画像）、`memory/`（一文件一记忆加索引）、`handoff/`（停在哪）、`rules/`、`env/`、`vault/`、`tools/`。`.ilang/` 标记为弃用，保留一个版本。
- **里程碑即交接。** 部署成功、配置改动、结论确定，skill 就更新 `handoff/CURRENT.md`，不等会话结束。读到 `status: open` 的会话先认领；git 就是锁。
- **OKF frontmatter。** `soul/`、`memory/`、`handoff/` 下每个文件都带 `type`。`brain.py check` 查三条规则并扫描密钥形态的文本。见 [docs/OKF.md](OKF.md)。
- **钥匙包。** API 密钥、SSH 私钥、记忆里 `[REDACTED 种类 指纹]` 标记背后的值，打进一个 [age](https://age-encryption.org) 加密包。私钥放密码管理器，另打印一份。见 [docs/VAULT.md](VAULT.md)。
- **记法对齐 iLang 正典。** `::STATE`、`::FACT{key|value|conf}`、`::PROGRESS{date|done|next|unverified}`、`::DECIDE{@X}{what|why|context}`、`::LESSON` 加一行正文、`::BOUNDARY{never|scope}`。模板里每个文件都过正典语法校验器，0 错 0 警。速查卡在十家分词器上 381 到 410 token（Claude 539）；卡上三条不显然的规则来自十二档模型的五问实测。
- **先判断再动手。** 读交接单、复述、导出都不算干活。`next` 里撞上边界的项停下；缺证据的问；该主人拍的往后放。一句「交接」不授权任何下一步。
- **先比对再合并。** 别的模型写的交接单是候选。`brain.py handoff review` 和已接受的那份逐块比对：删了边界、done 里出现被禁止或没证据的项、少键、空值、标识改了、项不声不响没了，都拒绝；其余列给你拍。
- **粘贴。** `brain.py paste` 拼出没有工具的对话 AI 需要的那一条消息；`docs/PASTE.md` 有五个检查问题和实测数据。
- **brain.py。** `check`、`migrate-cc`、`vault pack / unpack / verify`、`install`、`init`、`status`、`handoff open / claim / close / show / review`、`paste`、`export-drive`。单文件，零依赖。
- **提示词里不出现 token。** 访问权限走连接器或 clone。

## 从 1.0 过来

用任何工具打开你的仓库，skill 只迁一次：`.ilang/soul.md` 的内容移到 `soul/soul.md`，`.ilang/memory.md` 复制成 `memory/memory-1.0.md` 补上 frontmatter 并进索引，`.ilang/` 两个文件留作指针到 2.1。然后跑 `python -X utf8 tools/brain.py check`。旧块名（`::DECIDED`、`::LEARNED`、`::DNA{}` / `::CORE{}` 外壳）当笔记读，碰到那个文件时才改写。

---

## 工作原理

```
┌─────────────┐     ┌────────────────┐     ┌────────────────┐
│  你和任意    │────▶│  AI 读         │────▶│  AI 写         │
│  AI 工具     │     │  handoff/      │     │  memory/*.md   │
│  对话        │     │  soul/         │     │  handoff/      │
│              │     │  记忆索引      │     │  soul/         │
└─────────────┘     └────────────────┘     └───────┬────────┘
                                                   │
                                             git commit
                                             git push
                                                   │
                                            ┌──────▼──────┐
                                            │  你的私有    │
                                            │  GitHub 仓库 │
                                            │  + vault/    │
                                            └─────────────┘
```

**soul/soul.md** 是你的行为画像。从对话中建立，每次会话通过变异和衰减规则打磨。把它想成跟着你走的 DNA。

**memory/** 是你的日志，一事一文件。决策、教训、事实、引用。只追加。Git 历史保存一切。

**handoff/CURRENT.md** 是你留在桌上的那张条子：日期、做了什么、下一步、没验证的。下一个会话先读它。别的模型交回来的交接单，先和它比对，过了才能替换它。

你从不手写这些文件。你的 AI 来写。你可以随时查看、编辑、删除。它们是你的。

---

## 对比

| | Mem-Forever | Nowledge Mem | Mem0 |
|---|---|---|---|
| 安装 | 用模板 | 下载应用+配置 | pip install+API key |
| 配置 | 无 | MCP+插件+LLM | SDK集成 |
| 存储 | 你的GitHub仓库 | 本地SQLite | 云端向量库 |
| 跨工具 | 任何能读文件的工具 | 每个工具装插件 | 每个工具接API |
| 跨会话续接 | `handoff/CURRENT.md` | 会话历史 | 会话历史 |
| 新机器的钥匙 | `vault/`，age 加密 | 无 | 无 |
| 价格 | 永久免费 | 免费/付费 | 免费/付费 |
| 数据归属 | 你 | 你 | 他们 |
| 迁移 | `git clone` | 导出 | API调用 |

---

## 底层原理

指令文件包含用 [iLang v5.0](https://ilang.ai) 编写的行为规则，iLang 协议已在 ChatGPT、Claude、Gemini、DeepSeek、Kimi、Qwen、GLM 上测试。它们告诉 AI 如何提取偏好、格式化记忆、保持交接单最新、处理冲突、随时间演进你的画像。`rules/GRAMMAR-CARD.md` 九条规则一屏纸就是全部读法，十家分词器上数过。

你不需要了解 iLang。你只管和 AI 对话，它会越来越懂你。

---

## 许可证

MIT

---

<sub>由 <a href="https://ilang.ai">iLang Protocol</a> 构建 · 人工智能的原生语言</sub>
