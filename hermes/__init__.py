"""Mem-Forever memory provider for Hermes Agent.

Your private Git repository is the agent's brain (a fork of ilang-ai/Mem-Forever):
``BRAIN.md`` is the entry, ``handoff/CURRENT.md`` says where you stopped, ``soul/`` is
who you are, ``memory/`` is one file per memory, ``log/`` keeps the owner's words
verbatim, ``env/ledger.env`` is the ledger of doors. This provider gives Hermes the same
brain every other tool reads:

- session start: saves what a previous session left unsaved, pulls the brain, then
  injects ``BRAIN.md`` (system prompt) and the hand-off, soul and index (first prefetch);
- each turn: appends the owner's words to ``log/`` through ``tools/brain.py`` (background);
- before compression and at session end: commits and pushes ``soul/ memory/ handoff/ log/``
  and hands the ``::PROGRESS`` line to the summary;
- one tool, ``mem_forever``, runs the engine (status, check, ledger_verify, unlock,
  handoff_review, recognize, log, commit, pull). Files are edited with Hermes's own
  file tools; this provider never rewrites a memory.

Nothing leaves the machine except git traffic to the brain's own remote. The provider
holds no credentials: the ledger lives in the brain, encoded at rest (reversible, not
encryption), and a row reaches the context only through ``unlock`` with the owner's
grant on this machine. Subagent and cron runs read the brain and never write to it.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Optional

from agent.memory_provider import MemoryProvider, RecallStatus, spawn_context_thread

logger = logging.getLogger(__name__)

NAME = "mem-forever"
VERSION = "3.2.0"
TEMPLATE = "https://github.com/ilang-ai/Mem-Forever"
LABEL = "Mem-Forever"

# What the first prefetch of a session hands the model, in protocol order (README §4.2).
ENTRY_FILES = ("handoff/CURRENT.md", "soul/soul.md", "soul/agent.md", "memory/MEMORY.md")
# What a session leaves behind and the next one must save (README §4.2 step 2).
SAVE_PATHS = ("soul", "memory", "handoff", "log", "log.md")

_ENGINE_TIMEOUT = 60
_VERIFY_TIMEOUT = 180
_GIT_TIMEOUT = 90
_MAX_INDEX_CHARS = 40_000
_MAX_BUNDLE_CHARS = 90_000

_ACTIONS = ("status", "check", "ledger_verify", "unlock", "handoff_review", "recognize", "log", "commit", "pull")
_WRITE_ACTIONS = {"log", "commit", "pull"}

TOOL_SCHEMA = {
    "name": "mem_forever",
    "description": (
        "Run the Mem-Forever engine on the brain repository named in the system prompt. Actions: "
        "status (HEAD, remote, unsaved files, the ::PROGRESS line); check (brain.py check: 0 errors expected); "
        "ledger_verify (which doors open; name a row or 'all'); unlock (print one ledger row into this "
        "context: refused unless a next item names its door and this machine holds the owner's grant, a top "
        "door also needs the owner's one-time code); handoff_review (compare a candidate hand-off file with "
        "handoff/CURRENT.md before it may replace it); recognize (match the owner's recent words in log/ "
        "against the soul anchors); log (append text to today's log as the agent, kind decision|lesson|note); "
        "commit (commit and push soul/ memory/ handoff/ log/ with a message: do this at every milestone); "
        "pull (fetch and rebase the brain from its remote). Edit the brain's files with the normal file "
        "tools; this tool never edits them."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": list(_ACTIONS)},
            "name": {"type": "string", "description": "unlock: the door; ledger_verify: a row name or 'all' (default all)"},
            "path": {"type": "string", "description": "handoff_review: the candidate file"},
            "text": {"type": "string", "description": "log: the text to append; commit: the commit message"},
            "kind": {"type": "string", "description": "log: decision, lesson, note, ... (default note)"},
            "code": {"type": "string", "description": "unlock: the owner's one-time code for a top door"},
            "scope": {"type": "string", "description": "unlock: the scope label this session declares"},
            "days": {"type": "integer", "description": "recognize: window in days (default 7)"},
        },
        "required": ["action"],
    },
}


def _settings_from_config() -> dict[str, Any]:
    """``memory.mem-forever`` of the active profile's config.yaml; ``{}`` when absent."""
    try:
        from hermes_cli.config import load_config_readonly

        memory = load_config_readonly().get("memory", {})
        block = memory.get(NAME, {}) if isinstance(memory, dict) else {}
    except Exception:
        return {}
    return dict(block) if isinstance(block, dict) else {}


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(path)))


