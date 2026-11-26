"""
lib/suggestions.py için testler (ağ yok: yerel bare library + yerel sahte web sunucusu
+ sahte gh).

Çalıştır (repo kökünden):  python scripts/tests/test_suggestions.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from lib import suggestions as sg  # noqa: E402

GIT_ENV = {
    "GIT_AUTHOR_NAME": "eptran-bot", "GIT_AUTHOR_EMAIL": "bot@example.invalid",
    "GIT_COMMITTER_NAME": "eptran-bot", "GIT_COMMITTER_EMAIL": "bot@example.invalid",
}

CH = ("Bölüm 2: Sis\n\n"
      "Sis çöktü ve herkes eve döndü.\n\n"
      "Ertesi gün sis yine çöktü.\n\n"
      "\"Gitmeliyiz,\" dedi Mira.\n")


def S(id_, selected, suggested, before="", after="", slug="demo", index=1, **kw):
    d = {"id": id_, "status": "pending", "selectedText": selected, "suggestedText": suggested,
         "contextBefore": before, "contextAfter": after, "note": "", "prUrl": None,
         "chapterId": "c1", "chapterIndex": index, "chapterTitle": "Bölüm 2: Sis",
         "sourceKey": slug, "novelSlug": slug, "createdAt": "2026-11-23T00:00:00.000Z"}
    d.update(kw)
    return d


class LocateTest(unittest.TestCase):
    def test_exact_unique(self):
        pos = sg.locate(CH, "herkes eve döndü")
        self.assertEqual(CH[pos[0]:pos[1]], "herkes eve döndü")

    def test_ambiguous_without_context_is_none(self):
        self.assertIsNone(sg.locate(CH, "çöktü"))

    def test_ambiguous_resolved_by_context(self):
        pos = sg.locate(CH, "çöktü", before="Ertesi gün sis yine ", after=".")
        self.assertIsNotNone(pos)
        self.assertGreater(pos[0], CH.index("Ertesi"))

    def test_context_across_paragraph_boundary_ignores_whitespace(self):
        pos = sg.locate(CH, "Ertesi", before="herkes eve döndü.", after=" gün")
        self.assertEqual(CH[pos[0]:pos[1]], "Ertesi")

    def test_whitespace_tolerant(self):
        pos = sg.locate(CH, "Sis çöktü ve\nherkes   eve döndü.")
        self.assertIsNotNone(pos)

    def test_missing_is_none(self):
        self.assertIsNone(sg.locate(CH, "olmayan cümle"))
        self.assertIsNone(sg.locate(CH, "   "))


class SafetyTest(unittest.TestCase):
    def test_unsafe_reasons(self):
        self.assertIsNotNone(sg.unsafe_reason("a", "bak http://x.example"))
        self.assertIsNotNone(sg.unsafe_reason("a", "www.example.com"))
        self.assertIsNotNone(sg.unsafe_reason("a", "<script>x</script>"))
        self.assertIsNotNone(sg.unsafe_reason("a", "a\x07b"))
        self.assertIsNotNone(sg.unsafe_reason("a", "# Başlık"))
        self.assertIsNotNone(sg.unsafe_reason("a", "bir\n\niki"))
        self.assertIsNone(sg.unsafe_reason("a\n\nb", "x\n\ny"))   # zaten çok paragraf
        self.assertIsNone(sg.unsafe_reason("çöktü", "indi"))
        self.assertIsNone(sg.unsafe_reason("a", "2 < 3 olur"))     # '<' sonrası boşluk: HTML değil

    def test_apply_to_text(self):
        sugg = [S("1", "herkes eve döndü", "herkes evine döndü"),
                S("2", "çöktü", "indi"),                                   # belirsiz
                S("3", "Sis", "Duman"),                                    # başlık satırında / belirsiz
                S("4", "Gitmeliyiz", "Gitmeliyiz!", before="\""),          # tek yer
                S("5", "x", "http://kotu.example")]
        new, applied, rejected = sg.apply_to_text(CH, sugg)
        self.assertEqual([s["id"] for s in applied], ["1", "4"])
        self.assertIn("evine döndü", new)
        self.assertIn("\"Gitmeliyiz!,\"", new)
        self.assertEqual(sorted(s["id"] for s, _ in rejected), ["2", "3", "5"])

    def test_title_line_is_never_touched(self):
        text = "Bölüm 7: Uyanış\n\nUyanış bitti.\n"
        _, applied, rejected = sg.apply_to_text(text, [S("1", "Bölüm 7: Uyanış", "Bölüm 7: Uyanis")])
        self.assertEqual(applied, [])
        self.assertIn("başlık", rejected[0][1])

    def test_overlapping_second_suggestion_is_rejected(self):
        _, applied, rejected = sg.apply_to_text(CH, [
            S("1", "herkes eve döndü", "herkes dağıldı"),
            S("2", "eve döndü", "evine gitti"),
        ])
        self.assertEqual([s["id"] for s in applied], ["1"])
        self.assertEqual([s["id"] for s, _ in rejected], ["2"])

    def test_pr_body_neutralizes_user_text(self):
        body = sg.pr_body("demo", "002", "Bölüm 2", [
            S("a1", "x `kod` @herkes\n[link](http://e)", "y", note="not @biri")])
        self.assertNotIn("`kod`", body)
        self.assertIn("`x 'kod' @herkes [link](http://e)`", body)  # tek satır, kod aralığında
        self.assertEqual(body.count("\n- önce:"), 1)


class FakeWeb(BaseHTTPRequestHandler):
    state = {}

    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        st = FakeWeb.state
        if self.headers.get("Authorization") != "Bearer s3cret":
            return self._send({"error": "unauthorized"}, 401)
        status = self.path.split("status=")[-1]
        self._send([s for s in st["suggestions"] if s["status"] == status])

    def do_PATCH(self):
        st = FakeWeb.state
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        st["patches"].append(body)
        for s in st["suggestions"]:
            if s["id"] == body["id"]:
                s["status"] = body["status"]
                if body.get("prUrl"):
                    s["prUrl"] = body["prUrl"]
        self._send({"ok": True})

    def do_POST(self):
        st = FakeWeb.state
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        st["ingests"].append(body)
        self._send({"ok": True}, 200)


class FakeGh:
    def __init__(self):
        self.created = []
        self.views = {}
        self.open_branches = []

    def pr_create(self, head, title, body):
        url = f"https://github.com/o/r/pull/{len(self.created) + 1}"
        self.created.append({"head": head, "title": title, "body": body, "url": url})
        return url

    def pr_view(self, url):
        return self.views[url]

    def open_suggestion_branches(self):
        return list(self.open_branches)


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV}).stdout.strip()


class FlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="eptran-sugg-test-")
        self.old_env = dict(os.environ)
        os.environ.update(GIT_ENV)
        self.bare = os.path.join(self.tmp, "library.git")
        sh("git", "init", "--bare", "--initial-branch=main", self.bare)
        seed = os.path.join(self.tmp, "seed")
        sh("git", "clone", self.bare, seed)
        for slug in ("demo", "diger"):
            d = os.path.join(seed, "demo-seri", slug)
            os.makedirs(d)
            with open(os.path.join(d, "001.txt"), "w", encoding="utf-8") as f:
                f.write("Bölüm 1: Giriş\n\nİlk bölüm metni burada.\n")
            with open(os.path.join(d, "002.txt"), "w", encoding="utf-8") as f:
                f.write(CH)
        sh("git", "add", "-A", cwd=seed)
        sh("git", "commit", "-m", "init", cwd=seed)
        sh("git", "push", "origin", "HEAD:main", cwd=seed)
        os.environ["LIBRARY_CLONE_URL"] = self.bare

        FakeWeb.state = {"suggestions": [], "patches": [], "ingests": []}
        self.server = HTTPServer(("127.0.0.1", 0), FakeWeb)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.web = sg.WebClient(f"http://127.0.0.1:{self.server.server_port}/api/ingest", "s3cret")
        self.gh = FakeGh()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        os.environ.clear()
        os.environ.update(self.old_env)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def lib_file(self, ref, path):
        return sh("git", "show", f"{ref}:{path}", cwd=self.bare)

    def test_web_client_derives_base_url_and_authenticates(self):
        self.assertTrue(self.web.base.startswith("http://127.0.0.1:"))
        self.assertFalse(self.web.base.endswith("/api/ingest"))
        bad = sg.WebClient(self.web.base, "yanlis")
        with self.assertRaises(RuntimeError):
            bad.list("pending")

    def test_creates_one_pr_per_chapter_and_updates_status(self):
        FakeWeb.state["suggestions"] = [
            S("s1", "herkes eve döndü", "herkes evine döndü"),
            S("s2", "Gitmeliyiz", "Gitmeliyiz mutlaka", before="\""),
            S("s3", "çöktü", "indi"),                      # belirsiz -> rejected
            S("s4", "İlk bölüm", "Birinci bölüm", index=0),  # başka bölüm -> ayrı PR
        ]
        errors = sg.run(self.web, "x/y", gh=self.gh)
        self.assertEqual(errors, 0)
        self.assertEqual(len(self.gh.created), 2)
        heads = sorted(p["head"].rsplit("-", 1)[0] for p in self.gh.created)
        self.assertEqual(heads, ["oneri/demo-001", "oneri/demo-002"])
        # Dal içeriği düzeltilmiş, main dokunulmamış.
        branch2 = next(p["head"] for p in self.gh.created if "-002-" in p["head"])
        fixed = self.lib_file(branch2, "demo-seri/demo/002.txt")
        self.assertIn("evine döndü", fixed)
        self.assertIn("Gitmeliyiz mutlaka", fixed)
        self.assertIn("çöktü ve", fixed)   # belirsiz olan uygulanmadı
        self.assertEqual(self.lib_file("main", "demo-seri/demo/002.txt"), CH.rstrip("\n"))
        # Durumlar: 3 pr_open, 1 rejected.
        by = {p["id"]: p for p in FakeWeb.state["patches"]}
        self.assertEqual(by["s1"]["status"], "pr_open")
        self.assertTrue(by["s1"]["prUrl"].startswith("https://github.com/o/r/pull/"))
        self.assertEqual(by["s3"]["status"], "rejected")
        self.assertEqual(by["s4"]["status"], "pr_open")
        # Başka cilde (diger) dokunulmadı.
        self.assertEqual(self.lib_file("main", "demo-seri/diger/002.txt"), CH.rstrip("\n"))

    def test_unknown_book_or_missing_chapter_is_rejected(self):
        FakeWeb.state["suggestions"] = [
            S("a", "x", "y", slug="yok"),
            S("b", "x", "y", index=99),
        ]
        sg.run(self.web, "x/y", gh=self.gh)
        self.assertEqual(self.gh.created, [])
        self.assertEqual({p["status"] for p in FakeWeb.state["patches"]}, {"rejected"})

    def test_open_pr_for_same_chapter_blocks_new_one(self):
        self.gh.open_branches = ["oneri/demo-002-20260101000000"]
        FakeWeb.state["suggestions"] = [S("s1", "herkes eve döndü", "herkes evine döndü")]
        sg.run(self.web, "x/y", gh=self.gh)
        self.assertEqual(self.gh.created, [])
        self.assertEqual(FakeWeb.state["patches"], [])   # beklemede kaldı

    def test_pr_limits(self):
        FakeWeb.state["suggestions"] = [
            S("s1", "herkes eve döndü", "herkes evine döndü"),
            S("s2", "İlk bölüm", "Birinci bölüm", index=0),
        ]
        errors = sg.run(self.web, "x/y", gh=self.gh)
        self.assertEqual(errors, 0)
        # max_new_prs=1 ile ikinci PR açılmaz, öneri beklemede kalır.
        FakeWeb.state = {"suggestions": [
            S("t1", "herkes eve döndü", "herkes evine döndü", slug="diger"),
            S("t2", "İlk bölüm", "Birinci bölüm", index=0, slug="diger")], "patches": [], "ingests": []}
        self.gh = FakeGh()
        stats = sg.process_pending(FakeWeb.state["suggestions"], "x/y", self.web, self.gh,
                                   self.tmp, max_new_prs=1)
        self.assertEqual(stats["pr_opened"], 1)
        self.assertEqual(stats["skipped_limit"], 1)

    def test_old_shape_records_are_skipped_not_crashing(self):
        FakeWeb.state["suggestions"] = [
            {"id": "eski", "status": "pending", "selectedText": "x", "suggestedText": "y",
             "chapter": {"index": 1}},                       # sourceKey/chapterIndex yok
            S("ok1", "herkes eve döndü", "herkes evine döndü"),
        ]
        errors = sg.run(self.web, "x/y", gh=self.gh)
        self.assertEqual(errors, 0)
        self.assertEqual(len(self.gh.created), 1)

    def test_failed_pr_creation_deletes_orphan_branch_and_keeps_pending(self):
        class BrokenGh(FakeGh):
            def pr_create(self, head, title, body):
                raise RuntimeError("Resource not accessible by integration")
        FakeWeb.state["suggestions"] = [S("s1", "herkes eve döndü", "herkes evine döndü")]
        errors = sg.run(self.web, "x/y", gh=BrokenGh())
        self.assertEqual(errors, 1)
        self.assertNotIn("oneri/", sh("git", "branch", "-a", cwd=self.bare))   # dal temizlendi
        self.assertEqual(FakeWeb.state["patches"], [])                         # beklemede kaldı

    def test_dry_run_changes_nothing(self):
        FakeWeb.state["suggestions"] = [S("s1", "herkes eve döndü", "herkes evine döndü")]
        sg.run(self.web, "x/y", gh=self.gh, dry_run=True)
        self.assertEqual(self.gh.created, [])
        self.assertEqual(FakeWeb.state["patches"], [])
        self.assertNotIn("oneri/", sh("git", "branch", "-a", cwd=self.bare))

    def test_suggestions_file_mode_opens_pr_without_touching_web(self):
        path = os.path.join(self.tmp, "s.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump([S("f1", "herkes eve döndü", "herkes evine döndü")], f)
        errors = sg.run(None, "x/y", gh=self.gh, suggestions_file=path)
        self.assertEqual(errors, 0)
        self.assertEqual(len(self.gh.created), 1)

    def test_reconcile_merged_reingests_then_marks_merged(self):
        url = "https://github.com/o/r/pull/5"
        FakeWeb.state["suggestions"] = [
            S("m1", "a", "b", status="pr_open", prUrl=url),
            S("m2", "c", "d", status="pr_open", prUrl=url),
        ]
        self.gh.views[url] = {"state": "MERGED", "mergeCommit": {"oid": "abc123"}}
        sg.run(self.web, "x/y", gh=self.gh)
        self.assertEqual(FakeWeb.state["ingests"],
                         [{"series": "demo-seri", "slug": "demo", "sourceKey": "demo", "ref": "abc123"}])
        self.assertEqual([(p["id"], p["status"]) for p in FakeWeb.state["patches"]],
                         [("m1", "merged"), ("m2", "merged")])

    def test_reconcile_closed_is_rejected_and_open_is_left(self):
        FakeWeb.state["suggestions"] = [
            S("c1", "a", "b", status="pr_open", prUrl="https://github.com/o/r/pull/6"),
            S("o1", "a", "b", status="pr_open", prUrl="https://github.com/o/r/pull/7"),
        ]
        self.gh.views["https://github.com/o/r/pull/6"] = {"state": "CLOSED", "mergeCommit": None}
        self.gh.views["https://github.com/o/r/pull/7"] = {"state": "OPEN", "mergeCommit": None}
        sg.run(self.web, "x/y", gh=self.gh)
        self.assertEqual([(p["id"], p["status"]) for p in FakeWeb.state["patches"]], [("c1", "rejected")])
        self.assertEqual(FakeWeb.state["ingests"], [])

    def test_failed_reingest_keeps_pr_open_for_retry(self):
        url = "https://github.com/o/r/pull/8"
        FakeWeb.state["suggestions"] = [S("e1", "a", "b", status="pr_open", prUrl=url,
                                          slug="yok-boyle-kitap")]
        self.gh.views[url] = {"state": "MERGED", "mergeCommit": {"oid": "zzz"}}
        errors = sg.run(self.web, "x/y", gh=self.gh)
        self.assertGreater(errors, 0)
        self.assertEqual(FakeWeb.state["patches"], [])   # merged işaretlenmedi


if __name__ == "__main__":
    unittest.main(verbosity=2)
