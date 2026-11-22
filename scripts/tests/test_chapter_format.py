"""
lib/chapter_format.py ve library_promote'un yayın biçimine çevirmesi için testler.

Çalıştır (repo kökünden):  python scripts/tests/test_chapter_format.py

convert.py (ebooklib/bs4/lxml ister) kurulu değilse "convert ile aynı sonucu verir"
testi atlanır; geri kalanı yalnızca standart kütüphane ister.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from lib.chapter_format import parse_chapter, to_published  # noqa: E402

GIT_ENV = {
    "GIT_AUTHOR_NAME": "eptran-bot", "GIT_AUTHOR_EMAIL": "bot@example.invalid",
    "GIT_COMMITTER_NAME": "eptran-bot", "GIT_COMMITTER_EMAIL": "bot@example.invalid",
}

WORKING = ("# Chapter 1: The Lighthouse Keeper\n\n"
           "Bölüm 1: Fener Bekçisi\n\n"
           "Fener bekçisi merdivenleri yavaşça tırmandı.\n\n"
           "\"Yine sakin bir gece,\" diye mırıldandı.\n")

SAMPLES = {
    "001.txt": WORKING,
    # Ünlemle biten meşru başlık (knh-11 hatası): başlık sayılmalı.
    "002.txt": "# Chapter 2: The Strategist Moves\n\nBölüm 2: Stratejist Hamle Yapıyor!\n\nGövde burada.\n",
    # Türkçe başlık satırı yok: ilk satır cümle, başlık orijinal kalır.
    "003.txt": "# Chapter 3: Rain\n\nYağmur o gece hiç durmadı, sokaklar boşalmıştı.\n\nİkinci paragraf.\n",
    # '#' başlığı yok (yayın biçimi / elle yazılmış).
    "004.txt": "Bölüm 4: Sessizlik\n\nSessizlik her şeyi kapladı.\n",
    # Başlık orijinalle aynı.
    "005.txt": "# Prologue\n\nPrologue\n\nBaşlangıç metni.\n",
    # Sadece başlık, gövde yok.
    "006.txt": "# Chapter 6\n",
}


class ChapterFormatTest(unittest.TestCase):
    def test_working_to_published(self):
        out = to_published("001.txt", WORKING)
        self.assertEqual(
            out,
            "Bölüm 1: Fener Bekçisi\n\n"
            "Fener bekçisi merdivenleri yavaşça tırmandı.\n\n"
            "\"Yine sakin bir gece,\" diye mırıldandı.\n")

    def test_published_form_has_no_hash_header_or_english_title(self):
        out = to_published("001.txt", WORKING)
        self.assertFalse(out.startswith("#"))
        self.assertNotIn("Lighthouse", out)

    def test_idempotent(self):
        for name, content in SAMPLES.items():
            once = to_published(name, content)
            twice = to_published(name, once)
            self.assertEqual(once, twice, f"{name}: yayın biçimi tekrar uygulanınca değişti")

    def test_exclamation_title_is_kept_as_title(self):
        title, body = parse_chapter("002.txt", SAMPLES["002.txt"])
        self.assertEqual(title, "Bölüm 2: Stratejist Hamle Yapıyor!")
        self.assertEqual(body, "Gövde burada.")

    def test_matches_convert_load_txt_chapters(self):
        """Burada taşınan kural, convert.py'dekiyle aynı sonucu vermeli (kayma koruması)."""
        try:
            import convert  # noqa: F401
        except ModuleNotFoundError as e:  # ebooklib/bs4/lxml yok
            self.skipTest(f"convert.py import edilemedi: {e}")
        tmp = tempfile.mkdtemp(prefix="eptran-chfmt-")
        try:
            for name, content in SAMPLES.items():
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
                    f.write(content)
            loaded = {c["filename"]: (c["title"], c["body"]) for c in convert.load_txt_chapters(tmp)}
            for name, content in SAMPLES.items():
                self.assertEqual(parse_chapter(name, content), loaded[name], name)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV}).stdout.strip()


class PromoteNormalizesTest(unittest.TestCase):
    """library_promote: staging'deki çalışma biçimi, main'e YAYIN biçimiyle girmeli."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="eptran-promote-test-")
        self.old_env = dict(os.environ)
        os.environ.update(GIT_ENV)
        self.bare = os.path.join(self.tmp, "library.git")
        sh("git", "init", "--bare", "--initial-branch=main", self.bare)
        seed = os.path.join(self.tmp, "seed")
        sh("git", "clone", self.bare, seed)
        with open(os.path.join(seed, "README.md"), "w") as f:
            f.write("library\n")
        sh("git", "add", "-A", cwd=seed)
        sh("git", "commit", "-m", "init", cwd=seed)
        sh("git", "push", "origin", "HEAD:main", cwd=seed)
        # staging/demo: çalışma biçiminde bölüm + status aynası + index.json
        sh("git", "checkout", "-b", "staging/demo", cwd=seed)
        d = os.path.join(seed, "demo-seri", "demo")
        os.makedirs(d)
        with open(os.path.join(d, "001.txt"), "w", encoding="utf-8") as f:
            f.write(WORKING)
        with open(os.path.join(d, "status.json"), "w") as f:
            f.write('{"book": "demo"}')
        with open(os.path.join(seed, "demo-seri", "index.json"), "w") as f:
            json.dump({"seri": "demo-seri", "ad": "Demo", "ciltler": [
                {"slug": "demo", "baslik": "Demo", "yazar": None, "bolum_sayisi": 1,
                 "epub": "https://example.invalid/demo.epub"}]}, f)
        sh("git", "add", "-A", cwd=seed)
        sh("git", "commit", "-m", "staging", cwd=seed)
        sh("git", "push", "origin", "staging/demo", cwd=seed)
        os.environ["LIBRARY_CLONE_URL"] = self.bare

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old_env)
        shutil.rmtree(self.tmp, ignore_errors=True)
        for m in [m for m in sys.modules if m == "library_promote"]:
            del sys.modules[m]

    def test_main_gets_published_form(self):
        import library_promote
        series = library_promote._attempt("x/y", "demo", self.tmp, 1)
        self.assertEqual(series, "demo-seri")
        body = sh("git", "show", "main:demo-seri/demo/001.txt", cwd=self.bare)
        self.assertTrue(body.startswith("Bölüm 1: Fener Bekçisi"))
        self.assertNotIn("# Chapter 1", body)
        # status aynası ve index.json da ana dala geldi.
        files = sh("git", "ls-tree", "-r", "--name-only", "main", cwd=self.bare).splitlines()
        self.assertIn("demo-seri/demo/status.json", files)
        self.assertIn("demo-seri/index.json", files)
        # staging'deki çalışma biçimi bozulmadı (gidiş-dönüş için kalmalı).
        staged = sh("git", "show", "staging/demo:demo-seri/demo/001.txt", cwd=self.bare)
        self.assertTrue(staged.startswith("# Chapter 1"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
