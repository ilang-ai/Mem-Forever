# -*- coding: utf-8 -*-
"""Behavior tests for brain.py 2.1 (Mem-Forever 3.1): ledger, unlock, grants, one-time code, encoded rest, harvest, log,
recognize, provenance, evidence, review, import, verify, instructions, paste, the push guard parser.
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


EXCL = '::EXCLUDE{vault_packer|candidates:dell3660;claude_session;ds_other_machine|out:dell3660(path:~/.age/key.txt missing);claude_session(2026-11-03)|left:ds_other_machine|conf:tentative|by:agent_inferred}'


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
        def _rw(fn, path, exc):
            try:
                os.chmod(path, 0o700)
                fn(path)
            except OSError:
                pass
        for _ in range(3):
            shutil.rmtree(self.tmp, onerror=_rw)
            if not self.tmp.exists():
                break

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

    def test_check_exempts_env_and_log_and_warns_on_memory_keys(self):
        tok = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123456789"
        self.write("log/2026-11-08.md", f"# 2026-11-08\n\n::EVENT{{@OWNER, at:10:00, kind:turn}}\nthe pass" + "word: Example12345 and {tok}\n\n")
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("key-shaped", r.stdout)
        # 3.1: a key in memory text is a WARN with the harvest command, never a refused commit
        self.write("memory/leak.md", f"---\ntype: reference\nname: leak\ndescription: x\n---\n{tok}\n")
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("1 key-shaped value(s) outside the ledger in memory/leak.md", r.stdout)
        self.assertIn("ledger harvest", r.stdout)
        # a plain row in keys.env is a WARN with the encode command
        self.write("env/keys.env", f"GH={tok}\n")
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("1 plain row(s) in env/keys.env", r.stdout)

    # ---- ledger
    def grant_all(self):
        self.assertEqual(self.cli("grant", "--write").returncode, 0)
        self.assertEqual(self.cli("grant", "--all").returncode, 0)

    def declare_scope(self, scope="fleet"):
        cur = self.read("handoff/CURRENT.md")
        if "::PROGRESS{scope:" not in cur:
            cur = cur.replace("::PROGRESS{date:", f"::PROGRESS{{scope:{scope}|date:", 1)
            self.write("handoff/CURRENT.md", cur)

    def add_rows(self):
        self.grant_all()
        self.declare_scope()
        r = self.cli("ledger", "add", "hk", "--door", "ssh root@203.0.113.5", "--kind", "ssh_password", "--value", "pw-Example-123",
                     "--verify", '"' + sys.executable + '" -c "import os,sys;sys.exit(0 if os.environ.get(\'HK\') and os.environ.get(\'HK\')==os.environ.get(\'LEDGER_VALUE\') else 1)"',
                     "--recover", "provider console", "--scope", "fleet", "--why", "hub")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.cli("ledger", "add", "bank", "--door", "bank account", "--kind", "payment", "--value", "s3cret", "--recover", "branch")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_ledger_add_list_verify_and_stale(self):
        self.add_rows()
        keys = self.read("env/keys.env")
        self.assertIn("HK=enc1:", keys)
        self.assertNotIn("pw-Example-123", keys)
        r = self.cli("ledger", "decode")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("HK=pw-Example-123", r.stdout)
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
        self.cli("grant", "--write")
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

    def test_t11_evidence_without_transcript_is_claimed_until_the_owner_confirms(self):
        r = self.cli("evidence", "add", "该下判断就下判断", "--where", "chat")
        self.assertIn("owner_claimed", r.stdout)
        q = re.search(r"q:([0-9a-f]{8})", r.stdout).group(1)
        self.assertEqual(q, brain.quote_q("该下判断就下判断"))
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   f"::BOUNDARY{{never:ask twice|scope:global|by:owner_verbatim|q:{q}}}\n")
        rc, out = quiet(brain.cmd_provenance, self.repo, "check", None, False)
        self.assertEqual(rc, 1, out)
        self.assertIn("owner_verbatim_without_transcript", out)
        # the owner confirms in person: the quote is backed and the boundary stands
        r = self.cli("evidence", "confirm", q)
        self.assertEqual(r.returncode, 0, r.stdout)
        rc, out = quiet(brain.cmd_provenance, self.repo, "check", None, False)
        self.assertEqual(rc, 0, out)
        # without the confirmation, repair would have rewritten it to owner_claimed
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   f"::BOUNDARY{{never:ask thrice|scope:global|by:owner_verbatim|q:{brain.quote_q('别问三次')}}}\n")
        self.cli("evidence", "add", "别问三次")
        rc, out = quiet(brain.cmd_provenance, self.repo, "repair", "2026-11-08", False)
        self.assertIn("by:owner_claimed", self.read("soul/soul.md"))

    def test_t12_evidence_backed_by_a_transcript_is_verbatim(self):
        t = self.tmp / "s.jsonl"
        t.write_text('{"type":"user","message":{"role":"user","content":"该下判断就下判断"}}\n', encoding="utf-8")
        r = self.cli("evidence", "add", "该下判断就下判断", "--transcript", str(t))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("backed by the transcript", r.stdout)
        q = re.search(r"q:([0-9a-f]{8})", r.stdout).group(1)
        self.assertIn("by:owner_verbatim|src:transcript:", self.read("soul/evidence.md"))
        self.write("soul/soul.md", "---\ntype: profile\nname: soul\ndescription: t\nstatus: stable\n---\n"
                   f"::BOUNDARY{{never:ask twice|scope:global|by:owner_verbatim|q:{q}}}\n")
        rc, out = quiet(brain.cmd_provenance, self.repo, "check", None, False)
        self.assertEqual(rc, 0, out)
        r = self.cli("evidence", "add", "这句不在转录里", "--transcript", str(t))
        self.assertIn("owner_claimed", r.stdout)

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
        self.cli("grant", "--write")
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


    # ---- 3.1 three states, grants, harvest
    def test_t1_t2_encode_decode_roundtrip_and_missing_pepper(self):
        pepper = brain.load_pepper(self.repo)
        self.assertIsNotNone(pepper)
        self.assertEqual(len(pepper), 32)
        tok = brain.enc1_encode(pepper, "HK", "pw-Example-123 密码")
        self.assertTrue(tok.startswith("enc1:"))
        self.assertNotIn("Example", tok)
        self.assertEqual(brain.enc1_decode(pepper, "HK", tok), "pw-Example-123 密码")
        self.assertNotEqual(brain.enc1_decode(b"\x01" * 32, "HK", tok), "pw-Example-123 密码")
        self.assertNotEqual(brain.enc1_encode(pepper, "HK", "same"), brain.enc1_encode(pepper, "OTHER", "same"))
        self.write("env/keys.env", f"HK={tok}\n")
        hexpepper = self.read("env/pepper").strip()
        (self.repo / "env" / "pepper").unlink()
        r = self.cli("ledger", "decode")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("env/pepper missing", r.stdout)
        r = self.cli("check")
        self.assertIn("env/pepper missing", r.stdout)
        r = self.cli("ledger", "decode", "--pepper", hexpepper)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("HK=pw-Example-123 密码", r.stdout)

    def test_t3_t4_unlock_needs_a_grant_on_this_machine(self):
        self.add_rows()
        cur = re.sub(r"next:<[^|]*>", "next:log in to hk", self.read("handoff/CURRENT.md"), count=1)
        self.write("handoff/CURRENT.md", cur)
        r = self.cli("grant", "--revoke", "--all")
        self.assertEqual(r.returncode, 0, r.stdout)
        r = self.cli("unlock", "hk")
        self.assertEqual(r.returncode, 3, r.stdout)
        self.assertIn("no grant on this machine", r.stdout)
        self.assertIn("grant HK", r.stdout)
        r = self.cli("grant", "hk")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(run(["git", "config", "--bool", "brain.grant.HK"], self.repo).stdout.strip(), "true")
        r = self.cli("unlock", "hk")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("value:pw-Example-123", r.stdout)
        self.assertIn("grant:door", self.read(f"log/{brain._today()}.md"))
        r = self.cli("grant", "--list")
        self.assertIn("brain.grant.hk true", r.stdout.lower())
        # grant --all never covers a top door
        self.cli("grant", "--all")
        r = self.cli("unlock", "bank")
        self.assertEqual(r.returncode, 3)
        self.assertIn("top door", r.stdout)
        # the repository carries no grant
        self.assertNotIn("brain.grant", self.read(".gitignore") + self.read("env/ledger.env"))
        r = run(["git", "grep", "-l", "brain.grant", "HEAD", "--", "env"], self.repo)
        self.assertNotEqual(r.returncode, 0)

    def test_t5_storing_a_key_needs_the_write_grant_once(self):
        r = self.cli("ledger", "add", "api", "--door", "api.example.com", "--kind", "api_key", "--value", "v-Example-12345", "--recover", "dashboard")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("grant --write", r.stdout)
        self.assertFalse((self.repo / "env" / "keys.env").exists())
        self.cli("grant", "--write")
        r = self.cli("ledger", "add", "api", "--door", "api.example.com", "--kind", "api_key", "--value", "v-Example-12345", "--recover", "dashboard")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("API=enc1:", self.read("env/keys.env"))
        self.assertNotIn("v-Example-12345", self.read("env/keys.env"))

    def test_t6_t7_harvest_turns_memory_keys_into_doors_and_leaves_the_log_alone(self):
        tok = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123456789"
        self.write("memory/leak.md", f"---\ntype: reference\nname: leak\ndescription: x\n---\nthe token is {tok} and again {tok}\n")
        self.write("log/2026-11-08.md", f"# 2026-11-08\n\n::EVENT{{@OWNER, at:10:00, kind:turn}}\n{tok}\n\n")
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("1 key-shaped value(s) outside the ledger", r.stdout)
        r = self.cli("ledger", "harvest")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.cli("grant", "--write")
        r = self.cli("ledger", "harvest")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("GITHUB_TOKEN_LEAK", r.stdout)
        mem = self.read("memory/leak.md")
        self.assertNotIn(tok, mem)
        self.assertEqual(mem.count("{{GITHUB_TOKEN_LEAK}}"), 2)
        self.assertIn(tok, self.read("log/2026-11-08.md"))
        keys = self.read("env/keys.env")
        self.assertIn("GITHUB_TOKEN_LEAK=enc1:", keys)
        self.assertNotIn(tok, keys)
        self.assertRegex(self.read("env/ledger.env"), r"@GITHUB_TOKEN_LEAK, door:github_token found in memory/leak.md, kind:github_token, ref:GITHUB_TOKEN_LEAK, verify:none")
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("0 errors, 0 warnings", r.stdout)
        r = self.cli("ledger", "reveal", "GITHUB_TOKEN_LEAK")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(r.stdout.strip(), tok)
        r = self.cli("ledger", "verify", "all")
        self.assertIn("SKIP    GITHUB_TOKEN_LEAK", r.stdout)

    def test_t8_t9_paste_masks_what_was_not_harvested_and_never_carries_the_pepper(self):
        fake = "sk" + "-not-real-looks-like-one-1234567890"
        cur = self.read("handoff/CURRENT.md").replace("value:<what is stuck and who decides>", f"value:the api key is {fake}", 1)
        self.write("handoff/CURRENT.md", cur)
        out = self.tmp / "p.md"
        rc, _ = quiet(brain.cmd_paste, self.repo, out, "en", False)
        self.assertEqual(rc, 0)
        s = out.read_text(encoding="utf-8")
        self.assertNotIn(fake, s)
        self.assertIn("{{UNHARVESTED openai_key ", s)
        self.assertNotIn(self.read("env/pepper").strip(), s)
        rc, _ = quiet(brain.cmd_paste, self.repo, out, "en", True)
        self.assertIn(fake, out.read_text(encoding="utf-8"))

    def test_t10_migrate_cc_harvests_the_copied_memory(self):
        src = self.tmp / "cc"
        src.mkdir()
        gh = "gh" + "p_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        sk = "sk" + "-proj-abcdefghijklmnop1234567890"
        aws = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
        (src / "a.md").write_text(f"---\ntype: reference\nname: a\ndescription: a\n---\n{gh}\n{sk}\n", encoding="utf-8")
        (src / "b.md").write_text(f"---\ntype: reference\nname: b\ndescription: b\n---\nkey {aws} here\n", encoding="utf-8")
        rc, out = quiet(brain.cmd_migrate_cc, self.repo, src, False)
        self.assertEqual(rc, 0, out)
        self.assertIn("harvest: skipped", out)
        self.cli("grant", "--write")
        rc, out = quiet(brain.cmd_migrate_cc, self.repo, src, True)
        self.assertEqual(rc, 0, out)
        self.assertIn("3 door(s) created", out)
        a = self.read("memory/a.md")
        self.assertIn("{{GITHUB_TOKEN_A}}", a)
        self.assertIn("{{OPENAI_KEY_A}}", a)
        self.assertIn("{{AWS_KEY_B}}", self.read("memory/b.md"))
        for tok in (gh, sk, aws):
            self.assertNotIn(tok, a + self.read("memory/b.md") + self.read("env/keys.env"))
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(self.cli("ledger", "reveal", "AWS_KEY_B").stdout.strip(), aws)

    def test_t13_unlock_scope_comes_from_the_handoff_when_not_declared(self):
        self.add_rows()
        cur = re.sub(r"next:<[^|]*>", "next:log in to hk", self.read("handoff/CURRENT.md"), count=1)
        self.write("handoff/CURRENT.md", cur)
        r = self.cli("unlock", "hk")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.write("handoff/CURRENT.md", self.read("handoff/CURRENT.md").replace("::PROGRESS{scope:fleet|", "::PROGRESS{", 1))
        r = self.cli("unlock", "hk")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("none was declared", r.stdout)
        self.write("handoff/CURRENT.md", self.read("handoff/CURRENT.md").replace("::PROGRESS{date:", "::PROGRESS{scope:writing|date:", 1))
        r = self.cli("unlock", "hk")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("not inside the declared scope", r.stdout)

    def test_t14_check_warns_when_the_hooks_are_off_on_this_clone(self):
        run(["git", "config", "--unset", "core.hooksPath"], self.repo)
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("hooks are off on this clone", r.stdout)
        rc, out = quiet(brain.cmd_init, self.repo, "test", False)
        self.assertEqual(rc, 0, out)
        r = self.cli("check")
        self.assertNotIn("hooks are off", r.stdout)

    def test_t15_ledger_encode_is_reversible_and_idempotent(self):
        self.write("env/keys.env", "# keys\nHK=pw-Example-123\nAPI=\"quoted-Value-1\"\n")
        r = self.cli("ledger", "encode")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("2 row(s) encoded", r.stdout)
        self.assertTrue((self.repo / "env" / "keys.env.bak").is_file())
        keys = self.read("env/keys.env")
        self.assertIn("HK=enc1:", keys)
        self.assertIn("API=enc1:", keys)
        self.assertNotIn("pw-Example-123", keys)
        r = self.cli("ledger", "decode")
        self.assertIn("HK=pw-Example-123", r.stdout)
        self.assertIn("API=quoted-Value-1", r.stdout)
        r = self.cli("ledger", "encode")
        self.assertIn("0 row(s) encoded", r.stdout)
        self.assertEqual(self.read("env/keys.env"), keys)

    def test_t16_init_writes_the_pepper_once(self):
        hexpepper = self.read("env/pepper").strip()
        self.assertEqual(len(hexpepper), 64)
        rc, out = quiet(brain.cmd_init, self.repo, "test", False)
        self.assertEqual(self.read("env/pepper").strip(), hexpepper)
        self.assertIn("env/pepper", run(["git", "ls-files", "env/pepper"], self.repo).stdout)

    def test_t17_check_warns_on_a_row_with_nothing_to_open(self):
        self.grant_all()
        self.declare_scope()
        r = self.cli("ledger", "add", "repo", "--door", "https://github.com/example/repo", "--kind", "value", "--recover", "github")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("row REPO has nothing to open", r.stdout)
        self.assertIn("::FACT", r.stdout)
        r = self.cli("ledger", "add", "root", "--door", "ssh root@203.0.113.9", "--kind", "root", "--recover", "console")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.cli("check")
        self.assertNotIn("row ROOT has nothing to open", r.stdout)
        r = self.cli("ledger", "add", "api", "--door", "https://api.example.com", "--kind", "token", "--value", "tok-Example-1", "--recover", "console")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.cli("check")
        self.assertNotIn("row API has nothing to open", r.stdout)

    def test_t18_verify_output_is_decoded_in_the_shell_codepage(self):
        text = "不是内部或外部命令"
        self.assertEqual(brain._decode_output(text.encode("gbk"), fallback="gbk"), text)
        self.assertEqual(brain._decode_output(text.encode("utf-8"), fallback="gbk"), text)
        self.assertEqual(brain._decode_output(b"", fallback="gbk"), "")
        self.assertNotIn("\ufffd", brain._decode_output(text.encode("gbk"), fallback="gbk"))

    def test_t19_ledger_import_dir_one_row_per_file_encoded_public_and_code_skipped(self):
        src = self.tmp / "keys"
        src.mkdir()
        (src / "aliyun-zhangmei-v1.0-2026-09-23.env").write_bytes(b"ALIYUN_ID=id-Example-1\nALIYUN_SEC" + b"RET=sec-Example-2\n")
        (src / "tavily.key").write_bytes(b"tvly-Example-3\n")
        (src / "id_ed25519_bot").write_bytes(b"-----BE" + b"GIN OPENSSH PRIVATE KEY-----\nExampleKeyBody\n-----END OPENSSH PRIVATE KEY-----\n")
        (src / "server.pub").write_bytes(b"ssh-ed25519 AAAA public\n")
        (src / "helper.py").write_bytes(b"print(1)\n")
        (src / "authhub-backup-recipient-v1-2026-10-22.pem").write_bytes(b"-----BE" + b"GIN PUBLIC KEY-----\nX\n-----END PUBLIC KEY-----\n")
        r = self.cli("ledger", "import", str(src), "--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("would   ALIYUN_ZHANGMEI (env_file", r.stdout)
        self.assertIn("would   TAVILY (token", r.stdout)
        self.assertIn("would   ID_ED25519_BOT (ssh_key", r.stdout)
        self.assertNotIn("server.pub", r.stdout)
        self.assertNotIn("helper.py", r.stdout)
        self.assertNotIn("recipient", r.stdout)
        self.assertFalse((self.repo / "env" / "keys.env").exists() and "ALIYUN" in self.read("env/keys.env"))
        r = self.cli("ledger", "import", str(src))
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("needs the owner's yes once", r.stdout)
        self.cli("grant", "--write")
        r = self.cli("ledger", "import", str(src), "--scope", "fleet")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("3 row(s) added", r.stdout)
        keys = self.read("env/keys.env")
        self.assertIn("ALIYUN_ZHANGMEI=enc1:", keys)
        self.assertNotIn("sec-Example-2", keys)
        self.assertNotIn("ExampleKeyBody", keys)
        led = self.read("env/ledger.env")
        self.assertIn("@ALIYUN_ZHANGMEI, door:file:aliyun-zhangmei-v1.0-2026-09-23.env, kind:env_file, ref:ALIYUN_ZHANGMEI", led)
        self.assertIn("scope:fleet", led)
        self.assertNotIn("sec-Example-2", led)
        r = self.cli("ledger", "decode")
        self.assertIn("ALIYUN_SEC" + "RET=sec-Example-2", r.stdout)
        self.assertIn("ExampleKeyBody", r.stdout)
        self.assertTrue((src / "tavily.key").exists())
        r = self.cli("ledger", "import", str(src))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("ALIYUN_ZHANGMEI_2", self.read("env/ledger.env"))
        r = self.cli("check")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("nothing to open", r.stdout)

    def test_t20_verify_checks_what_refuted_each_struck_candidate(self):
        self.write("memory/vault.md", "---\nname: vault\ndescription: who packed the vault\ntype: project\n---\n\n" + EXCL + "\n")
        r = self.cli("verify")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("1 exclusion(s)", r.stdout)
        self.assertIn("MISSING memory/vault.md vault_packer: out -> claude_session: 2026-11-03 names nothing the brain can see", r.stdout)
        self.assertNotIn("dell3660", r.stdout.replace("candidates:dell3660", ""))
        self.write("log/2026-11-03.md", "# 2026-11-03\n\n- the main session packed the vault\n")
        r = self.cli("verify")
        self.assertNotIn("MISSING", r.stdout)
        self.write("memory/guess.md", "---\nname: guess\ndescription: x\ntype: project\n---\n\n::EXCLUDE{guess|candidates:a;b|out:none|left:a|conf:tentative|by:agent_inferred}\n")
        r = self.cli("verify")
        self.assertIn("MISSING memory/guess.md guess: out -> empty: a guess, not an elimination", r.stdout)

    def test_t21_review_refuses_an_exclusion_without_out(self):
        self.write("memory/guess.md", "---\nname: guess\ndescription: x\ntype: project\n---\n\n::EXCLUDE{guess|candidates:a;b|left:a|conf:tentative|by:agent_inferred}\n")
        r = self.cli("review", "memory/guess.md")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("exclusion without out:", r.stdout)
        self.write("memory/good.md", "---\nname: good\ndescription: x\ntype: project\n---\n\n" + EXCL + "\n")
        r = self.cli("review", "memory/good.md")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.write("memory/bad.md", "---\nname: bad\ndescription: x\ntype: project\n---\n\n" + EXCL + "\n::BOUNDARY{never:trust_ds_other_machine|scope:all|by:agent_inferred}\n")
        r = self.cli("review", "memory/bad.md")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("new boundary without owner source", r.stdout)

    def test_t22_evidence_confirm_turns_left_into_a_fact_and_keeps_the_trail(self):
        self.write("log/2026-11-03.md", "# 2026-11-03\n")
        self.write("memory/vault.md", "---\nname: vault\ndescription: x\ntype: project\n---\n\n" + EXCL + "\n")
        r = self.cli("evidence", "confirm", "vault_packer")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("left written as ::FACT{key:vault_packer}", r.stdout)
        t = self.read("memory/vault.md")
        self.assertIn("left:ds_other_machine|conf:confirmed|by:agent_inferred}", t)
        self.assertIn("::FACT{key:vault_packer|value:ds_other_machine|why:vault_packer|used_by:none|conf:confirmed|by:owner_confirmed}", t)
        r = self.cli("verify")
        self.assertNotIn("MISSING", r.stdout)
        self.write("memory/open.md", "---\nname: open\ndescription: x\ntype: project\n---\n\n::EXCLUDE{open_gap|candidates:a;b|out:a(2026-11-03);b(2026-11-03)|left:none|conf:tentative|by:agent_inferred}\n")
        r = self.cli("evidence", "confirm", "open_gap")
        self.assertIn("nothing was left, the gap stays open", r.stdout)
        self.assertNotIn("::FACT{key:open_gap", self.read("memory/open.md"))

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
