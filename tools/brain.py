#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brain.py v1.5  可移植 Agent 大脑（brain 仓库）的单文件工具。

只用 Python 标准库，Python 3.10 以上。Windows 控制台请用：
    python -X utf8 tools/brain.py <命令>

本版实现（工程书 4.1 第 3 条与 4.4）：

  check [--repo 目录]
      OKF v0.2 三条合规：frontmatter 可解析；顶层 type 非空；
      保留名 index.md / log.md 结构正确。
      另做：全仓库密钥前缀扫描（GitHub PAT、OpenAI 风格 key、AWS access key、
      PEM 私钥块、乐享 MCP 令牌）；BRAIN.md 与 rules/GRAMMAR-CARD.md 的
      字节上限（400 token 的代理指标，只告警，token 数要用 Playground 实测）。
      有错误退出码 1，否则 0。扫描到的密钥只报文件和行号，不回显内容。

  migrate-cc [源目录] [--repo 目录] [--overwrite]
      把 Claude Code 自动记忆目录里的 *.md 复制进 memory/（附件 C 映射）：
      metadata.type 的值补成顶层 type；补 generated{by, at}，at 取源文件
      mtime，RFC 3339 带时区；其余字节原样。MEMORY.md 原样复制。
      源目录永不改动。目标已存在默认跳过，--overwrite 才覆盖。
      源文件没有 frontmatter 时只复制不改并提示（工程书 4.9 要停下来问）。
      源目录缺省按仓库上一级目录算 Claude Code 的 slug：
      ~/.claude/projects/<slug>/memory

  vault pack [--out vault/keys-YYYY-MM-DD.age] [--recipients vault/recipients.txt]
             [--keys-dir 目录] [--ssh-dir 目录] [--ssh-key 名 ...] [--source 源记忆目录]
      工程书 3.6 / 4.4：三类东西打成一个 tar，再用 age 按 recipients.txt 的公钥
      加密成 vault/keys-YYYY-MM-DD.age。
        keys/<名>.env      密钥目录下的 *.env，按字节打包，本工具不解析、不打印
        ssh/<名>           ssh 目录下 id_* 且非 .pub 的私钥文件，同上
        memory-values.json memory/ 里每个 [REDACTED 种类 指纹] 标记对应的值：
                           到源记忆同名文件里按上下文对齐取出，按 rules/SECRETS.md
                           的指纹规则核对；对不上的、源记忆里本来就只有指纹的，
                           都列进 unresolved，不猜
        MANIFEST.json      每个文件的大小与 sha256，打包时间与来源目录
      tar 只在内存里，不落明文中间文件；值不打印，只打印种类与指纹。
      密钥目录缺省 ~/.keys；没有这个目录就退到仓库上一级的 _keys；--keys-dir 可指定别处。

  vault unpack [--in 文件] [--to 目录] [--identity ~/.age/key.txt] [--overwrite]
      age 私钥解密后解 tar。给 --to 时全部解到该目录（往返验证用）；缺省解回原位：
      keys/ 到 ~/.keys、ssh/ 到 ~/.ssh、其余到 ~/.keys。已存在的文件默认不覆盖。

  vault verify [--in 文件] [--identity ...] [--keys-dir ...] [--ssh-dir ...]
      在内存里解密，逐文件与本机原件比 sha256，与 MANIFEST 比 sha256，
      memory-values.json 里的条目与 memory/ 里去重后的标记一一对上且指纹相符。
      不写任何明文到磁盘。全一致退出码 0。

  age 可执行文件按 --age-dir、环境变量 BRAIN_AGE_DIR、PATH、winget 包目录的顺序找。

  install [--cc-home ~/.claude] [--project-dir 目录] [--date YYYY-MM-DD] [--dry-run]
      工程书 3.9 第一行、4.5：本机 Claude Code 接线。本版只做 CC，其它端不做。
        1. rules/CLAUDE.md、rules/AGENTS.md、env/settings.json 与 ~/.claude/ 同名文件比 sha256：
           仓库里没有就 skip；本机没有就复制过去；一致 skip；不一致就停下回报，不覆盖
           （settings.json 的合并本版未实现）。
        2. memory junction：~/.claude/projects/<slug>/memory 若是普通目录，先改名成
           memory.pre-junction-<日期>（保留不删），再在原路径建 junction 指向仓库 memory/；
           两步在同一进程里连着做。已是指向仓库的 junction 则 skip。建完验证：是 junction、
           经 junction 能列出与仓库 memory/ 相同数量的文件、仓库 git status 没被改动。
           slug 按 --project-dir（默认仓库上一级目录）的实际路径算，不写死。
        3. soul/dna.md 存在才复制到 ~/.claude/.dna.md（缺失复制，一致 skip，不一致停下）；
           仓库里没有就 skip 并提示。
      回滚：删 junction 只能用  cmd /c rmdir <junction 路径>  或 PowerShell
      (Get-Item <junction 路径>).Delete()，然后把 memory.pre-junction-<日期> 改名回 memory。
      !! 对 junction 绝对不能 Remove-Item -Recurse / rm -rf，那会把仓库 memory/ 里的真文件删光。
      !! junction 之后，仓库里的 git checkout -- memory、git clean、git reset --hard 都会直接
         改写本机正在用的记忆，操作仓库前先想这一点。

  export-drive [--to 目录] [--account 账号]
      生成 mirror/brain-index.md（OKF 头 + BRAIN.md 全文 + soul/ 全文 + handoff/CURRENT.md
      全文 + memory/MEMORY.md 全文），打印字节数与粗估 token（字节/2.5，只是估算），
      粗估超过 16k 打 WARN 不阻止。然后跑一遍密钥扫描，有命中就拒绝导出。
      给了 --to：把索引、memory/*.md、soul/ 非隐藏文件、handoff/CURRENT.md 一对一复制到
      目标同名路径，按 sha256 只复制有变化的，目标 memory/ soul/ handoff/ 里多出的文件删掉
      （只删这三个子目录里的普通文件，不碰目标根下别的东西，不碰隐藏文件与 desktop.ini），
      打印 copied / unchanged / deleted；目标路径与账号写进 env/drive.json（folder_id 留给
      连接器补）。目标是 Drive 桌面版的同步文件夹时，上传由桌面版自动完成。
      没给 --to：只生成索引并列出要镜像的文件清单。

  status [--json]
      未提交改动数、未推送提交数（无远端或无上游就说明）、距上次提交多久、
      handoff/CURRENT.md 的 status / opened / claimed_by。有未提交或未推送（含无远端）
      退出码 1，备份脚本据此告警；--json 给脚本读。

  init [目录] [--agent 名] [--no-git]
      建 3.2 节的目录与骨架文件：BRAIN.md、index.md、log.md、soul/ 三个模板、memory/MEMORY.md、
      handoff/CURRENT.md、rules/GRAMMAR-CARD.md 与 GRAMMAR-CARD.zh.md、env/README.md、.gitignore、各目录 .gitkeep，
      并把本文件复制进 tools/。已存在的文件一律不覆盖。没有 .git 就 git init（分支 main）。

  sync [--direction both|to-cc|from-cc] [--dry-run]
      junction 不可用时的兜底：仓库 memory/ 与 ~/.claude/projects/<slug>/memory 双向复制。
      只在一边的复制过去；两边都有且不同的，mtime 新的覆盖旧的；从不删除。
      记忆目录已经是指向仓库的 junction 时什么都不做。

  handoff open|claim|close|show [--agent 名] [--project 名] [--task 一句话] [--slug 名] [--no-commit]
      3.5 节协议。open：没有活跃交接单时按模板新开一份并提交 "handoff: open <project>"。
      claim：把 agent 追加进 claimed_by、status 改 claimed，提交 "handoff: claim by <agent>"。
      close：status 改 closed，整文件移到 handoff/archive/YYYY-MM-DD-<slug>.md，新开一份空的
      CURRENT.md，两步一次提交。show：打印 status / opened / claimed_by 与 PROGRESS 的
      date / done / next / unverified 四段，不改任何东西。

  handoff review <候选文件> [--baseline handoff/CURRENT.md] [--validator 校验器路径]

  3.0（设计 MEM-FOREVER-3-ILANG-CRYPTO-DESIGN v1.1）：记忆是一条推导，钥匙推出任务，任务取定常数，中间逻辑是注释
  ledger list | add <名> --door --kind --value|--ref --verify --recover [--scope] [--why] [--top] | verify [all|名] | show <名> [--with-value]
      env/ledger.env 一行一门，明文放在私有仓库；verify 退出 0 才算门开着，写 last_verified
  unlock <名> [--scope 标签] [--code 一次性码]   当前 next 项点到这扇门且在范围内才打出值；顶门只认 otp issue 发的码
  otp issue|revoke|list <名>                  owner 在场时给顶门发一次性码（env/otp.json 只存哈希）
  pair <对方公钥> --scope 标签 ; unseal <文件>  配对时才封：范围内的行封给对方与 owner，写 declaration.md
  log owner|agent "<原文>" ; recognize [--days N] 原始轨迹按日追加到 log/；认人＝owner 发言对 soul 锚点命中率≥0.30 且零越界
  provenance init|check|repair [--transcript JSONL]  来源键 by:；无 owner 证据的边界读作建议；review [--staged] 是每个写入者的同一道门
  import <目录|文件> --from <名> ; verify [--online] ; instructions sync|check ; remote-check <url> ; migrate-2to3
      别的模型或别的会话交回来的交接单先当候选，与基线逐块比对后才准替换（2.0 的 REVIEW）：
      基线里的每条 BOUNDARY 必须原样在候选里，少了、改了、挂了 when: 都 REJECT；
      候选每个块的必填键齐全且值非空（none / 无 算有值），缺键空值 REJECT；
      PROGRESS 的 done / next / unverified 按 ；; 拆项：基线 done 少了、next 或 unverified
      的项没交代就不见了、新进 done 的项撞上某条 BOUNDARY 的 never 文本，都 REJECT；
      基线里的 FACT key、LESSON id、STATE 实体、GENE 名、DECIDE 块、未知块必须还在，
      不在 REJECT；FACT 值改了、conf 升降了、LESSON 正文改了、next 项进了 done（要证据）
      列 FLAG / TRANSITION 给人拍；候选新增的块列 ADD。候选先过密钥扫描，命中 REJECT。
      给了 --validator 就再跑一遍正典校验器 --lint --strict，非零 REJECT。
      只读不写：有 REJECT 退出码 1，只有 FLAG / TRANSITION 退出码 3，干净 0。
      --overlay：候选只含它改过的块（例如网页模型贴回的那一个 PROGRESS 块）时，先把候选的块
      按标识叠到基线上拼成完整候选再审，基线里其余块与 frontmatter 原样带入；--out 把拼好的
      完整候选写到文件，接受时就拿它替换 CURRENT.md。不给 --overlay 时候选必须是完整交接单。

  paste [--out 文件] [--lang auto|zh|en]
      给没有工具的对话 AI 用的那条消息（docs/PASTE.md，适配工程书的粘贴档）：
      开场一句 + 速查卡全文 + --- + handoff/CURRENT.md 的声明块；卡按主人的语言挑：
      --lang auto 看交接单（中文占比 >= 0.2 取 zh），rules/GRAMMAR-CARD.<lang>.md 优先，
      其次 rules/GRAMMAR-CARD.md；开场句跟实际用的那张卡走
      （去掉 frontmatter 与 "## " 之后的说明）。拼好先过密钥扫描，命中就拒绝。
      --out 写文件，否则打到标准输出；统计行走 stderr，方便 > 重定向。
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import locale
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

VERSION = "2.2"
GENERATED_BY = f"brain.py/{VERSION}"
OKF_VERSION = "0.2"
OKF_DIRS = ("soul", "memory", "handoff")
OKF_EXEMPT = {"memory/MEMORY.md"}  # Claude Code 原生索引，原样保留，不按 OKF 文件检查
BYTE_LIMITS = {"BRAIN.md": 2000, "rules/GRAMMAR-CARD.md": 2000}
SCAN_SKIP_DIRS = {".git", "__pycache__"}
SCAN_SKIP_SUFFIX = {".age", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".gz", ".7z"}
FENCE = "---"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KEY_RE = re.compile(r"^([^\s#\-][^:]*?)\s*:(?:\s+(.*))?$")

# 密钥形态（rules/SECRETS.md 第 2 条）。字面量拆开写，免得本文件被自己扫出来。
_PW = r"[A-Za-z0-9!@#$%^&*\[\]{}_+=?~]"        # 口令字符集：不含 . - / \，免得把文件名、版本号当口令
_MIXED = r"(?=" + _PW + r"*[0-9])(?=" + _PW + r"*[A-Za-z])" + _PW + r"{8,}"   # 同时含字母和数字的 8 位以上串
SECRET_PATTERNS = [
    ("GitHub PAT", re.compile("gh" + "p_")),
    ("OpenAI 风格 key", re.compile(r"(?<![A-Za-z0-9])" + "s" + "k-")),
    ("AWS access key", re.compile("AK" + "IA" + r"[0-9A-Z]{4,}")),
    ("PEM 私钥块", re.compile("-----BE" + "GIN")),
    ("乐享 MCP 令牌", re.compile("lxm" + "cp_")),
    ("Cloudflare API 令牌", re.compile("cf" + "at_" + r"[A-Za-z0-9]{20,}")),
    ("厂商前缀令牌", re.compile(r"(?<![A-Za-z0-9])(?:xox[abpr]-|gl" + r"pat-|github_" + r"pat_|gh[sou]_|ya29\.|[sr]k_live_|ts" + r"key-|AI" + r"za)[A-Za-z0-9_\-.]{8,}")),
    ("JWT", re.compile(r"ey" + r"J[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("Bearer 令牌", re.compile(r"Bearer\s+(?!\$\{VAULT)[A-Za-z0-9_\-.]{16,}")),
    ("URL 内嵌密码", re.compile(r"://[^\s/:@]+:(?!\$\{)[^\s/@]{4,}@")),   # ${VAR} 占位不算
    ("口令（密码/口令/root 后的混合串）", re.compile(r"(?:密码|口令|password|passwd|root\s*/)\s*[:：=]?\s*[`'\"]?" + _MIXED + r"(?![/\\.])")),
    ("键值凭据（Secret/Token/Key= 后的长串）", re.compile(r"(?:Secret|Token|EncodingAESKey|CorpID|AppSecret|SecretKey|AccessKey|API_KEY|api_key|ApiKey|client_secret|app_secret|access_key|secret_key)\s*[=:：]\s*[`'\"]?[A-Za-z0-9_\-+/=]{12,}")),
    ("带凭据标签的十六进制串", re.compile(r"(?i)(?:AccessKey|SecretKey|Secret|Token|账户|account id|account|密钥|private_key_id)[^\n]{0,12}[`'\"]?(?<![A-Za-z0-9])[0-9a-f]{32}(?:[0-9a-f]{8}|[0-9a-f]{32})?(?![A-Za-z0-9])")),
]


# ---------------------------------------------------------------- frontmatter

class FrontmatterError(Exception):
    """frontmatter 缺失、未闭合或 YAML 子集解析失败。"""


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    if text.startswith("﻿"):
        text = text[1:]
    return text


def split_frontmatter(text: str) -> tuple[list[str], int, str]:
    """返回 (frontmatter 原始行列表, 闭合 --- 所在行号, 换行风格)。

    行号按 text.split("\\n") 计，首行 --- 是第 0 行。
    """
    nl = "\r\n" if "\r\n" in text[:4000] else "\n"
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != FENCE:
        raise FrontmatterError("no frontmatter (file does not start with ---)")
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r") == FENCE:
            return [ln.rstrip("\r") for ln in lines[1:i]], i, nl
    raise FrontmatterError("frontmatter not closed (second --- missing)")


def _scalar(s: str):
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1].replace("''", "'")
    if s == "[]":
        return []
    if s.startswith("[") and s.endswith("]"):
        return [_scalar(p.strip()) for p in s[1:-1].split(",") if p.strip()]
    if s in ("null", "~"):
        return None
    return s


def _parse_block(items, i, indent):
    if items[i][2].startswith("- ") or items[i][2] == "-":
        return _parse_list(items, i, indent)
    result: dict = {}
    while i < len(items):
        n, ind, text = items[i]
        if ind < indent:
            break
        if ind > indent:
            raise FrontmatterError(f"line {n}: unexpected indentation")
        if text.startswith("- ") or text == "-":
            raise FrontmatterError(f"line {n}: list item where a key was expected")
        m = KEY_RE.match(text)
        if not m:
            raise FrontmatterError(f"line {n}: not a 'key: value' line")
        key, rest = m.group(1).strip(), m.group(2)
        if rest is None or rest.strip() == "":
            if i + 1 < len(items) and items[i + 1][1] > ind:
                child, i = _parse_block(items, i + 1, items[i + 1][1])
                result[key] = child
            else:
                result[key] = ""
                i += 1
            continue
        result[key] = _scalar(rest.strip())
        i += 1
    return result, i


def _parse_list(items, i, indent):
    result: list = []
    while i < len(items):
        n, ind, text = items[i]
        if ind < indent:
            break
        if ind > indent:
            raise FrontmatterError(f"line {n}: unexpected indentation")
        if not (text.startswith("- ") or text == "-"):
            raise FrontmatterError(f"line {n}: expected a '- ' list item")
        body = text[2:].strip() if text != "-" else ""
        m = KEY_RE.match(body) if body else None
        if m:
            key, rest = m.group(1).strip(), m.group(2)
            entry = {key: _scalar(rest.strip()) if rest and rest.strip() else ""}
            i += 1
            if i < len(items) and items[i][1] > ind:
                more, i = _parse_block(items, i, items[i][1])
                if isinstance(more, dict):
                    entry.update(more)
            result.append(entry)
        else:
            result.append(_scalar(body))
            i += 1
    return result, i


def parse_yaml(fm_lines: list[str]):
    """解析 frontmatter 用到的 YAML 子集：映射、嵌套映射、列表、带引号标量。"""
    items = []
    for n, raw in enumerate(fm_lines, 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        lead = raw[: len(raw) - len(raw.lstrip())]
        if "\t" in lead:
            raise FrontmatterError(f"line {n}: tab indentation")
        items.append((n, len(lead), raw.strip()))
    if not items:
        return {}
    obj, i = _parse_block(items, 0, items[0][1])
    if i != len(items):
        raise FrontmatterError(f"line {items[i][0]}: unexpected indentation")
    return obj


def load_frontmatter(path: Path):
    fm, _, _ = split_frontmatter(read_text(path))
    return parse_yaml(fm)


# ---------------------------------------------------------------------- check

def iter_repo_files(repo: Path):
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SCAN_SKIP_DIRS)
        for f in sorted(files):
            p = Path(root) / f
            if p.suffix.lower() in SCAN_SKIP_SUFFIX:
                continue
            yield p


def secret_scan(repo: Path) -> tuple[list[str], list[str], int]:
    """全仓库密钥形态扫描。返回 (命中列表, 警告列表, 扫过的文件数)；命中只报 文件:行:形态，不回显内容。"""
    hits: list[str] = []
    warnings: list[str] = []
    scanned = 0
    for p in iter_repo_files(repo):
        rel = p.relative_to(repo).as_posix()
        if rel.split("/", 1)[0] in SCAN_EXEMPT_TOP:
            continue
        try:
            text = p.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            warnings.append(f"{rel}: not UTF-8, skipped by secret scan")
            continue
        scanned += 1
        for n, line in enumerate(text.splitlines(), 1):
            for label, rx in SECRET_PATTERNS:
                if rx.search(line):
                    hits.append(f"{rel}:{n}: secret-like token ({label})")
    return hits, warnings, scanned


def cmd_check(repo: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # 1. index.md：bundle 根索引，须有 okf_version
    idx = repo / "index.md"
    if not idx.is_file():
        errors.append("index.md: missing")
    else:
        try:
            data = load_frontmatter(idx)
            v = data.get("okf_version") if isinstance(data, dict) else None
            if v in (None, ""):
                errors.append("index.md: okf_version missing in frontmatter")
            elif str(v) != OKF_VERSION:
                warnings.append(f"index.md: okf_version is {v!r}, expected {OKF_VERSION!r}")
        except (FrontmatterError, UnicodeDecodeError) as e:
            errors.append(f"index.md: {e}")

    # 2. log.md：## YYYY-MM-DD 标题，新的在前
    log = repo / "log.md"
    if not log.is_file():
        errors.append("log.md: missing")
    else:
        try:
            text = read_text(log)
            body_start = 0
            if text.startswith(FENCE):
                _, close_idx, _ = split_frontmatter(text)
                parse_yaml(_)
                body_start = close_idx + 1
            dates = []
            for n, line in enumerate(text.split("\n")[body_start:], body_start + 1):
                line = line.rstrip("\r")
                if line.startswith("## "):
                    head = line[3:].strip()
                    if not DATE_RE.match(head):
                        errors.append(f"log.md:{n}: heading {head!r} is not YYYY-MM-DD")
                        continue
                    try:
                        datetime.strptime(head, "%Y-%m-%d")
                    except ValueError:
                        errors.append(f"log.md:{n}: {head!r} is not a real date")
                        continue
                    dates.append((n, head))
            for (n1, d1), (n2, d2) in zip(dates, dates[1:]):
                if d2 > d1:
                    errors.append(f"log.md:{n2}: {d2} comes after {d1}; entries must be newest first")
                elif d2 == d1:
                    warnings.append(f"log.md:{n2}: duplicate date heading {d2}")
            if not dates:
                warnings.append("log.md: no ## YYYY-MM-DD entries")
        except (FrontmatterError, UnicodeDecodeError) as e:
            errors.append(f"log.md: {e}")

    # 3. soul/ memory/ handoff/ 下每个 .md：frontmatter 可解析，type 非空
    checked = 0
    for d in OKF_DIRS:
        base = repo / d
        if not base.is_dir():
            warnings.append(f"{d}/: directory missing")
            continue
        for p in sorted(base.rglob("*.md")):
            rel = p.relative_to(repo).as_posix()
            if rel in OKF_EXEMPT:
                continue
            checked += 1
            try:
                data = load_frontmatter(p)
            except (FrontmatterError, UnicodeDecodeError) as e:
                errors.append(f"{rel}: {e}")
                continue
            if not isinstance(data, dict):
                errors.append(f"{rel}: frontmatter is not a mapping")
                continue
            t = data.get("type")
            if not isinstance(t, str) or not t.strip():
                errors.append(f"{rel}: type missing or empty")
            g = data.get("generated")
            if g is not None and (not isinstance(g, dict) or not g.get("by")):
                warnings.append(f"{rel}: generated present but generated.by missing")

    # 4. key-shaped text: since 3.1 a WARN with the harvest command, never a refused commit (the repository is private;
    #    the push guard is the gate). The locations are listed, the content never echoed.
    hits, scan_warnings, scanned = secret_scan(repo)
    if hits:
        where = sorted({h.split(":", 1)[0] for h in hits})
        warnings.append(f"{len(hits)} key-shaped value(s) outside the ledger in {', '.join(where[:6])}{'...' if len(where) > 6 else ''}; "
                        f"python -X utf8 tools/brain.py ledger harvest turns them into ledger rows and {{{{DOOR}}}} tokens")
    warnings += scan_warnings
    raw_keys = _keys_env(repo)
    plain = [k for k, v in raw_keys.items() if v and not is_encoded(v)]
    if plain:
        warnings.append(f"{len(plain)} plain row(s) in {KEYS_REL}; python -X utf8 tools/brain.py ledger encode")
    if any(is_encoded(v) for v in raw_keys.values()) and load_pepper(repo) is None:
        warnings.append(f"{PEPPER_REL} missing: encoded rows cannot be read on this clone (ledger decode --pepper <hex>)")
    if (repo / ".git").exists():
        rc, out = _git(repo, "config", "core.hooksPath")
        if out.strip() != "tools/hooks":
            warnings.append("hooks are off on this clone (core.hooksPath is not tools/hooks); run python -X utf8 tools/brain.py init .")

    # 5. 字节上限（代理指标）
    for rel, limit in BYTE_LIMITS.items():
        p = repo / rel
        if not p.is_file():
            warnings.append(f"{rel}: missing")
        elif p.stat().st_size > limit:
            warnings.append(f"{rel}: {p.stat().st_size} bytes > {limit} (400 token 需用 Playground 实测)")

    # 6. 3.0: the ledger parses, log/ files are dated, provenance and the five instruction files
    rows, _ = load_ledger(repo)
    for r in rows:
        if r.get("error"):
            errors.append(f"{LEDGER_REL}:{r['line'] + 1}: {r['error']}")
    for r in rows:
        if not r.get("error") and not r["kv"].get("door"):
            errors.append(f"{LEDGER_REL}:{r['line'] + 1}: row {r['name']} has no door")
    # 3.1.1: a standing row with no value and no ref that resolves is not a door yet. Seen in the wild: public
    # repository addresses written as doors with verify:gh_public. Top and once doors are exempt (the owner's code).
    keys_now = _keys_env(repo)
    for r in rows:
        if r.get("error") or not r["kv"].get("door") or is_top(r) or grant_mode(r) != "standing":
            continue
        kv = r["kv"]
        if kv.get("value") not in (None, "", "none"):
            continue
        ref = kv.get("ref") or ""
        if ref not in ("", "none") and ref in keys_now:
            continue
        warnings.append(f"{LEDGER_REL}:{r['line'] + 1}: row {r['name']} has nothing to open (no value, no ref in {KEYS_REL}); "
                        f"store the key (ledger add --value, or ledger encode) or, if it is a public address, keep it as a ::FACT and drop the row")
    logdir = repo / LOG_DIR
    if logdir.is_dir():
        for p in sorted(logdir.glob("*.md")):
            if not DATE_RE.match(p.stem):
                warnings.append(f"log/{p.name}: name is not YYYY-MM-DD.md")
    try:
        violations, decays = provenance_scan(repo)
        for v in violations:
            warnings.append(f"provenance {v['file']}:{v['line']} {v['rule']} (brain.py provenance repair)")
        if decays:
            warnings.append(f"provenance: {len(decays)} block(s) due for decay (brain.py provenance repair)")
    except Exception as e:  # noqa: BLE001 - a broken file must not hide the other checks
        warnings.append(f"provenance scan failed: {e}")
    skill = repo / "skills" / "mem-forever" / "SKILL.md"
    if skill.is_file():
        body = skill_body(repo)
        for rel in INSTRUCTION_FILES:
            p = repo / rel
            if p.is_file() and read_text(p).replace("\r\n", "\n") != body:
                warnings.append(f"{rel}: not identical to the skill body (brain.py instructions sync)")
    if (repo / ".git").exists() and not (repo / "tools" / "hooks" / "pre-commit").is_file():
        warnings.append("tools/hooks/pre-commit missing (brain.py install writes the hooks)")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"check: {len(errors)} errors, {len(warnings)} warnings "
          f"({checked} OKF files, {scanned} files scanned for secrets)")
    return 1 if errors else 0


# ----------------------------------------------------------------- migrate-cc

def cc_slug(project_dir: Path) -> str:
    """Claude Code 把项目目录路径里的 : \\ / 都换成 - 作目录名。"""
    return re.sub(r"[:\\/]", "-", str(project_dir))


def default_cc_memory_dir(repo: Path, cc_home: Path | None = None, project_dir: Path | None = None) -> Path:
    project_dir = (project_dir or repo.resolve().parent).resolve()
    return (cc_home or Path.home() / ".claude") / "projects" / cc_slug(project_dir) / "memory"


