# -*- coding: utf-8 -*-
"""Behavior tests for brain.py 2.0 (Mem-Forever 3.0): ledger, unlock, one-time code, log, recognize, provenance,
review, import, verify, instructions, paste, the push guard parser, the secret-scan exemptions.
Standard library only. Run: python -X utf8 tools/test_brain.py
Every test builds its own brain in a temporary directory; nothing touches the user's machine (install is dry-run only)."""
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("brain", HERE / "brain.py")
brain = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brain)

ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")


def run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace", env=ENV)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(*a, **k)
    return rc, buf.getvalue()


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="brain3-"))
        self.repo = self.tmp / "b"
        rc, out = quiet(brain.cmd_init, self.repo, "test", False)
        self.assertEqual(rc, 0, out)
        run(["git", "config", "core.autocrlf", "false"], self.repo)
        run(["git", "add", "-A"], self.repo)
        r = run(["git", "commit", "-q", "-m", "init"], self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.B = [sys.executable, "-X", "utf8", str(self.repo / "tools" / "brain.py")]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cli(self, *args):
        return run(self.B + list(args), self.repo)

    def write(self, rel, text):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))

    def read(self, rel):
        return (self.repo / rel).read_bytes().decode("utf-8")

    # ---- init / hooks / check
    def test_init_writes_ledger_log_pair_and_hooks(self):
        self.assertTrue((self.repo / "env" / "ledger.env").is_file())
        self.assertTrue((self.repo / "log").is_dir())
        self.assertTrue((self.repo / "pair").is_dir())
        self.assertTrue((self.repo / "tools" / "hooks" / "pre-commit").is_file())
        self.assertTrue((self.repo / "tools" / "hooks" / "pre-push").is_file())
        self.assertEqual(run(["git", "config", "core.hooksPath"], self.repo).stdout.strip(), "tools/hooks")
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_check_exempts_env_and_log_from_the_secret_scan(self):
        tok = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123456789"
        self.write("env/keys.env", f"GH={tok}\n")
        self.write("log/2026-11-08.md", f"# 2026-11-08\n\n::EVENT{{@OWNER, at:10:00, kind:turn}}\nthe pass" + "word: Example12345 and {tok}\n\n")
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.write("memory/leak.md", f"---\ntype: reference\nname: leak\ndescription: x\n---\n{tok}\n")
        r = self.cli("check")
        self.assertEqual(r.returncode, 1, r.stdout)

    # ---- ledger
    def add_rows(self):
        r = self.cli("ledger", "add", "hk", "--door", "ssh root@203.0.113.5", "--kind", "ssh_password", "--value", "pw-Example-123",
                     "--verify", '"' + sys.executable + '" -c "import os,sys;sys.exit(0 if os.environ.get(\'HK\') and os.environ.get(\'HK\')==os.environ.get(\'LEDGER_VALUE\') else 1)"',
                     "--recover", "provider console", "--scope", "fleet", "--why", "hub")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.cli("ledger", "add", "bank", "--door", "bank account", "--kind", "payment", "--value", "s3cret", "--recover", "branch")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_ledger_add_list_verify_and_stale(self):
        self.add_rows()
        keys = self.read("env/keys.env")
        self.assertIn("HK=pw-Example-123", keys)
        r = self.cli("ledger", "list")
        self.assertIn("HK", r.stdout)
        self.assertIn("stale   2", r.stdout)
        r = self.cli("ledger", "verify", "all")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PASS    HK", r.stdout)
        self.assertIn("SKIP    BANK", r.stdout)
        self.assertIn("1 stale", r.stdout)
        self.assertRegex(self.read("env/ledger.env"), r"@HK,.*last_verified:\d{4}-\d{2}-\d{2}")
        r = self.cli("ledger", "show", "hk")
        self.assertNotIn("pw-Example", r.stdout)
        r = self.cli("ledger", "show", "hk", "--with-value")
        self.assertIn("pw-Example-123", r.stdout)

    def test_ledger_verify_failure_exits_one(self):
        self.cli("ledger", "add", "dead", "--door", "nowhere", "--kind", "token", "--value", "x", "--verify", '"' + sys.executable + '" -c "import sys;sys.exit(3)"', "--recover", "none")
        r = self.cli("ledger", "verify", "dead")
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL    DEAD", r.stdout)

    # ---- unlock / otp
    def test_unlock_requires_a_next_item_that_names_the_door(self):
        self.add_rows()
        r = self.cli("unlock", "hk")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no next item", r.stdout)
        cur = self.read("handoff/CURRENT.md")
        cur = re.sub(r"next:<[^|]*>", "next:log in to hk and check the cron", cur, count=1)
        self.write("handoff/CURRENT.md", cur)
        r = self.cli("unlock", "hk")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("value:pw-Example-123", r.stdout)
        self.assertIn("unlock HK", self.read(f"log/{brain._today()}.md"))

    def test_unlock_refuses_a_row_outside_the_declared_scope(self):
        self.add_rows()
        cur = re.sub(r"next:<[^|]*>", "next:log in to hk", self.read("handoff/CURRENT.md"), count=1)
        self.write("handoff/CURRENT.md", cur)
        r = self.cli("unlock", "hk", "--scope", "writing")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not inside the declared scope", r.stdout)
        r = self.cli("unlock", "hk", "--scope", "fleet,writing")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_top_door_needs_a_one_time_code_used_once(self):
        self.add_rows()
        r = self.cli("unlock", "bank")
        self.assertEqual(r.returncode, 3)
        self.assertIn("top door", r.stdout)
        r = self.cli("otp", "issue", "bank")
        code = re.search(r"BANK: ([0-9a-f]{8})", r.stdout).group(1)
        r = self.cli("unlock", "bank", "--code", "deadbeef")
        self.assertEqual(r.returncode, 3)
        r = self.cli("unlock", "bank", "--code", code)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("value:s3cret", r.stdout)
        r = self.cli("unlock", "bank", "--code", code)
        self.assertEqual(r.returncode, 3)

    # ---- log / recognize
    def soul_with_anchors(self, q=""):
        tail = f"|q:{q}" if q else ""
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   "::STATE{@OWNER, kind:person, role:owner, alias:the I in this chat}\n"
                   f"::GENE{{style|conf:confirmed|scope:global|by:legacy}}\n"
                   f"  T:judge_first_then_reasons|by:legacy|words:该下判断 先回判断\n"
                   f"  T:one_item_at_a_time|by:legacy|words:一条一条 拍板\n"
                   f"  T:books_not_packages|by:legacy|words:工程书 不发包\n"
                   f"  A:asking_instead_of_judging⇒owner_angry|by:legacy|words:问而不判\n"
                   f"  T:never_in_this_window|by:agent_inferred|words:火星\n"
                   "::BOUNDARY{never:push private memory to a public remote|scope:global|by:legacy}\n")

    def test_recognize_reads_the_owner_turns_not_the_agent_lines(self):
        self.soul_with_anchors()
        self.cli("log", "owner", "一条一条拍板 出工程书 别发包")
        self.cli("log", "agent", "::DECIDE{@AGENT}{what:judge_first_then_reasons 该下判断|why:x|context:none}")
        rc, out = quiet(brain.cmd_recognize, self.repo, 1, None, False, None)
        self.assertEqual(rc, 0, out)
        self.assertIn("RECOGNIZED", out)
        r = brain.recognize(self.repo, 1)
        self.assertEqual(r["applicable"], 2)
        self.assertEqual(r["hits"], 2)

    def test_recognize_refuses_another_person(self):
        self.soul_with_anchors()
        self.cli("log", "owner", "Hello, could you summarize the repository and list the commands please?")
        rc, out = quiet(brain.cmd_recognize, self.repo, 1, None, False, None)
        self.assertEqual(rc, 1, out)
        self.assertIn("NOT RECOGNIZED", out)

    def test_recognize_resets_on_a_boundary_contradiction(self):
        self.soul_with_anchors()
        self.cli("log", "owner", "一条一条拍板 出工程书")
        cur = re.sub(r"done:§<[^|]*>", "done:push private memory to a public remote", self.read("handoff/CURRENT.md"), count=1)
        self.write("handoff/CURRENT.md", cur)
        r = brain.recognize(self.repo, 1)
        self.assertFalse(r["recognized"])
        self.assertEqual(len(r["contradictions"]), 1)

    def test_cjk_boundary_matching_by_bigrams(self):
        self.assertTrue(brain._touches_boundary("把私人记忆推到公开仓库 done", "推送私人记忆到公开仓库"))
        self.assertFalse(brain._touches_boundary("写了市场页", "推送私人记忆到公开仓库"))

    # ---- provenance
    def test_provenance_init_stamps_legacy_and_check_passes(self):
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   "::STATE{@OWNER, kind:person, role:owner, alias:me}\n::GENE{style|conf:confirmed|scope:global}\n  T:short\n  A:long⇒bored\n"
                   "::FACT{key:k|value:v|conf:tentative}\n::BOUNDARY{never:x|scope:global}\n")
        rc, out = quiet(brain.cmd_provenance, self.repo, "init", "2026-11-08", False)
        self.assertEqual(rc, 0, out)
        s = self.read("soul/soul.md")
        self.assertIn("::STATE{@OWNER, kind:person, role:owner, alias:me, by:legacy}", s)
        self.assertIn("::GENE{style|conf:confirmed|scope:global|by:legacy}", s)
        self.assertIn("  T:short|by:legacy|last:2026-11-08", s)
        self.assertIn("::FACT{key:k|value:v|conf:tentative|by:legacy|last:2026-11-08}", s)
        self.assertIn("::BOUNDARY{never:x|scope:global|by:legacy}", s)
        rc, out = quiet(brain.cmd_provenance, self.repo, "check", None, False)
        self.assertEqual(rc, 0, out)

    def test_t1_agent_boundary_becomes_advice_t2_claim_without_quote_downgrades(self):
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   "::STATE{@OWNER, kind:person, role:owner, alias:me, by:legacy}\n"
                   "::BOUNDARY{never:call the owner SUN|scope:global|by:agent_inferred}\n"
                   "::FACT{key:claimed|value:v|conf:tentative|by:owner_verbatim}\n"
                   "::FACT{key:deploy|value:hk|conf:confirmed|by:agent_inferred|seen:1|last:2026-11-08}\n")
        rc, out = quiet(brain.cmd_provenance, self.repo, "check", None, False)
        self.assertEqual(rc, 1)
        self.assertIn("boundary_without_owner_source", out)
        self.assertIn("owner_verbatim_without_evidence", out)
        self.assertIn("confirmed_without_three_days", out)
        rc, out = quiet(brain.cmd_provenance, self.repo, "repair", "2026-11-08", False)
        s = self.read("soul/soul.md")
        self.assertNotIn("::BOUNDARY", s)
        self.assertIn("::FACT{key:advice_call_the_owner_SUN|value:call the owner SUN|conf:tentative|by:agent_inferred", s)
        self.assertIn("key:claimed|value:v|conf:tentative|by:owner_claimed", s)
        self.assertIn("key:deploy|value:hk|conf:tentative|by:agent_inferred", s)

    def test_evidence_makes_owner_verbatim_valid(self):
        r = self.cli("evidence", "add", "该下判断就下判断", "--where", "chat")
        q = re.search(r"q:([0-9a-f]{8})", r.stdout).group(1)
        self.assertEqual(q, brain.quote_q("该下判断就下判断"))
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   f"::BOUNDARY{{never:ask twice|scope:global|by:owner_verbatim|q:{q}}}\n")
        rc, out = quiet(brain.cmd_provenance, self.repo, "check", None, False)
        self.assertEqual(rc, 0, out)

    def test_transcript_adapter_reads_user_turns_only(self):
        t = self.tmp / "s.jsonl"
        t.write_text('{"type":"user","message":{"role":"user","content":"该下判断就下判断"}}\n'
                     '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"别问我"}]}}\n', encoding="utf-8")
        qs = brain.transcript_user_q(t)
        self.assertIn(brain.quote_q("该下判断就下判断"), qs)
        self.assertNotIn(brain.quote_q("别问我"), qs)

    def test_decay_tentative_after_30_days(self):
        self.write("memory/m.md", "---\ntype: project\nname: m\ndescription: t\n---\n"
                   "::FACT{key:old|value:v|conf:tentative|by:agent_inferred|last:2026-01-01}\n"
                   "::FACT{key:stale_confirmed|value:v|conf:confirmed|by:agent_inferred|seen:3|last:2026-01-01}\n"
                   "::FACT{key:owner|value:v|conf:confirmed|by:legacy|last:2026-01-01}\n")
        rc, out = quiet(brain.cmd_provenance, self.repo, "repair", "2026-11-08", False)
        s = self.read("memory/m.md")
        self.assertNotIn("key:old|", s)
        self.assertIn("key:stale_confirmed|value:v|conf:tentative|by:agent_inferred|seen:3|last:2026-11-08", s)
        self.assertIn("key:owner|value:v|conf:confirmed|by:legacy|last:2026-01-01", s)

    # ---- review and the gate
    def commit_all(self, msg):
        run(["git", "add", "-A"], self.repo)
        return run(["git", "commit", "-q", "-m", msg], self.repo)

    def test_review_rejects_boundary_removal_without_tombstone_and_accepts_with(self):
        q = brain.quote_q("no more")
        self.write("soul/evidence.md", f"---\ntype: reference\nname: evidence\ndescription: e\n---\n::EVIDENCE{{q:{q}|date:2026-11-08|where:chat|text:no more}}\n")
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   f"::BOUNDARY{{never:deploy on friday|scope:global|by:owner_verbatim|q:{q}}}\n")
        r = self.commit_all("soul")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n")
        rc, out = quiet(brain.cmd_review, self.repo, ["soul/soul.md"], False, False)
        self.assertEqual(rc, 1)
        self.assertIn("without an owner tombstone", out)
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   f"::DECIDE{{@OWNER}}{{what:retire deploy on friday|why:no more|context:q:{q}|by:owner_verbatim|q:{q}}}\n")
        rc, out = quiet(brain.cmd_review, self.repo, ["soul/soul.md"], False, False)
        self.assertEqual(rc, 0, out)
        self.assertIn("retired by an owner tombstone", out)

    def test_review_rejects_new_boundary_or_antipattern_without_owner_source(self):
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   "::BOUNDARY{never:call the owner SUN|scope:global|by:agent_inferred}\n"
                   "::GENE{g|conf:tentative|scope:global|by:agent_inferred}\n  A:x⇒y|by:agent_inferred\n")
        rc, out = quiet(brain.cmd_review, self.repo, ["soul/soul.md"], False, False)
        self.assertEqual(rc, 1)
        self.assertIn("new boundary without owner source", out)
        self.assertIn("new anti-pattern line without owner source", out)

    def test_review_rejects_owner_block_changed_by_agent_and_downgrades_conf(self):
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   "::FACT{key:home|value:hk|conf:confirmed|by:legacy}\n::FACT{key:guess|value:a|conf:tentative|by:agent_inferred|seen:1}\n")
        self.commit_all("soul")
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   "::FACT{key:home|value:sg|conf:confirmed|by:agent_inferred}\n::FACT{key:guess|value:a|conf:confirmed|by:agent_inferred|seen:1}\n")
        rc, out = quiet(brain.cmd_review, self.repo, ["soul/soul.md"], False, True)
        self.assertEqual(rc, 1)
        self.assertIn("owner-sourced block changed", out)
        self.assertIn("DOWNGRADE", out)
        self.assertIn("key:guess|value:a|conf:tentative|", self.read("soul/soul.md"))

    def test_pre_commit_hook_blocks_an_agent_boundary(self):
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   "::BOUNDARY{never:call the owner SUN|scope:global|by:agent_inferred}\n")
        if shutil.which("sh") is None:
            self.skipTest("no sh for git hooks")
        r = self.commit_all("bad")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("review rejected", r.stdout + r.stderr)

    # ---- import / verify
    def test_import_stamps_everything_and_converts_boundaries(self):
        src = self.tmp / "imp"
        src.mkdir()
        (src / "x.md").write_text("prose\n::BOUNDARY{never:deploy on friday|scope:global}\n::FACT{key:ed|value:vim|conf:confirmed}\n"
                                  "::GENE{h|conf:confirmed|scope:global}\n  T:tabs\n  A:spaces⇒complains\n", encoding="utf-8")
        rc, out = quiet(brain.cmd_import, self.repo, src, "other", "2026-11-08")
        self.assertEqual(rc, 0, out)
        files = list((self.repo / "memory" / "imports").glob("*.md"))
        self.assertEqual(len(files), 1)
        s = files[0].read_text(encoding="utf-8")
        self.assertNotIn("::BOUNDARY", s)
        self.assertIn("::FACT{key:imported_boundary_deploy_on_friday|value:deploy on friday|conf:tentative|by:imported|from:other|last:2026-11-08}", s)
        self.assertIn("conf:tentative|by:imported|from:other", s)
        self.assertIn("T:avoid_spaces_which_leads_to_complains|by:imported", s)
        self.assertNotIn("A:", s)
        self.assertIn("import other 2026-11-08", self.read("memory/MEMORY.md"))
        self.assertNotIn("deploy on friday", self.read("soul/soul.md"))

    def test_verify_reports_missing_edges_and_orphans(self):
        self.write("memory/c.md", "---\ntype: reference\nname: c\ndescription: t\n---\n"
                   "::FACT{key:a|value:1|conf:confirmed|by:legacy|why:b|used_by:nothing_here}\n"
                   "::FACT{key:b|value:2|conf:confirmed|by:legacy|used_by:a}\n::FACT{key:lonely|value:3|conf:tentative|by:legacy}\n")
        rc, out = quiet(brain.cmd_verify, self.repo, False, True)
        self.assertEqual(rc, 1)
        self.assertIn("MISSING memory/c.md a: used_by -> nothing_here", out)
        self.assertIn("ORPHAN  memory/c.md lonely", out)
        self.assertNotIn("ORPHAN  memory/c.md b", out)

    # ---- instructions / paste / remote
    def test_instructions_sync_and_check(self):
        self.write("skills/mem-forever/SKILL.md", "---\nname: mem-forever\n---\n\n# body\n\nline\n")
        rc, out = quiet(brain.cmd_instructions, self.repo, "sync")
        self.assertEqual(rc, 0)
        self.assertEqual(self.read("CLAUDE.md"), "# body\n\nline\n")
        rc, out = quiet(brain.cmd_instructions, self.repo, "check")
        self.assertEqual(rc, 0, out)
        self.write("AGENTS.md", "# changed\n")
        rc, out = quiet(brain.cmd_instructions, self.repo, "check")
        self.assertEqual(rc, 1)

    def test_paste_carries_the_ledger_without_values_by_default(self):
        fake = "sk" + "-not-real-looks-like-one-1234567890"
        self.cli("ledger", "add", "api", "--door", "api.example.com", "--kind", "api_key", "--value", fake, "--verify", "none", "--recover", "dashboard")
        out = self.tmp / "p.md"
        rc, _ = quiet(brain.cmd_paste, self.repo, out, "en", False)
        self.assertEqual(rc, 0)
        s = out.read_text(encoding="utf-8")
        self.assertIn("::STATE{@LEDGER, rows:1, values:omitted", s)
        self.assertIn("@API, door:api.example.com", s)
        self.assertNotIn(fake, s)
        rc, _ = quiet(brain.cmd_paste, self.repo, out, "en", True)
        self.assertEqual(rc, 0)
        self.assertIn(fake, out.read_text(encoding="utf-8"))

    def test_remote_parser(self):
        self.assertEqual(brain.parse_remote("https://github.com/ilang-ai/Mem-Forever.git"), ("github.com", "ilang-ai", "Mem-Forever"))
        self.assertEqual(brain.parse_remote("git@github.com:ilang-ai/Mem-Forever.git"), ("github.com", "ilang-ai", "Mem-Forever"))
        self.assertEqual(brain.parse_remote("https://gitee.com/monetize/DeepSeekHarness"), ("gitee.com", "monetize", "DeepSeekHarness"))
        self.assertIsNone(brain.parse_remote("https://example.com/x/y"))
        self.assertEqual(brain.remote_check("https://example.com/x/y"), 2)

    def test_install_dry_run_touches_nothing(self):
        cc = self.tmp / "cc"
        cc.mkdir()
        rc, out = quiet(brain.cmd_install, self.repo, cc, self.tmp, "2026-11-08", True)
        self.assertEqual(rc, 0, out)
        self.assertFalse((cc / "projects").exists())


if __name__ == "__main__":
    unittest.main(verbosity=1)
