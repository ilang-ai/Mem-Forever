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
import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

VERSION = "1.5"
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

    # 4. 密钥前缀扫描：全仓库，只报位置不回显
    hits, scan_warnings, scanned = secret_scan(repo)
    errors += hits
    warnings += scan_warnings

    # 5. 字节上限（代理指标）
    for rel, limit in BYTE_LIMITS.items():
        p = repo / rel
        if not p.is_file():
            warnings.append(f"{rel}: missing")
        elif p.stat().st_size > limit:
            warnings.append(f"{rel}: {p.stat().st_size} bytes > {limit} (400 token 需用 Playground 实测)")

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
             "vault", "projects", "mirror", "tools")
INIT_KEEP = ("handoff/archive", "skills", "env/scheduled-tasks", "vault", "projects", "mirror")

INIT_BRAIN_MD = """# BRAIN.md · read this and take over

This is the entry point of one person's agent brain. No runtime to load; read in this order.

1. `handoff/CURRENT.md` first: what was done, what comes next, what is unverified. Restate it in two sentences, then start.
2. Then every file under `soul/`: how the user works and where the lines are, and the agent's own soul in `soul/agent.md`. Follow it; do not recite it.
3. Then `memory/MEMORY.md`, one line per memory. Open a file under `memory/` only when the task needs it.
4. Reading or updating the hand-off is not doing the work. Judge each `next` item before acting: it crosses a boundary, stop; evidence is missing, ask; it is the owner's call, defer. A recap or hand-off request authorizes nothing.
5. New facts: if you can write this repo, edit the file, commit and push at once, one change per commit. If you cannot, hand the change back as `::PROGRESS{date|done|next|unverified}`, `::DECIDE{}` or `::LESSON{}` blocks in one code fence, every key present, `none` where there is no material; a git-capable tool reviews and records it.
6. Update `handoff/CURRENT.md` at every milestone, not at session end.
7. No secrets live here. `vault/` is encrypted and opens only when the owner says so.
8. `::BLOCK{k:v|k:v}`, `T:` and `A:⇒` are declaration notation: read them literally; the quick card is `rules/GRAMMAR-CARD.md`.

<!-- Gate: about 400 tokens on the receiving model's tokenizer; measure before changing. Doubles as Claude.ai project, ChatGPT custom and Gemini Gem instructions. -->
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

INIT_ENV_README = """# env/ — machine environment, no secrets

settings.json (agent CLI settings), mcp.json (key fields as ${VAULT:name}), scheduled-tasks/, ssh_config.template, install.ps1 / install.sh.
Anything that would let someone act as you goes into vault/ (see docs/VAULT.md or rules/SECRETS.md), never here.
"""

INIT_GITIGNORE = "__pycache__/\n*.pyc\n*.tmp\n"

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
    put(".gitignore", INIT_GITIGNORE)
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
    "zh": "下面是一张记法速查卡和一份用这种记法写的工作交接单。请先读卡，再读交接单，然后只回一句「读完了」。后面我会提问。",
    "en": "Below are a notation quick card and a hand-off note written in that notation. Read the card first, then the hand-off, then reply with just: done reading. I will ask questions after that.",
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


def build_paste(repo: Path, lang: str) -> tuple[str, Path]:
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
    return f"{opening}\n\n{card}\n\n---\n\n{blocks}\n", card_path


def cmd_paste(repo: Path, out: Path | None, lang: str) -> int:
    try:
        text, card_path = build_paste(repo, lang)
    except FileNotFoundError as e:
        print(f"ERROR   {e}", file=sys.stderr)
        return 1
    hits = _secret_hits_in_text(text)
    if hits:
        for h in hits:
            print(f"ERROR   {h}", file=sys.stderr)
        print(f"paste: refused, {len(hits)} secret-like hits; nothing written", file=sys.stderr)
        return 1
    data = text.encode("utf-8")
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print(f"paste   {out}: {len(data)} bytes, card {card_path.name}, 0 secret-like hits; send it as one message (docs/PASTE.md)", file=sys.stderr)
    else:
        sys.stdout.write(text)
        sys.stdout.flush()
        print(f"paste   {len(data)} bytes, card {card_path.name}, 0 secret-like hits; send it as one message (docs/PASTE.md)", file=sys.stderr)
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
    return bool(toks_a & toks_b)


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
        return cmd_paste(Path(args.repo).resolve(), Path(args.out).resolve() if args.out else None, args.lang)
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