def _copy_mtime(src: Path, dst: Path) -> None:
    st = src.stat()
    os.utime(dst, ns=(st.st_atime_ns, st.st_mtime_ns))


def cmd_migrate_cc(repo: Path, src: Path, overwrite: bool) -> int:
    rc = _migrate_cc_copy(repo, src, overwrite)
    if rc != 0:
        return rc
    # 3.1: the keys inside the migrated memory become ledger rows; without them the new session knows its next step
    # and can enter no machine
    if has_grant(repo, "write"):
        created = harvest(repo, ["memory"])
        for c in created:
            print(f"door    {c['door']} ({c['kind']}) from {c['file']}:{c['line']}")
        print(f"harvest: {len(created)} door(s) created from the migrated memory; run ledger verify and fill verify for each")
    else:
        print("harvest: skipped, no write grant on this machine; python -X utf8 tools/brain.py grant --write ; then ledger harvest memory")
    return 0


def _migrate_cc_copy(repo: Path, src: Path, overwrite: bool) -> int:
    if not src.is_dir():
        print(f"ERROR source directory not found: {src}")
        return 1
    dest = repo / "memory"
    dest.mkdir(parents=True, exist_ok=True)
    stats: Counter = Counter()
    print(f"source: {src}")
    print(f"dest:   {dest}")
    for p in sorted(src.glob("*.md")):
        target = dest / p.name
        if target.exists() and not overwrite:
            print(f"skip    {p.name}: already in memory/ (use --overwrite)")
            stats["skipped"] += 1
            continue
        raw = p.read_bytes()
        if p.name == "MEMORY.md":
            target.write_bytes(raw)
            _copy_mtime(p, target)
            print(f"copy    {p.name}: verbatim (Claude Code index)")
            stats["verbatim"] += 1
            continue
        bom = raw.startswith(b"\xef\xbb\xbf")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            print(f"ERROR   {p.name}: not UTF-8, not copied")
            stats["errors"] += 1
            continue
        if bom:
            text = text[1:]
        try:
            fm, close_idx, nl = split_frontmatter(text)
            data = parse_yaml(fm)
            if not isinstance(data, dict):
                raise FrontmatterError("frontmatter is not a mapping")
        except FrontmatterError as e:
            target.write_bytes(raw)
            _copy_mtime(p, target)
            print(f"WARN    {p.name}: {e}; copied verbatim, nothing added (book 4.9)")
            stats["no_frontmatter"] += 1
            continue

        lines = text.split("\n")
        cr = "\r" if nl == "\r\n" else ""
        added = []
        t = data.get("type")
        if not (isinstance(t, str) and t.strip()):
            meta = data.get("metadata")
            mt = meta.get("type") if isinstance(meta, dict) else None
            if isinstance(mt, str) and mt.strip():
                pos = next((i for i in range(1, close_idx)
                            if re.match(r"^metadata\s*:", lines[i])), None)
                if pos is None:
                    pos = close_idx
                lines.insert(pos, f"type: {mt.strip()}{cr}")
                close_idx += 1
                added.append(f"type={mt.strip()}")
            else:
                print(f"WARN    {p.name}: no top-level type and no metadata.type; type not added")
                stats["no_type"] += 1
        if "generated" not in data:
            at = datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat(timespec="seconds")
            block = ["generated:", f"  by: {GENERATED_BY}", f"  at: {at}"]
            for k, ln in enumerate(block):
                lines.insert(close_idx + k, ln + cr)
            close_idx += len(block)
            added.append("generated")

        out = "\n".join(lines)
        try:
            fm2, _, _ = split_frontmatter(out)
            parse_yaml(fm2)
        except FrontmatterError as e:
            print(f"ERROR   {p.name}: result would not parse ({e}); not written")
            stats["errors"] += 1
            continue
        if bom:
            out = "﻿" + out
        target.write_bytes(out.encode("utf-8"))
        _copy_mtime(p, target)
        print(f"migrate {p.name}: " + (", ".join(added) if added else "already compliant"))
        stats["migrated"] += 1

    print("migrate-cc: " + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    return 1 if stats["errors"] else 0


# ---------------------------------------------------------------------- vault

MEMORY_VALUES_NAME = "memory-values.json"
MANIFEST_NAME = "MANIFEST.json"
MARKER_RE = re.compile(r"\[REDACTED ([^\s\]]+) ([^\]]+)\]")
MARKER_TEMPLATE = ("种类", "指纹")          # 文档里举例用的字面标记，不是真标记
FP_PREFIXES = ("s" + "k-", "gh" + "p_", "lxm" + "cp_", "cf" + "at_")   # 拆开写，免得本文件被 check 扫出来
AGE_WINGET_GLOB = "Microsoft/WinGet/Packages/FiloSottile.age_*/age"


def fingerprint(value: str) -> str:
    """rules/SECRETS.md 的指纹规则：去掉四种已知令牌前缀后，24 位及以上取前 4 后 4，否则前 2 后 2。"""
    core = value
    for p in FP_PREFIXES:
        if core.startswith(p):
            core = core[len(p):]
            break
    return (core[:4] + "..." + core[-4:]) if len(core) >= 24 else (core[:2] + "..." + core[-2:])


def find_age_tool(name: str, age_dir: str | None) -> str:
    """找 age / age-keygen：--age-dir、环境变量 BRAIN_AGE_DIR、PATH、winget 包目录。"""
    exe = name + (".exe" if os.name == "nt" else "")
    for d in (age_dir, os.environ.get("BRAIN_AGE_DIR")):
        if d and (Path(d) / exe).is_file():
            return str(Path(d) / exe)
    found = shutil.which(name)
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA")
    if local:
        for d in sorted(Path(local).glob(AGE_WINGET_GLOB)):
            if (d / exe).is_file():
                return str(d / exe)
    raise FileNotFoundError(f"{name} not found: install FiloSottile.age (winget) or pass --age-dir")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _literal(seg: str) -> str:
    """字面段转正则；段里别的标记换成任意非换行串。"""
    out, last = [], 0
    for m in MARKER_RE.finditer(seg):
        out.append(re.escape(seg[last:m.start()]) + r"[^\n]+?")
        last = m.end()
    out.append(re.escape(seg[last:]))
    return "".join(out)


def _align(line: str, markers: list, idx: int, src_lines: list[str], src_text: str):
    """在源文件里找 line 的原文，取第 idx 个标记位置上的原值。

    先整行对齐（标记以外逐字相同），再退到标记前后 24 与 8 个字符的窗口；
    每种方法都必须恰好一处命中。返回 (值, 方法) 或 (None, 原因)。
    """
    m = markers[idx]
    before, after = line[:m.start()], line[m.end():]
    rx = re.compile("^" + _literal(before) + r"([^\n]+?)" + _literal(after) + "$")
    hits = [h for h in (rx.match(s) for s in src_lines) if h]
    if len(hits) == 1:
        return hits[0].group(1), "line"
    for width in (24, 8):
        pre, suf = before[-width:] if before else "", after[:width]
        group = r"([^\n]+?)" if suf else r"([^\n]+)"
        rx = re.compile(_literal(pre) + group + _literal(suf))
        hits = list(rx.finditer(src_text))
        if len(hits) == 1:
            return hits[0].group(1), f"window{width}"
    return None, f"{len(hits)} alignments in source"


def collect_memory_values(repo: Path, source: Path):
    """按 memory/ 里的 [REDACTED 种类 指纹] 标记到源记忆同名文件里取值并核指纹。

    返回 (resolved, unresolved, template_hits)。值只在返回的字典里，本函数不打印值。
    同一个 (种类, 指纹) 多处出现只记一条；对齐到两个不同的值时按冲突处理，不猜。
    """
    entries: dict[tuple[str, str], dict] = {}
    template_hits: list[str] = []
    for p in sorted((repo / "memory").glob("*.md")):
        text = read_text(p)
        src = source / p.name
        src_text = read_text(src) if src.is_file() else None
        src_lines = [ln.rstrip("\r") for ln in src_text.split("\n")] if src_text is not None else []
        for line in text.split("\n"):
            line = line.rstrip("\r")
            found = list(MARKER_RE.finditer(line))
            for i, m in enumerate(found):
                kind, fpv = m.group(1), m.group(2)
                if (kind, fpv) == MARKER_TEMPLATE:
                    template_hits.append(p.name)
                    continue
                e = entries.setdefault((kind, fpv), {"kind": kind, "fingerprint": fpv, "sources": [],
                                                     "value": None, "value_from": None, "notes": [], "conflict": False})
                if p.name not in e["sources"]:
                    e["sources"].append(p.name)
                if src_text is None:
                    e["notes"].append(f"{p.name}: source file missing")
                    continue
                value, how = _align(line, found, i, src_lines, src_text)
                if value is None:
                    e["notes"].append(f"{p.name}: {how}")
                elif value == fpv or "..." in value or "…" in value:
                    # 短指纹（xx...yy）按 2+2 规则算出来等于自己，不能当值收
                    e["notes"].append(f"{p.name}: source holds only the fingerprint, not the value")
                elif fingerprint(value) != fpv:
                    e["notes"].append(f"{p.name}: aligned text does not match the fingerprint (source may hold only a fingerprint)")
                elif e["value"] is None and not e["conflict"]:
                    e["value"], e["value_from"] = value, f"{p.name} ({how})"
                elif e["value"] is not None and e["value"] != value:
                    e["value"], e["value_from"], e["conflict"] = None, None, True
                    e["notes"].append(f"{p.name}: two different values match the same fingerprint; left unresolved")
    resolved = [e for e in entries.values() if e["value"] is not None]
    unresolved = [e for e in entries.values() if e["value"] is None]
    return resolved, unresolved, template_hits


def repo_markers(repo: Path) -> set[tuple[str, str]]:
    found = set()
    for p in sorted((repo / "memory").glob("*.md")):
        for m in MARKER_RE.finditer(read_text(p)):
            if (m.group(1), m.group(2)) != MARKER_TEMPLATE:
                found.add((m.group(1), m.group(2)))
    return found


def _tar_add_bytes(tar: tarfile.TarFile, name: str, data: bytes, mtime: float) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mtime = int(mtime)
    info.mode = 0o600
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    tar.addfile(info, io.BytesIO(data))


def default_keys_dir(repo: Path) -> Path:
    home_keys = Path.home() / ".keys"
    return home_keys if home_keys.is_dir() else repo.resolve().parent / "_keys"


def vault_inputs(keys_dir: Path, ssh_dir: Path, ssh_keys: list[str] | None) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    if keys_dir.is_dir():
        files += [(f"keys/{p.name}", p) for p in sorted(keys_dir.glob("*.env"))]
    if ssh_keys:
        names = list(ssh_keys)
    elif ssh_dir.is_dir():
        names = sorted(q.name for q in ssh_dir.iterdir()
                       if q.is_file() and q.name.startswith("id_") and not q.name.endswith(".pub"))
    else:
        names = []
    files += [(f"ssh/{n}", ssh_dir / n) for n in names]
    return files


def latest_vault_file(repo: Path) -> Path | None:
    files = sorted((repo / "vault").glob("keys-*.age"))
    return files[-1] if files else None


def _vault_decrypt(infile: Path, identity: Path, age_dir: str | None) -> bytes:
    age = find_age_tool("age", age_dir)
    if not infile.is_file():
        raise FileNotFoundError(f"vault file not found: {infile}")
    if not identity.is_file():
        raise FileNotFoundError(f"identity file not found: {identity}")
    r = subprocess.run([age, "-d", "-i", str(identity), str(infile)], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("age -d failed: " + r.stderr.decode("utf-8", errors="replace").strip())
    return r.stdout


def cmd_vault_pack(repo: Path, out: Path, recipients: Path, keys_dir: Path, ssh_dir: Path,
                   ssh_keys: list[str] | None, source: Path, age_dir: str | None,
                   overwrite: bool, with_memory: bool) -> int:
    try:
        age = find_age_tool("age", age_dir)
    except FileNotFoundError as e:
        print(f"ERROR {e}")
        return 1
    if not recipients.is_file() or not recipients.read_text(encoding="utf-8").strip():
        print(f"ERROR recipients file missing or empty: {recipients}")
        return 1
    if out.exists() and not overwrite:
        print(f"ERROR {out} already exists (use --overwrite)")
        return 1
    files = vault_inputs(keys_dir, ssh_dir, ssh_keys)
    missing = [str(p) for _, p in files if not p.is_file()]
    if missing:
        print("ERROR input file(s) missing: " + ", ".join(missing))
        return 1
    if not files:
        print(f"ERROR nothing to pack: no *.env in {keys_dir}, no id_* private keys in {ssh_dir}")
        return 1
    print(f"keys:   {keys_dir}")
    print(f"ssh:    {ssh_dir}")
    now = datetime.now()
    manifest = {"format": "brain-vault/1", "packed_at": _now_iso(), "by": GENERATED_BY,
                "host": platform.node(), "keys_dir": str(keys_dir), "ssh_dir": str(ssh_dir), "files": []}
    resolved: list = []
    unresolved: list = []
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, p in files:
            data = p.read_bytes()
            st = p.stat()
            manifest["files"].append({"path": name, "size": len(data), "sha256": _sha256(data),
                                      "mtime": datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds")})
            _tar_add_bytes(tar, name, data, st.st_mtime)
            print(f"add     {name} ({len(data)} bytes)")
        if with_memory:
            print(f"memory: {source}")
            if not source.is_dir():
                print(f"ERROR source memory directory not found: {source}")
                return 1
            resolved, unresolved, template_hits = collect_memory_values(repo, source)
            payload = {
                "format": "brain-memory-values/1",
                "packed_at": manifest["packed_at"],
                "source_dir": str(source),
                "fingerprint_rule": "rules/SECRETS.md",
                "values": [{"kind": e["kind"], "fingerprint": e["fingerprint"], "value": e["value"],
                            "sources": e["sources"], "value_from": e["value_from"]} for e in resolved],
                "unresolved": [{"kind": e["kind"], "fingerprint": e["fingerprint"], "sources": e["sources"],
                                "notes": e["notes"]} for e in unresolved],
            }
            data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            manifest["memory_values"] = {"source_dir": str(source), "resolved": len(resolved), "unresolved": len(unresolved)}
            _tar_add_bytes(tar, MEMORY_VALUES_NAME, data, now.timestamp())
            for e in resolved:
                print(f"value   {e['kind']} {e['fingerprint']}: from {e['value_from']}")
            for e in unresolved:
                print(f"UNRESOLVED {e['kind']} {e['fingerprint']}: " + "; ".join(e["notes"]))
            if template_hits:
                print("note    literal template marker skipped in: " + ", ".join(sorted(set(template_hits))))
        _tar_add_bytes(tar, MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
                       now.timestamp())
    plain = buf.getvalue()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    r = subprocess.run([age, "-R", str(recipients), "-o", str(out)], input=plain, capture_output=True)
    del plain, buf
    err = r.stderr.decode("utf-8", errors="replace").strip()
    if r.returncode != 0:
        print("ERROR age failed: " + err)
        return 1
    if err:
        print("age:    " + err)
    print(f"vault pack: {len(files)} files + {MEMORY_VALUES_NAME} ({len(resolved)} values, "
          f"{len(unresolved)} unresolved) -> {out} ({out.stat().st_size} bytes)")
    return 0


def _member_dest(name: str, to: Path | None) -> Path:
    parts = Path(name).parts
    if Path(name).is_absolute() or ".." in parts or not parts:
        raise ValueError(f"unsafe member name in tar: {name!r}")
    if to is not None:
        return to / Path(*parts)
    home = Path.home()
    if parts[0] == "keys" and len(parts) > 1:
        return home / ".keys" / Path(*parts[1:])
    if parts[0] == "ssh" and len(parts) > 1:
        return home / ".ssh" / Path(*parts[1:])
    return home / ".keys" / Path(*parts)


def cmd_vault_unpack(infile: Path, to: Path | None, identity: Path, age_dir: str | None, overwrite: bool) -> int:
    try:
        data = _vault_decrypt(infile, identity, age_dir)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"ERROR {e}")
        return 1
    written = skipped = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r") as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            try:
                dest = _member_dest(m.name, to)
            except ValueError as e:
                print(f"ERROR {e}")
                return 1
            if dest.exists() and not overwrite:
                print(f"skip    {m.name}: {dest} exists (use --overwrite)")
                skipped += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(tar.extractfile(m).read())
            os.utime(dest, (m.mtime, m.mtime))
            if os.name != "nt":
                os.chmod(dest, 0o600)
            print(f"write   {m.name} -> {dest}")
            written += 1
    del data
    print(f"vault unpack: {written} files written, {skipped} skipped, from {infile}")
    return 0


def cmd_vault_verify(repo: Path, infile: Path, identity: Path, keys_dir: Path, ssh_dir: Path, age_dir: str | None) -> int:
    try:
        data = _vault_decrypt(infile, identity, age_dir)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"ERROR {e}")
        return 1
    problems = compared = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r") as tar:
        members = {m.name: m for m in tar.getmembers() if m.isfile()}
        manifest = json.loads(tar.extractfile(members[MANIFEST_NAME]).read()) if MANIFEST_NAME in members else None
        listed = {f["path"]: f["sha256"] for f in manifest["files"]} if manifest else {}
        for name, m in sorted(members.items()):
            if name in (MANIFEST_NAME, MEMORY_VALUES_NAME):
                continue
            blob = tar.extractfile(m).read()
            parts = Path(name).parts
            if parts[0] == "keys" and len(parts) == 2:
                orig = keys_dir / parts[1]
            elif parts[0] == "ssh" and len(parts) == 2:
                orig = ssh_dir / parts[1]
            else:
                print(f"?       {name}: unexpected member")
                problems += 1
                continue
            if not orig.is_file():
                print(f"MISSING {name}: original {orig} not found")
                problems += 1
                continue
            digest = _sha256(blob)
            same = digest == _sha256(orig.read_bytes())
            compared += 1
            print(f"{'OK' if same else 'MISMATCH':8s} {name} <-> {orig} ({len(blob)} bytes)")
            if not same:
                problems += 1
            if listed and listed.get(name) != digest:
                print(f"MANIFEST {name}: sha256 differs from MANIFEST.json")
                problems += 1
        if MEMORY_VALUES_NAME in members:
            payload = json.loads(tar.extractfile(members[MEMORY_VALUES_NAME]).read())
            packed = {(e["kind"], e["fingerprint"]) for e in payload.get("values", [])}
            unres = {(e["kind"], e["fingerprint"]) for e in payload.get("unresolved", [])}
            markers = repo_markers(repo)
            bad_fp = [(e["kind"], e["fingerprint"]) for e in payload.get("values", [])
                      if fingerprint(e["value"]) != e["fingerprint"]]
            missing = sorted(markers - packed - unres)
            extra = sorted((packed | unres) - markers)
            print(f"values  {len(packed)} packed + {len(unres)} unresolved = {len(packed) + len(unres)}; "
                  f"distinct markers in memory/: {len(markers)}; fingerprint mismatches: {len(bad_fp)}")
            for kind, fpv in sorted(unres):
                print(f"unresolved {kind} {fpv}")
            for label, items in (("MISSING", missing), ("EXTRA", extra), ("BADFP", bad_fp)):
                for kind, fpv in items:
                    print(f"{label} {kind} {fpv}")
                problems += len(items)
        else:
            print(f"WARN    {MEMORY_VALUES_NAME} not in vault")
    del data
    print(f"vault verify: {compared} files compared, {problems} problems")
    return 1 if problems else 0


# -------------------------------------------------------------------- install

RULES_FILES = ("CLAUDE.md", "AGENTS.md")
ROLLBACK_HELP = (
    "回滚：删 junction 只能用  cmd /c rmdir \"{link}\"  或 PowerShell  (Get-Item \"{link}\").Delete()，\n"
    "      然后 Rename-Item \"{backup}\" memory。\n"
    "!! 对 junction 绝对不能 Remove-Item -Recurse / rm -rf：那会把仓库 memory/ 里的真文件删光。\n"
    "!! junction 之后，仓库里的 git checkout -- memory、git clean、git reset --hard 都直接改写本机正在用的记忆。"
)


def _is_junction(p: Path) -> bool:
    if hasattr(os.path, "isjunction"):
        return os.path.isjunction(p)
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return bool(getattr(st, "st_file_attributes", 0) & 0x400)   # FILE_ATTRIBUTE_REPARSE_POINT


def _link_target(p: Path) -> Path | None:
    try:
        t = os.readlink(p)
    except OSError:
        return None
    if t.startswith("\\\\?\\"):
        t = t[4:]
    return Path(t)


def _make_junction(link: Path, target: Path) -> None:
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(str(target), str(link), target_is_directory=True)


def _git_status(repo: Path) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True)
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def _same_file(a: Path, b: Path) -> bool:
    return a.is_file() and b.is_file() and _sha256(a.read_bytes()) == _sha256(b.read_bytes())


def cmd_install(repo: Path, cc_home: Path, project_dir: Path, date: str, dry_run: bool) -> int:
    problems = 0
    tag = "DRY  " if dry_run else ""
    print(f"repo:     {repo}")
    print(f"cc-home:  {cc_home}")
    print(f"project:  {project_dir}  (slug {cc_slug(project_dir)})")

    # 1. rules 与 settings：仓库里没有就 skip；本机没有就复制；两边不同就停下不写
    for rel, dst in [(f"rules/{n}", cc_home / n) for n in RULES_FILES] + [("env/settings.json", cc_home / "settings.json")]:
        src = repo / rel
        label = rel.split("/")[-1]
        if not src.is_file():
            print(f"skip     {label}: {rel} not in this repo")
        elif _same_file(src, dst):
            print(f"skip     {label}: ~/.claude/{label} identical to {rel}")
        elif not dst.exists():
            print(f"{tag}copy     {rel} -> {dst}")
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
        else:
            print(f"STOP     {label}: ~/.claude/{label} differs from {rel}; not overwritten"
                  + (" (merge not implemented in this version)" if label == "settings.json" else ""))
            problems += 1
    if problems:
        print(f"install: {problems} problems in step 1; junction not attempted")
        return 1

    # 2. memory junction
    target = (repo / "memory").resolve()
    link = default_cc_memory_dir(repo, cc_home, project_dir)
    backup = link.with_name(f"memory.pre-junction-{date}")
    if not target.is_dir():
        print(f"STOP     memory: {target} is not a directory")
        return 1
    if _is_junction(link) or link.is_symlink():
        got = _link_target(link)
        if got is not None and got.resolve() == target:
            print(f"skip     memory: {link} is already a junction to {target}")
        else:
            print(f"STOP     memory: {link} is a junction/symlink to {got}, not to {target}; left alone")
            return 1
    else:
        if link.exists() and not link.is_dir():
            print(f"STOP     memory: {link} exists and is not a directory")
            return 1
        if link.is_dir() and backup.exists():
            print(f"STOP     memory: backup {backup} already exists; remove or pass another --date")
            return 1
        before = _git_status(repo)
        if link.is_dir():
            n_src = sum(1 for _ in link.iterdir())
            print(f"{tag}rename   {link} -> {backup.name}  ({n_src} entries kept, not deleted)")
        else:
            print(f"{tag}mkdir    {link.parent}")
        print(f"{tag}junction {link} -> {target}")
        if not dry_run:
            link.parent.mkdir(parents=True, exist_ok=True)
            renamed = False
            try:
                if link.is_dir():
                    os.rename(link, backup)
                    renamed = True
                _make_junction(link, target)
            except OSError as e:
                print(f"ERROR    junction failed: {e}")
                if renamed and not link.exists():
                    os.rename(backup, link)
                    print(f"rollback {backup.name} renamed back to memory; nothing changed")
                return 1
            ok_j = _is_junction(link)
            got = _link_target(link)
            ok_t = got is not None and got.resolve() == target
            n_link = sum(1 for _ in link.iterdir())
            n_target = sum(1 for _ in target.iterdir())
            after = _git_status(repo)
            print(f"verify   is junction: {ok_j}; target: {got} ({'OK' if ok_t else 'WRONG'})")
            print(f"verify   entries via junction: {n_link}; in repo memory/: {n_target} ({'OK' if n_link == n_target else 'DIFF'})")
            print(f"verify   git status unchanged: {before == after}" + ("" if before == after else f"\n{after}"))
            if not (ok_j and ok_t and n_link == n_target and before == after):
                problems += 1
        print(ROLLBACK_HELP.format(link=link, backup=backup))

    # 2b. hooks: every writer passes the same gate; the push guard keeps the brain private
    problems += install_hooks(repo, dry_run)
    # 3. soul/dna.md
    dna_src, dna_dst = repo / "soul" / "dna.md", cc_home / ".dna.md"
    dna_status = None
    if dna_src.is_file():
        try:
            fm = load_frontmatter(dna_src)
            dna_status = fm.get("status") if isinstance(fm, dict) else None
        except (FrontmatterError, UnicodeDecodeError):
            dna_status = None
    if not dna_src.is_file():
        print("skip     .dna.md: soul/dna.md not in repo yet (see handoff blockers)")
    elif dna_status == "template":
        print("skip     .dna.md: soul/dna.md is still the template (status: template); nothing to copy")
    elif _same_file(dna_src, dna_dst):
        print("skip     .dna.md: identical")
    elif dna_dst.exists():
        print(f"STOP     .dna.md: {dna_dst} differs from soul/dna.md; not overwritten")
        problems += 1
    else:
        print(f"{tag}copy     soul/dna.md -> {dna_dst}")
        if not dry_run:
            dna_dst.write_bytes(dna_src.read_bytes())

    print(f"install: {problems} problems" + (" (dry run, nothing changed)" if dry_run else ""))
    return 1 if problems else 0


# ----------------------------------------------------------------- export-drive

INDEX_REL = "mirror/brain-index.md"
MIRROR_SUBDIRS = ("memory", "soul", "handoff")
MIRROR_KEEP = {"desktop.ini"}          # 同步客户端自己放的东西，不当多余文件删
TOKEN_ESTIMATE_DIVISOR = 2.5           # 中英混排的粗估：字节数 / 2.5 ≈ token 数
INDEX_TOKEN_WARN = 16000       # 3.8 的闸门，2026-11-03 从 8k 放宽到 16k（首测 12.6k，handoff 的 done 与 unverified 不裁）


def _mirror_plan(repo: Path) -> list[tuple[str, Path]]:
    """要一对一镜像的文件：索引单文件、memory/*.md、soul/ 下非隐藏文件、handoff/CURRENT.md。"""
    plan: list[tuple[str, Path]] = [("brain-index.md", repo / INDEX_REL)]
    plan += [(f"memory/{p.name}", p) for p in sorted((repo / "memory").glob("*.md"))]
    soul = repo / "soul"
    if soul.is_dir():
        plan += [(f"soul/{p.name}", p) for p in sorted(soul.iterdir()) if p.is_file() and not p.name.startswith(".")]
    cur = repo / "handoff" / "CURRENT.md"
    if cur.is_file():
        plan.append(("handoff/CURRENT.md", cur))
    return plan


def build_index(repo: Path) -> str:
    """mirror/brain-index.md 的正文：OKF 头 + BRAIN.md 全文 + soul/ 全文 + handoff/CURRENT.md 全文 + memory/MEMORY.md 全文。"""
    def section(title: str, text: str) -> str:
        return f"\n\n<!-- ===== {title} ===== -->\n\n{text.strip()}\n"

    def read_or(p: Path, missing: str) -> str:
        return read_text(p) if p.is_file() else missing

    head = ["---", "type: index", "name: brain-index",
            "description: Single-file index for mirrors (Drive, project knowledge): BRAIN.md, soul/, handoff/CURRENT.md, memory/MEMORY.md. Generated; do not edit.",
            "generated:", f"  by: {GENERATED_BY}", f"  at: {_now_iso()}", "---", "", "# brain-index", "",
            "Read in this order. Single memory files are mirrored next to this file under memory/; open one only when needed."]
    out = "\n".join(head)
    out += section("BRAIN.md", read_or(repo / "BRAIN.md", "(BRAIN.md missing)"))
    soul_files = [p for p in sorted((repo / "soul").glob("*")) if p.is_file() and not p.name.startswith(".")] if (repo / "soul").is_dir() else []
    if soul_files:
        for p in soul_files:
            out += section(f"soul/{p.name}", read_text(p))
    else:
        out += section("soul/", "soul/ 尚未写（soul/ not written yet）")
    out += section("handoff/CURRENT.md", read_or(repo / "handoff" / "CURRENT.md", "(handoff/CURRENT.md missing)"))
    out += section("memory/MEMORY.md", read_or(repo / "memory" / "MEMORY.md", "(memory/MEMORY.md missing)"))
    return out


def cmd_export_drive(repo: Path, to: Path | None, account: str | None) -> int:
    index_path = repo / INDEX_REL
    index_path.parent.mkdir(parents=True, exist_ok=True)
    text = build_index(repo)
    index_path.write_bytes(text.encode("utf-8"))
    size = index_path.stat().st_size
    est = round(size / TOKEN_ESTIMATE_DIVISOR)
    print(f"index   {INDEX_REL}: {size} bytes, ≈{est} tokens (estimate: bytes/{TOKEN_ESTIMATE_DIVISOR}; measure with a real counter before relying on it)")
    if est > INDEX_TOKEN_WARN:
        print(f"WARN    index estimate {est} > {INDEX_TOKEN_WARN} tokens; trim BRAIN.md / soul / MEMORY.md")

    hits, scan_warnings, scanned = secret_scan(repo)
    for w in scan_warnings:
        print(f"WARN    {w}")
    if hits:
        for h in hits:
            print(f"ERROR   {h}")
        print(f"export-drive: refused, {len(hits)} secret-like hits in {scanned} files; nothing copied")
        return 1
    print(f"scan    {scanned} files, 0 secret-like hits")

    plan = _mirror_plan(repo)
    if to is None:
        print("files to mirror (pass --to <dir> to copy):")
        for rel, _ in plan:
            print(f"        {rel}")
        print(f"export-drive: index written, {len(plan)} files listed, no --to given")
        return 0

    to.mkdir(parents=True, exist_ok=True)
    for sub in MIRROR_SUBDIRS:
        (to / sub).mkdir(exist_ok=True)
    copied = unchanged = deleted = 0
    wanted: set[str] = set()
    for rel, src in plan:
        wanted.add(rel)
        dst = to / Path(rel)
        data = src.read_bytes()
        if dst.is_file() and _sha256(dst.read_bytes()) == _sha256(data):
            unchanged += 1
            continue
        dst.write_bytes(data)
        _copy_mtime(src, dst)
        copied += 1
    for sub in MIRROR_SUBDIRS:
        for p in sorted((to / sub).iterdir()):
            if p.is_file() and not p.name.startswith(".") and p.name not in MIRROR_KEEP and f"{sub}/{p.name}" not in wanted:
                p.unlink()
                deleted += 1
                print(f"delete  {sub}/{p.name}")
    print(f"export-drive: copied={copied} unchanged={unchanged} deleted={deleted} -> {to} ({len(plan)} files)")

    drive_json = repo / "env" / "drive.json"
    info: dict = {}
    if drive_json.is_file():
        try:
            info = json.loads(drive_json.read_bytes().decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            info = {}
    info["target"] = str(to)
    info["account"] = account or info.get("account", "")
    info.setdefault("folder_id", "")
    info["files"] = len(plan)
    info["updated"] = _now_iso()
    drive_json.parent.mkdir(parents=True, exist_ok=True)
    drive_json.write_bytes((json.dumps(info, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"drive   env/drive.json updated (folder_id {'set' if info['folder_id'] else 'empty, fill in via the Drive connector'})")
    return 0


# --------------------------------------------------------------------- status

def _git(repo: Path, *args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError as e:
        return 127, str(e)
    return r.returncode, r.stdout.strip()


def _human_age(seconds: float) -> str:
    seconds = max(0, int(seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    return f"{d}d {h}h {m}m" if d else (f"{h}h {m}m" if h else f"{m}m")


def cmd_status(repo: Path, as_json: bool) -> int:
    """3.7：未提交改动数、未推送提交数（无远端就说无远端）、距上次提交多久、handoff 状态。有未提交或未推送退出码 1。"""
    rc, porcelain = _git(repo, "status", "--porcelain")
    if rc != 0:
        print(f"ERROR not a git repository: {repo}")
        return 1
    uncommitted = len([ln for ln in porcelain.splitlines() if ln.strip()])
    _, branch = _git(repo, "branch", "--show-current")
    _, remotes = _git(repo, "remote")
    remotes_list = remotes.split()
    rc_up, upstream = _git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if not remotes_list:
        unpushed: int | None = None
        push_note = "no remote"
    elif rc_up != 0:
        unpushed = None
        push_note = f"branch {branch} has no upstream"
    else:
        _, n = _git(repo, "rev-list", "--count", "@{u}..HEAD")
        unpushed = int(n or 0)
        push_note = f"vs {upstream}"
    _, ts = _git(repo, "log", "-1", "--format=%ct")
    _, last_subject = _git(repo, "log", "-1", "--format=%h %s")
    since_commit = _human_age(datetime.now().timestamp() - int(ts)) if ts else "n/a"
    _, total = _git(repo, "rev-list", "--count", "HEAD")
    handoff: dict = {}
    cur = repo / "handoff" / "CURRENT.md"
    if cur.is_file():
        try:
            fm = load_frontmatter(cur)
            if isinstance(fm, dict):
                handoff = {k: fm.get(k) for k in ("status", "opened", "claimed_by", "project")}
        except (FrontmatterError, UnicodeDecodeError) as e:
            handoff = {"error": str(e)}
    alert = uncommitted > 0 or unpushed is None or unpushed > 0
    report = {
        "repo": str(repo), "branch": branch, "commits": int(total or 0), "uncommitted": uncommitted,
        "unpushed": unpushed, "push_note": push_note, "last_commit": last_subject, "since_last_commit": since_commit,
        "handoff": handoff, "alert": alert, "checked_at": _now_iso(),
    }
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"repo:        {repo} ({branch}, {report['commits']} commits)")
        print(f"uncommitted: {uncommitted}")
        print(f"unpushed:    {unpushed if unpushed is not None else 'n/a'} ({push_note})")
        print(f"last commit: {last_subject}  ({since_commit} ago)")
        print(f"handoff:     status={handoff.get('status')} opened={handoff.get('opened')} claimed_by={handoff.get('claimed_by')}")
        print(f"status: {'ALERT' if alert else 'ok'} (uncommitted or unpushed work exists)" if alert else "status: ok")
    return 1 if alert else 0


# ----------------------------------------------------------------------- init

INIT_DIRS = ("soul", "memory", "handoff/archive", "rules", "skills", "env/scheduled-tasks",
             "vault", "projects", "mirror", "tools", "log", "pair")
INIT_KEEP = ("handoff/archive", "skills", "env/scheduled-tasks", "vault", "projects", "mirror", "log", "pair")

INIT_BRAIN_MD = """# BRAIN.md · read this and take over

This is the entry point of one person's agent brain. No runtime to load; read in this order.

0. Keys first: `python -X utf8 tools/brain.py ledger verify`. Every door this brain can open is one row in `env/ledger.env`. A key reaches your context only when a `next` item names its door and this machine holds the owner's grant (`brain.py unlock`; `brain.py grant` once per machine); top doors need the owner's code. Fresh clone: `brain.py init .` once.
1. `handoff/CURRENT.md`: what was done, what comes next, what is unverified. Restate it in two sentences, then start.
2. Then every file under `soul/`: how the owner works and where the lines are, and the agent's own soul in `soul/agent.md`. Follow it; do not recite it.
3. Then `memory/MEMORY.md`, one line per memory. Open a file under `memory/` only when the task needs it. Code and machines are read from themselves.
4. Reading or updating the hand-off is not doing the work. Judge each `next` item before acting: it crosses a boundary, stop; evidence is missing, ask; it is the owner's call, defer. A recap or hand-off request authorizes nothing.
5. New facts: if you can write this repo, edit the file, commit and push at once, one change per commit, each block with `by:`. If you cannot, hand the change back as `::PROGRESS{date|done|next|unverified}`, `::DECIDE{}`, `::LESSON{}` or `::EXCLUDE{}` blocks in one code fence, every key present, `none` where there is no material.
6. Update `handoff/CURRENT.md` at every milestone, not at session end. Log the owner's words verbatim in `log/`.
7. No key value in memory text: a key is a ledger row, encoded at rest in this private repository (reversible, not encryption), `{{DOOR}}` where it stood, sealed only when paired.
8. `::BLOCK{k:v|k:v}`, `T:` and `A:⇒` are declaration notation: read them literally; the quick card is `rules/GRAMMAR-CARD.md`.

<!-- Gate: about 400 tokens on the receiving model's tokenizer; measure before changing. -->
"""

INIT_GRAMMAR_CARD = """# iLang notation quick card (for reading a brain)

- `::NAME{k:v|k2:v2}` is one declaration block. NAME is upper case. Fields split on `|`, key and value on `:`.
- `::GENE{name|conf|scope}` is followed by `T:` lines (traits: I do it this way) and `A:x⇒y` lines (anti-patterns: x leads to y, don't).
- `conf:tentative|confirmed` confidence; `scope:global|project` scope; `when:condition` says when a block applies; it is not a release clause.
- `@NAME` in upper case is an entity: person, repo, machine, task.
- `::STATE{@X, k:v}` an entity's state now. `::FACT{key|value|conf}` a fact. `::PROGRESS{date|done|next|unverified}` progress.
  `::DECIDE{@X}{what|why|context}` a decision, X = who decided. `::LESSON{id|type|scope|conf}` plus the next line of prose = a lesson.
  `::BOUNDARY{never|scope}` a hard boundary: it always wins, no condition lifts it, never offer a way around it.
- How to read: take keys and values literally; no dictionary needed. An unknown block is a labelled note: read its body.
- Restating a hand-off: item by item, verbatim, keep the numbering, do not rephrase.
- Writing a block back: the whole block inside a triple-backtick fence; every key present, `none` for a key you have no material for; count the keys before sending.
- Never say DNA, gene or mutation to the user; say "I noted that" or "you told me last time".
"""

INIT_GRAMMAR_CARD_ZH = """# iLang 记法速查（读大脑用）

- `::NAME{k:v|k2:v2}` 一个声明块。NAME 大写。字段用 | 分隔，键值用 : 分隔。
- `::GENE{名|conf|scope}` 后跟 `T:` 行（特征，「我这样做」）和 `A:x⇒y` 行（反模式，「x 会导致 y，别做」）。
- `conf:tentative|confirmed` 置信度；`scope:global|project` 作用域；`when:条件` 说明何时生效，不是解除指引。
- `@NAME` 大写是实体：人、仓库、机器、任务。
- `::STATE{@X, k:v}` 实体此刻状态。`::FACT{key|value|conf}` 事实。`::PROGRESS{date|done|next|unverified}` 进度。
  `::DECIDE{@X}{what|why|context}` 决定，X＝决定者。`::LESSON{id|type|scope|conf}` 加下一行正文＝教训。
  `::BOUNDARY{never|scope}` 硬边界：永远优先，不随条件变化解除，不给绕过方案。
- 读法：按字面理解键值，不需要字典。不认识的块当带标签的笔记读正文。
- 复述交接单：逐条原文、保留编号、不改写。
- 回写块：整块放三反引号围栏里；键一个不能少，没素材的键写 `无`；发出前数一遍键。
- 不对用户说 DNA、gene、mutation 这些词；说「我记下来了」「上次你说过」。
"""

INIT_SOUL_MD = """---
type: profile
name: soul
description: Behavioral profile. Your agent writes it from conversation; you can edit it any time.
status: template
---
# Soul

<!-- Auto-generated by your agent during onboarding. Do not fill this in by hand. -->
<!-- Just start a conversation; it will ask you a few questions, then set status: stable above. -->
<!-- You can edit it any time. It's your file. -->
"""

INIT_DNA_MD = """---
type: profile
name: dna
description: Working-style and judgement profile written by Imprint. Optional. brain.py install copies it to ~/.claude/.dna.md.
status: template
---
# DNA

<!-- Optional. If you use Imprint (github.com/ilang-ai/Imprint), keep its .dna.md content here; `python -X utf8 tools/brain.py install` copies it to ~/.claude/.dna.md. -->
<!-- Without Imprint, leave this file as it is. -->
"""

INIT_AGENT_SOUL = """---
type: profile
name: agent-soul
description: The agent's own soul, separate from the owner's. Part one is a persona the owner gave it; part two is what it learned working with this owner.
status: template
soul_id: none
soul_version: none
soul_sha256: none
updated: none
---
# agent.md · the agent's own soul

`soul/soul.md` answers "who is the owner". This file answers "who is the agent that works for them". It travels with the brain across models, accounts and machines; a new model reads it after the hand-off and before it starts.

## Part one · given soul

<!-- A persona the owner hands the agent, kept whole and verbatim (an iLang SOUL block, for example). Replace the whole block when the owner gives a new version and update soul_id, soul_version and soul_sha256 above. Empty until the owner gives one. -->

## Part two · grown with this owner

<!-- Written by the agent at milestones, in the canon notation: a LESSON block plus one line of prose, or a GENE block with T: and A: lines. First time tentative; confirmed after three. No secrets. The owner can read and edit it at any time. -->
"""

INIT_MEMORY_INDEX = """# Memory Index

<!-- One line per file in memory/: `- [Title](file.md) — one-line hook`. -->
<!-- Your agent appends a line here every time it adds a memory file. Claude Code reads this index natively. -->
<!-- Keep it an index: no memory content in this file. -->
"""

INIT_ENV_README = """# env/ — the ledger and the machine environment

This directory is where the derivation starts. It lives in a **private** repository; `brain.py check` does not scan it for secret-like text, and `tools/hooks/pre-push` refuses to push it to a public remote.

| File | Content |
|---|---|
| `ledger.env` | the authorization ledger: one `::STATE{@name, door, kind, ref or value, verify, last_verified, recover, scope, top, why}` row per door; see [docs/LEDGER.md](../docs/LEDGER.md) |
| `pepper` | 32 random bytes (hex), written by `brain.py init`, committed; the encoded rows of `keys.env` are reversible with it and this tool, and with nothing else. Not encryption: a holder of the repository reads everything; it keeps keys out of grep, screenshots, model context and pastes |
| `keys.env` | `KEY=enc1:...` rows the ledger points at with `ref:KEY`, encoded at rest; written by `brain.py ledger add --value`, `ledger harvest`, `ledger encode`; `ledger decode` prints them plain for the owner |
| `otp.json` | hashes of one-time codes the owner issued for top doors; expires; ignored by git |
| `ssh/` | SSH private keys `migrate-2to3` brought over from a 2.1 vault, one ledger row each |
| `settings.json` | your agent CLI settings (Claude Code reads `~/.claude/settings.json`) |
| `mcp.json` | MCP servers; a key field may say `${VAULT:name}` and is filled from the ledger at install time |
| `scheduled-tasks/` | scheduled task definitions, one folder per task |
| `ssh_config.template` | host aliases and jump hosts |
| `install.ps1`, `install.sh` | new-machine checklist as a script: git, python, your agent CLI, then `brain.py install` and `brain.py ledger verify all` |

Rule: a key reaches a model's context only when a `next` item names its door (`brain.py unlock`) and this machine holds the owner's grant (`brain.py grant <DOOR>` or `--all`, git config, never in the repository; top doors keep the one-time code), never by reading this directory into the conversation. The pasted brain (`brain.py paste`) carries the ledger without values unless the owner says `--with-values`.
"""

INIT_GITIGNORE = "__pycache__/\n*.pyc\n*.tmp\nenv/otp.json\n"

HANDOFF_TEMPLATE = """---
type: handoff
name: handoff-current
description: The one active hand-off note. A session that reads status: open claims it first.
project: {project}
opened: {opened}
agent: {agent}
status: open
claimed_by: []
generated:
  by: {by}
  at: {opened}
---

::STATE{{@OWNER, kind:person, role:owner, alias:the I in this chat}}
::STATE{{@TASK, name:{task}, repo:{repo}, branch:{branch}, cwd:{cwd}, owner:@OWNER}}
::PROGRESS{{date:{date}|done:§<section> <finished, listed by milestone>|next:<the first thing to do next>|unverified:<claimed done but not tested>}}
::FACT{{key:where_files_are|value:<paths of deliverables, scripts, logs>|conf:confirmed}}
::FACT{{key:blockers|value:<what is stuck and who decides>|conf:confirmed}}
::DECIDE{{@OWNER}}{{what:<what was settled this round>|why:<why, or none>|context:<the block above it rests on, or none>}}
::LESSON{{id:<key>|type:<kind>|scope:project|conf:tentative}}
<the lesson in one line. Source: where it came from>

## Claim and close

- A new session that reads `status: open`: append yourself to `claimed_by`, set `status: claimed`, commit `handoff: claim by <agent>`.
- When the task is done: set `status: closed`, move the whole file to `handoff/archive/YYYY-MM-DD-<slug>.md`, open a fresh CURRENT.md; one commit for both steps.
- Two CURRENT.md files collide: the newer `opened` stays, the older goes to archive.
- When to write: a deploy succeeded, a config changed, a conclusion was reached, and any moment before the session might be cut off. Do not wait for the session to end.
"""


def _git_branch(repo: Path) -> str:
    rc, out = _git(repo, "branch", "--show-current")
    return out if rc == 0 and out else "main"


def render_handoff(repo: Path, project: str, task: str, agent: str) -> str:
    now = _now_iso()
    return HANDOFF_TEMPLATE.format(project=project, opened=now, date=now[:10], agent=agent, by=GENERATED_BY, task=task,
                                   repo=repo.name, branch=_git_branch(repo), cwd=str(repo))


def cmd_init(repo: Path, agent: str, no_git: bool) -> int:
    """工程书 3.2 的骨架：目录、BRAIN.md、index.md、log.md、soul/ 与 memory/ 与 handoff/ 模板、语法卡、
    本工具自身复制到 tools/。已存在的文件一律不覆盖。没有 .git 就 git init（分支 main）。"""
    repo.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    skipped: list[str] = []

    def put(rel: str, text: str) -> None:
        p = repo / rel
        if p.exists():
            skipped.append(rel)
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
        created.append(rel)

    for d in INIT_DIRS:
        (repo / d).mkdir(parents=True, exist_ok=True)
    for d in INIT_KEEP:
        put(f"{d}/.gitkeep", "")
    today = f"{datetime.now():%Y-%m-%d}"
    put("BRAIN.md", INIT_BRAIN_MD)
    put("index.md", '---\nokf_version: "0.2"\n---\n')
    put("log.md", "# Changelog\n\nOne `## YYYY-MM-DD` section per day, newest first, prose bullets (OKF v0.2 reserved file). "
                  "Record changes to the layout, rules and tools here. Memories go to `memory/`, progress goes to `handoff/CURRENT.md`.\n\n"
                  f"## {today}\n\n- Repository skeleton created by brain.py init.\n")
    put("memory/MEMORY.md", INIT_MEMORY_INDEX)
    put("handoff/CURRENT.md", render_handoff(repo, "global", "<one-line task>", agent))
    put("rules/GRAMMAR-CARD.md", INIT_GRAMMAR_CARD)
    put("rules/GRAMMAR-CARD.zh.md", INIT_GRAMMAR_CARD_ZH)
    put("soul/soul.md", INIT_SOUL_MD)
    put("soul/dna.md", INIT_DNA_MD)
    put("soul/agent.md", INIT_AGENT_SOUL)
    put("env/README.md", INIT_ENV_README)
    put("env/ledger.env", LEDGER_HEADER)
    put(".gitignore", INIT_GITIGNORE)
    if write_pepper(repo):
        created.append(PEPPER_REL)
    me = Path(__file__).resolve()
    tool = repo / "tools" / "brain.py"
    if not tool.exists():
        tool.write_bytes(me.read_bytes())
        created.append("tools/brain.py")
    elif tool.resolve() != me:
        skipped.append("tools/brain.py")

    git_note = "skipped (--no-git)"
    if not no_git:
        if (repo / ".git").exists():
            git_note = "already a repository"
        else:
            rc, out = _git(repo, "init", "-q", "-b", "main")
            if rc != 0:
                rc, out = _git(repo, "init", "-q")
                _git(repo, "symbolic-ref", "HEAD", "refs/heads/main")
            git_note = "git init (branch main)" if rc == 0 else f"git init failed: {out}"
    install_hooks(repo)
    for rel in created:
        print(f"create  {rel}")
    for rel in skipped:
        print(f"skip    {rel}: exists")
    print(f"git:    {git_note}")
    print(f"init: {len(created)} created, {len(skipped)} kept -> {repo}")
    print("next:   python -X utf8 tools/brain.py check ; then git add -A && git commit -m 'init: brain skeleton'")
    return 0


# ----------------------------------------------------------------------- sync

def cmd_sync(repo: Path, cc_home: Path, project_dir: Path, direction: str, dry_run: bool) -> int:
    """junction 不可用时的兜底：仓库 memory/ 与 ~/.claude/projects/<slug>/memory 双向复制。
    只在一边的复制到另一边；两边都有且不同的，mtime 新的覆盖旧的；从不删除。"""
    target = (repo / "memory").resolve()
    link = default_cc_memory_dir(repo, cc_home, project_dir)
    if _is_junction(link) or link.is_symlink():
        got = _link_target(link)
        if got is not None and got.resolve() == target:
            print(f"skip    {link} is a junction to {target}; nothing to sync")
            return 0
        print(f"STOP    {link} is a junction/symlink to {got}, not to {target}")
        return 1
    if not target.is_dir():
        print(f"STOP    {target} missing")
        return 1
    tag = "DRY  " if dry_run else ""
    if not link.is_dir():
        if direction == "from-cc":
            print(f"STOP    {link} missing and direction is from-cc")
            return 1
        print(f"{tag}mkdir    {link}")
        if not dry_run:
            link.mkdir(parents=True, exist_ok=True)
    names = sorted({p.name for p in target.iterdir() if p.is_file() and not p.name.startswith(".")}
                   | ({p.name for p in link.iterdir() if p.is_file() and not p.name.startswith(".")} if link.is_dir() else set()))
    to_cc = from_cc = unchanged = held = 0

    def copy(src: Path, dst: Path, label: str) -> None:
        print(f"{tag}{label:9s}{src.name}")
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            _copy_mtime(src, dst)

    for name in names:
        a, b = target / name, link / name
        if a.is_file() and not b.is_file():
            if direction in ("both", "to-cc"):
                copy(a, b, "to-cc")
                to_cc += 1
            else:
                held += 1
        elif b.is_file() and not a.is_file():
            if direction in ("both", "from-cc"):
                copy(b, a, "from-cc")
                from_cc += 1
            else:
                held += 1
        else:
            da, db = a.read_bytes(), b.read_bytes()
            if da == db:
                unchanged += 1
                continue
            newer_is_repo = a.stat().st_mtime >= b.stat().st_mtime
            if newer_is_repo and direction in ("both", "to-cc"):
                copy(a, b, "to-cc")
                to_cc += 1
            elif not newer_is_repo and direction in ("both", "from-cc"):
                copy(b, a, "from-cc")
                from_cc += 1
            else:
                held += 1
    print(f"sync: to-cc={to_cc} from-cc={from_cc} unchanged={unchanged} held={held} ({direction}"
          + (", dry run" if dry_run else "") + f") {target} <-> {link}")
    return 0


# -------------------------------------------------------------------- handoff

PROGRESS_RE = re.compile(r"^::PROGRESS\{(.*)\}\s*$")


def _handoff_path(repo: Path) -> Path:
    return repo / "handoff" / "CURRENT.md"


def _fm_region(lines: list[str]) -> int:
    """返回闭合 --- 的行号（text.split('\\n') 计），没有 frontmatter 抛 FrontmatterError。"""
    if not lines or lines[0].rstrip("\r") != FENCE:
        raise FrontmatterError("no frontmatter")
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r") == FENCE:
            return i
    raise FrontmatterError("frontmatter not closed")


def _set_fm(lines: list[str], close_idx: int, key: str, value: str) -> int:
    """把顶层 key 的那一行改成 'key: value'，连带删掉它下面的缩进子行；没有就插在闭合 --- 前。返回新的闭合行号。"""
    cr = "\r" if lines[0].endswith("\r") else ""
    for i in range(1, close_idx):
        if re.match(rf"^{re.escape(key)}\s*:", lines[i]):
            j = i + 1
            while j < close_idx and (lines[j].startswith(" ") or lines[j].startswith("\t")):
                j += 1
            lines[i:j] = [f"{key}: {value}{cr}"]
            return close_idx - (j - i - 1)
    lines.insert(close_idx, f"{key}: {value}{cr}")
    return close_idx + 1


def _set_generated_at(lines: list[str], close_idx: int) -> int:
    cr = "\r" if lines[0].endswith("\r") else ""
    for i in range(1, close_idx):
        if re.match(r"^generated\s*:", lines[i]):
            for j in range(i + 1, close_idx):
                if re.match(r"^\s+at\s*:", lines[j]):
                    lines[j] = f"  at: {_now_iso()}{cr}"
                    return close_idx
                if not (lines[j].startswith(" ") or lines[j].startswith("\t")):
                    break
            lines.insert(i + 1, f"  at: {_now_iso()}{cr}")
            return close_idx + 1
    block = ["generated:" + cr, f"  by: {GENERATED_BY}{cr}", f"  at: {_now_iso()}{cr}"]
    lines[close_idx:close_idx] = block
    return close_idx + len(block)


def _progress_parts(text: str) -> dict[str, str]:
    for line in text.split("\n"):
        m = PROGRESS_RE.match(line.rstrip("\r"))
        if m:
            body = m.group(1)
            parts: dict[str, str] = {}
            positions: list[tuple[int, str, int]] = []
            for k in ("date", "done", "next", "unverified"):
                if body.startswith(k + ":"):
                    positions.append((0, k, len(k) + 1))
                    continue
                idx = body.find("|" + k + ":")
                if idx >= 0:
                    positions.append((idx, k, len(k) + 2))
            positions.sort()
            for n, (idx, k, plen) in enumerate(positions):
                end = positions[n + 1][0] if n + 1 < len(positions) else len(body)
                parts[k] = body[idx + plen:end].strip()
            return parts
    return {}


def _handoff_commit(repo: Path, message: str, no_commit: bool) -> int:
    if no_commit:
        print(f"nocommit {message}")
        return 0
    rc, out = _git(repo, "add", "-A", "handoff")
    if rc != 0:
        print(f"ERROR git add failed: {out}")
        return 1
    rc, out = _git(repo, "commit", "-q", "-m", message)
    if rc != 0:
        print(f"ERROR git commit failed: {out}")
        return 1
    _, h = _git(repo, "rev-parse", "--short", "HEAD")
    print(f"commit  {h} {message}")
    return 0


def _slugify(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "-", s.strip(), flags=re.UNICODE).strip("-")
    return s[:60] or "task"


def cmd_handoff(repo: Path, action: str, agent: str, project: str | None, task: str | None,
                slug: str | None, no_commit: bool) -> int:
    cur = _handoff_path(repo)
    if action == "open":
        if cur.is_file():
            try:
                fm = load_frontmatter(cur)
                st = fm.get("status") if isinstance(fm, dict) else None
            except (FrontmatterError, UnicodeDecodeError):
                st = None
            if st in ("open", "claimed"):
                print(f"STOP    {cur} is already {st}; close it first")
                return 1
            if st != "closed":
                print(f"STOP    {cur} exists with status {st!r}; close or remove it first")
                return 1
        cur.parent.mkdir(parents=True, exist_ok=True)
        proj = project or "global"
        cur.write_bytes(render_handoff(repo, proj, task or "<one-line task>", agent).encode("utf-8"))
        print(f"open    {cur} (project {proj}, agent {agent})")
        return _handoff_commit(repo, f"handoff: open {proj}", no_commit)

    if not cur.is_file():
        print(f"STOP    {cur} missing (handoff open first)")
        return 1
    text = read_text(cur)
    lines = text.split("\n")
    try:
        close_idx = _fm_region(lines)
        fm = parse_yaml([ln.rstrip("\r") for ln in lines[1:close_idx]])
    except FrontmatterError as e:
        print(f"ERROR   {cur}: {e}")
        return 1
    status = fm.get("status") if isinstance(fm, dict) else None
    claimed = fm.get("claimed_by") if isinstance(fm, dict) else None
    claimed = list(claimed) if isinstance(claimed, list) else ([claimed] if claimed else [])

    if action == "show":
        print(f"file:       {cur}")
        print(f"project:    {fm.get('project')}")
        print(f"status:     {status}   opened: {fm.get('opened')}   claimed_by: {claimed}")
        parts = _progress_parts(text)
        for k in ("date", "done", "next", "unverified"):
            print(f"{k:<11} {parts.get(k, '(missing)')}")
        return 0

    if status not in ("open", "claimed"):
        print(f"STOP    status is {status!r}; only open or claimed hand-offs can be {action}ed")
        return 1

    if action == "claim":
        if agent not in claimed:
            claimed.append(agent)
        close_idx = _set_fm(lines, close_idx, "claimed_by", "[" + ", ".join(claimed) + "]")
        close_idx = _set_fm(lines, close_idx, "status", "claimed")
        close_idx = _set_generated_at(lines, close_idx)
        cur.write_bytes("\n".join(lines).encode("utf-8"))
        print(f"claim   {cur}: claimed_by {claimed}")
        return _handoff_commit(repo, f"handoff: claim by {agent}", no_commit)

    if action == "close":
        close_idx = _set_fm(lines, close_idx, "status", "closed")
        close_idx = _set_generated_at(lines, close_idx)
        archive_dir = cur.parent / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        name = f"{datetime.now():%Y-%m-%d}-{_slugify(slug or str(fm.get('project') or 'task'))}.md"
        dest = archive_dir / name
        if dest.exists():
            print(f"STOP    {dest} exists; pass another --slug")
            return 1
        dest.write_bytes("\n".join(lines).encode("utf-8"))
        proj = project or str(fm.get("project") or "global")
        cur.write_bytes(render_handoff(repo, proj, task or "<one-line task>", agent).encode("utf-8"))
        print(f"close   -> handoff/archive/{name}; fresh CURRENT.md (project {proj})")
        return _handoff_commit(repo, f"handoff: close {name[:-3]}; fresh CURRENT.md", no_commit)

    print(f"ERROR   unknown handoff action {action!r}")
    return 2


# ----------------------------------------------------------------------- paste

PASTE_OPENING = {
    "zh": "下面是一张记法速查卡和一份用这种记法写的工作交接单。请先读卡，再读交接单，然后只回一句「读完了」。后面我会提问。记忆里缺的东西不要靠回忆补：列出候选、每个候选被什么否掉、剩下什么，用 ::EXCLUDE{编号|candidates:…|out:候选(否掉它的常数);…|left:…|conf:tentative} 块交回来。",
    "en": "Below are a notation quick card and a hand-off note written in that notation. Read the card first, then the hand-off, then reply with just: done reading. I will ask questions after that. A gap in the memory is not filled from recall: list the candidates, what refuted each one, and what remains, and hand it back as an ::EXCLUDE{id|candidates:…|out:candidate(the constant that refutes it);…|left:…|conf:tentative} block.",
}


def _has_cjk(s: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in s)


def handoff_blocks(text: str) -> str:
    """CURRENT.md 去掉 frontmatter，取第一个 '## ' 标题之前的声明块区。"""
    lines = text.split("\n")
    try:
        body = lines[_fm_region(lines) + 1:]
    except FrontmatterError:
        body = lines
    out: list[str] = []
    for ln in body:
        if ln.startswith("## "):
            break
        out.append(ln.rstrip("\r"))
    return "\n".join(out).strip("\n")


def _secret_hits_in_text(text: str) -> list[str]:
    hits: list[str] = []
    for n, line in enumerate(text.splitlines(), 1):
        for label, rx in SECRET_PATTERNS:
            if rx.search(line):
                hits.append(f"line {n}: secret-like token ({label})")
    return hits


def _cjk_ratio(s: str) -> float:
    letters = [ch for ch in s if ch.isalnum() or "\u4e00" <= ch <= "\u9fff"]
    if not letters:
        return 0.0
    return sum(1 for ch in letters if "\u4e00" <= ch <= "\u9fff") / len(letters)


def pick_card(repo: Path, lang: str) -> Path:
    """按语言挑速查卡：rules/GRAMMAR-CARD.<lang>.md 优先；其次 rules/GRAMMAR-CARD.md 且语言相符；
    再退到 rules/ 下任何一张语言相符的卡；都没有就用 rules/GRAMMAR-CARD.md。"""
    rules = repo / "rules"
    want = rules / f"GRAMMAR-CARD.{lang}.md"
    if want.is_file():
        return want
    default = rules / "GRAMMAR-CARD.md"
    if default.is_file() and (lang == "zh") == _has_cjk(read_text(default).split("\n", 1)[0]):
        return default
    for p in sorted(rules.glob("GRAMMAR-CARD*.md")):
        if (lang == "zh") == _has_cjk(read_text(p).split("\n", 1)[0]):
            return p
    if default.is_file():
        return default
    raise FileNotFoundError(f"{default} missing")


def build_paste(repo: Path, lang: str, with_values: bool = False) -> tuple[str, Path]:
    """开场句 + 速查卡 + --- + 交接单声明块。lang=auto 按交接单的语言挑卡（中文占比 >= 0.2 取 zh），
    开场句跟实际用的那张卡走。返回 (消息, 卡的路径)。"""
    cur = _handoff_path(repo)
    if not cur.is_file():
        raise FileNotFoundError(f"{cur} missing (handoff open first)")
    blocks = handoff_blocks(read_text(cur))
    if lang == "auto":
        lang = "zh" if _cjk_ratio(blocks) >= 0.2 else "en"
    card_path = pick_card(repo, lang)
    card = read_text(card_path).strip("\n")
    opening = PASTE_OPENING["zh" if _has_cjk(card.split("\n", 1)[0]) else "en"]
    ledger = ledger_section(repo, with_values)
    tail = f"\n\n---\n\n{ledger}" if ledger else ""
    return f"{opening}\n\n{card}\n\n---\n\n{blocks}{tail}\n", card_path


def cmd_paste(repo: Path, out: Path | None, lang: str, with_values: bool = False) -> int:
    try:
        text, card_path = build_paste(repo, lang, with_values)
    except FileNotFoundError as e:
        print(f"ERROR   {e}", file=sys.stderr)
        return 1
    masked = 0
    if not with_values:
        text, masked = mask_key_values(text)
    data = text.encode("utf-8")
    note = ("ledger VALUES INCLUDED, nothing masked: this message leaves the private repository, hand it only where the work needs the keys"
            if with_values else f"{masked} key-shaped string(s) masked as {{{{UNHARVESTED ...}}}}; the ledger rows carry no values")
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print(f"paste   {out}: {len(data)} bytes, card {card_path.name}, {note}; send it as one message (docs/PASTE.md)", file=sys.stderr)
    else:
        sys.stdout.write(text)
        sys.stdout.flush()
        print(f"paste   {len(data)} bytes, card {card_path.name}, {note}; send it as one message (docs/PASTE.md)", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- handoff review

BLOCK_RE = re.compile(r"^::([A-Z][A-Z0-9_]*)\s*\{([^{}]*)\}\s*(?:\{(.*)\})?\s*$")
REQUIRED_KEYS = {
    "FACT": ("key", "value", "conf"),
    "DECIDE": ("what", "why", "context"),
    "LESSON": ("id", "type", "scope", "conf"),
    "PROGRESS": ("date", "done", "next", "unverified"),
    "BOUNDARY": ("never", "scope"),
}
ITEM_SPLIT_RE = re.compile(r"\s*[；;]\s*")


def _fields(s: str, sep: str) -> tuple[list[str], dict[str, str]]:
    """'k:v|k2:v2' 或 '@X, k:v, k2:v2' → (无键的位置项, {k: v})。"""
    if sep == ",":
        parts = re.split(r",\s*(?=[A-Za-z_][A-Za-z0-9_]*\s*:)", s)
    else:
        parts = s.split("|")
    positional: list[str] = []
    kv: dict[str, str] = {}
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:(.*)$", part, re.S)
        if m:
            kv[m.group(1)] = m.group(2).strip()
        else:
            positional.append(part)
    return positional, kv


def parse_blocks(text: str) -> list[dict]:
    """逐行识别 ::NAME{...} 块；GENE 收后续 T:/A: 行，LESSON 收紧跟的一行正文。围栏行跳过。"""
    blocks: list[dict] = []
    cur: dict | None = None
    for n, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r").strip()
        if line.startswith("```"):
            continue
        m = BLOCK_RE.match(line)
        if m:
            kind, head, extra = m.group(1), m.group(2).strip(), m.group(3)
            b: dict = {"kind": kind, "head": head, "extra": extra, "body": [], "raw": line, "line": n}
            if kind == "STATE":
                pos, kv = _fields(head, ",")
            elif kind == "DECIDE":
                pos, kv = [head], _fields(extra or "", "|")[1]
            else:
                pos, kv = _fields(head, "|")
            b["entity"] = pos[0] if pos else ""
            b["kv"] = kv
            blocks.append(b)
            cur = b
            continue
        if not line:
            cur = None
            continue
        if cur is not None:
            if cur["kind"] == "GENE" and (line.startswith("T:") or line.startswith("A:")):
                cur["body"].append(line)
                continue
            if cur["kind"] == "LESSON" and not cur["body"] and not line.startswith("#"):
                cur["body"].append(line)
                continue
        cur = None
    return blocks


def _block_id(b: dict) -> tuple:
    k = b["kind"]
    kv = b.get("kv", {})
    if k in ("STATE", "GENE"):
        return (k, b.get("entity", ""))
    if k == "FACT":
        return (k, kv.get("key", ""))
    if k == "LESSON":
        return (k, kv.get("id", ""))
    if k == "DECIDE":
        return (k, b.get("entity", ""), kv.get("what", ""))
    if k == "BOUNDARY":
        return (k, kv.get("never", ""))
    if k == "PROGRESS":
        return (k,)
    if k == "EXCLUDE":
        return (k, b.get("entity", ""))
    return (k, b["raw"])


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _items(s: str) -> list[str]:
    return [i for i in (x.strip() for x in ITEM_SPLIT_RE.split(s or "")) if i and i not in ("none", "无")]


def _touches_boundary(item: str, never: str) -> bool:
    a, b = _norm(item).lower(), _norm(never).lower()
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    toks_a = set(re.findall(r"[a-z][a-z0-9_\-]{4,}", a))
    toks_b = set(re.findall(r"[a-z][a-z0-9_\-]{4,}", b))
    if toks_a & toks_b:
        return True
    return _bigram_overlap(a, b) >= 0.5


def overlay_candidate(base_text: str, cand_text: str) -> tuple[str, int, int, int]:
    """把候选里的块按标识叠到基线文本上：同标识的块（含 GENE 的 T:/A: 行、LESSON 的正文行）整段替换，
    候选独有的块追加在基线最后一个块之后，基线其余内容（frontmatter、说明、未被替换的块）原样保留。
    返回 (拼好的文本, 替换块数, 新增块数, 原样带入的块数)。换行风格跟基线。"""
    nl = "\r\n" if "\r\n" in base_text else "\n"
    base_lines = base_text.replace("\r\n", "\n").split("\n")
    cand_lines = cand_text.replace("\r\n", "\n").split("\n")
    base_blocks = parse_blocks("\n".join(base_lines))
    cand_blocks = parse_blocks("\n".join(cand_lines))
    cand_by: dict[tuple, dict] = {}
    for b in cand_blocks:
        cand_by.setdefault(_block_id(b), b)

    def span(b: dict) -> tuple[int, int]:
        start = b["line"] - 1
        return start, start + 1 + len(b["body"])

    used: set[tuple] = set()
    plan: dict[int, tuple[int, list[str] | None]] = {}
    for b in base_blocks:
        s, e = span(b)
        bid = _block_id(b)
        c = cand_by.get(bid)
        if c is None or bid in used:
            plan[s] = (e, None)
            continue
        used.add(bid)
        cs, ce = span(c)
        plan[s] = (e, cand_lines[cs:ce])
    extra: list[str] = []
    seen: set[tuple] = set()
    for c in cand_blocks:
        cid = _block_id(c)
        if cid in used or cid in seen:
            continue
        seen.add(cid)
        cs, ce = span(c)
        extra.extend(cand_lines[cs:ce])
    last_end = max((e for e, _ in plan.values()), default=len(base_lines))
    out: list[str] = []
    i = 0
    while i < len(base_lines):
        if i in plan:
            e, new = plan[i]
            out.extend(new if new is not None else base_lines[i:e])
            i = e
            if i == last_end and extra:
                out.extend(extra)
                extra = []
            continue
        out.append(base_lines[i])
        i += 1
    if extra:
        out.extend(extra)
    return nl.join(out), len(used), len(seen), len(base_blocks) - len(used)


def cmd_handoff_review(repo: Path, candidate: Path, baseline: Path | None, validator: Path | None,
                       overlay: bool = False, out: Path | None = None) -> int:
    base_path = baseline or _handoff_path(repo)
    if not base_path.is_file():
        print(f"STOP    baseline {base_path} missing; a candidate cannot be its own baseline")
        return 1
    if not candidate.is_file():
        print(f"ERROR   candidate {candidate} missing")
        return 1
    if candidate.resolve() == base_path.resolve():
        print("STOP    candidate and baseline are the same file")
        return 1
    base_text = read_text(base_path)
    cand_text = read_text(candidate)
    reviewed_path = candidate
    if overlay:
        cand_text, n_rep, n_add, n_keep = overlay_candidate(base_text, cand_text)
        reviewed_path = out if out is not None else Path(tempfile.gettempdir()) / f"brain-review-overlay-{os.getpid()}.md"
        reviewed_path.write_bytes(cand_text.encode("utf-8"))
        print(f"overlay  {n_rep} block(s) replaced from the candidate, {n_add} added, {n_keep} carried from the baseline -> {reviewed_path}")
    rejects: list[str] = []
    flags: list[str] = []
    transitions: list[str] = []
    adds: list[str] = []

    for h in _secret_hits_in_text(cand_text):
        rejects.append(f"candidate {h}")

    base = parse_blocks(base_text)
    cand = parse_blocks(cand_text)
    base_by: dict[tuple, dict] = {}
    for b in base:
        base_by.setdefault(_block_id(b), b)
    cand_by: dict[tuple, dict] = {}
    for b in cand:
        cand_by.setdefault(_block_id(b), b)
    if not cand:
        rejects.append("candidate has no declaration blocks")

    # 1. 边界：原样保留，不挂 when:
    base_bounds = {_norm(b["raw"]) for b in base if b["kind"] == "BOUNDARY"}
    cand_bounds = {_norm(b["raw"]) for b in cand if b["kind"] == "BOUNDARY"}
    for raw in sorted(base_bounds - cand_bounds):
        rejects.append(f"boundary deleted or rewritten: {raw}")
    for b in cand:
        if b["kind"] == "BOUNDARY" and "when" in b["kv"]:
            rejects.append(f"boundary carries when: (line {b['line']}): {b['raw']}")

    # 2. 必填键、空值
    for b in cand:
        req = REQUIRED_KEYS.get(b["kind"])
        if req:
            for k in req:
                if k not in b["kv"]:
                    rejects.append(f"{b['kind']} line {b['line']}: key {k} missing")
                elif b["kv"][k] == "":
                    rejects.append(f"{b['kind']} line {b['line']}: key {k} empty (write none)")
        if b["kind"] == "LESSON" and not b["body"]:
            rejects.append(f"LESSON line {b['line']}: body line missing")
        if b["kind"] == "STATE" and not b.get("entity", "").startswith("@"):
            rejects.append(f"STATE line {b['line']}: no @entity")
        if b["kind"] == "DECIDE" and not b.get("entity", "").startswith("@"):
            rejects.append(f"DECIDE line {b['line']}: decider missing")

    # 3. PROGRESS 逐项
    bp = next((b for b in base if b["kind"] == "PROGRESS"), None)
    cp = next((b for b in cand if b["kind"] == "PROGRESS"), None)
    if bp and not cp:
        rejects.append("PROGRESS block missing in candidate")
    if bp and cp:
        bd, bn, bu = (_items(bp["kv"].get(k, "")) for k in ("done", "next", "unverified"))
        cd, cn, cu = (_items(cp["kv"].get(k, "")) for k in ("done", "next", "unverified"))
        cand_all = set(cd) | set(cn) | set(cu)
        for it in bd:
            if it not in cd:
                rejects.append(f"done item removed: {it}")
        for it in bn:
            if it not in cand_all:
                rejects.append(f"next item dropped without a word: {it}")
        for it in bu:
            if it not in cand_all:
                rejects.append(f"unverified item dropped without a word: {it}")
        nevers = [b["kv"].get("never", "") for b in base + cand if b["kind"] == "BOUNDARY"]
        for it in cd:
            if it in bd:
                continue
            hit = next((nv for nv in nevers if _touches_boundary(it, nv)), None)
            if hit:
                rejects.append(f"done item touches a boundary ({hit}): {it}")
            elif it in bn or it in bu:
                transitions.append(f"next/unverified -> done, needs evidence: {it}")
            else:
                flags.append(f"new done item not in baseline, needs evidence: {it}")
        for it in cn:
            if it not in bn and it not in bd and it not in bu:
                adds.append(f"next: {it}")
        for it in cu:
            if it not in bu and it not in bn and it not in bd:
                adds.append(f"unverified: {it}")
        if bp["kv"].get("date") and cp["kv"].get("date") and cp["kv"]["date"] < bp["kv"]["date"]:
            flags.append(f"PROGRESS date went backwards: {bp['kv']['date']} -> {cp['kv']['date']}")

    # 4. 标识与值
    for bid, b in base_by.items():
        if b["kind"] in ("PROGRESS", "BOUNDARY"):
            continue
        c = cand_by.get(bid)
        if c is None:
            label = {"DECIDE": "decision rewritten or removed", "FACT": "fact dropped", "LESSON": "lesson dropped",
                     "STATE": "entity dropped", "GENE": "gene dropped"}.get(b["kind"], "block dropped")
            rejects.append(f"{label}: {b['raw']}")
            continue
        if b["kind"] == "FACT" and _norm(c["kv"].get("value", "")) != _norm(b["kv"].get("value", "")):
            flags.append(f"fact {bid[1]} value changed: {b['kv'].get('value')} -> {c['kv'].get('value')}")
        if b["kind"] == "DECIDE":
            for k in ("why", "context"):
                if _norm(c["kv"].get(k, "")) != _norm(b["kv"].get(k, "")):
                    flags.append(f"decision {bid[2]!r}: {k} changed")
        if b["kind"] in ("FACT", "LESSON", "GENE"):
            o, n2 = b["kv"].get("conf", ""), c["kv"].get("conf", "")
            if o != n2:
                flags.append(f"{b['kind']} {bid[1]} conf changed {o} -> {n2} (needs support)")
        if b["kind"] in ("LESSON", "GENE") and [_norm(x) for x in c["body"]] != [_norm(x) for x in b["body"]]:
            flags.append(f"{b['kind']} {bid[1]} body changed")
        if b["kind"] == "STATE":
            for k, v in b["kv"].items():
                if k not in c["kv"]:
                    rejects.append(f"state {bid[1]} key {k} dropped")
                elif _norm(c["kv"][k]) != _norm(v):
                    flags.append(f"state {bid[1]} {k} changed: {v} -> {c['kv'][k]}")
    for cid, c in cand_by.items():
        if cid not in base_by and c["kind"] != "PROGRESS":
            adds.append(f"{c['kind']}: {c['raw']}")

    # 5. 可选：正典校验器
    if validator is not None:
        if not validator.is_file():
            rejects.append(f"validator {validator} not found")
        else:
            try:
                r = subprocess.run([sys.executable, "-X", "utf8", str(validator), "--lint", str(reviewed_path), "--strict"],
                                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
                tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
                if r.returncode != 0:
                    rejects.append("canon validator --strict failed: " + " | ".join(tail))
                else:
                    print("ok      canon validator --strict passed")
            except (OSError, subprocess.TimeoutExpired) as e:
                rejects.append(f"canon validator could not run: {e}")

    print(f"review  baseline  {base_path}")
    print(f"        candidate {reviewed_path}: {len(cand)} blocks vs {len(base)} in baseline")
    for s in rejects:
        print(f"REJECT  {s}")
    for s in flags:
        print(f"FLAG    {s}")
    for s in transitions:
        print(f"TRANSITION {s}")
    for s in adds:
        print(f"ADD     {s}")
    if rejects:
        print(f"review: REJECTED ({len(rejects)}); baseline stays; nothing written")
        return 1
    if flags or transitions:
        print(f"review: {len(flags)} to decide, {len(transitions)} transitions need evidence; baseline stays until the owner accepts; nothing written")
        return 3
    print(f"review: clean, {len(adds)} additions; accept by saving the candidate as CURRENT.md and committing handoff: accept from <who> (nothing written)")
    return 0


# ====================================================== 3.0: ledger, log, recognize, unlock, pair, provenance, import, verify
# Design: MEM-FOREVER-3-ILANG-CRYPTO-DESIGN v1.1 (2026-11-08). Memory is a derivation: keys derive tasks, tasks
# yield constants, the logic between them is annotation. The ledger (env/ledger.env) is the start of the derivation;
# nothing is sealed at rest in the private repository; sealing is a pairing act; the owner is always a recipient.

import secrets as _secrets
import math as _math
import urllib.request as _urlreq
import urllib.error as _urlerr

LEDGER_REL = "env/ledger.env"
KEYS_REL = "env/keys.env"
PEPPER_REL = "env/pepper"                        # 3.1: 32 random bytes, hex, committed; the encoded state needs nothing else
ENC_TAG = "enc1:"
GRANT_PREFIX = "brain.grant."                    # 3.1: grants are git config of the machine, never a file of the repository
HARVEST_DEFAULT_PATHS = ("memory", "soul", "handoff")
HARVEST_SKIP = ("soul/evidence.md",)
OTP_REL = "env/otp.json"
LOG_DIR = "log"
PAIR_DIR = "pair"
SCAN_EXEMPT_TOP = {"env", "log", "pair"}          # private repository: the ledger, the verbatim log and sealed rows are not scanned
TOP_KINDS = ("root", "sudo", "payment", "account_security", "recovery_code", "registrar", "dns", "age_identity")
STALE_DAYS = 90
TENTATIVE_TTL = 30
CONFIRMED_AGENT_TTL = 90
RECOGNIZE_THRESHOLD = 0.30
OWNER_SOURCES = ("owner_verbatim", "owner_confirmed", "legacy")
SOURCES = ("owner_verbatim", "owner_confirmed", "owner_claimed", "agent_inferred", "imported", "legacy")
PROV_KINDS = ("FACT", "LESSON", "DECIDE", "BOUNDARY", "GENE", "STATE")
LEDGER_HEADER = ("# env/ledger.env - the authorization ledger: one row per door (3.0). Plain in a private repository.\n"
                 "# ::STATE{@name, door:..., kind:..., ref:KEY | value:..., verify:<command, exit 0 = the door opens>, "
                 "last_verified:YYYY-MM-DD|none, recover:<how to get back in>, scope:<tags>, top:true|false, why:<what it serves>}\n"
                 "# Values live here or in env/keys.env as KEY=value (ref:KEY). Top doors (root, payment, registrar, dns, "
                 "account_security, recovery_code, age_identity) never unlock from the record; the owner issues a one-time code.\n")


def _today() -> str:
    return f"{datetime.now():%Y-%m-%d}"


def _parse_date(s: str):
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def _days_since(s: str):
    d = _parse_date(s or "")
    return None if d is None else (datetime.now() - d).days


def _write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def _write_lf_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    _write_lf(tmp, text)
    os.replace(tmp, path)


# ---------------------------------------------------------------- ledger

def ledger_name(name: str) -> str:
    """Row names are canon entities, @[A-Z][A-Z0-9_]*: upper case, other characters become _."""
    n = re.sub(r"[^A-Za-z0-9_]", "_", (name or "").strip()).upper().strip("_")
    return n if n and n[0].isalpha() else ("K_" + n if n else "")


def ledger_path(repo: Path) -> Path:
    return repo / LEDGER_REL


def load_ledger(repo: Path) -> tuple[list[dict], list[str]]:
    """Rows of env/ledger.env as dicts {name, kv, line, raw}; also the raw lines. Comment and blank lines are kept."""
    p = ledger_path(repo)
    if not p.is_file():
        return [], []
    lines = read_text(p).replace("\r\n", "\n").split("\n")
    rows: list[dict] = []
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = BLOCK_RE.match(s)
        if not m or m.group(1) != "STATE":
            rows.append({"name": "", "kv": {}, "line": i, "raw": s, "error": "not a ::STATE{@name, k:v} row"})
            continue
        pos, kv = _fields(m.group(2).strip(), ",")
        name = pos[0][1:] if pos and pos[0].startswith("@") else ""
        rows.append({"name": name, "kv": kv, "line": i, "raw": s, "error": "" if name else "row has no @name"})
    return rows, lines

# ---------------------------------------------------------------- 3.1 three states: plain in a process, encoded at rest, sealed when pairing

def pepper_path(repo: Path) -> Path:
    return repo / PEPPER_REL


def load_pepper(repo: Path, override: str | None = None) -> bytes | None:
    if override:
        try:
            return bytes.fromhex(override.strip())
        except ValueError:
            return None
    p = pepper_path(repo)
    if not p.is_file():
        return None
    try:
        return bytes.fromhex(read_text(p).strip())
    except ValueError:
        return None


def write_pepper(repo: Path) -> bool:
    """Create env/pepper when missing. Never overwrites. Returns True when written."""
    p = pepper_path(repo)
    if p.is_file():
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    _write_lf(p, _secrets.token_hex(32) + "\n")
    return True


def _keystream(pepper: bytes, door: str, n: int) -> bytes:
    out = b""
    c = 0
    while len(out) < n:
        out += hashlib.sha256(pepper + door.encode("utf-8") + c.to_bytes(4, "big")).digest()
        c += 1
    return out[:n]


def is_encoded(v: str | None) -> bool:
    return isinstance(v, str) and v.startswith(ENC_TAG)


def enc1_encode(pepper: bytes, door: str, value: str) -> str:
    """Reversible encoding, not encryption: anyone holding the repository (pepper) and this tool can read it back.
    It keeps a key out of grep, screenshots, model context and pastes; it does not protect against a holder of the repository."""
    b = value.encode("utf-8")
    ks = _keystream(pepper, door, len(b))
    return ENC_TAG + base64.urlsafe_b64encode(bytes(x ^ y for x, y in zip(b, ks))).decode("ascii").rstrip("=")


def enc1_decode(pepper: bytes, door: str, token: str) -> str:
    t = token[len(ENC_TAG):]
    t += "=" * (-len(t) % 4)
    raw = base64.urlsafe_b64decode(t.encode("ascii"))
    ks = _keystream(pepper, door, len(raw))
    return bytes(x ^ y for x, y in zip(raw, ks)).decode("utf-8", errors="replace")


def _git_config_bool(repo: Path, key: str) -> bool:
    rc, out = _git(repo, "config", "--bool", key)
    return rc == 0 and out.strip() == "true"


def has_grant(repo: Path, name: str) -> bool:
    """A grant is a line of this machine's git config: brain.grant.<DOOR>, brain.grant.all, brain.grant.write."""
    return _git_config_bool(repo, GRANT_PREFIX + name)


def grant_mode(row: dict) -> str:
    g = row["kv"].get("grant", "").strip().lower()
    if g in ("once", "standing"):
        return g
    return "once" if is_top(row) else "standing"


def _need_write_grant(repo: Path, what: str) -> bool:
    """True when storing may proceed. Prints the one-sentence ask otherwise."""
    if has_grant(repo, "write"):
        return True
    print(f"GRANT   storing a key ({what}) needs the owner's yes once on this machine: python -X utf8 tools/brain.py grant --write")
    return False


# Harvest: find the value, not just the prefix. Group 1 is the value. Built by concatenation so this file does not
# trip its own scan. The table is the only place the tool names a vendor.
HARVEST_PATTERNS = [
    ("anthropic_key", re.compile(r"(?<![A-Za-z0-9_\-])(" + "s" + r"k-ant-[A-Za-z0-9_\-]{16,})")),
    ("openai_key", re.compile(r"(?<![A-Za-z0-9_\-])(" + "s" + r"k-(?!ant-)[A-Za-z0-9_\-]{16,})")),
    ("github_token", re.compile(r"(?<![A-Za-z0-9_])(" + "gh" + r"[pousr]_[A-Za-z0-9]{20,}|github_" + r"pat_[A-Za-z0-9_]{20,})")),
    ("aws_key", re.compile(r"(?<![A-Za-z0-9])(" + "AK" + "IA" + r"[0-9A-Z]{16})(?![A-Za-z0-9])")),
    ("vendor_token", re.compile(r"(?<![A-Za-z0-9_\-])((?:xox[abpr]-|gl" + r"pat-|cf" + r"at_|lxm" + r"cp_|ts" + r"key-|AI" + r"za|ya29\.|[sr]k_live_)[A-Za-z0-9_\-.]{8,})")),
    ("jwt", re.compile(r"(ey" + r"J[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,})")),
    ("bearer_token", re.compile(r"Bearer\s+((?!\$\{)[A-Za-z0-9_\-.]{16,})")),
    ("url_credential", re.compile(r"://[^\s/:@]+:((?!\$\{)[^\s/@]{4,})@")),
    ("credential", re.compile(r"(?:Secret|Token|EncodingAESKey|CorpID|AppSecret|SecretKey|AccessKey|API_KEY|api_key|ApiKey|client_secret|app_secret|access_key|secret_key)\s*[=:：]\s*[`'\"]?([A-Za-z0-9_\-+/=]{12,})")),
    ("generic_password", re.compile(r"(?:密码|口令|password|passwd|pwd|root\s*/)\s*[:：=]?\s*[`'\"]?(" + _MIXED + r")(?![/\\.])")),
    ("ssh_private_key", re.compile("(-----BE" + r"GIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----)")),
]
TOKEN_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")


def find_key_values(text: str) -> list[tuple[str, str, int]]:
    """(kind, value, line) for every key-shaped value in text; a value inside a {{TOKEN}} is skipped."""
    out: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    for kind, rx in HARVEST_PATTERNS:
        for m in rx.finditer(text):
            v = m.group(1)
            if not v or v in seen or "{{" in v:
                continue
            seen.add(v)
            out.append((kind, v, text.count("\n", 0, m.start(1)) + 1))
    return out


def _harvest_door_name(kind: str, stem: str, taken: set[str]) -> str:
    base = re.sub(r"[^A-Z0-9]+", "_", (kind + "_" + stem).upper()).strip("_") or "KEY"
    if base[0].isdigit():
        base = "K_" + base
    name, n = base, 1
    while name in taken:
        n += 1
        name = f"{base}_{n}"
    taken.add(name)
    return name


def harvest(repo: Path, paths: list[str] | None = None) -> list[dict]:
    """Turn key-shaped values under memory/ soul/ handoff/ (or the given paths) into ledger rows: the value encoded into
    env/keys.env, one ::STATE row with verify:none, and the text replaced by {{DOOR}}. log/ env/ pair/ and
    soul/evidence.md are never touched. Returns the doors created."""
    rows, lines = load_ledger(repo)
    taken = {r["name"] for r in rows if not r.get("error")}
    pepper = load_pepper(repo)
    if pepper is None:
        write_pepper(repo)
        pepper = load_pepper(repo)
    keys = _keys_env(repo)
    kp = repo / KEYS_REL
    keys_text = read_text(kp).replace("\r\n", "\n") if kp.is_file() else "# env/keys.env - KEY=value rows referenced by env/ledger.env (ref:KEY). Private repository; never pasted.\n"
    if not lines:
        lines = LEDGER_HEADER.rstrip("\n").split("\n")
    lines = [ln for ln in lines]
    while lines and not lines[-1].strip():
        lines.pop()
    value_door: dict[str, str] = {}
    created: list[dict] = []
    targets: list[Path] = []
    for rel in (paths or list(HARVEST_DEFAULT_PATHS)):
        p = repo / rel
        if p.is_file():
            targets.append(p)
        elif p.is_dir():
            targets += [q for q in sorted(p.rglob("*")) if q.is_file()]
    for p in targets:
        rel = p.relative_to(repo).as_posix()
        top = rel.split("/", 1)[0]
        if top in SCAN_EXEMPT_TOP or rel in HARVEST_SKIP or "/.git/" in f"/{rel}/":
            continue
        try:
            text = p.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            continue
        nl = "\r\n" if "\r\n" in text else "\n"
        body = text.replace("\r\n", "\n")
        found = find_key_values(body)
        if not found:
            continue
        stem = re.sub(r"\.[^.]+$", "", p.name)
        for kind, value, line in found:
            if value in value_door:
                door = value_door[value]
            else:
                door = _harvest_door_name(kind, stem, taken)
                value_door[value] = door
                keys_text = keys_text.rstrip("\n") + f"\n{door}={enc1_encode(pepper, door, value)}\n"
                keys[door] = value
                fields = [f"@{door}", f"door:{kind} found in {rel}", f"kind:{kind}", f"ref:{door}", "verify:none",
                          "last_verified:none", f"recover:see {rel}:{line} and the service that issued it", f"scope:{stem}",
                          "top:false", f"why:harvested from {rel}:{line} on {_today()}"]
                lines.append("::STATE{" + ", ".join(fields) + "}")
                created.append({"door": door, "kind": kind, "file": rel, "line": line})
            body = body.replace(value, "{{" + door + "}}")
        p.write_bytes(body.replace("\n", nl).encode("utf-8"))
    if created:
        _write_lf_atomic(kp, keys_text)
        _save_ledger(repo, lines)
    return created


def mask_key_values(text: str) -> tuple[str, int]:
    """For text that leaves the repository: every key-shaped value becomes {{UNHARVESTED <kind> <fingerprint>}}."""
    n = 0
    for kind, value, _ in find_key_values(text):
        text = text.replace(value, "{{UNHARVESTED " + kind + " " + _sha256(value.encode("utf-8"))[:8] + "}}")
        n += 1
    # anything the prefix scan still sees: mask the token run from the match to the next whitespace
    for label, rx in SECRET_PATTERNS:
        for m in list(rx.finditer(text))[::-1]:
            start = m.start()
            end = start
            while end < len(text) and not text[end].isspace():
                end += 1
            if "{{UNHARVESTED" in text[start:end]:
                continue
            text = text[:start] + "{{UNHARVESTED " + re.sub(r"[^A-Za-z0-9_]+", "_", label).strip("_").lower() + " " + _sha256(text[start:end].encode("utf-8"))[:8] + "}}" + text[end:]
            n += 1
    return text, n


def _handoff_scope(repo: Path) -> set[str] | None:
    """The scope the hand-off declares: scope: on the PROGRESS block. None when it declares none."""
    cur = _handoff_path(repo)
    if not cur.is_file():
        return None
    for b in parse_blocks(read_text(cur)):
        if b["kind"] == "PROGRESS":
            sc = b["kv"].get("scope", "").strip()
            if sc and sc != "none":
                return {t for t in re.split(r"[\s,]+", sc) if t}
    return None


def _keys_env(repo: Path) -> dict[str, str]:
    p = repo / KEYS_REL
    out: dict[str, str] = {}
    if not p.is_file():
        return out
    for ln in read_text(p).replace("\r\n", "\n").split("\n"):
        s = ln.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[k.strip()] = v
    return out


def ledger_value(repo: Path, row: dict, pepper: bytes | None = None) -> str | None:
    kv = row["kv"]
    if kv.get("value") not in (None, "", "none"):
        v = kv["value"]
    else:
        ref = kv.get("ref")
        if not ref:
            return None
        v = _keys_env(repo).get(ref)
        if v is None:
            return None
    if is_encoded(v):
        pepper = pepper or load_pepper(repo)
        if pepper is None:
            return None
        return enc1_decode(pepper, kv.get("ref") or row["name"], v)
    return v


def value_problem(repo: Path, row: dict) -> str:
    """Why ledger_value returned None, for the messages."""
    kv = row["kv"]
    ref = kv.get("ref")
    raw = kv.get("value") if kv.get("value") not in (None, "", "none") else (_keys_env(repo).get(ref) if ref else None)
    if raw is None:
        return f"no value or ref resolves ({KEYS_REL})"
    if is_encoded(raw) and load_pepper(repo) is None:
        return f"{PEPPER_REL} missing: the encoded value cannot be read on this clone (ledger decode --pepper <hex> if the owner kept it)"
    return "value unreadable"


def _is_stale(row: dict) -> bool:
    d = _days_since(row['kv'].get('last_verified', ''))
    return d is None or d > STALE_DAYS


def is_top(row: dict) -> bool:
    kv = row["kv"]
    return kv.get("top", "").lower() == "true" or kv.get("kind", "").lower() in TOP_KINDS


def row_scope(row: dict) -> set[str]:
    s = row["kv"].get("scope", "")
    return {t for t in re.split(r"[\s,]+", s) if t and t != "none"}


def row_text(row: dict, with_value: bool = False, value: str | None = None) -> str:
    """The row as a ::STATE line; the value masked unless with_value."""
    kv = dict(row["kv"])
    if with_value:
        if value is not None:
            kv["value"] = value
            kv.pop("ref", None)
    else:
        if "value" in kv and kv["value"] not in ("", "none"):
            kv["value"] = "[set]"
    parts = [f"@{row['name']}"] + [f"{k}:{v}" for k, v in kv.items()]
    return "::STATE{" + ", ".join(parts) + "}"


def _set_state_key(raw: str, key: str, value: str) -> str:
    """Set key:value inside a ::STATE{...} line, replacing or appending before the closing brace."""
    m = BLOCK_RE.match(raw.strip())
    if not m:
        return raw
    head = m.group(2)
    parts = re.split(r",\s*(?=[A-Za-z_][A-Za-z0-9_]*\s*:)", head)
    done = False
    for i, part in enumerate(parts):
        mm = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", part)
        if mm and mm.group(1) == key:
            parts[i] = f"{key}:{value}"
            done = True
    if not done:
        parts.append(f"{key}:{value}")
    return "::STATE{" + ", ".join(p.strip() for p in parts) + "}"


def _save_ledger(repo: Path, lines: list[str]) -> None:
    _write_lf_atomic(ledger_path(repo), "\n".join(lines).rstrip("\n") + "\n")


def _decode_output(b: bytes, fallback: str | None = None) -> str:
    """Text of a child process: UTF-8 when it is UTF-8, else the shell's own codepage (cmd.exe on a Chinese Windows
    answers in cp936), so a FAIL line shows the shell's words and not replacement characters."""
    if not b:
        return ""
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        pass
    cands: list[str] = [fallback] if fallback else []
    if os.name == "nt":
        try:
            import ctypes
            cands.append("cp%d" % ctypes.windll.kernel32.GetOEMCP())
        except Exception:
            pass
    getenc = getattr(locale, "getencoding", None)   # 3.11+: the locale's encoding, UTF-8 mode ignored
    if getenc:
        cands.append(getenc())
    cands.append(locale.getpreferredencoding(False))
    for enc in cands:
        if not enc:
            continue
        try:
            return b.decode(enc, errors="replace")
        except LookupError:
            continue
    return b.decode("utf-8", errors="replace")


def _ledger_verify_env(repo: Path, row: dict) -> dict:
    env = dict(os.environ)
    val = ledger_value(repo, row)
    if val is not None:
        env["LEDGER_VALUE"] = val
        ref = row["kv"].get("ref")
        if ref:
            env[ref] = val
    env["LEDGER_NAME"] = row["name"]
    env["LEDGER_DOOR"] = row["kv"].get("door", "")
    return env


IMPORT_SKIP = "*.py,*.pyc,*.bak*,*.md,*.pub,*.pub.*,*recipient*,*fullchain*,*.gitkeep"
IMPORT_KINDS = {".env": "env_file", ".key": "token", ".txt": "token", ".pem": "private_key", ".conf": "config",
                ".json": "credential_json", ".pw": "password", ".token": "token", ".secret": "token"}
_IMPORT_VERSION_SUFFIX = re.compile(r"([-_.]v\d+(?:\.\d+)*)?(?:[-_]\d{4}-\d{2}-\d{2})?$")


def import_row_name(filename: str) -> str:
    """ALIYUN_ZHANGMEI from aliyun-zhangmei-v1.0-2026-09-23.env: the stem without a version or date suffix."""
    stem = filename
    for ext in sorted(IMPORT_KINDS, key=len, reverse=True):
        if stem.lower().endswith(ext):
            stem = stem[: -len(ext)]
            break
    stem = _IMPORT_VERSION_SUFFIX.sub("", stem, count=1)
    return ledger_name(stem) or ledger_name(filename)


def import_kind(filename: str) -> str:
    low = filename.lower()
    for ext, kind in IMPORT_KINDS.items():
        if low.endswith(ext):
            return kind
    if low.startswith("id_") or low.endswith("_ed25519") or low.endswith("_rsa"):
        return "ssh_key"
    return "file"


def ledger_import_dir(repo: Path, src: str | None, opts: dict) -> int:
    """3.1.2: one ledger row per file in a directory, the file text encoded into env/keys.env. Nothing is deleted or moved;
    the files stay where they are. --glob picks files (comma-separated patterns, default *), --skip drops the public and
    the code (default IMPORT_SKIP), --kind overrides the kind guessed from the extension, --dry-run only lists."""
    import fnmatch
    if not src:
        print("ERROR   ledger import needs a directory: ledger import <dir> [--glob a,b] [--skip a,b] [--kind k] [--scope s] [--dry-run]")
        return 2
    d = Path(src).expanduser()
    if not d.is_dir():
        print(f"ERROR   {src} is not a directory")
        return 2
    globs = [g.strip() for g in (opts.get("glob") or "*").split(",") if g.strip()]
    skips = [g.strip() for g in (opts.get("skip") if opts.get("skip") is not None else IMPORT_SKIP).split(",") if g.strip()]
    dry = bool(opts.get("dry_run"))
    if not dry and not _need_write_grant(repo, f"ledger import {d.name}"):
        return 2
    rows, _ = load_ledger(repo)
    taken = {r["name"] for r in rows if not r.get("error")}
    done = skipped = 0
    for p in sorted(d.iterdir()):
        if not p.is_file():
            continue
        if not any(fnmatch.fnmatch(p.name, g) for g in globs) or any(fnmatch.fnmatch(p.name, g) for g in skips):
            continue
        try:
            value = p.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            print(f"skip    {p.name}: not UTF-8 text")
            skipped += 1
            continue
        if not value.strip():
            print(f"skip    {p.name}: empty")
            skipped += 1
            continue
        base = import_row_name(p.name)
        name, n = base, 2
        while name in taken:
            name, n = f"{base}_{n}", n + 1
        kind = opts.get("kind") or import_kind(p.name)
        if dry:
            print(f"would   {name} ({kind}, {len(value.encode('utf-8'))} bytes) <- {p.name}")
            done += 1
            continue
        rc = cmd_ledger(repo, "add", name, {
            "door": f"file:{p.name}", "kind": kind, "value": value, "verify": opts.get("verify") or "none",
            "recover": opts.get("recover") or f"{d} on {platform.node()}", "scope": opts.get("scope") or "none",
            "why": opts.get("why") or f"imported {_today()} from {d.name}/; the owner writes the door and the why",
            "top": bool(opts.get("top")), "grant": opts.get("grant")})
        if rc != 0:
            print(f"ERROR   {p.name}: ledger add returned {rc}")
            return rc
        taken.add(name)
        done += 1
    print(f"ledger import: {done} row(s) {'listed' if dry else 'added'}, {skipped} skipped; files untouched in {d}; "
          f"values {'not written' if dry else 'encoded in ' + KEYS_REL}; verify:none until the owner fills it")
    return 0


def cmd_ledger(repo: Path, action: str, name: str | None, opts: dict) -> int:
    rows, lines = load_ledger(repo)
    bad = [r for r in rows if r.get("error")]
    for r in bad:
        print(f"ERROR   ledger line {r['line'] + 1}: {r['error']}")
    rows = [r for r in rows if not r.get("error")]

    if action == "list":
        if not rows:
            print("ledger: no rows yet (brain.py ledger add <name> --door ... --kind ... --verify ... --recover ...)")
            return 0
        print(f"{'name':20s} {'kind':16s} {'last_verified':14s} {'top':5s} {'scope':16s} door")
        for r in rows:
            kv = r["kv"]
            print(f"{r['name']:20s} {kv.get('kind', ''):16s} {kv.get('last_verified', 'none'):14s} "
                  f"{'yes' if is_top(r) else 'no':5s} {kv.get('scope', '') or '-':16s} {kv.get('door', '')}")
        stale = [r for r in rows if _is_stale(r)]
        if stale:
            print(f"stale   {len(stale)} row(s) unverified for more than {STALE_DAYS} days or never: "
                  + ", ".join(r["name"] for r in stale))
        return 1 if bad else 0

    if action in ("add", "show", "verify", "reveal") and name and name != "all":
        name = ledger_name(name)
    if action == "add":
        if not name:
            print("ERROR   ledger add needs a name (letters, digits, _; it is written upper case)")
            return 2
        if any(r["name"] == name for r in rows):
            print(f"ERROR   ledger row {name} exists; edit env/ledger.env or choose another name")
            return 1
        door, kind = opts.get("door") or "", opts.get("kind") or ""
        if not door or not kind:
            print("ERROR   --door and --kind are required")
            return 2
        value, ref = opts.get("value"), opts.get("ref")
        if value and not ref:
            if not _need_write_grant(repo, f"ledger add {name}"):
                return 2
            ref = name
            kp = repo / KEYS_REL
            existing = read_text(kp).replace("\r\n", "\n") if kp.is_file() else "# env/keys.env - KEY=value rows referenced by env/ledger.env (ref:KEY). Private repository; never pasted.\n"
            if re.search(r"(?m)^" + re.escape(ref) + r"=", existing):
                print(f"ERROR   {KEYS_REL} already has {ref}; pass --ref with another key name")
                return 1
            pepper = load_pepper(repo)
            if pepper is None:
                write_pepper(repo)
                pepper = load_pepper(repo)
            _write_lf_atomic(kp, existing.rstrip("\n") + f"\n{ref}={enc1_encode(pepper, ref, value)}\n")
        fields = [f"@{name}", f"door:{door}", f"kind:{kind}"]
        if ref:
            fields.append(f"ref:{ref}")
        elif value:
            fields.append(f"value:{value}")
        fields.append(f"verify:{opts.get('verify') or 'none'}")
        fields.append("last_verified:none")
        fields.append(f"recover:{opts.get('recover') or 'none'}")
        fields.append(f"scope:{opts.get('scope') or 'none'}")
        fields.append(f"top:{'true' if opts.get('top') or kind.lower() in TOP_KINDS else 'false'}")
        if opts.get("grant") in ("once", "standing"):
            fields.append(f"grant:{opts['grant']}")
        fields.append(f"why:{opts.get('why') or 'none'}")
        row = "::STATE{" + ", ".join(fields) + "}"
        if not lines:
            lines = LEDGER_HEADER.rstrip("\n").split("\n")
        lines = [ln for ln in lines]
        while lines and not lines[-1].strip():
            lines.pop()
        lines.append(row)
        _save_ledger(repo, lines)
        print(f"ledger  added {name} ({kind}) -> {LEDGER_REL}" + (f"; value stored encoded in {KEYS_REL} as {ref}" if value else ""))
        return 0

    if action == "encode":
        kp = repo / KEYS_REL
        if not kp.is_file():
            print(f"ledger encode: no {KEYS_REL}; nothing to do")
            return 0
        pepper = load_pepper(repo)
        if pepper is None:
            write_pepper(repo)
            pepper = load_pepper(repo)
            print(f"create  {PEPPER_REL}")
        text = read_text(kp).replace("\r\n", "\n")
        out, n = [], 0
        for ln in text.split("\n"):
            st = ln.strip()
            if st and not st.startswith("#") and "=" in st:
                k, v = st.split("=", 1)
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                if v and not is_encoded(v):
                    out.append(f"{k.strip()}={enc1_encode(pepper, k.strip(), v)}")
                    n += 1
                    continue
            out.append(ln)
        if n:
            bak = kp.with_suffix(".env.bak")
            if not bak.exists():
                bak.write_bytes(kp.read_bytes())
                print(f"backup  {bak.relative_to(repo).as_posix()} (plain; delete it after ledger decode shows the rows open)")
            _write_lf_atomic(kp, "\n".join(out).rstrip("\n") + "\n")
        print(f"ledger encode: {n} row(s) encoded; the encoding is reversible with {PEPPER_REL} and this tool, it is not encryption")
        return 0

    if action == "decode":
        kp = repo / KEYS_REL
        raw = _keys_env(repo)
        if not raw:
            print(f"ledger decode: no rows in {KEYS_REL}")
            return 0
        pepper = load_pepper(repo, opts.get("pepper"))
        if pepper is None and any(is_encoded(v) for v in raw.values()):
            print(f"ERROR   {PEPPER_REL} missing: the repository is incomplete. The owner's copy of the pepper opens it: ledger decode --pepper <hex>")
            return 2
        for k, v in raw.items():
            print(f"{k}={enc1_decode(pepper, k, v) if is_encoded(v) else v}")
        return 0

    if action == "reveal":
        if not name:
            print("ERROR   ledger reveal needs the door name")
            return 2
        r = next((x for x in rows if x["name"] == name), None)
        if r is None:
            print(f"ERROR   no ledger row named {name}")
            return 1
        val = ledger_value(repo, r)
        if val is None:
            print(f"ERROR   {name}: {value_problem(repo, r)}")
            return 2
        print(val)
        return 0

    if action == "import":
        return ledger_import_dir(repo, name, opts)

    if action == "harvest":
        if not _need_write_grant(repo, "ledger harvest"):
            return 2
        created = harvest(repo, opts.get("paths") or None)
        for c in created:
            print(f"door    {c['door']} ({c['kind']}) from {c['file']}:{c['line']} -> {{{{{c['door']}}}}} in the text, value encoded in {KEYS_REL}, verify:none")
        print(f"ledger harvest: {len(created)} door(s) created; fill verify with ledger verify or the owner's word; log/ and {HARVEST_SKIP[0]} untouched")
        return 0

    if action == "show":
        r = next((x for x in rows if x["name"] == name), None)
        if r is None:
            print(f"ERROR   no ledger row named {name}")
            return 1
        val = ledger_value(repo, r) if opts.get("with_value") else None
        print(row_text(r, bool(opts.get("with_value")), val))
        return 0

    if action == "verify":
        wanted = [r for r in rows if not name or r["name"] == name or name == "all"]
        if name and name != "all" and not wanted:
            print(f"ERROR   no ledger row named {name}")
            return 1
        timeout = int(opts.get("timeout") or 30)
        failed = passed = skipped = 0
        for r in wanted:
            cmd = r["kv"].get("verify", "none")
            if cmd in ("", "none"):
                print(f"SKIP    {r['name']}: no verify command")
                skipped += 1
                continue
            try:
                res = subprocess.run(cmd, shell=True, capture_output=True,
                                     timeout=timeout, env=_ledger_verify_env(repo, r), cwd=str(repo))
                rc = res.returncode
                out = _decode_output(res.stdout) + _decode_output(res.stderr)
                tail = out.strip().splitlines()[-1:] if out.strip() else []
            except subprocess.TimeoutExpired:
                rc, tail = 124, ["timeout"]
            except OSError as e:
                rc, tail = 127, [str(e)]
            if rc == 0:
                passed += 1
                lines[r["line"]] = _set_state_key(lines[r["line"]], "last_verified", _today())
                print(f"PASS    {r['name']} ({r['kv'].get('door', '')})")
            else:
                failed += 1
                print(f"FAIL    {r['name']} ({r['kv'].get('door', '')}): exit {rc} {' '.join(tail)[:120]}")
        if passed:
            _save_ledger(repo, lines)
        rows2, _ = load_ledger(repo)
        stale = [r for r in rows2 if not r.get("error") and _is_stale(r)]
        print(f"ledger verify: {passed} passed, {failed} failed, {skipped} skipped; {len(stale)} stale (> {STALE_DAYS} days or never)")
        return 1 if failed else 0

    print(f"ERROR   unknown ledger action {action}")
    return 2


# ---------------------------------------------------------------- one-time code (top doors)

def _otp_load(repo: Path) -> dict:
    p = repo / OTP_REL
    if not p.is_file():
        return {}
    try:
        return json.loads(read_text(p))
    except json.JSONDecodeError:
        return {}


def _otp_save(repo: Path, data: dict) -> None:
    _write_lf_atomic(repo / OTP_REL, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def cmd_otp(repo: Path, action: str, name: str, minutes: int) -> int:
    name = ledger_name(name) if name else name
    data = _otp_load(repo)
    if action == "issue":
        code = _secrets.token_hex(4)
        expires = datetime.now() + timedelta(minutes=minutes)
        data[name] = {"sha256": _sha256(code.encode()), "expires": expires.isoformat(timespec="seconds"), "issued": _now_iso()}
        _otp_save(repo, data)
        print(f"otp     {name}: {code}  (valid {minutes} min, until {expires:%H:%M}; used once; revoke with brain.py otp revoke {name})")
        return 0
    if action == "revoke":
        if data.pop(name, None) is None:
            print(f"otp     {name}: nothing to revoke")
        else:
            _otp_save(repo, data)
            print(f"otp     {name}: revoked")
        return 0
    if action == "list":
        now = datetime.now()
        for k, v in data.items():
            exp = datetime.fromisoformat(v["expires"])
            print(f"{k:20s} {'valid' if exp > now else 'expired'} until {v['expires']}")
        if not data:
            print("otp     none issued")
        return 0
    print(f"ERROR   unknown otp action {action}")
    return 2


def _otp_consume(repo: Path, name: str, code: str) -> tuple[bool, str]:
    data = _otp_load(repo)
    rec = data.get(name)
    if not rec:
        return False, "no code issued for this door"
    if datetime.fromisoformat(rec["expires"]) < datetime.now():
        data.pop(name, None)
        _otp_save(repo, data)
        return False, "code expired; the owner issues a new one"
    if _sha256(code.strip().encode()) != rec["sha256"]:
        return False, "code does not match"
    data.pop(name, None)
    _otp_save(repo, data)
    return True, "code accepted and consumed"


# ---------------------------------------------------------------- unlock

def handoff_next_items(repo: Path) -> list[str]:
    cur = _handoff_path(repo)
    if not cur.is_file():
        return []
    for b in parse_blocks(read_text(cur)):
        if b["kind"] == "PROGRESS":
            return _items(b["kv"].get("next", ""))
    return []


def _item_names_door(item: str, row: dict) -> bool:
    a = _norm(item).lower()
    name = row["name"].lower()
    door = _norm(row["kv"].get("door", "")).lower()
    return (name and name in a) or (door and door in a) or (door and _bigram_overlap(a, door) >= 0.5)


def cmd_unlock(repo: Path, name: str, scope: str | None, code: str | None, no_log: bool = False) -> int:
    name = ledger_name(name)
    rows, _ = load_ledger(repo)
    row = next((r for r in rows if not r.get("error") and r["name"] == name), None)
    if row is None:
        print(f"ERROR   no ledger row named {name}")
        return 1
    mode = grant_mode(row)
    if is_top(row) or mode == "once":
        if not code:
            what = "a top door" if is_top(row) else "a once door (grant:once)"
            print(f"TOP     {name} is {what} ({row['kv'].get('kind', '')}); it never unlocks from the record. "
                  f"The owner issues a one-time code in person: brain.py otp issue {name}; then brain.py unlock {name} --code <code>")
            return 3
        ok, why = _otp_consume(repo, name, code)
        if not ok:
            print(f"REFUSE  {name}: {why}")
            return 3
    else:
        if not (has_grant(repo, name) or has_grant(repo, "all")):
            print(f"REFUSE  {name}: no grant on this machine. The owner says yes once: python -X utf8 tools/brain.py grant {name}"
                  f"   (or: grant --all, every standing door on this machine)")
            return 3
        rs = row_scope(row)
        declared = {t for t in re.split(r"[\s,]+", scope) if t} if scope else _handoff_scope(repo)
        if rs:
            if declared is None:
                print(f"REFUSE  {name}: the row has scope {sorted(rs)} and none was declared; pass --scope or put scope: on the PROGRESS block of handoff/CURRENT.md")
                return 1
            if not rs <= declared:
                print(f"REFUSE  {name}: row scope {sorted(rs)} is not inside the declared scope {sorted(declared)}; the item stays in next")
                return 1
        items = handoff_next_items(repo)
        if not any(_item_names_door(it, row) for it in items):
            print(f"REFUSE  {name}: no next item in handoff/CURRENT.md names this door; the key reaches context only when the work reaches it")
            return 1
    val = ledger_value(repo, row)
    if val is None:
        print(f"ERROR   {name}: {value_problem(repo, row)}")
        return 1
    print(row_text(row, True, val))
    if not no_log:
        _log_append(repo, "AGENT", f"unlock {name} ({row['kv'].get('door', '')}) grant:{'code' if (is_top(row) or mode == 'once') else ('door' if has_grant(repo, name) else 'all')}", kind="unlock")
    return 0


def cmd_grant(repo: Path, door: str | None, all_: bool, write: bool, revoke: bool, list_: bool) -> int:
    if not (repo / ".git").exists():
        print("ERROR   grants live in this clone's git config; there is no .git here")
        return 1
    if list_:
        rc, out = _git(repo, "config", "--get-regexp", "^brain\\.grant\\.")
        print(out.strip() if out.strip() else "grant: none on this machine")
        return 0
    targets: list[str] = []
    if all_:
        targets.append("all")
    if write:
        targets.append("write")
    if door:
        targets.append(ledger_name(door))
    if not targets:
        print("ERROR   grant needs <DOOR>, --all or --write (add --revoke to take one back, --list to see them)")
        return 2
    for t in targets:
        if revoke:
            _git(repo, "config", "--unset", GRANT_PREFIX + t)
            print(f"grant   revoked {t} on this machine")
        else:
            rc, out = _git(repo, "config", "--bool", GRANT_PREFIX + t, "true")
            if rc != 0:
                print(f"ERROR   git config failed: {out}")
                return 1
            print(f"grant   {t} on this machine ({GRANT_PREFIX}{t} true in .git/config; the repository never carries it)")
    _log_append(repo, "OWNER", f"grant {'revoke ' if revoke else ''}{' '.join(targets)}", kind="grant")
    return 0


# ---------------------------------------------------------------- pair / unseal

def owner_recipients(repo: Path) -> list[str]:
    p = repo / "vault" / "recipients.txt"
    if not p.is_file():
        return []
    return [ln.strip() for ln in read_text(p).splitlines() if ln.strip() and not ln.strip().startswith("#")]


def cmd_pair(repo: Path, recipient: str, scope: str, out: Path | None, age_dir: str | None, label: str | None) -> int:
    rec = recipient.strip()
    rp = Path(rec).expanduser()
    if rp.is_file():
        rec = next((ln.strip() for ln in read_text(rp).splitlines() if ln.strip() and not ln.startswith("#")), "")
    if not rec.startswith("age1"):
        print("ERROR   recipient must be an age public key (age1...) or a file holding one")
        return 2
    owners = owner_recipients(repo)
    if not owners:
        print("ERROR   vault/recipients.txt is empty; the owner must always be a recipient (age-keygen -y ~/.age/key.txt > vault/recipients.txt)")
        return 1
    try:
        age = find_age_tool("age", age_dir)
    except FileNotFoundError as e:
        print(f"ERROR   {e}")
        return 1
    declared = {t for t in re.split(r"[\s,]+", scope or "") if t}
    rows, _ = load_ledger(repo)
    chosen = [r for r in rows if not r.get("error") and not is_top(r) and (not row_scope(r) or (row_scope(r) & declared))]
    label = label or _sha256(rec.encode())[:8]
    outdir = out or repo / PAIR_DIR / f"{_today()}-{label}"
    outdir.mkdir(parents=True, exist_ok=True)
    sealed = []
    for r in chosen:
        val = ledger_value(repo, r)
        if val is None:
            print(f"skip    {r['name']}: no value resolves")
            continue
        text = row_text(r, True, val) + "\n"
        args = [age]
        for o in [rec] + owners:
            args += ["-r", o]
        target = outdir / f"{r['name']}.age"
        args += ["-o", str(target)]
        res = subprocess.run(args, input=text.encode("utf-8"), capture_output=True)
        if res.returncode != 0:
            print(f"ERROR   age failed for {r['name']}: {res.stderr.decode('utf-8', 'replace').strip()}")
            return 1
        sealed.append(r["name"])
        print(f"seal    {r['name']} -> {target.name} (recipients: receiver + {len(owners)} owner key(s))")
    decl = (f"::STATE{{@PAIR, date:{_today()}, receiver:{_sha256(rec.encode())[:12]}, scope:{' '.join(sorted(declared)) or 'none'}, "
            f"authorization:@OWNER, rows:{' '.join(sealed) or 'none'}, top_doors:excluded, owner_recipient:true}}\n"
            f"::BOUNDARY{{never:use_a_row_outside_the_declared_scope_or_before_a_next_item_names_its_door|scope:this_pairing}}\n")
    _write_lf(outdir / "declaration.md", "# pairing declaration\n\n" + decl)
    print(f"pair    {len(sealed)} row(s) sealed to {outdir}; declaration.md states identity, scope and authorization")
    return 0


def cmd_unseal(infile: Path, identity: Path, age_dir: str | None) -> int:
    try:
        data = _vault_decrypt(infile, identity, age_dir)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"ERROR   {e}")
        return 1
    sys.stdout.write(data.decode("utf-8", errors="replace"))
    sys.stdout.flush()
    return 0


# ---------------------------------------------------------------- log (the raw trajectory)

def log_path(repo: Path, date: str | None = None) -> Path:
    return repo / LOG_DIR / f"{date or _today()}.md"


def _log_append(repo: Path, who: str, text: str, kind: str = "turn", date: str | None = None) -> Path:
    p = log_path(repo, date)
    head = "" if p.is_file() else f"# {date or _today()}\n\n"
    body = text.replace("\r\n", "\n").strip("\n")
    entry = f"::EVENT{{@{who}, at:{datetime.now():%H:%M}, kind:{kind}}}\n{body}\n\n"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "ab") as f:
        f.write((head + entry).encode("utf-8"))
    return p


def cmd_log(repo: Path, who: str, text: str | None, file: Path | None, kind: str, show: str | None) -> int:
    if show is not None:
        p = log_path(repo, show or None)
        if not p.is_file():
            print(f"log     {p.name}: no entries")
            return 1
        sys.stdout.write(read_text(p))
        return 0
    if file is not None:
        text = read_text(file)
    elif text is None or text == "-":
        text = sys.stdin.read()
    if not text or not text.strip():
        print("ERROR   nothing to log")
        return 2
    p = _log_append(repo, "OWNER" if who == "owner" else "AGENT", text, kind=kind)
    print(f"log     {who} -> {p.relative_to(repo).as_posix()} ({len(text.encode('utf-8'))} bytes)")
    return 0


def log_events(repo: Path, days: int | None = None, since: str | None = None) -> list[dict]:
    """EVENT blocks of log/*.md inside the window, each with who, kind, date, text."""
    d = repo / LOG_DIR
    if not d.is_dir():
        return []
    lo = None
    if since:
        lo = since
    elif days is not None:
        lo = f"{datetime.now() - timedelta(days=max(0, days - 1)):%Y-%m-%d}"
    events: list[dict] = []
    for p in sorted(d.glob("*.md")):
        date = p.stem
        if not DATE_RE.match(date) or (lo and date < lo):
            continue
        cur: dict | None = None
        for raw in read_text(p).replace("\r\n", "\n").split("\n"):
            m = BLOCK_RE.match(raw.strip())
            if m and m.group(1) == "EVENT":
                pos, kv = _fields(m.group(2).strip(), ",")
                who = pos[0][1:] if pos and pos[0].startswith("@") else ""
                cur = {"who": who, "kind": kv.get("kind", "turn"), "date": date, "at": kv.get("at", ""), "lines": []}
                events.append(cur)
                continue
            if cur is not None and raw.startswith("#") and not raw.startswith("##"):
                continue
            if cur is not None:
                cur["lines"].append(raw.rstrip("\r"))
    for e in events:
        e["text"] = "\n".join(e["lines"]).strip("\n")
    return events


# ---------------------------------------------------------------- recognize (the action is the pairing)

def _content_words(s: str) -> set[str]:
    words: set[str] = set()
    for tok in re.findall(r"[A-Za-z][A-Za-z0-9\-]{4,}", s.replace("_", " ")):
        words.add(tok.lower())
    for run in re.findall(r"[一-鿿]{2,}", s):
        for i in range(len(run) - 1):
            words.add(run[i:i + 2])
    return words


def _bigram_overlap(a: str, b: str) -> float:
    """Jaccard overlap of CJK character bigrams (plus ASCII tokens) of two strings; 0 when either has none."""
    wa, wb = _content_words(a), _content_words(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _split_trailing(line: str) -> tuple[str, dict[str, str]]:
    """'T:text|k:v|k2:v2' -> ('T:text', {k: v}); keys are plain identifiers."""
    parts = line.split("|")
    text, kv = parts[0], {}
    for part in parts[1:]:
        m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:(.*)$", part, re.S)
        if m:
            kv[m.group(1)] = m.group(2).strip()
        else:
            text += "|" + part
    return text, kv


def soul_anchors(repo: Path, soul: Path | None = None) -> list[dict]:
    p = soul or repo / "soul" / "soul.md"
    if not p.is_file():
        return []
    anchors: list[dict] = []
    for b in parse_blocks(read_text(p)):
        if b["kind"] != "GENE":
            continue
        for line in b["body"]:
            text, kv = _split_trailing(line)
            by = kv.get("by", "legacy")
            if by not in OWNER_SOURCES:
                continue
            kind = "T" if text.startswith("T:") else "A"
            body = text[2:].strip()
            ante, cons = (body.split("⇒", 1) + [""])[:2] if kind == "A" else (body, "")
            words = {w for w in re.split(r"[\s,;]+", kv.get("words", "")) if w}
            anchors.append({"gene": b.get("entity", ""), "kind": kind, "line": line, "text": body,
                            "words": words or _content_words(ante), "cons": _content_words(cons), "by": by})
    return anchors


def _present(words: set[str], text: str, token_set: set[str]) -> set[str]:
    out = set()
    for w in words:
        if w in token_set or (not w.isascii() and w in text):
            out.add(w)
    return out


def recognize(repo: Path, days: int = 1, since: str | None = None, soul: Path | None = None) -> dict:
    anchors = soul_anchors(repo, soul)
    events = log_events(repo, days=None if since else days, since=since)
    turns = [e for e in events if e["who"] == "OWNER" and e["kind"] == "turn" and e["text"]]
    agent_text = "\n".join(e["text"] for e in events if e["who"] == "AGENT")
    agent_tokens = _content_words(agent_text)
    window_text = "\n".join(t["text"] for t in turns)
    window_tokens = _content_words(window_text)
    applicable = hits = 0
    detail = []
    for a in anchors:
        pres = _present(a["words"], window_text, window_tokens)
        if not pres:
            continue
        applicable += 1
        if a["kind"] == "T":
            need = max(1, _math.ceil(len(a["words"]) / 2))
            hit = any(len(_present(a["words"], t["text"], _content_words(t["text"]))) >= need for t in turns)
        else:
            hit = not _present(a["cons"], agent_text, agent_tokens) if a["cons"] else True
        hits += 1 if hit else 0
        detail.append((a["kind"], a["text"][:60], "hit" if hit else "miss"))
    ratio = hits / applicable if applicable else 0.0
    # boundary contradictions: done items touching a boundary of soul.md or the hand-off
    nevers = []
    for p in (repo / "soul" / "soul.md", _handoff_path(repo)):
        if p.is_file():
            nevers += [b["kv"].get("never", "") for b in parse_blocks(read_text(p)) if b["kind"] == "BOUNDARY"]
    done = []
    cur = _handoff_path(repo)
    if cur.is_file():
        for b in parse_blocks(read_text(cur)):
            if b["kind"] == "PROGRESS":
                done = _items(b["kv"].get("done", ""))
    contradictions = [(it, nv) for it in done for nv in nevers if _touches_boundary(it, nv)]
    recognized = bool(turns) and applicable > 0 and ratio >= RECOGNIZE_THRESHOLD and not contradictions
    return {"turns": len(turns), "anchors": len(anchors), "applicable": applicable, "hits": hits, "ratio": round(ratio, 3),
            "contradictions": contradictions, "recognized": recognized, "detail": detail,
            "threshold": RECOGNIZE_THRESHOLD}


def cmd_recognize(repo: Path, days: int, since: str | None, as_json: bool, soul: Path | None) -> int:
    r = recognize(repo, days, since, soul)
    if as_json:
        print(json.dumps({k: v for k, v in r.items() if k != "detail"}, ensure_ascii=False))
    else:
        for kind, text, verdict in r["detail"]:
            print(f"{verdict:5s} {kind}: {text}")
        for it, nv in r["contradictions"]:
            print(f"BOUNDARY done item touches a boundary: {it} <-> {nv}")
        print(f"recognize: {r['turns']} owner turn(s), {r['applicable']}/{r['anchors']} anchors applicable, "
              f"{r['hits']} hit, ratio {r['ratio']:.2f} (threshold {RECOGNIZE_THRESHOLD}), "
              f"{len(r['contradictions'])} boundary contradiction(s) -> {'RECOGNIZED' if r['recognized'] else 'NOT RECOGNIZED'}")
    if not r["turns"]:
        return 2
    return 0 if r["recognized"] else 1


# ---------------------------------------------------------------- provenance (by: on every block)

def _prov_files(repo: Path) -> list[Path]:
    out = []
    for rel in ("soul/soul.md", "soul/agent.md", "handoff/CURRENT.md"):
        p = repo / rel
        if p.is_file():
            out.append(p)
    mem = repo / "memory"
    if mem.is_dir():
        for p in sorted(mem.rglob("*.md")):
            if p.name != "MEMORY.md":
                out.append(p)
    return out


def _stamp_block_line(raw: str, kind: str, adds: dict[str, str]) -> str:
    """Add missing keys to one block line. STATE uses ', k:v'; DECIDE adds into its second brace; others use '|k:v'."""
    s = raw.rstrip("\r\n")
    m = BLOCK_RE.match(s.strip())
    if not m:
        return raw
    indent = s[: len(s) - len(s.lstrip())]
    if kind == "STATE":
        _, kv = _fields(m.group(2).strip(), ",")
        line = s.strip()
        for k, v in adds.items():
            if k not in kv:
                line = _set_state_key(line, k, v)
        return indent + line
    if kind == "DECIDE":
        head, extra = m.group(2), m.group(3) or ""
        _, kv = _fields(extra, "|")
        for k, v in adds.items():
            if k not in kv:
                extra = (extra + "|" if extra else "") + f"{k}:{v}"
        return f"{indent}::DECIDE{{{head}}}{{{extra}}}"
    head = m.group(2)
    _, kv = _fields(head, "|")
    for k, v in adds.items():
        if k not in kv:
            head = head + f"|{k}:{v}"
    return f"{indent}::{kind}{{{head}}}"


def _stamp_trait_line(raw: str, adds: dict[str, str]) -> str:
    s = raw.rstrip("\r\n")
    indent = s[: len(s) - len(s.lstrip())]
    text, kv = _split_trailing(s.strip())
    line = s.strip()
    for k, v in adds.items():
        if k not in kv:
            line += f"|{k}:{v}"
    return indent + line


def _set_kv_generic(raw: str, kind: str, key: str, value: str) -> str:
    """Replace or add key:value on a block line of any kind."""
    s = raw.rstrip("\r\n")
    indent = s[: len(s) - len(s.lstrip())]
    m = BLOCK_RE.match(s.strip())
    if not m:
        return raw
    if kind == "STATE":
        return indent + _set_state_key(s.strip(), key, value)
    if kind == "DECIDE":
        head, extra = m.group(2), m.group(3) or ""
        parts = [p for p in extra.split("|") if p.strip()]
        done = False
        for i, p in enumerate(parts):
            if re.match(r"^\s*" + key + r"\s*:", p):
                parts[i] = f"{key}:{value}"
                done = True
        if not done:
            parts.append(f"{key}:{value}")
        return f"{indent}::DECIDE{{{head}}}{{{'|'.join(parts)}}}"
    parts = m.group(2).split("|")
    done = False
    for i, p in enumerate(parts):
        if re.match(r"^\s*" + key + r"\s*:", p):
            parts[i] = f"{key}:{value}"
            done = True
    if not done:
        parts.append(f"{key}:{value}")
    return f"{indent}::{kind}{{{'|'.join(p.strip() for p in parts)}}}"


def _set_trait_kv(raw: str, key: str, value: str) -> str:
    s = raw.rstrip("\r\n")
    indent = s[: len(s) - len(s.lstrip())]
    text, kv = _split_trailing(s.strip())
    kv[key] = value
    return indent + text + "".join(f"|{k}:{v}" for k, v in kv.items())


def quote_q(text: str) -> str:
    """The evidence key of a quote: first 8 hex of sha256 over the whitespace-normalized text."""
    return _sha256(_norm(text).encode("utf-8"))[:8]


BACKED_SOURCES = ("owner_verbatim", "owner_confirmed")


def _evidence_q(repo_text: str) -> dict[str, str]:
    """q -> 'backed' (a transcript or the owner confirmed it) or 'claimed' (the agent wrote it down)."""
    qs: dict[str, str] = {}
    for b in parse_blocks(repo_text):
        if b["kind"] == "EVIDENCE":
            q, text = b["kv"].get("q", ""), b["kv"].get("text", "")
            if q and text and quote_q(text) == q:
                level = "backed" if b["kv"].get("by", "") in BACKED_SOURCES else "claimed"
                if qs.get(q) != "backed":
                    qs[q] = level
    return qs


def evidence_backing(repo: Path, transcript: Path | None = None) -> dict[str, str]:
    """Every known evidence key with its backing: EVIDENCE blocks in soul/ memory/ handoff/ and soul/evidence.md;
    a transcript's user turns are backed (Claude Code JSONL adapter: type user, message.role user)."""
    out: dict[str, str] = {}
    files = _prov_files(repo)
    ev = repo / "soul" / "evidence.md"
    if ev.is_file() and ev not in files:
        files.append(ev)
    for p in files:
        for q, level in _evidence_q(read_text(p)).items():
            if out.get(q) != "backed":
                out[q] = level
    if transcript is not None:
        for q in transcript_user_q(transcript):
            out[q] = "backed"
    return out


def evidence_keys(repo: Path, transcript: Path | None = None) -> set[str]:
    return set(evidence_backing(repo, transcript))


def transcript_user_q(transcript: Path) -> set[str]:
    qs: set[str] = set()
    try:
        raw = transcript.read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return qs
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") != "user":
            continue
        msg = d.get("message") or {}
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        texts = []
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text" and isinstance(c.get("text"), str):
                    texts.append(c["text"])
        for t in texts:
            qs.add(quote_q(t))
            for para in re.split(r"\n\s*\n", t):
                if para.strip():
                    qs.add(quote_q(para))
    return qs


def _evidence_append(repo: Path, q: str, where: str, by: str, src: str, clean: str) -> None:
    p = repo / "soul" / "evidence.md"
    head = "" if p.is_file() else ("---\ntype: reference\nname: evidence\ndescription: The owner's words that soul blocks cite by q, with by: saying what backs each one. Appended by brain.py evidence; never edited.\n---\n# Evidence\n\n")
    block = f"::EVIDENCE{{q:{q}|date:{_today()}|where:{where}|by:{by}" + (f"|src:{src}" if src else "") + f"|text:{clean}}}\n"
    with open(p, "ab") as fh:
        fh.write((head + block).encode("utf-8"))


def cmd_evidence(repo: Path, action: str, text: str | None, where: str | None, transcript: Path | None = None) -> int:
    if action == "q":
        if not text:
            print("ERROR   evidence q needs the quoted text")
            return 2
        print(quote_q(text))
        return 0
    if action == "add":
        if not text:
            print("ERROR   evidence add needs the owner's words")
            return 2
        q = quote_q(text)
        clean = _norm(text).replace("|", "/").replace("}", ")").replace("{", "(")
        by, src = "owner_claimed", ""
        if transcript is not None:
            if not transcript.is_file():
                print(f"ERROR   transcript not found: {transcript}")
                return 2
            if q in transcript_user_q(transcript):
                by, src = "owner_verbatim", "transcript:" + _sha256(transcript.read_bytes())[:8]
            else:
                print(f"WARN    the text is not a user turn of {transcript.name}; recorded as owner_claimed")
        _evidence_append(repo, q, (where or "chat").replace("|", "/"), by, src, clean)
        if by == "owner_verbatim":
            print(f"evidence q:{q} -> soul/evidence.md (backed by the transcript); tag the block: by:owner_verbatim|q:{q}")
        else:
            print(f"evidence q:{q} -> soul/evidence.md as owner_claimed (no transcript backs it); tag the block: by:owner_claimed|q:{q} "
                  f"(authority of agent_inferred; the owner backs it with: evidence confirm {q}, or add it with --transcript)")
        return 0
    if action == "confirm":
        if not text:
            print("ERROR   evidence confirm needs the q to confirm")
            return 2
        q = text.strip()
        # 3.2: the owner confirms an exclusion by its id: left becomes a FACT by:owner_confirmed, the trail stays
        for p in _prov_files(repo):
            ptext = read_text(p)
            for b in parse_blocks(ptext):
                if b["kind"] == "EXCLUDE" and b.get("entity", "") == q:
                    nl = "\r\n" if "\r\n" in ptext else "\n"
                    lines = ptext.replace("\r\n", "\n").split("\n")
                    i = b["line"] - 1
                    lines[i] = _set_kv_generic(lines[i], "EXCLUDE", "conf", "confirmed")
                    left = b["kv"].get("left", "none").strip()
                    if left and left != "none":
                        lines.insert(i + 1, f"::FACT{{key:{q}|value:{left}|why:{q}|used_by:none|conf:confirmed|by:owner_confirmed}}")
                    p.write_bytes(nl.join(lines).encode("utf-8"))
                    rel = p.relative_to(repo).as_posix()
                    if left and left != "none":
                        print(f"exclusion {q} confirmed by the owner; left written as ::FACT{{key:{q}}} by:owner_confirmed in {rel}; the exclusion stays as the trail")
                    else:
                        print(f"exclusion {q} confirmed by the owner; nothing was left, the gap stays open and says so in {rel}")
                    return 0
        p = repo / "soul" / "evidence.md"
        found = None
        if p.is_file():
            for b in parse_blocks(read_text(p)):
                if b["kind"] == "EVIDENCE" and b["kv"].get("q") == q:
                    found = b["kv"].get("text", "")
        if found is None:
            print(f"ERROR   no evidence with q:{q}")
            return 1
        _evidence_append(repo, q, "owner_confirm", "owner_confirmed", "", found)
        print(f"evidence q:{q} confirmed by the owner; blocks citing it may say by:owner_verbatim")
        return 0
    print(f"ERROR   unknown evidence action {action}")
    return 2


def provenance_scan(repo: Path, transcript: Path | None = None) -> tuple[list[dict], list[dict]]:
    """Return (violations, decays). Each entry: file, line (1-based), kind, text, rule, fix."""
    violations: list[dict] = []
    decays: list[dict] = []
    backing = evidence_backing(repo, transcript)
    qs = set(backing)
    for p in _prov_files(repo):
        text = read_text(p)
        lines = text.replace("\r\n", "\n").split("\n")
        rel = p.relative_to(repo).as_posix()
        for b in parse_blocks(text):
            kind = b["kind"]
            if kind not in PROV_KINDS:
                continue
            kv = b["kv"]
            by = kv.get("by", "")
            n = b["line"]
            if kind == "BOUNDARY" and by and by not in OWNER_SOURCES:
                violations.append({"file": rel, "line": n, "kind": kind, "text": b["raw"], "rule": "boundary_without_owner_source", "by": by})
            if by == "owner_verbatim" and kv.get("q", "") not in qs:
                violations.append({"file": rel, "line": n, "kind": kind, "text": b["raw"], "rule": "owner_verbatim_without_evidence", "by": by})
            elif by == "owner_verbatim" and backing.get(kv.get("q", "")) == "claimed":
                violations.append({"file": rel, "line": n, "kind": kind, "text": b["raw"], "rule": "owner_verbatim_without_transcript", "by": by})
            if kind in ("FACT", "LESSON", "GENE", "EXCLUDE") and kv.get("conf") == "confirmed" and by == "agent_inferred":
                try:
                    seen = int(kv.get("seen", "0"))
                except ValueError:
                    seen = 0
                if seen < 3:
                    violations.append({"file": rel, "line": n, "kind": kind, "text": b["raw"], "rule": "confirmed_without_three_days", "by": by})
            age = _days_since(kv.get("last", ""))
            if age is not None and kind in ("FACT", "LESSON", "EXCLUDE"):
                if kv.get("conf") == "tentative" and age > TENTATIVE_TTL:
                    decays.append({"file": rel, "line": n, "kind": kind, "text": b["raw"], "rule": "tentative_expired", "by": by})
                elif kv.get("conf") == "confirmed" and by not in OWNER_SOURCES and age > CONFIRMED_AGENT_TTL:
                    decays.append({"file": rel, "line": n, "kind": kind, "text": b["raw"], "rule": "agent_confirmed_stale", "by": by})
            if kind == "GENE":
                for i, line in enumerate(b["body"], 1):
                    t, tkv = _split_trailing(line)
                    tby = tkv.get("by", "")
                    if t.startswith("A:") and tby and tby not in OWNER_SOURCES:
                        violations.append({"file": rel, "line": n + i, "kind": "A", "text": line, "rule": "antipattern_without_owner_source", "by": tby})
                    if tby == "owner_verbatim" and tkv.get("q", "") not in qs:
                        violations.append({"file": rel, "line": n + i, "kind": "TA", "text": line, "rule": "owner_verbatim_without_evidence", "by": tby})
                    elif tby == "owner_verbatim" and backing.get(tkv.get("q", "")) == "claimed":
                        violations.append({"file": rel, "line": n + i, "kind": "TA", "text": line, "rule": "owner_verbatim_without_transcript", "by": tby})
                    tage = _days_since(tkv.get("last", ""))
                    if tage is not None and tby not in OWNER_SOURCES and tage > CONFIRMED_AGENT_TTL + TENTATIVE_TTL:
                        decays.append({"file": rel, "line": n + i, "kind": "TA", "text": line, "rule": "trait_expired", "by": tby})
    return violations, decays


def cmd_provenance(repo: Path, action: str, date: str | None, commit: bool, transcript: Path | None = None) -> int:
    date = date or _today()
    if action == "init":
        stamped = 0
        for p in _prov_files(repo):
            text = read_text(p)
            nl = "\r\n" if "\r\n" in text else "\n"
            lines = text.replace("\r\n", "\n").split("\n")
            changed = False
            for b in parse_blocks(text):
                kind = b["kind"]
                if kind not in PROV_KINDS:
                    continue
                i = b["line"] - 1
                adds = {"by": "legacy"}
                if kind in ("FACT", "LESSON"):
                    adds["last"] = date
                new = _stamp_block_line(lines[i], kind, adds)
                if new != lines[i]:
                    lines[i] = new
                    changed = True
                    stamped += 1
                if kind == "GENE":
                    for j in range(1, len(b["body"]) + 1):
                        new = _stamp_trait_line(lines[i + j], {"by": "legacy", "last": date})
                        if new != lines[i + j]:
                            lines[i + j] = new
                            changed = True
                            stamped += 1
            if changed:
                p.write_bytes(nl.join(lines).encode("utf-8"))
                print(f"stamp   {p.relative_to(repo).as_posix()}")
        print(f"provenance init: {stamped} block(s) and trait line(s) stamped by:legacy (last:{date} on facts, lessons, traits)")
        if commit and stamped:
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "mem: provenance init (by:legacy)")
        return 0
    violations, decays = provenance_scan(repo, transcript)
    if action == "check":
        for v in violations:
            print(f"VIOLATE {v['file']}:{v['line']} {v['rule']} (by:{v['by'] or 'none'}): {v['text'][:100]}")
        for d in decays:
            print(f"DECAY   {d['file']}:{d['line']} {d['rule']}: {d['text'][:100]}")
        print(f"provenance check: {len(violations)} violation(s), {len(decays)} decay(s) due")
        return 1 if violations else 0
    if action == "repair":
        edits: dict[str, list] = {}
        for v in violations + decays:
            edits.setdefault(v["file"], []).append(v)
        fixed = 0
        for rel, items in edits.items():
            p = repo / rel
            text = read_text(p)
            nl = "\r\n" if "\r\n" in text else "\n"
            lines = text.replace("\r\n", "\n").split("\n")
            removed: set[int] = set()
            for v in sorted(items, key=lambda x: -x["line"]):
                i = v["line"] - 1
                raw = lines[i]
                rule, kind = v["rule"], v["kind"]
                if rule == "boundary_without_owner_source":
                    m = BLOCK_RE.match(raw.strip())
                    _, kv = _fields(m.group(2), "|")
                    never = kv.get("never", "")
                    slug = re.sub(r"[^A-Za-z0-9一-鿿]+", "_", never)[:40].strip("_") or "boundary"
                    indent = raw[: len(raw) - len(raw.lstrip())]
                    lines[i] = (f"{indent}::FACT{{key:advice_{slug}|value:{never}|conf:tentative|by:{v['by']}|last:{date}"
                                f"|note:was_a_boundary_without_owner_evidence}}")
                elif rule == "antipattern_without_owner_source":
                    t, tkv = _split_trailing(raw.strip())
                    body = t[2:].strip()
                    ante, cons = (body.split("⇒", 1) + [""])[:2]
                    indent = raw[: len(raw) - len(raw.lstrip())]
                    newt = f"T:avoid_{ante.strip()}" + (f"_which_leads_to_{cons.strip()}" if cons.strip() else "")
                    lines[i] = indent + newt + "".join(f"|{k}:{vv}" for k, vv in tkv.items())
                elif rule in ("owner_verbatim_without_evidence", "owner_verbatim_without_transcript"):
                    if kind in ("A", "TA"):
                        lines[i] = _set_trait_kv(raw, "by", "owner_claimed")
                    else:
                        lines[i] = _set_kv_generic(raw, kind, "by", "owner_claimed")
                elif rule == "confirmed_without_three_days":
                    lines[i] = _set_kv_generic(raw, kind, "conf", "tentative")
                elif rule == "tentative_expired":
                    removed.add(i)
                    if kind == "LESSON" and i + 1 < len(lines) and lines[i + 1].strip() and not BLOCK_RE.match(lines[i + 1].strip()):
                        removed.add(i + 1)
                elif rule == "agent_confirmed_stale":
                    lines[i] = _set_kv_generic(raw, kind, "conf", "tentative")
                    lines[i] = _set_kv_generic(lines[i], kind, "last", date)
                elif rule == "trait_expired":
                    removed.add(i)
                else:
                    continue
                fixed += 1
            lines = [ln for k, ln in enumerate(lines) if k not in removed]
            p.write_bytes(nl.join(lines).encode("utf-8"))
            print(f"repair  {rel}: {len(items)} change(s)")
        print(f"provenance repair: {fixed} change(s) applied; blocks without owner evidence are read as advice, nothing owner-sourced was touched")
        if commit and fixed:
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "mem: provenance repair")
        return 0
    print(f"ERROR   unknown provenance action {action}")
    return 2


# ---------------------------------------------------------------- review (every writer passes the same gate)

def _git_show(repo: Path, rel: str, ref: str = "HEAD") -> str | None:
    rc, out = _git(repo, "show", f"{ref}:{rel}")
    return out if rc == 0 else None


def review_text(base_text: str | None, cand_text: str, rel: str) -> tuple[list[str], list[str], list[str]]:
    """Source rules for soul/ and memory/ files. Returns (rejects, downgrades, notes)."""
    rejects: list[str] = []
    downgrades: list[str] = []
    notes: list[str] = []
    if not rel.startswith(LOG_DIR + "/"):
        for h in _secret_hits_in_text(cand_text):
            rejects.append(f"secret-like text: {h}")
    base = parse_blocks(base_text or "")
    cand = parse_blocks(cand_text)
    base_by = {}
    for b in base:
        base_by.setdefault(_block_id(b), b)
    cand_by = {}
    for b in cand:
        cand_by.setdefault(_block_id(b), b)
    tomb = {_norm(b["kv"].get("what", "")[7:]).lower() for b in cand
            if b["kind"] == "DECIDE" and b["kv"].get("what", "").lower().startswith("retire ")
            and b["kv"].get("by", "") in OWNER_SOURCES[:2]}
    for bid, b in base_by.items():
        if b["kind"] == "BOUNDARY" and bid not in cand_by:
            if _norm(b["kv"].get("never", "")).lower() in tomb:
                notes.append(f"boundary retired by an owner tombstone: {b['raw']}")
            else:
                rejects.append(f"boundary deleted or rewritten without an owner tombstone: {b['raw']}")
    for bid, c in cand_by.items():
        by = c["kv"].get("by", "")
        if c["kind"] == "EXCLUDE":
            ekv = c["kv"]
            if not _items(ekv.get("candidates", "")):
                rejects.append(f"exclusion without candidates: {c['raw']}")
            if not _items(ekv.get("out", "")):
                rejects.append(f"exclusion without out: (a guess, not an elimination): {c['raw']}")
            if "left" not in ekv:
                rejects.append(f"exclusion without left: (write left:none when everything was struck): {c['raw']}")
        if c["kind"] == "BOUNDARY" and bid not in base_by and by not in OWNER_SOURCES[:2]:
            rejects.append(f"new boundary without owner source (by:{by or 'none'}): {c['raw']}")
        if c["kind"] == "GENE":
            base_body = {_norm(x) for x in base_by.get(bid, {}).get("body", [])}
            for line in c["body"]:
                t, tkv = _split_trailing(line)
                if t.startswith("A:") and _norm(line) not in base_body and tkv.get("by", "") not in OWNER_SOURCES[:2]:
                    rejects.append(f"new anti-pattern line without owner source (by:{tkv.get('by') or 'none'}): {line}")
        b = base_by.get(bid)
        if b is not None and b["kind"] in ("FACT", "DECIDE", "LESSON", "STATE"):
            bby = b["kv"].get("by", "")
            changed = (_norm(b["raw"]) != _norm(c["raw"])) or ([_norm(x) for x in b["body"]] != [_norm(x) for x in c["body"]])
            if changed and bby in OWNER_SOURCES and by not in OWNER_SOURCES:
                rejects.append(f"owner-sourced block changed by a {by or 'unsourced'} writer: {b['raw']}")
        if b is not None and b["kind"] in ("FACT", "LESSON", "GENE"):
            if b["kv"].get("conf") == "tentative" and c["kv"].get("conf") == "confirmed" and by not in OWNER_SOURCES:
                try:
                    seen = int(c["kv"].get("seen", "0"))
                except ValueError:
                    seen = 0
                if seen < 3:
                    downgrades.append(f"conf raised without three days (seen:{seen}), read as tentative: {c['raw']}")
    return rejects, downgrades, notes


def cmd_review(repo: Path, files: list[str], staged: bool, fix: bool) -> int:
    targets = list(files)
    if staged:
        rc, out = _git(repo, "diff", "--cached", "--name-only")
        targets += [ln.strip() for ln in out.splitlines() if ln.strip()]
    targets = [t for t in dict.fromkeys(targets)]
    watched = [t for t in targets if t.replace("\\", "/").startswith(("soul/", "memory/", "handoff/")) and t.endswith(".md")]
    if not watched:
        print("review: nothing under soul/ memory/ handoff/ to review")
        return 0
    total_rejects = 0
    for rel in watched:
        rel = rel.replace("\\", "/")
        p = repo / rel
        if not p.is_file():
            print(f"review  {rel}: deleted in the working tree")
            if rel.startswith("soul/") or rel == "handoff/CURRENT.md":
                print(f"REJECT  {rel}: deleting this file is not a memory change")
                total_rejects += 1
            continue
        cand_text = _git_show(repo, rel, ":") if staged else read_text(p)
        if cand_text is None:
            cand_text = read_text(p)
        base_text = _git_show(repo, rel, "HEAD")
        if rel == "handoff/CURRENT.md" and base_text is not None:
            tmpb = Path(tempfile.gettempdir()) / f"brain-review-base-{os.getpid()}.md"
            tmpc = Path(tempfile.gettempdir()) / f"brain-review-cand-{os.getpid()}.md"
            tmpb.write_bytes(base_text.encode("utf-8"))
            tmpc.write_bytes(cand_text.encode("utf-8"))
            rc = cmd_handoff_review(repo, tmpc, tmpb, None)
            tmpb.unlink(missing_ok=True)
            tmpc.unlink(missing_ok=True)
            if rc == 1:
                total_rejects += 1
            elif rc == 3:
                print("NOTE    owner items in the hand-off are recorded, not blocking; the owner reads them in the next session")
        rejects, downgrades, notes = review_text(base_text, cand_text, rel)
        for s in rejects:
            print(f"REJECT  {rel}: {s}")
        for s in downgrades:
            print(f"DOWNGRADE {rel}: {s}")
        for s in notes:
            print(f"NOTE    {rel}: {s}")
        if downgrades and fix and not staged:
            text = read_text(p)
            nl = "\r\n" if "\r\n" in text else "\n"
            lines = text.replace("\r\n", "\n").split("\n")
            for b in parse_blocks(text):
                if b["kind"] in ("FACT", "LESSON", "GENE") and b["kv"].get("conf") == "confirmed" and b["kv"].get("by", "") not in OWNER_SOURCES:
                    try:
                        seen = int(b["kv"].get("seen", "0"))
                    except ValueError:
                        seen = 0
                    if seen < 3:
                        lines[b["line"] - 1] = _set_kv_generic(lines[b["line"] - 1], b["kind"], "conf", "tentative")
            p.write_bytes(nl.join(lines).encode("utf-8"))
            print(f"fixed   {rel}: {len(downgrades)} conf downgraded to tentative")
        total_rejects += len(rejects)
        if not rejects:
            print(f"ok      {rel}: {len(downgrades)} downgrade(s), {len(notes)} note(s)")
    print(f"review: {total_rejects} reject(s) across {len(watched)} file(s)")
    return 1 if total_rejects else 0


# ---------------------------------------------------------------- import (bulk and selective)

def _existing_ids(repo: Path) -> set[tuple]:
    ids: set[tuple] = set()
    for p in _prov_files(repo):
        for b in parse_blocks(read_text(p)):
            ids.add(_block_id(b))
    return ids


def cmd_import(repo: Path, src: Path, source: str, date: str | None) -> int:
    date = date or _today()
    if not src.exists():
        print(f"ERROR   {src} not found")
        return 1
    files = [src] if src.is_file() else sorted(src.rglob("*.md"))
    existing = _existing_ids(repo)
    kept: list[str] = []
    dropped_prose = dropped_dup = converted = 0
    seen_ids: set[tuple] = set()
    for f in files:
        try:
            text = read_text(f)
        except UnicodeDecodeError:
            continue
        blocks = parse_blocks(text)
        dropped_prose += max(0, len([ln for ln in text.splitlines() if ln.strip()]) - sum(1 + len(b["body"]) for b in blocks))
        for b in blocks:
            kind = b["kind"]
            if kind not in PROV_KINDS or kind == "STATE":
                continue
            bid = _block_id(b)
            if bid in existing or bid in seen_ids:
                dropped_dup += 1
                continue
            seen_ids.add(bid)
            raw = b["raw"]
            if kind == "BOUNDARY":
                never = b["kv"].get("never", "")
                slug = re.sub(r"[^A-Za-z0-9一-鿿]+", "_", never)[:40].strip("_") or "boundary"
                raw = f"::FACT{{key:imported_boundary_{slug}|value:{never}|conf:tentative}}"
                kind = "FACT"
                converted += 1
            raw = _stamp_block_line(raw, kind, {"by": "imported", "from": source, "last": date})
            raw = _set_kv_generic(raw, kind, "by", "imported")
            if kind in ("FACT", "LESSON", "GENE"):
                raw = _set_kv_generic(raw, kind, "conf", "tentative")
            kept.append(raw)
            for line in b["body"]:
                if kind == "GENE":
                    t, tkv = _split_trailing(line)
                    if t.startswith("A:"):
                        body = t[2:].strip()
                        ante, cons = (body.split("⇒", 1) + [""])[:2]
                        t = f"T:avoid_{ante.strip()}" + (f"_which_leads_to_{cons.strip()}" if cons.strip() else "")
                        converted += 1
                    tkv["by"] = "imported"
                    tkv.setdefault("last", date)
                    kept.append("  " + t + "".join(f"|{k}:{v}" for k, v in tkv.items()))
                else:
                    kept.append(line)
    if not kept:
        print(f"import: nothing kept from {src} ({dropped_prose} prose line(s), {dropped_dup} duplicate(s))")
        return 1
    out = repo / "memory" / "imports" / f"{re.sub(r'[^A-Za-z0-9_.-]+', '-', source)}-{date}.md"
    fm = (f"---\ntype: reference\nname: import-{re.sub(r'[^A-Za-z0-9_.-]+', '-', source)}-{date}\n"
          f"description: Imported from {source} on {date}; every block by:imported, conf tentative, no authority until the owner re-states it\n---\n")
    _write_lf(out, fm + "\n".join(kept) + "\n")
    idx = repo / "memory" / "MEMORY.md"
    line = f"- [import {source} {date}](imports/{out.name}) — {len(kept)} block line(s), by:imported, no authority\n"
    if idx.is_file():
        with open(idx, "ab") as fh:
            fh.write(line.encode("utf-8"))
    print(f"import: kept {len(kept)} block line(s) -> {out.relative_to(repo).as_posix()}; dropped {dropped_prose} prose line(s), "
          f"{dropped_dup} duplicate(s); {converted} boundary/anti-pattern(s) converted to advice; nothing entered soul.md")
    return 0


# ---------------------------------------------------------------- verify (constants with their edges)

def cmd_verify(repo: Path, online: bool, strict: bool) -> int:
    ids: set[str] = set()
    facts: list[tuple[str, dict]] = []
    refs: dict[str, set[str]] = {}
    excl: list[tuple[str, dict]] = []
    for p in _prov_files(repo):
        rel = p.relative_to(repo).as_posix()
        for b in parse_blocks(read_text(p)):
            k = b["kind"]
            if k == "FACT":
                ids.add(b["kv"].get("key", ""))
                facts.append((rel, b))
            elif k == "LESSON":
                ids.add(b["kv"].get("id", ""))
            elif k in ("GENE", "STATE"):
                ids.add(b.get("entity", "").lstrip("@"))
            elif k == "EXCLUDE":
                ids.add(b.get("entity", ""))
                excl.append((rel, b))
    rows, _ = load_ledger(repo)
    for r in rows:
        if not r.get("error"):
            ids.add(r["name"])
            facts.append((LEDGER_REL, {"kind": "STATE", "kv": r["kv"], "raw": r["raw"], "key": r["name"]}))
    ids.discard("")
    missing = []
    for rel, b in facts:
        key = b["kv"].get("key") or b.get("key", "")
        for field in ("why", "used_by"):
            for t in re.split(r"[\s,]+", b["kv"].get(field, "")):
                t = t.strip().lstrip("@")
                if t and t != "none":
                    refs.setdefault(t, set()).add(key)
                    if t not in ids:
                        missing.append((rel, key, field, t))
    orphans = [(rel, b["kv"].get("key") or b.get("key", "")) for rel, b in facts
               if not b["kv"].get("why") and (b["kv"].get("key") or b.get("key", "")) not in refs]
    # 3.2: an exclusion's out: names what refuted each struck candidate; a door, a FACT key, a log/ date or an evidence q
    # must exist, a path or free text is taken as named
    logdir = repo / LOG_DIR
    log_dates = {p.stem for p in logdir.glob("*.md")} if logdir.is_dir() else set()
    evp = repo / "soul" / "evidence.md"
    qs = {b["kv"].get("q", "") for b in parse_blocks(read_text(evp)) if b["kind"] == "EVIDENCE"} if evp.is_file() else set()
    for rel, b in excl:
        eid = b.get("entity", "")
        outs = _items(b["kv"].get("out", ""))
        if not outs:
            missing.append((rel, eid, "out", "empty: a guess, not an elimination"))
        for o in outs:
            m = re.match(r"^(.*?)\((.*)\)\s*$", o)
            cand, const = (m.group(1).strip(), m.group(2).strip()) if m else (o, "")
            if not const:
                missing.append((rel, eid, "out", f"{cand}: no refuting constant in parentheses"))
                continue
            c = const.lstrip("@")
            if re.fullmatch(r"[A-Z][A-Z0-9_]*", c):
                ok = c in ids
            elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", c):
                ok = c in log_dates
            elif c.startswith("q:"):
                ok = c[2:] in qs
            elif c.startswith("fact:"):
                ok = c[5:] in ids
            else:
                ok = True
            if not ok:
                missing.append((rel, eid, "out", f"{cand}: {const} names nothing the brain can see"))
    for rel, key, field, t in missing:
        print(f"MISSING {rel} {key}: {field} -> {t}" + ("" if field == "out" else " (no such constant, function or door)"))
    for rel, key in orphans:
        print(f"ORPHAN  {rel} {key}: no why and nothing points at it; listed as dead, dropped after {STALE_DAYS} days")
    checked = 0
    if online:
        for rel, b in facts:
            for field in ("doi", "url", "value"):
                v = b["kv"].get(field, "")
                url = f"https://doi.org/{v}" if field == "doi" or re.match(r"^10\.\d{4,}/", v) else (v if v.startswith("http") else "")
                if not url:
                    continue
                try:
                    req = _urlreq.Request(url, method="HEAD", headers={"User-Agent": "brain.py"})
                    with _urlreq.urlopen(req, timeout=10) as resp:
                        code = resp.status
                except _urlerr.HTTPError as e:
                    code = e.code
                except (_urlerr.URLError, OSError):
                    code = 0
                checked += 1
                print(f"{'OK  ' if 200 <= code < 400 else 'DEAD'}    {rel} {b['kv'].get('key', '')}: {url} -> {code}")
    print(f"verify: {len(facts)} constant(s), {len(excl)} exclusion(s), {len(missing)} missing edge(s), {len(orphans)} orphan(s)" + (f", {checked} online check(s)" if online else ""))
    return 1 if (strict and (missing or orphans)) else 0


# ---------------------------------------------------------------- instructions (five files mirror the skill body)

INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules", ".github/copilot-instructions.md")


def skill_body(repo: Path) -> str:
    sk = repo / "skills" / "mem-forever" / "SKILL.md"
    if not sk.is_file():
        raise FileNotFoundError(f"{sk.relative_to(repo).as_posix()} missing; a brain made by init has no skill copy, the template repository does")
    text = read_text(sk).replace("\r\n", "\n")
    try:
        _, close_idx, _ = split_frontmatter(text)
        body = "\n".join(text.split("\n")[close_idx + 1:])
    except FrontmatterError:
        body = text
    return body.lstrip("\n")


def cmd_instructions(repo: Path, action: str) -> int:
    try:
        body = skill_body(repo)
    except FileNotFoundError as e:
        print(f"ERROR   {e}")
        return 1
    bad = 0
    for rel in INSTRUCTION_FILES:
        p = repo / rel
        if action == "sync":
            _write_lf(p, body)
            print(f"write   {rel}")
            continue
        cur = read_text(p).replace("\r\n", "\n") if p.is_file() else None
        if cur != body:
            bad += 1
            print(f"DIFF    {rel}: not identical to the skill body")
    if action == "check":
        print(f"instructions check: {len(INSTRUCTION_FILES) - bad}/{len(INSTRUCTION_FILES)} identical")
    return 1 if bad else 0


# ---------------------------------------------------------------- hooks and the private-remote guard

HOOK_PRE_COMMIT = """#!/bin/sh
# Mem-Forever 3.0: every writer passes the same gate. Reviews staged soul/ memory/ handoff/ files against HEAD
# with the source rules, then runs check. Installed by brain.py install (core.hooksPath tools/hooks).
set -u
PY="${BRAIN_PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
"$PY" -X utf8 tools/brain.py review --staged || { echo "pre-commit: review rejected the change; nothing committed"; exit 1; }
"$PY" -X utf8 tools/brain.py check || { echo "pre-commit: check failed; nothing committed"; exit 1; }
exit 0
"""

HOOK_PRE_PUSH = """#!/bin/sh
# Mem-Forever 3.0 push guard: the brain is private. A push that carries soul/ memory/ handoff/ env/ log/ pair/ or log.md
# goes only to a remote that is private. GitHub and Gitee are checked through their API (brain.py remote-check);
# a remote the check cannot read needs a one-time confirmation: git config --bool brain.allowPush.<remote> true
set -u
remote="$1"; url="$2"
PATTERN='^(soul|memory|handoff|vault|env|log|pair|projects|mirror|\\.ilang)/|^log\\.md$'
ZEROS="0000000000000000000000000000000000000000"
carries=0
while read -r local_ref local_sha remote_ref remote_sha; do
  [ -n "${local_sha:-}" ] || continue
  if [ "$remote_sha" = "$ZEROS" ]; then base="$(git rev-parse "${local_sha}^" 2>/dev/null || echo "")"; else base="$remote_sha"; fi
  [ -n "$base" ] || { carries=1; continue; }
  files="$(git diff --name-only "$base" "$local_sha" 2>/dev/null)" || continue
  if printf '%s\\n' "$files" | grep -qE "$PATTERN"; then carries=1; fi
done
[ "$carries" = "1" ] || exit 0
if [ "$(git config --bool "brain.allowPush.$remote" 2>/dev/null)" = "true" ]; then exit 0; fi
PY="${BRAIN_PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
"$PY" -X utf8 tools/brain.py remote-check "$url"
rc=$?
if [ "$rc" = "0" ]; then exit 0; fi
if [ "$rc" = "1" ]; then
  echo "push guard: $url is PUBLIC; this push carries private memory. Push cancelled."
  exit 1
fi
echo "push guard: cannot tell whether $url is private. If it is your own private repository, confirm once:"
echo "  git config --bool brain.allowPush.$remote true"
exit 1
"""


REMOTE_RE = re.compile(r"(github\.com|gitee\.com)[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")


def parse_remote(url: str) -> tuple[str, str, str] | None:
    m = REMOTE_RE.search(url.strip())
    return (m.group(1), m.group(2), m.group(3)) if m else None


def remote_check(url: str) -> int:
    """0 private or not public as far as the host API shows, 1 public, 2 unknown."""
    parsed = parse_remote(url)
    if not parsed:
        return 2
    host, owner, name = parsed
    api = f"https://api.github.com/repos/{owner}/{name}" if host == "github.com" else f"https://gitee.com/api/v5/repos/{owner}/{name}"
    try:
        req = _urlreq.Request(api, headers={"User-Agent": "brain.py", "Accept": "application/json"})
        with _urlreq.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
            if isinstance(data, dict) and data.get("private") is False:
                return 1
            return 0
    except _urlerr.HTTPError as e:
        return 0 if e.code == 404 else 2
    except (_urlerr.URLError, OSError, ValueError):
        return 2


def cmd_remote_check(url: str) -> int:
    rc = remote_check(url)
    print({0: "private (or not visible to the public API)", 1: "PUBLIC", 2: "unknown"}[rc] + f": {url}")
    return rc


def install_hooks(repo: Path, dry_run: bool = False) -> int:
    hooks = repo / "tools" / "hooks"
    problems = 0
    for name, text in (("pre-commit", HOOK_PRE_COMMIT), ("pre-push", HOOK_PRE_PUSH)):
        p = hooks / name
        if not dry_run:
            _write_lf(p, text)
            if os.name != "nt":
                os.chmod(p, 0o755)
        print(f"{'DRY  ' if dry_run else ''}hook     tools/hooks/{name}")
    if not dry_run and (repo / ".git").exists():
        rc, out = _git(repo, "config", "core.hooksPath", "tools/hooks")
        if rc != 0:
            print(f"ERROR    git config core.hooksPath failed: {out}")
            problems += 1
        else:
            print("config   core.hooksPath = tools/hooks")
    return problems


# ---------------------------------------------------------------- migrate 2.1 -> 3.0

def cmd_migrate_2to3(repo: Path, infile: Path | None, identity: Path, age_dir: str | None) -> int:
    rows_added = files_written = 0
    rows, lines = load_ledger(repo)
    names = {r["name"] for r in rows}
    if not lines:
        lines = LEDGER_HEADER.rstrip("\n").split("\n")

    def add_row(name: str, door: str, kind: str, ref: str | None, why: str) -> None:
        nonlocal rows_added
        base = ledger_name(name) or "ROW"
        n, k = base, 1
        while n in names:
            k += 1
            n = f"{base}_{k}"
        names.add(n)
        fields = [f"@{n}", f"door:{door}", f"kind:{kind}"] + ([f"ref:{ref}"] if ref else []) + \
                 ["verify:none", "last_verified:none", "recover:none", "scope:legacy", f"top:{'true' if kind in TOP_KINDS else 'false'}", f"why:{why}"]
        lines.append("::STATE{" + ", ".join(fields) + "}")
        rows_added += 1

    infile = infile or latest_vault_file(repo)
    if infile is not None and infile.is_file():
        try:
            data = _vault_decrypt(infile, identity, age_dir)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"ERROR   {e}")
            return 1
        kp = repo / KEYS_REL
        keys_text = read_text(kp).replace("\r\n", "\n") if kp.is_file() else "# env/keys.env - KEY=value rows referenced by env/ledger.env (ref:KEY). Private repository; never pasted.\n"
        with tarfile.open(fileobj=io.BytesIO(data), mode="r") as tar:
            for m in tar.getmembers():
                if not m.isfile():
                    continue
                parts = Path(m.name).parts
                blob = tar.extractfile(m).read()
                if parts[0] == "keys" and len(parts) == 2:
                    dest = repo / "env" / parts[1]
                    if not dest.exists():
                        dest.write_bytes(blob)
                        files_written += 1
                    add_row(Path(parts[1]).stem, f"env/{parts[1]}", "env_file", None, "migrated_from_vault_keys")
                elif parts[0] == "ssh" and len(parts) == 2:
                    dest = repo / "env" / "ssh" / parts[1]
                    if not dest.exists():
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(blob)
                        files_written += 1
                    add_row(parts[1], f"env/ssh/{parts[1]}", "ssh_key", None, "migrated_from_vault_ssh")
                elif m.name == MEMORY_VALUES_NAME:
                    payload = json.loads(blob)
                    for e in payload.get("values", []):
                        ref = re.sub(r"[^A-Za-z0-9_]", "_", e["kind"]).upper()
                        if not re.search(r"(?m)^" + re.escape(ref) + r"=", keys_text):
                            keys_text = keys_text.rstrip("\n") + f"\n{ref}={e['value']}\n"
                        add_row(e["kind"], f"memory marker [REDACTED {e['kind']} {e['fingerprint']}]", "value", ref, "migrated_from_vault_memory_values")
        del data
        _write_lf_atomic(kp, keys_text)
        print(f"vault   {infile.name}: {files_written} file(s) written under env/, rows added for keys, ssh keys and memory values")
    else:
        print("vault   no vault/keys-*.age bundle; only provenance init runs")
    if rows_added:
        _save_ledger(repo, lines)
    print(f"migrate-2to3: {rows_added} ledger row(s) added -> {LEDGER_REL}; fill verify and recover for each row, then brain.py ledger verify")
    rc = cmd_provenance(repo, "init", None, False)
    print("migrate-2to3: old vault files stay in git history; the owner's age key remains the owner recipient for pairing")
    return rc


# ---------------------------------------------------------------- paste: the ledger without values by default

def ledger_section(repo: Path, with_values: bool) -> str:
    rows, _ = load_ledger(repo)
    rows = [r for r in rows if not r.get("error")]
    if not rows:
        return ""
    out = [f"::STATE{{@LEDGER, rows:{len(rows)}, values:{'included' if with_values else 'omitted'}, note:a_key_reaches_a_model_only_when_a_next_item_names_its_door}}"]
    for r in rows:
        val = ledger_value(repo, r) if (with_values and not is_top(r)) else None
        out.append(row_text(r, with_values and not is_top(r), val))
    return "\n".join(out)


# ------------------------------------------------------------------------ main


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    default_repo = Path(__file__).resolve().parent.parent
    ap = argparse.ArgumentParser(prog="brain.py", description="可移植 Agent 大脑工具 v" + VERSION)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="OKF 三条合规 + 密钥前缀扫描 + 字节上限")
    c.add_argument("--repo", default=str(default_repo), help="仓库根目录（默认 tools/ 的上一级）")

    m = sub.add_parser("migrate-cc", help="从 Claude Code 自动记忆目录迁入 memory/")
    m.add_argument("src", nargs="?", help="源目录；缺省按仓库上一级目录算 slug")
    m.add_argument("--repo", default=str(default_repo))
    m.add_argument("--overwrite", action="store_true", help="覆盖 memory/ 里已存在的同名文件")

    v = sub.add_parser("vault", help="tar 加 age 加解密（工程书 3.6 / 4.4）")
    vs = v.add_subparsers(dest="vcmd", required=True)
    vp = vs.add_parser("pack", help="打包 *.env、ssh 私钥、memory 标记对应的值 -> vault/keys-<日期>.age")
    vp.add_argument("--repo", default=str(default_repo))
    vp.add_argument("--out", help="默认 vault/keys-YYYY-MM-DD.age（今天）")
    vp.add_argument("--recipients", help="默认 vault/recipients.txt")
    vp.add_argument("--keys-dir", help="默认 ~/.keys，不存在则仓库上一级的 _keys")
    vp.add_argument("--ssh-dir", help="默认 ~/.ssh")
    vp.add_argument("--ssh-key", action="append", help="ssh 私钥文件名，可重复；默认 id_* 且非 .pub")
    vp.add_argument("--source", help="源记忆目录；默认按仓库上一级目录算 slug")
    vp.add_argument("--age-dir", help="age 可执行文件所在目录")
    vp.add_argument("--overwrite", action="store_true", help="覆盖已存在的输出文件")
    vp.add_argument("--no-memory-values", action="store_true", help="不打包 memory-values.json")
    vu = vs.add_parser("unpack", help="解密并解 tar；--to 解到目录，缺省解回原位")
    vu.add_argument("--repo", default=str(default_repo))
    vu.add_argument("--in", dest="infile", help="默认 vault/ 下名字最新的 keys-*.age")
    vu.add_argument("--to", help="全部解到这个目录（往返验证用）")
    vu.add_argument("--identity", help="默认 ~/.age/key.txt")
    vu.add_argument("--age-dir")
    vu.add_argument("--overwrite", action="store_true", help="覆盖已存在的文件")
    vv = vs.add_parser("verify", help="内存里解密，逐文件比 sha256，标记与值一一对上")
    vv.add_argument("--repo", default=str(default_repo))
    vv.add_argument("--in", dest="infile")
    vv.add_argument("--identity")
    vv.add_argument("--keys-dir")
    vv.add_argument("--ssh-dir")
    vv.add_argument("--age-dir")

    i = sub.add_parser("install", help="本机 Claude Code 接线：rules 比对、memory junction、.dna.md（工程书 3.9 / 4.5）")
    i.add_argument("--repo", default=str(default_repo))
    i.add_argument("--cc-home", help="默认 ~/.claude")
    i.add_argument("--project-dir", help="算 slug 用的项目目录；默认仓库上一级目录")
    i.add_argument("--date", help="备份目录名 memory.pre-junction-<日期>；默认今天")
    i.add_argument("--dry-run", action="store_true", help="只打印要做什么，不改任何东西")

    e = sub.add_parser("export-drive", help="生成 mirror/brain-index.md；--to 时把索引、memory/、soul/、handoff/CURRENT.md 一对一镜像到目录")
    e.add_argument("--repo", default=str(default_repo))
    e.add_argument("--to", help="镜像目标目录（例如 Drive 桌面版的同步文件夹）；缺省只生成索引并列清单")
    e.add_argument("--account", help="写进 env/drive.json 的账号")

    s = sub.add_parser("status", help="未提交改动、未推送提交、距上次提交、handoff 状态；有未提交或未推送退出码 1")
    s.add_argument("--repo", default=str(default_repo))
    s.add_argument("--json", action="store_true", help="JSON 输出，给备份脚本用")

    n = sub.add_parser("init", help="建 3.2 节目录与骨架文件（已有的不覆盖），没有 .git 就 git init")
    n.add_argument("target", nargs="?", help="仓库目录；缺省当前工作目录")
    n.add_argument("--agent", help="写进 handoff 模板的 agent 名；默认环境变量 BRAIN_AGENT 或 brain.py")
    n.add_argument("--no-git", action="store_true", help="不做 git init")

    y = sub.add_parser("sync", help="junction 不可用时的兜底：memory/ 与 ~/.claude/projects/<slug>/memory 双向复制，从不删除")
    y.add_argument("--repo", default=str(default_repo))
    y.add_argument("--cc-home", help="默认 ~/.claude")
    y.add_argument("--project-dir", help="算 slug 用的项目目录；默认仓库上一级目录")
    y.add_argument("--direction", choices=("both", "to-cc", "from-cc"), default="both")
    y.add_argument("--dry-run", action="store_true")

    h = sub.add_parser("handoff", help="3.5 协议：open / claim / close / show；review 比对别的模型交回的候选交接单")
    h.add_argument("action", choices=("open", "claim", "close", "show", "review"))
    h.add_argument("candidate", nargs="?", help="review：候选交接单文件")
    h.add_argument("--repo", default=str(default_repo))
    h.add_argument("--agent", help="默认环境变量 BRAIN_AGENT 或 brain.py")
    h.add_argument("--project", help="open / close 时写进新 CURRENT.md 的 project")
    h.add_argument("--task", help="open / close 时写进 ::STATE 的一句话任务")
    h.add_argument("--slug", help="close 时归档文件名 YYYY-MM-DD-<slug>.md 的 slug；默认用 project")
    h.add_argument("--no-commit", action="store_true", help="只改文件不提交")
    h.add_argument("--baseline", help="review：基线文件；默认 handoff/CURRENT.md")
    h.add_argument("--validator", help="review：正典校验器 ilang_grammar_validator.py 的路径，给了就跑 --lint --strict")
    h.add_argument("--overlay", action="store_true", help="review：候选只含改过的块时，先按标识叠到基线上拼成完整候选再审")
    h.add_argument("--out", help="review --overlay：把拼好的完整候选写到这个文件（接受时替换 CURRENT.md 用）")

    p = sub.add_parser("paste", help="拼给没有工具的对话 AI 的那条消息：开场句 + 速查卡 + --- + 交接单声明块（docs/PASTE.md）")
    p.add_argument("--repo", default=str(default_repo))
    p.add_argument("--out", help="写到文件；缺省打到标准输出")
    p.add_argument("--lang", choices=("auto", "zh", "en"), default="auto", help="速查卡与开场句的语言；auto 按交接单判断（中文占比 >= 0.2 取 zh）；有 rules/GRAMMAR-CARD.<lang>.md 就用它")
    p.add_argument("--with-values", action="store_true", help="3.0：账本行带上值（默认不带；贴给没有工具的聊天模型用不上值）")

    lg = sub.add_parser("ledger", help="3.0 授权账本 env/ledger.env：list / add / verify / show；3.1 encode / decode / harvest / reveal；3.1.2 import <目录>")
    lg.add_argument("action", choices=("list", "add", "verify", "show", "encode", "decode", "harvest", "reveal", "import"))
    lg.add_argument("name", nargs="?", help="行名；verify 可用 all；import 时是目录")
    lg.add_argument("--glob", help="import：只收匹配的文件名，逗号分隔，默认 *")
    lg.add_argument("--skip", help="import：跳过的文件名模式，逗号分隔，默认跳过代码、备份、公钥、证书链")
    lg.add_argument("--dry-run", action="store_true", dest="dry_run", help="import：只列出会建哪些行，不写")
    lg.add_argument("--path", action="append", dest="paths", help="harvest：只收这些路径（默认 memory soul handoff）")
    lg.add_argument("--pepper", help="decode：env/pepper 丢了时用 owner 留的十六进制")
    lg.add_argument("--grant", choices=("once", "standing"), help="add：授权档，默认顶门 once 其他 standing")
    lg.add_argument("--repo", default=str(default_repo))
    lg.add_argument("--door", help="add：这把钥匙开哪扇门（机器 API 仓库 账户）")
    lg.add_argument("--kind", help="add：种类，例如 ssh_password api_key token root payment")
    lg.add_argument("--value", help="add：值，写进 env/keys.env 并以 ref 引用")
    lg.add_argument("--ref", help="add：env/keys.env 里的 KEY 名")
    lg.add_argument("--verify", help="add：验证命令，退出 0 表示门开着；$LEDGER_VALUE 与 $<REF> 可用")
    lg.add_argument("--recover", help="add：丢了怎么回来（控制台、救援模式、第二把钥匙、谁手里有）")
    lg.add_argument("--scope", help="add：范围标签，空格或逗号分隔")
    lg.add_argument("--why", help="add：这扇门为什么存在（它服务的函数或常数）")
    lg.add_argument("--top", action="store_true", help="add：顶门，永远不从记录解锁，只认一次性码")
    lg.add_argument("--with-value", action="store_true", help="show：把值打出来（进上下文）")
    lg.add_argument("--timeout", type=int, default=30, help="verify：每条命令的秒数")

    ul = sub.add_parser("unlock", help="3.0 解锁一行：当前 next 项点到这扇门且在范围内才打出值；顶门只认一次性码")
    ul.add_argument("name")
    ul.add_argument("--repo", default=str(default_repo))
    ul.add_argument("--scope", help="接手方声明的范围标签")
    ul.add_argument("--code", help="顶门的一次性码")
    ul.add_argument("--no-log", action="store_true")

    gr = sub.add_parser("grant", help="3.1 授权记在本机 git config：grant <DOOR> | --all | --write；--revoke 收回；--list 查看")
    gr.add_argument("door", nargs="?")
    gr.add_argument("--repo", default=str(default_repo))
    gr.add_argument("--all", action="store_true", help="本机放行所有 standing 门（顶门与 once 门除外）")
    gr.add_argument("--write", action="store_true", help="本机允许存新钥匙（ledger add --value / harvest / migrate-cc）")
    gr.add_argument("--revoke", action="store_true")
    gr.add_argument("--list", action="store_true")

    ot = sub.add_parser("otp", help="3.0 一次性码（顶门）：issue / revoke / list；owner 在场时发")
    ot.add_argument("action", choices=("issue", "revoke", "list"))
    ot.add_argument("name", nargs="?")
    ot.add_argument("--repo", default=str(default_repo))
    ot.add_argument("--minutes", type=int, default=120)

    pr = sub.add_parser("pair", help="3.0 配对时封装：把范围内的账本行封给对方公钥与 owner 公钥，写声明块")
    pr.add_argument("recipient", help="对方 age 公钥（age1...）或存着它的文件")
    pr.add_argument("--repo", default=str(default_repo))
    pr.add_argument("--scope", default="", help="对方声明的范围标签")
    pr.add_argument("--out", help="输出目录；默认 pair/<日期>-<标签>")
    pr.add_argument("--label")
    pr.add_argument("--age-dir")

    us = sub.add_parser("unseal", help="3.0 用 owner 私钥解开一个封好的行（工具动作）")
    us.add_argument("infile")
    us.add_argument("--identity", help="默认 ~/.age/key.txt")
    us.add_argument("--age-dir")

    lo = sub.add_parser("log", help="3.0 原始轨迹：owner 的发言原文与 agent 的决策行，按日追加到 log/<日期>.md")
    lo.add_argument("who", nargs="?", choices=("owner", "agent"), default="owner")
    lo.add_argument("text", nargs="?", help="文本；- 或缺省读标准输入")
    lo.add_argument("--repo", default=str(default_repo))
    lo.add_argument("--file", help="从文件读文本")
    lo.add_argument("--kind", default="turn", help="turn / decision / unlock ...")
    lo.add_argument("--show", nargs="?", const="", help="打印某天的日志（缺省今天）")

    rz = sub.add_parser("recognize", help="3.0 认人：owner 发言对 soul 锚点的命中率（默认门槛 0.30）与边界矛盾")
    rz.add_argument("--repo", default=str(default_repo))
    rz.add_argument("--days", type=int, default=1, help="窗口天数（含今天）")
    rz.add_argument("--since", help="窗口起始日期 YYYY-MM-DD")
    rz.add_argument("--soul", help="默认 soul/soul.md")
    rz.add_argument("--json", action="store_true")

    pv = sub.add_parser("provenance", help="3.0 来源键 by: ：init 盖 legacy / check / repair（读时规则）")
    pv.add_argument("action", choices=("init", "check", "repair"))
    pv.add_argument("--repo", default=str(default_repo))
    pv.add_argument("--date", help="init：写进 last: 的日期；默认今天")
    pv.add_argument("--commit", action="store_true", help="改完提交")
    pv.add_argument("--transcript", help="宿主转录（Claude Code JSONL）：只有出现在 user 消息里的引文算 owner_verbatim 证据")

    ev = sub.add_parser("evidence", help="3.0 证据：add 记进 soul/evidence.md 并给出 q（3.1 默认 owner_claimed，--transcript 命中才 owner_verbatim）；confirm <q> owner 本人确认；q 只算哈希")
    ev.add_argument("action", choices=("add", "q", "confirm"))
    ev.add_argument("text", nargs="?")
    ev.add_argument("--repo", default=str(default_repo))
    ev.add_argument("--where", help="原话在哪说的（会话、日期、文件）")
    ev.add_argument("--transcript", help="宿主转录（Claude Code JSONL）；原话是其中一条 user 消息才记 owner_verbatim")

    rv = sub.add_parser("review", help="3.0 同一道门：按来源规则审 soul/ memory/ handoff/ 的改动（--staged 给 pre-commit 用）")
    rv.add_argument("files", nargs="*")
    rv.add_argument("--repo", default=str(default_repo))
    rv.add_argument("--staged", action="store_true")
    rv.add_argument("--fix", action="store_true", help="把越过计数器抬上去的 conf 改回 tentative")

    im = sub.add_parser("import", help="3.0 灌记忆：一个入口，全部 by:imported、conf 重置、边界降成 FACT，落 memory/imports/")
    im.add_argument("src")
    im.add_argument("--from", dest="source", required=True, help="来源名")
    im.add_argument("--repo", default=str(default_repo))
    im.add_argument("--date")

    vf = sub.add_parser("verify", help="3.0 常数的边：why / used_by 指向存在的东西，孤儿常数列出来；--online 查 DOI 与 URL")
    vf.add_argument("--repo", default=str(default_repo))
    vf.add_argument("--online", action="store_true")
    vf.add_argument("--strict", action="store_true", help="有缺边或孤儿就退出 1")

    ins = sub.add_parser("instructions", help="3.0 五份指令文件与 SKILL.md 正文逐字一致：sync / check")
    ins.add_argument("action", choices=("sync", "check"))
    ins.add_argument("--repo", default=str(default_repo))

    rm = sub.add_parser("remote-check", help="3.0 推送守卫：远端是不是公开仓库（0 私有/看不见，1 公开，2 不知道）")
    rm.add_argument("url")

    mg = sub.add_parser("migrate-2to3", help="3.0 迁移：把 2.1 的 vault 包解成账本行，所有块盖 by:legacy（owner 跑，要 age 私钥）")
    mg.add_argument("--repo", default=str(default_repo))
    mg.add_argument("--in", dest="infile")
    mg.add_argument("--identity")
    mg.add_argument("--age-dir")

    args = ap.parse_args(argv)
    agent_default = os.environ.get("BRAIN_AGENT") or "brain.py"
    if args.cmd == "check":
        return cmd_check(Path(args.repo).resolve())
    if args.cmd == "init":
        return cmd_init(Path(args.target).resolve() if args.target else Path.cwd(), args.agent or agent_default, args.no_git)
    if args.cmd == "sync":
        repo = Path(args.repo).resolve()
        cc_home = Path(args.cc_home).expanduser() if args.cc_home else Path.home() / ".claude"
        project_dir = Path(args.project_dir).resolve() if args.project_dir else repo.parent
        return cmd_sync(repo, cc_home, project_dir, args.direction, args.dry_run)
    if args.cmd == "handoff":
        if args.action == "review":
            if not args.candidate:
                print("ERROR   handoff review needs the candidate file")
                return 2
            return cmd_handoff_review(Path(args.repo).resolve(), Path(args.candidate).resolve(),
                                      Path(args.baseline).resolve() if args.baseline else None,
                                      Path(args.validator).resolve() if args.validator else None,
                                      args.overlay, Path(args.out).resolve() if args.out else None)
        return cmd_handoff(Path(args.repo).resolve(), args.action, args.agent or agent_default,
                           args.project, args.task, args.slug, args.no_commit)
    if args.cmd == "paste":
        return cmd_paste(Path(args.repo).resolve(), Path(args.out).resolve() if args.out else None, args.lang, args.with_values)
    if args.cmd == "ledger":
        return cmd_ledger(Path(args.repo).resolve(), args.action, args.name,
                          {"door": args.door, "kind": args.kind, "value": args.value, "ref": args.ref, "verify": args.verify,
                           "recover": args.recover, "scope": args.scope, "why": args.why, "top": args.top,
                           "with_value": args.with_value, "timeout": args.timeout, "paths": args.paths, "pepper": args.pepper,
                           "grant": args.grant, "glob": args.glob, "skip": args.skip, "dry_run": args.dry_run})
    if args.cmd == "unlock":
        return cmd_unlock(Path(args.repo).resolve(), args.name, args.scope, args.code, args.no_log)
    if args.cmd == "otp":
        if args.action in ("issue", "revoke") and not args.name:
            print("ERROR   otp issue/revoke needs the door name")
            return 2
        return cmd_otp(Path(args.repo).resolve(), args.action, args.name or "", args.minutes)
    if args.cmd == "pair":
        return cmd_pair(Path(args.repo).resolve(), args.recipient, args.scope, Path(args.out).resolve() if args.out else None,
                        args.age_dir, args.label)
    if args.cmd == "unseal":
        identity = Path(args.identity).expanduser() if args.identity else Path.home() / ".age" / "key.txt"
        return cmd_unseal(Path(args.infile).resolve(), identity, args.age_dir)
    if args.cmd == "log":
        return cmd_log(Path(args.repo).resolve(), args.who, args.text, Path(args.file).resolve() if args.file else None, args.kind, args.show)
    if args.cmd == "recognize":
        return cmd_recognize(Path(args.repo).resolve(), args.days, args.since, args.json, Path(args.soul).resolve() if args.soul else None)
    if args.cmd == "provenance":
        return cmd_provenance(Path(args.repo).resolve(), args.action, args.date, args.commit,
                              Path(args.transcript).resolve() if args.transcript else None)
    if args.cmd == "evidence":
        return cmd_evidence(Path(args.repo).resolve(), args.action, args.text, args.where,
                            Path(args.transcript).resolve() if args.transcript else None)
    if args.cmd == "grant":
        return cmd_grant(Path(args.repo).resolve(), args.door, args.all, args.write, args.revoke, args.list)
    if args.cmd == "review":
        return cmd_review(Path(args.repo).resolve(), args.files, args.staged, args.fix)
    if args.cmd == "import":
        return cmd_import(Path(args.repo).resolve(), Path(args.src).resolve(), args.source, args.date)
    if args.cmd == "verify":
        return cmd_verify(Path(args.repo).resolve(), args.online, args.strict)
    if args.cmd == "instructions":
        return cmd_instructions(Path(args.repo).resolve(), args.action)
    if args.cmd == "remote-check":
        return cmd_remote_check(args.url)
    if args.cmd == "migrate-2to3":
        identity = Path(args.identity).expanduser() if args.identity else Path.home() / ".age" / "key.txt"
        return cmd_migrate_2to3(Path(args.repo).resolve(), Path(args.infile).resolve() if args.infile else None, identity, args.age_dir)
    if args.cmd == "export-drive":
        return cmd_export_drive(Path(args.repo).resolve(), Path(args.to) if args.to else None, args.account)
    if args.cmd == "status":
        return cmd_status(Path(args.repo).resolve(), args.json)
    if args.cmd == "install":
        repo = Path(args.repo).resolve()
        cc_home = Path(args.cc_home).expanduser() if args.cc_home else Path.home() / ".claude"
        project_dir = Path(args.project_dir).resolve() if args.project_dir else repo.parent
        return cmd_install(repo, cc_home, project_dir, args.date or f"{datetime.now():%Y-%m-%d}", args.dry_run)
    if args.cmd == "migrate-cc":
        repo = Path(args.repo).resolve()
        src = Path(args.src).resolve() if args.src else default_cc_memory_dir(repo)
        return cmd_migrate_cc(repo, src, args.overwrite)
    if args.cmd == "vault":
        repo = Path(args.repo).resolve()
        identity = Path(args.identity).expanduser() if getattr(args, "identity", None) else Path.home() / ".age" / "key.txt"
        if args.vcmd == "pack":
            out = Path(args.out) if args.out else repo / "vault" / f"keys-{datetime.now():%Y-%m-%d}.age"
            recipients = Path(args.recipients) if args.recipients else repo / "vault" / "recipients.txt"
            keys_dir = Path(args.keys_dir).expanduser() if args.keys_dir else default_keys_dir(repo)
            ssh_dir = Path(args.ssh_dir).expanduser() if args.ssh_dir else Path.home() / ".ssh"
            source = Path(args.source).expanduser() if args.source else default_cc_memory_dir(repo)
            return cmd_vault_pack(repo, out, recipients, keys_dir, ssh_dir, args.ssh_key, source,
                                  args.age_dir, args.overwrite, not args.no_memory_values)
        infile = Path(args.infile) if args.infile else latest_vault_file(repo)
        if infile is None:
            print("ERROR no vault/keys-*.age found; pass --in")
            return 1
        if args.vcmd == "unpack":
            return cmd_vault_unpack(infile, Path(args.to) if args.to else None, identity, args.age_dir, args.overwrite)
        keys_dir = Path(args.keys_dir).expanduser() if args.keys_dir else default_keys_dir(repo)
        ssh_dir = Path(args.ssh_dir).expanduser() if args.ssh_dir else Path.home() / ".ssh"
        return cmd_vault_verify(repo, infile, identity, keys_dir, ssh_dir, args.age_dir)
    print(f"{args.cmd}: not implemented in brain.py {VERSION} (see 附件 E)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