def _is_brain(path: Path) -> bool:
    return (path / "tools" / "brain.py").is_file() and (path / "BRAIN.md").is_file()


class MemForeverProvider(MemoryProvider):
    """One instance per agent; everything is bound in ``initialize()`` from ``hermes_home``."""

    def __init__(self, settings: Optional[dict[str, Any]] = None):
        self._settings = dict(settings) if settings is not None else None
        self._repo: Optional[Path] = None
        self._hermes_home = ""
        self._session_id = ""
        self._context = "primary"
        self._ready = False
        self._reason = ""
        self._injected = False
        self._current_sig = ""
        self._last_recall: Optional[RecallStatus] = None
        self._log_thread: Optional[threading.Thread] = None
        self._push_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    # -- identity and availability -------------------------------------------------------------

    @property
    def name(self) -> str:
        return NAME

    def _conf(self) -> dict[str, Any]:
        return dict(self._settings) if self._settings is not None else _settings_from_config()

    def _default_repo(self, hermes_home: str = "") -> Path:
        if not hermes_home:
            from hermes_constants import get_hermes_home

            hermes_home = str(get_hermes_home())
        return Path(hermes_home) / NAME / "brain"

    def _resolve_repo(self, hermes_home: str) -> Path:
        raw = str(self._conf().get("repo") or "").strip()
        return _expand(raw) if raw else self._default_repo(hermes_home)

    def is_available(self) -> bool:
        """A git binary and either a brain on disk or a remote to clone. No network."""
        if not shutil.which("git"):
            self._reason = "git is not on PATH"
            return False
        conf = self._conf()
        raw = str(conf.get("repo") or "").strip()
        try:
            repo = _expand(raw) if raw else self._default_repo()
        except Exception:
            repo = _expand(raw) if raw else Path()
        if raw and _is_brain(repo) or (not raw and repo != Path() and _is_brain(repo)):
            return True
        if str(conf.get("remote") or "").strip():
            return True
        self._reason = (
            f"no brain repository: run `hermes memory setup`, give memory.{NAME}.repo (a clone of your "
            f"private fork of {TEMPLATE}) or memory.{NAME}.remote (its git URL, cloned on first use)"
        )
        return False

    def unavailable_reason(self) -> str:
        return self._reason

    # -- lifecycle -----------------------------------------------------------------------------

    def initialize(self, session_id: str, **kwargs) -> None:
        self._session_id = session_id
        self._hermes_home = str(kwargs.get("hermes_home") or "")
        if not self._hermes_home:
            self._hermes_home = str(self._default_repo().parent.parent)
        context = kwargs.get("agent_context")
        self._context = context if isinstance(context, str) and context.strip() else "primary"
        self._repo = self._resolve_repo(self._hermes_home)
        self._injected = False
        self._current_sig = ""
        if not _is_brain(self._repo):
            remote = str(self._conf().get("remote") or "").strip()
            if remote and not self._repo.exists():
                self._clone(remote)
        if not _is_brain(self._repo):
            self._ready = False
            self._reason = f"{self._repo} is not a Mem-Forever brain (no tools/brain.py and BRAIN.md)"
            logger.warning("mem-forever: %s", self._reason)
            return
        self._ready = True
        if not self._writes_allowed():
            return
        # Protocol §4.2 step 2: a previous session's unsaved memories are saved first, then the brain
        # is brought level with its remote so this session reads what other tools wrote.
        saved = self._save_leftovers("previous session")
        if saved.get("committed"):
            logger.info("mem-forever: saved %d file(s) a previous session left: %s", saved["committed"], saved["message"])
        pulled = self._pull()
        if pulled.get("error"):
            logger.warning("mem-forever: pull failed, working from the local brain: %s", pulled["error"])
        if saved.get("committed"):
            self._push_async()

    def on_session_switch(self, new_session_id: str, *, parent_session_id: str = "", reset: bool = False,
                          rewound: bool = False, **kwargs) -> None:
        self._session_id = new_session_id
        if reset:
            self._injected = False
            self._current_sig = ""

    def shutdown(self) -> None:
        self._join(self._log_thread, 10.0)
        self._join(self._push_thread, 10.0)

    def _writes_allowed(self) -> bool:
        return self._ready and self._context == "primary"

    # -- what the model sees -------------------------------------------------------------------

    def system_prompt_block(self) -> str:
        if not self._ready:
            return f"# {LABEL}\nNot active: {self._reason}" if self._reason else ""
        brain = self._read("BRAIN.md").strip()
        head = (
            f"# {LABEL} brain\n"
            f"Repository: {self._repo}\n"
            "Read and edit its files with the normal file tools; `mem_forever` runs the engine "
            "(status, check, ledger_verify, unlock, handoff_review, recognize, log, commit, pull). "
            "Hermes saves soul/ memory/ handoff/ log/ before compression and at session end; "
            "at a milestone, save yourself with mem_forever(action=\"commit\")."
        )
        if self._context != "primary":
            head += f"\nThis is a {self._context} run: read the brain, never write to it."
        return f"{head}\n\n{brain}" if brain else head

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if not self._ready:
            return ""
        if not self._injected:
            self._injected = True
            self._current_sig = self._sig("handoff/CURRENT.md")
            parts: list[str] = []
            for rel in ENTRY_FILES:
                text = self._read(rel).strip()
                if not text:
                    continue
                if rel == "memory/MEMORY.md" and len(text) > _MAX_INDEX_CHARS:
                    cut = text[:_MAX_INDEX_CHARS]
                    cut = cut[: cut.rfind("\n") + 1] or cut
                    text = cut + f"\n[index cut at {_MAX_INDEX_CHARS} characters; read {rel} for the rest]"
                parts.append(f"## {rel}\n{text}")
            self._last_recall = RecallStatus(provider_label=LABEL, count=len(parts)) if parts else None
            if not parts:
                return ""
            bundle = "\n\n".join([f"# {LABEL} brain · {self._short_status()}", *parts])
            return bundle[:_MAX_BUNDLE_CHARS]
        sig = self._sig("handoff/CURRENT.md")
        if sig and sig != self._current_sig:
            self._current_sig = sig
            self._last_recall = RecallStatus(provider_label=LABEL, count=1)
            return f"# {LABEL}: handoff/CURRENT.md changed on disk\n{self._read('handoff/CURRENT.md').strip()}"
        self._last_recall = None
        return ""

    def recall_status(self) -> Optional[RecallStatus]:
        return self._last_recall

    # -- writes --------------------------------------------------------------------------------

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "",
                  messages: Optional[list[dict[str, Any]]] = None,
                  turn_author: Optional[dict[str, Any]] = None) -> None:
        """The owner's words go to log/ verbatim (README §4.5); non-blocking, never the assistant's."""
        if not self._writes_allowed():
            return
        text = (user_content or "").strip()
        if not text or (isinstance(turn_author, dict) and turn_author.get("is_bot")):
            return

        def _work() -> None:
            result = self._engine("log", "owner", "--kind", "turn", "-", text=text)
            if not result["ok"]:
                logger.warning("mem-forever: log owner failed: %s", result.get("error") or result.get("output"))

        self._join(self._log_thread, 5.0)
        self._log_thread = spawn_context_thread(_work, name="mem-forever-log")
        self._log_thread.start()

    def on_memory_write(self, action: str, target: str, content: str,
                        metadata: Optional[dict[str, Any]] = None) -> None:
        """A write through Hermes's built-in memory tool leaves a trace in the brain's log."""
        if not self._writes_allowed() or not content or action not in {"add", "replace"}:
            return
        text = f"[hermes built-in memory {action} {target}] {content}"

        def _work() -> None:
            self._engine("log", "agent", "--kind", "memory_write", "-", text=text)

        thread = spawn_context_thread(_work, name="mem-forever-mirror")
        thread.start()

    def on_pre_compress(self, messages: list[dict[str, Any]]) -> str:
        if not self._ready:
            return ""
        if self._writes_allowed():
            self._join(self._log_thread, 10.0)
            self._save_leftovers("before compression")
            self._push_async()
        line = self._progress_line()
        if not line:
            return ""
        return f"{LABEL} hand-off; keep its done, next and unverified verbatim in the summary:\n{line}"

    def on_session_end(self, messages: list[dict[str, Any]]) -> None:
        if not self._writes_allowed():
            return
        self._join(self._log_thread, 10.0)
        saved = self._save_leftovers("session end")
        if saved.get("committed"):
            self._push()

    def on_delegation(self, task: str, result: str, *, child_session_id: str = "", **kwargs) -> None:
        return None

    # -- tools ---------------------------------------------------------------------------------

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [TOOL_SCHEMA] if self._ready or self._repo is None else []

    def handle_tool_call(self, tool_name: str, args: dict[str, Any], **kwargs) -> str:
        from tools.registry import tool_error

        if tool_name != TOOL_SCHEMA["name"]:
            return tool_error(f"Unknown tool: {tool_name}")
        if not self._ready:
            return tool_error(f"{LABEL} is not active: {self._reason}")
        action = str(args.get("action") or "").strip()
        if action not in _ACTIONS:
            return tool_error(f"action must be one of {', '.join(_ACTIONS)}")
        if action in _WRITE_ACTIONS and not self._writes_allowed():
            return tool_error(f"{action} is refused in a {self._context} run: the brain is read-only here")
        try:
            result = self._run_action(action, args)
        except Exception as exc:  # the engine's own error text is the useful part
            return tool_error(f"{action} failed: {exc}")
        if not result.get("ok", True):
            return tool_error(result.get("error") or result.get("output") or f"{action} failed")
        return json.dumps(result, ensure_ascii=False)

    def _run_action(self, action: str, args: dict[str, Any]) -> dict[str, Any]:
        if action == "status":
            engine = self._engine("status", "--json")
            payload: dict[str, Any] = {"ok": True, "repo": str(self._repo), "context": self._context,
                                       "head": self._head(), "remote": self._remote_name(),
                                       "unsaved": self._dirty(), "progress": self._progress_line()}
            if engine["ok"]:
                try:
                    payload["engine"] = json.loads(engine["output"])
                except ValueError:
                    payload["engine"] = engine["output"]
            else:
                payload["engine_error"] = engine.get("error") or engine.get("output")
            return payload
        if action == "check":
            return self._engine("check")
        if action == "ledger_verify":
            return self._engine("ledger", "verify", str(args.get("name") or "all"), timeout=_VERIFY_TIMEOUT)
        if action == "unlock":
            door = str(args.get("name") or "").strip()
            if not door:
                return {"ok": False, "error": "unlock needs name (the door)"}
            cmd = ["unlock", door]
            if args.get("scope"):
                cmd += ["--scope", str(args["scope"])]
            if args.get("code"):
                cmd += ["--code", str(args["code"])]
            return self._engine(*cmd)
        if action == "handoff_review":
            candidate = str(args.get("path") or "").strip()
            if not candidate:
                return {"ok": False, "error": "handoff_review needs path (the candidate file)"}
            result = self._engine("handoff", "review", candidate)
            # exit 0 clean, 1 rejected, 3 for the owner: all three are answers, not failures
            result["ok"] = result.get("exit") in (0, 1, 3)
            result["verdict"] = {0: "clean", 1: "rejected", 3: "for the owner"}.get(result.get("exit"), "error")
            return result
        if action == "recognize":
            days = args.get("days")
            cmd = ["recognize", "--json"]
            if isinstance(days, int) and days > 0:
                cmd += ["--days", str(days)]
            return self._engine(*cmd)
        if action == "log":
            text = str(args.get("text") or "").strip()
            if not text:
                return {"ok": False, "error": "log needs text"}
            kind = str(args.get("kind") or "note").strip() or "note"
            return self._engine("log", "agent", "--kind", kind, "-", text=text)
        if action == "commit":
            message = str(args.get("text") or "").strip() or "milestone"
            self._join(self._log_thread, 10.0)
            saved = self._save_leftovers(message)
            if saved.get("error"):
                return {"ok": False, "error": saved["error"]}
            pushed = self._push() if saved.get("committed") else {"skipped": "nothing to commit"}
            return {"ok": True, "saved": saved, "pushed": pushed}
        if action == "pull":
            pulled = self._pull()
            return {"ok": not pulled.get("error"), **pulled}
        return {"ok": False, "error": f"unknown action {action}"}

    # -- setup ---------------------------------------------------------------------------------

    def get_config_schema(self) -> list[dict[str, Any]]:
        return [
            {
                "key": "repo",
                "description": (
                    f"Path of your brain repository, a clone of your private fork of {TEMPLATE}; "
                    f"empty = <hermes_home>/{NAME}/brain"
                ),
                "default": "",
            },
            {
                "key": "remote",
                "description": (
                    "Git URL of that private repository, cloned into the path on first use when the path "
                    "is empty (git on this machine must already be able to read it); empty if the path exists"
                ),
                "default": "",
            },
        ]

    def save_config(self, values: dict[str, Any], hermes_home: str) -> None:
        from hermes_cli.config import load_config, save_config

        config = load_config()
        memory = config.get("memory")
        if not isinstance(memory, dict):
            memory = {}
            config["memory"] = memory
        block = memory.get(NAME)
        if not isinstance(block, dict):
            block = {}
        for key in ("repo", "remote"):
            if key in values:
                block[key] = str(values.get(key) or "").strip()
        memory[NAME] = block
        save_config(config, merge_existing=True)

    def backup_paths(self) -> list[str]:
        conf = self._conf()
        raw = str(conf.get("repo") or "").strip()
        if not raw:
            return []
        repo = _expand(raw)
        return [str(repo)] if repo.is_dir() else []

    # -- the brain on disk ---------------------------------------------------------------------

    def _read(self, rel: str) -> str:
        if self._repo is None:
            return ""
        path = self._repo / rel
        try:
            return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        except OSError:
            return ""

    def _sig(self, rel: str) -> str:
        text = self._read(rel)
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16] if text else ""

    def _progress_line(self) -> str:
        for line in self._read("handoff/CURRENT.md").splitlines():
            if line.startswith("::PROGRESS{"):
                return line.strip()
        return ""

    def _short_status(self) -> str:
        head = self._head()
        dirty = self._dirty()
        state = "clean" if not dirty else f"{len(dirty)} file(s) unsaved"
        return f"{self._repo} · HEAD {head or 'none'} · {state}"

    # -- subprocesses --------------------------------------------------------------------------

    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env.setdefault("GIT_TERMINAL_PROMPT", "0")
        env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env.setdefault("BRAIN_AGENT", "hermes")
        return env

    def _engine(self, *args: str, text: Optional[str] = None, timeout: int = _ENGINE_TIMEOUT) -> dict[str, Any]:
        """Run ``tools/brain.py`` of the brain; ``text`` feeds stdin (``-`` arguments read it)."""
        if self._repo is None:
            return {"ok": False, "error": "no brain bound"}
        cmd = [sys.executable, "-X", "utf8", str(self._repo / "tools" / "brain.py"), *args]
        run_kwargs: dict[str, Any] = {"input": text} if text is not None else {"stdin": subprocess.DEVNULL}
        try:
            with self._lock:
                proc = subprocess.run(
                    cmd, cwd=str(self._repo), capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=timeout, env=self._env(), check=False, **run_kwargs,
                )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"brain.py {args[0]} timed out after {timeout}s"}
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        return {"ok": proc.returncode == 0, "exit": proc.returncode, "output": out,
                "error": err if proc.returncode else ""}

    def _git(self, *args: str, timeout: int = _GIT_TIMEOUT) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self._repo), *args], capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, env=self._env(), stdin=subprocess.DEVNULL, check=False,
        )

    def _head(self) -> str:
        try:
            proc = self._git("rev-parse", "--short", "HEAD", timeout=15)
        except (subprocess.TimeoutExpired, OSError):
            return ""
        return proc.stdout.strip() if proc.returncode == 0 else ""

    def _remote_name(self) -> str:
        try:
            proc = self._git("remote", timeout=15)
        except (subprocess.TimeoutExpired, OSError):
            return ""
        names = [n for n in proc.stdout.split() if n]
        return names[0] if proc.returncode == 0 and names else ""

    def _dirty(self, paths: tuple[str, ...] = SAVE_PATHS) -> list[str]:
        try:
            proc = self._git("status", "--porcelain", "--untracked-files=all", "--", *paths, timeout=30)
        except (subprocess.TimeoutExpired, OSError):
            return []
        if proc.returncode != 0:
            return []
        return [line[3:].strip() for line in proc.stdout.splitlines() if line.strip()]

    def _save_leftovers(self, why: str) -> dict[str, Any]:
        """Commit soul/ memory/ handoff/ log/ (README §4.2 step 2); ``{"committed": n}`` or ``{"error"}``."""
        with self._lock:
            dirty = self._dirty()
            if not dirty:
                return {"committed": 0}
            try:
                self._git("add", "-A", "--", *SAVE_PATHS, timeout=30)
                message = f"mem-forever ({why}): {len(dirty)} file(s), Hermes session {self._session_id[:8]}"
                proc = self._git("commit", "-q", "-m", message, timeout=30)
            except (subprocess.TimeoutExpired, OSError) as exc:
                return {"error": f"git commit failed: {exc}"}
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout).strip()
                logger.warning("mem-forever: commit failed: %s", detail)
                return {"error": f"git commit failed: {detail}"}
            return {"committed": len(dirty), "message": message, "files": dirty}

    def _pull(self) -> dict[str, Any]:
        if not self._remote_name():
            return {"skipped": "no remote"}
        with self._lock:
            try:
                proc = self._git("pull", "--rebase", "--autostash", "-q")
            except (subprocess.TimeoutExpired, OSError) as exc:
                self._abort_rebase()
                return {"error": f"git pull failed: {exc}"}
            if proc.returncode != 0:
                self._abort_rebase()
                return {"error": (proc.stderr or proc.stdout).strip() or f"git pull exited {proc.returncode}"}
            return {"pulled": True, "head": self._head()}

    def _abort_rebase(self) -> None:
        try:
            self._git("rebase", "--abort", timeout=30)
        except (subprocess.TimeoutExpired, OSError):
            pass

    def _push(self) -> dict[str, Any]:
        if not self._remote_name():
            return {"skipped": "no remote"}
        with self._lock:
            try:
                proc = self._git("push", "-q")
            except (subprocess.TimeoutExpired, OSError) as exc:
                return {"error": f"git push failed: {exc}"}
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip()
            logger.warning("mem-forever: push failed: %s", detail)
            return {"error": detail or f"git push exited {proc.returncode}"}
        return {"pushed": True}

    def _push_async(self) -> None:
        if not self._remote_name():
            return
        self._join(self._push_thread, 5.0)
        self._push_thread = spawn_context_thread(self._push, name="mem-forever-push")
        self._push_thread.start()

    def _clone(self, remote: str) -> None:
        assert self._repo is not None
        self._repo.parent.mkdir(parents=True, exist_ok=True)
        try:
            proc = subprocess.run(
                ["git", "clone", "-q", remote, str(self._repo)], capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=300, env=self._env(), stdin=subprocess.DEVNULL,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.warning("mem-forever: clone of %s failed: %s", remote, exc)
            return
        if proc.returncode != 0:
            logger.warning("mem-forever: clone of %s failed: %s", remote, (proc.stderr or proc.stdout).strip())

    @staticmethod
    def _join(thread: Optional[threading.Thread], timeout: float) -> None:
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)


def register(ctx) -> None:
    """Hermes memory plugin entry point: the provider plus the protocol as a read-only skill."""
    ctx.register_memory_provider(MemForeverProvider())
    skill = Path(__file__).parent / "skills" / "mem-forever" / "SKILL.md"
    register_skill = getattr(ctx, "register_skill", None)
    if register_skill is None or not skill.is_file():
        return
    try:
        register_skill(
            "mem-forever", skill,
            "The Mem-Forever protocol: load the brain at session start, save at every milestone, "
            "review a hand-off another model wrote before it replaces CURRENT.md",
        )
    except Exception as exc:  # an older Hermes or a probe context; the provider still works
        logger.debug("mem-forever: skill registration skipped: %s", exc)
