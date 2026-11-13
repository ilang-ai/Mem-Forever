"""Behavior tests for the Hermes memory provider in hermes/.

Runs against a real Hermes checkout when ``agent.memory_provider`` is importable, otherwise
against a stub of the three Hermes modules the provider touches, so the template's CI can
exercise the provider without Hermes. Everything happens in a temporary brain created by
``tools/brain.py init``; nothing on the machine is touched.

    python -X utf8 hermes/test_hermes_plugin.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import types
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ENGINE = ROOT / "tools" / "brain.py"


def _stub_hermes() -> None:
    """Minimal stand-ins for agent.memory_provider, tools.registry, hermes_cli.config, hermes_constants."""
    import abc
    from dataclasses import dataclass

    mp = types.ModuleType("agent.memory_provider")

    @dataclass
    class RecallStatus:
        provider_label: str
        count: int
        glyph: str = "🧠"

    class MemoryProvider(abc.ABC):
        def unavailable_reason(self): return ""
        def system_prompt_block(self): return ""
        def prefetch(self, query, *, session_id=""): return ""
        def queue_prefetch(self, query, *, session_id=""): return None
        def recall_status(self): return None
        def sync_turn(self, *a, **k): return None
        def handle_tool_call(self, tool_name, args, **kwargs): raise NotImplementedError
        def shutdown(self): return None
        def on_memory_write(self, *a, **k): return None
        def on_session_end(self, messages): return None
        def on_session_switch(self, *a, **k): return None
        def on_pre_compress(self, messages): return ""
        def on_delegation(self, *a, **k): return None
        def get_config_schema(self): return []
        def save_config(self, values, hermes_home): return None
        def backup_paths(self): return []

    def spawn_context_thread(target, *, name, daemon=True, args=(), kwargs=None):
        return threading.Thread(target=target, name=name, daemon=daemon, args=args, kwargs=kwargs or {})

    mp.MemoryProvider, mp.RecallStatus, mp.spawn_context_thread = MemoryProvider, RecallStatus, spawn_context_thread
    agent = types.ModuleType("agent")
    agent.memory_provider = mp
    sys.modules["agent"], sys.modules["agent.memory_provider"] = agent, mp

    registry = types.ModuleType("tools.registry")
    registry.tool_error = lambda message: json.dumps({"error": message})
    tools = types.ModuleType("tools")
    tools.registry = registry
    sys.modules["tools"], sys.modules["tools.registry"] = tools, registry

    config = types.ModuleType("hermes_cli.config")
    config.load_config_readonly = lambda: {}
    config.load_config = lambda: {}
    config.save_config = lambda cfg, **kw: None
    hermes_cli = types.ModuleType("hermes_cli")
    hermes_cli.config = config
    sys.modules["hermes_cli"], sys.modules["hermes_cli.config"] = hermes_cli, config

    constants = types.ModuleType("hermes_constants")
    constants.get_hermes_home = lambda: Path(tempfile.gettempdir()) / "hermes-home-stub"
    sys.modules["hermes_constants"] = constants


def _load_plugin():
    spec = importlib.util.spec_from_file_location("mem_forever_hermes", HERE / "__init__.py",
                                                  submodule_search_locations=[str(HERE)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", check=False)


def _make_brain(home: Path) -> Path:
    brain = home / "mem-forever" / "brain"
    proc = subprocess.run([sys.executable, "-X", "utf8", str(ENGINE), "init", str(brain)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    for key, value in (("user.name", "mem-forever test"), ("user.email", "test@example.invalid"),
                       ("commit.gpgsign", "false")):
        _git(brain, "config", key, value)
    _git(brain, "add", "-A")
    _git(brain, "commit", "-q", "-m", "brain: init")
    assert _git(brain, "rev-parse", "HEAD").returncode == 0, "init did not leave a git repository"
    return brain


def main() -> int:
    stubbed = False
    try:
        import agent.memory_provider  # noqa: F401
    except ImportError:
        _stub_hermes()
        stubbed = True
    plugin = _load_plugin()
    passed = 0

    def ok(cond: bool, what: str) -> None:
        nonlocal passed
        assert cond, what
        passed += 1
        print(f"  ok  {what}")

    with tempfile.TemporaryDirectory(prefix="mem-forever-hermes-") as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        brain = _make_brain(home)
        today = f"{datetime.now():%Y-%m-%d}"

        # register() hands Hermes one provider and the skill
        recorded: dict = {}

        class Ctx:
            def register_memory_provider(self, provider): recorded["provider"] = provider
            def register_skill(self, name, path, description=""): recorded["skill"] = (name, Path(path))

        plugin.register(Ctx())
        ok(isinstance(recorded.get("provider"), plugin.MemForeverProvider), "register() registers the provider")
        ok(recorded.get("skill", ("",))[0] == "mem-forever" and recorded["skill"][1].is_file(),
           "register() registers the mem-forever skill from the plugin directory")
        root_skill = (ROOT / "skills" / "mem-forever" / "SKILL.md").read_bytes()
        ok(recorded["skill"][1].read_bytes() == root_skill, "the plugin's SKILL.md is byte-identical to skills/mem-forever/SKILL.md")

        # availability and binding
        provider = plugin.MemForeverProvider({"repo": str(brain)})
        ok(provider.name == "mem-forever", "name")
        ok(provider.is_available(), "is_available with a brain on disk")
        missing = plugin.MemForeverProvider({"repo": str(home / "nowhere")})
        ok(not missing.is_available() and "no brain repository" in missing.unavailable_reason(),
           "is_available false without a brain or a remote, with a reason")
        provider.initialize("session-0001", hermes_home=str(home), platform="cli", agent_context="primary")
        ok(provider._ready, "initialize binds the brain")

        # what the model sees
        block = provider.system_prompt_block()
        ok(block.startswith("# Mem-Forever brain") and "BRAIN.md" in block and "mem_forever" in block,
           "system prompt block carries BRAIN.md and names the tool")
        bundle = provider.prefetch("where did we stop last time")
        ok("## handoff/CURRENT.md" in bundle and "::PROGRESS{" in bundle and "## memory/MEMORY.md" in bundle,
           "first prefetch hands over the hand-off, soul and index")
        ok(provider.recall_status() is not None and provider.recall_status().count >= 3, "recall status counts the files")
        ok(provider.prefetch("and now?") == "", "second prefetch is empty while CURRENT.md is unchanged")
        current = brain / "handoff" / "CURRENT.md"
        current.write_text(current.read_text(encoding="utf-8").replace("<one-line task>", "ship the plugin"), encoding="utf-8")
        ok("CURRENT.md changed on disk" in provider.prefetch("next"), "a changed CURRENT.md is handed over again")
        tools = provider.get_tool_schemas()
        ok(len(tools) == 1 and tools[0]["name"] == "mem_forever", "one tool, mem_forever")

        # the owner's words go to log/ verbatim, in the background
        provider.sync_turn("Decide: the plugin ships tonight, not tomorrow.", "Noted.", session_id="session-0001")
        provider.sync_turn("ok", "", session_id="session-0001", turn_author={"id": "bot", "name": "b", "is_bot": True})
        provider.shutdown()
        log_file = brain / "log" / f"{today}.md"
        log_text = log_file.read_text(encoding="utf-8") if log_file.is_file() else ""
        ok("Decide: the plugin ships tonight, not tomorrow." in log_text and "::EVENT{@OWNER" in log_text,
           "sync_turn logs the owner's words through brain.py log owner")
        ok(log_text.count("::EVENT{") == 1, "a bot author's turn is not logged")

        # tool actions
        status = json.loads(provider.handle_tool_call("mem_forever", {"action": "status"}))
        ok(status.get("ok") and status.get("head") and "::PROGRESS{" in status.get("progress", ""),
           "status reports HEAD and the ::PROGRESS line")
        ok(any(p.startswith("log/") for p in status.get("unsaved", [])) and "handoff/CURRENT.md" in status["unsaved"],
           "status lists the unsaved log and hand-off")
        check = json.loads(provider.handle_tool_call("mem_forever", {"action": "check"}))
        ok(check.get("ok") and "0 errors" in check.get("output", ""), "check runs brain.py check: 0 errors")
        logged = json.loads(provider.handle_tool_call("mem_forever", {"action": "log", "text": "lesson: test first", "kind": "lesson"}))
        ok(logged.get("ok") and "lesson: test first" in log_file.read_text(encoding="utf-8"), "log appends the agent's lesson")
        bad = json.loads(provider.handle_tool_call("mem_forever", {"action": "fly"}))
        ok("error" in bad, "an unknown action is a tool error")
        review = json.loads(provider.handle_tool_call("mem_forever", {"action": "handoff_review", "path": str(current)}))
        ok(review.get("verdict") in {"clean", "rejected", "for the owner"}, f"handoff_review returns a verdict ({review.get('verdict')})")

        # before compression: save, push (no remote: skipped), hand the PROGRESS line to the summary
        summary = provider.on_pre_compress([])
        ok(summary.startswith("Mem-Forever hand-off") and "::PROGRESS{" in summary, "on_pre_compress hands the ::PROGRESS line to the summary")
        provider.shutdown()
        after = json.loads(provider.handle_tool_call("mem_forever", {"action": "status"}))
        ok(after["head"] != status["head"] and not after["unsaved"], "on_pre_compress committed the unsaved files")
        last = _git(brain, "log", "-1", "--format=%s").stdout.strip()
        ok(last.startswith("mem-forever (before compression)"), f"commit message names the moment: {last}")
        committed = json.loads(provider.handle_tool_call("mem_forever", {"action": "commit", "text": "nothing new"}))
        ok(committed.get("ok") and committed["saved"].get("committed") == 0, "commit with nothing to save is a no-op")

        # a new session saves what the previous one left behind
        (brain / "memory" / "note-one.md").write_text("---\ntype: project\nname: note-one\ndescription: a note\n---\n\nleft unsaved\n", encoding="utf-8")
        again = plugin.MemForeverProvider({"repo": str(brain)})
        again.initialize("session-0002", hermes_home=str(home), platform="cli", agent_context="primary")
        ok(not again._dirty(), "initialize of the next session commits the leftover memory file")
        ok(_git(brain, "log", "-1", "--format=%s").stdout.startswith("mem-forever (previous session)"), "the leftover commit names the previous session")

        # subagent and cron runs never write
        sub = plugin.MemForeverProvider({"repo": str(brain)})
        sub.initialize("session-0003", hermes_home=str(home), platform="cli", agent_context="subagent")
        before = (brain / "log" / f"{today}.md").read_text(encoding="utf-8")
        sub.sync_turn("a subagent's user message", "reply", session_id="session-0003")
        sub.shutdown()
        ok((brain / "log" / f"{today}.md").read_text(encoding="utf-8") == before, "a subagent run does not log")
        refused = json.loads(sub.handle_tool_call("mem_forever", {"action": "commit", "text": "x"}))
        ok("error" in refused and "read-only" in refused["error"], "commit is refused in a subagent run")
        ok("subagent run" in sub.system_prompt_block(), "the subagent's system prompt says the brain is read-only")
        ok("## handoff/CURRENT.md" in sub.prefetch("status?"), "a subagent still reads the hand-off")

        # config schema and backup paths
        schema = provider.get_config_schema()
        ok([f["key"] for f in schema] == ["repo", "remote"] and not any(f.get("secret") for f in schema),
           "config schema: repo and remote, no secrets")
        ok(provider.backup_paths() == [str(brain)], "backup_paths names the brain outside hermes_home")

    print(f"hermes plugin tests: {passed} passed ({'stubbed Hermes' if stubbed else 'real Hermes'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
