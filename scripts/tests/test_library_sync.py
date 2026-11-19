"""
lib/library_sync.py için uçtan uca test (ağ yok, yerel bare repo'lar).

Çalıştır (repo kökünden):  python scripts/tests/test_library_sync.py

Senaryo: sahte bir library (bare) + sahte eptran origin (bare) + book/test dalında
çalışan bir eptran çalışma kopyası. git_utils.write_status() gerçek akışı gibi
git_push()'u çağırır.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(SCRIPTS))

GIT_ENV = {
    "GIT_AUTHOR_NAME": "eptran-bot", "GIT_AUTHOR_EMAIL": "bot@example.invalid",
    "GIT_COMMITTER_NAME": "eptran-bot", "GIT_COMMITTER_EMAIL": "bot@example.invalid",
}


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV}).stdout.strip()


class LibrarySyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="eptran-sync-test-")
        self.old_cwd = os.getcwd()
        self.old_env = dict(os.environ)
        os.environ.update(GIT_ENV)

        # Sahte library: bare repo + main'de bir README.
        self.lib_bare = os.path.join(self.tmp, "library.git")
        sh("git", "init", "--bare", "--initial-branch=main", self.lib_bare)
        seed = os.path.join(self.tmp, "seed")
        sh("git", "clone", self.lib_bare, seed)
        with open(os.path.join(seed, "README.md"), "w") as f:
            f.write("library\n")
        sh("git", "add", "-A", cwd=seed)
        sh("git", "commit", "-m", "init", cwd=seed)
        sh("git", "push", "origin", "HEAD:main", cwd=seed)

        # Sahte eptran origin + çalışma kopyası (book/test dalında).
        self.ep_bare = os.path.join(self.tmp, "eptran.git")
        sh("git", "init", "--bare", "--initial-branch=main", self.ep_bare)
        self.ep = os.path.join(self.tmp, "eptran")
        sh("git", "clone", self.ep_bare, self.ep)
        with open(os.path.join(self.ep, "README.md"), "w") as f:
            f.write("eptran\n")
        sh("git", "add", "-A", cwd=self.ep)
        sh("git", "commit", "-m", "init", cwd=self.ep)
        sh("git", "push", "origin", "HEAD:main", cwd=self.ep)
        sh("git", "checkout", "-b", "book/test", cwd=self.ep)

        os.makedirs(os.path.join(self.ep, "output", "test", ".originals"))
        os.makedirs(os.path.join(self.ep, "output", "test", ".translated"))
        self.write("output/test/.originals/000_00.txt", "ENGLISH SOURCE\n")
        self.write("output/test/.translated/000_00.txt", "parça çevirisi\n")
        self.write("output/test/001_test.txt", "# Bölüm 1: Başlangıç\n\nMerhaba.\n")
        self.status = {"book": "test", "series": "Demo Seri", "status": "running",
                       "total": 2, "completed": 1}
        self.write("status.json", json.dumps(self.status))
        os.chdir(self.ep)

    def tearDown(self):
        os.chdir(self.old_cwd)
        os.environ.clear()
        os.environ.update(self.old_env)
        shutil.rmtree(self.tmp, ignore_errors=True)
        for m in [m for m in sys.modules if m == "lib" or m.startswith("lib.")]:
            del sys.modules[m]

    def write(self, rel, content):
        path = os.path.join(self.ep if hasattr(self, "ep") else ".", rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def enable(self):
        os.environ["LIBRARY_SYNC"] = "1"
        os.environ["LIBRARY_CLONE_URL"] = self.lib_bare

    def push_status(self, label="test"):
        from lib import git_utils
        git_utils.write_status(dict(self.status), label)

    def lib_files(self, branch="staging/test"):
        out = sh("git", "ls-tree", "-r", "--name-only", branch, cwd=self.lib_bare)
        return set(out.splitlines())

    def ep_files(self):
        out = sh("git", "ls-tree", "-r", "--name-only", "book/test", cwd=self.ep_bare)
        return set(out.splitlines())

    # ---- testler ----

    def test_disabled_is_noop(self):
        """Kapalıyken eski davranış: txt eptran'a gider, library'ye dokunulmaz."""
        self.push_status()
        self.assertIn("output/test/001_test.txt", self.ep_files())
        self.assertFalse(os.path.exists(".library"))
        refs = sh("git", "branch", "--list", cwd=self.lib_bare)
        self.assertNotIn("staging", refs)

    def test_enabled_splits_state_and_product(self):
        self.enable()
        self.push_status()
        lib = self.lib_files()
        self.assertIn("demo-seri/test/001.txt", lib)
        self.assertIn("demo-seri/test/status.json", lib)
        # İngilizce kaynak ve parça çevirileri library'ye GİRMEZ.
        self.assertFalse([p for p in lib if "originals" in p or "translated" in p])
        ep = self.ep_files()
        # Biten txt eptran'a girmez; çalışma durumu girer.
        self.assertNotIn("output/test/001_test.txt", ep)
        self.assertIn("output/test/.originals/000_00.txt", ep)
        self.assertIn("output/test/.translated/000_00.txt", ep)
        self.assertIn("status.json", ep)
        self.assertNotIn(".library/README.md", ep)
        # Seri yolu sabitlendi.
        pinned = json.loads(sh("git", "show", "book/test:status.json", cwd=self.ep_bare))
        self.assertEqual(pinned["library_series"], "demo-seri")
        # Metin birebir (round trip için).
        body = sh("git", "show", "staging/test:demo-seri/test/001.txt", cwd=self.lib_bare)
        self.assertEqual(body, "# Bölüm 1: Başlangıç\n\nMerhaba.")

    def test_idempotent_no_extra_commit(self):
        self.enable()
        self.push_status()
        n1 = sh("git", "rev-list", "--count", "staging/test", cwd=self.lib_bare)
        from lib import library_sync
        self.assertFalse(library_sync.sync_if_enabled())
        n2 = sh("git", "rev-list", "--count", "staging/test", cwd=self.lib_bare)
        self.assertEqual(n1, n2)

    def test_never_deletes_from_library(self):
        """Yerel output/ boşken (pull yapılmamış job) senkron library'yi silmemeli."""
        self.enable()
        self.push_status()
        os.remove("output/test/001_test.txt")
        self.status["completed"] = 1
        self.push_status("ikinci")
        self.assertIn("demo-seri/test/001.txt", self.lib_files())

    def test_pull_restores_finals_and_round_trips(self):
        self.enable()
        self.push_status()
        os.remove("output/test/001_test.txt")
        from lib import library_sync
        self.assertEqual(library_sync.pull(), 1)
        with open("output/test/001_test.txt", encoding="utf-8") as f:
            self.assertEqual(f.read(), "# Bölüm 1: Başlangıç\n\nMerhaba.\n")
        # Düzenle (review gibi) → tekrar senkron → library'de güncel.
        self.write("output/test/001_test.txt", "# Bölüm 1: Başlangıç\n\nMerhaba, dünya.\n")
        self.push_status("review")
        body = sh("git", "show", "staging/test:demo-seri/test/001.txt", cwd=self.lib_bare)
        self.assertIn("Merhaba, dünya.", body)

    def test_not_on_book_branch_is_noop(self):
        """main gibi dallarda aynayı bayat status ile ezmemeli."""
        self.enable()
        sh("git", "checkout", "-q", "main", cwd=self.ep)
        from lib import library_sync
        self.assertFalse(library_sync.sync_if_enabled())

    def test_series_pin_survives_later_series_change(self):
        self.enable()
        self.push_status()
        self.status["series"] = "Baska Seri"
        # İkinci çağrıda status.json'daki sabit değer kullanılmalı (dict'i kopya
        # yazmak sabiti ezer; gerçek akışta write_status dosyadan okunan dict'i yazar).
        pinned = json.load(open("status.json"))
        self.status["library_series"] = pinned["library_series"]
        self.push_status("ikinci")
        self.assertIn("demo-seri/test/001.txt", self.lib_files())
        self.assertFalse([p for p in self.lib_files() if p.startswith("baska-seri/")])

    def test_missing_token_raises(self):
        os.environ["LIBRARY_SYNC"] = "1"
        os.environ.pop("GH_TOKEN", None)
        os.environ.pop("LIBRARY_CLONE_URL", None)
        from lib import library_sync
        with self.assertRaises(RuntimeError):
            library_sync.sync_if_enabled()

    # ---- publish_library ile uyum ----

    def _patch_release(self):
        from lib import library_publish
        library_publish._ensure_release = (
            lambda repo, tag, title, epub: f"https://example.invalid/{tag}/{os.path.basename(epub)}")
        return library_publish

    def test_epub_is_not_committed_to_eptran(self):
        self.enable()
        self.push_status()
        self.write("output/test/test_tr.epub", "PK-fake-epub")
        self.status["convert_status"] = "completed"
        self.push_status("convert")
        self.assertNotIn("output/test/test_tr.epub", self.ep_files())

    def test_publish_in_sync_mode_keeps_incremental_content(self):
        """Senkron açıkken publish, bölümleri/status aynasını silmeden sadece index.json ekler."""
        self.enable()
        self.push_status()
        self.write("output/test/test_tr.epub", "PK-fake-epub")
        lp = self._patch_release()
        info = lp.publish_to_library("test", [{"title": "B", "body": "x"}],
                                     "output/test/test_tr.epub", "Başlık", None, "demo-seri")
        self.assertIsNotNone(info)
        lib = self.lib_files()
        self.assertIn("demo-seri/index.json", lib)
        self.assertIn("demo-seri/test/status.json", lib)
        # Bölüm, çalışma dosyasının BİREBİR haliyle duruyor (yeniden yazılmadı).
        body = sh("git", "show", "staging/test:demo-seri/test/001.txt", cwd=self.lib_bare)
        self.assertEqual(body, "# Bölüm 1: Başlangıç\n\nMerhaba.")
        index = json.loads(sh("git", "show", "staging/test:demo-seri/index.json", cwd=self.lib_bare))
        self.assertEqual(index["ciltler"][0]["slug"], "test")

    def test_publish_without_sync_keeps_legacy_behavior(self):
        """Senkron kapalıyken publish eski gibi bölümleri sıfırdan yazar."""
        os.environ["LIBRARY_CLONE_URL"] = self.lib_bare
        self.write("output/test/test_tr.epub", "PK-fake-epub")
        lp = self._patch_release()
        lp.publish_to_library("test", [{"title": "B", "body": "x"}],
                              "output/test/test_tr.epub", "Başlık", None, "demo-seri")
        body = sh("git", "show", "staging/test:demo-seri/test/001.txt", cwd=self.lib_bare)
        self.assertEqual(body, "B\n\nx")


if __name__ == "__main__":
    unittest.main(verbosity=2)
