#!/usr/bin/env python3
"""
eptran — eval/run_eval.py

Altın test setini (eval/gold/*.jsonl + eval/private/*.jsonl) hattın
GERÇEK çeviri fonksiyonundan (translate.translate_chapter — aynı sistem
prompt'u, common_pitfalls, few-shot dahil) geçirir ve referans çeviriyle
karşılaştırıp puanlar. Amaç: prompt/model/QA değişikliklerinin çeviriyi
gerçekten iyileştirip iyileştirmediğini "galiba" yerine sayıyla görmek.

Kullanım (repo kökünden):
  python eval/run_eval.py --label baseline --limit 20
  python eval/run_eval.py --label fewshot-on --baseline eval/baseline.json
  EPTRAN_FEWSHOT=0 python eval/run_eval.py --label fewshot-off
  python eval/run_eval.py --dry-run            # API'siz: veriyi + puanlamayı sına

Metrikler (hepsi referansa göre; küçük sette GÜRÜLTÜLÜ — >=30 çift ideal):
  chrF        : karakter n-gram benzerliği, 0-100, yüksek iyi (sacrebleu)
  repeat_gap  : çeviride yakın mesafeli kelime tekrar oranı MİNUS referansınki.
                0'a yakın iyi, pozitif = referanstan daha tekrarcı ("var" tekrarı sorunu)
  en_residue  : çevrilmemiş İngilizce kalıntı kelime oranı (düşük iyi)
  len_ratio   : çeviri uzunluğu / referans uzunluğu (1.0 civarı iyi; çok düşük
                = içerik atlama şüphesi)
  failed      : API'nin boş döndürdüğü çiftler (chrF 0 sayılır)

Sonuç JSON'u eval/results/ altına yazılır (git'e girmez; workflow artifact
olarak yükler). Beğendiğin bir sonucu eval/baseline.json olarak kopyalayıp
commit'lersen sonraki koşular ona göre fark gösterir.
"""
import argparse
import glob
import json
import os
import re
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

GOLD_DIRS = [
    os.path.join(ROOT, "eval", "gold"),
    os.environ.get("EVAL_GOLD_DIR") or os.path.join(ROOT, "eval", "private"),
]
RESULTS_DIR = os.path.join(ROOT, "eval", "results")
CHRF_REGRESSION_THRESHOLD = 1.0
MIN_RELIABLE_ITEMS = 30


# ── Veri ─────────────────────────────────────────────────────────────────────

def load_gold() -> list:
    items, seen = [], set()
    for directory in GOLD_DIRS:
        for path in sorted(glob.glob(os.path.join(directory, "*.jsonl"))):
            if os.path.basename(path).startswith("_"):
                continue  # biçim örnekleri puanlanmaz
            with open(path, encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"Uyarı: {path}:{n} bozuk JSON, atlandı.")
                        continue
                    if not item.get("id") or not item.get("source") or not item.get("reference"):
                        print(f"Uyarı: {path}:{n} id/source/reference eksik, atlandı.")
                        continue
                    if item["id"] in seen:
                        print(f"Uyarı: yinelenen id '{item['id']}' atlandı.")
                        continue
                    seen.add(item["id"])
                    items.append(item)
    return items


# ── Metrikler (API'siz, tek başına test edilebilir) ──────────────────────────

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def repeat_rate(text: str, window: int = 12) -> float:
    """4+ harfli kelimelerin son `window` kelime içinde tekrar etme oranı."""
    tokens = [t for t in _WORD_RE.findall(text.lower()) if len(t) >= 4]
    if len(tokens) < 2:
        return 0.0
    repeats = sum(1 for i, t in enumerate(tokens) if t in tokens[max(0, i - window):i])
    return repeats / len(tokens)


def english_residue(text: str):
    """Çevrilmemiş İngilizce kelime oranı; english_detector yüklenemezse None."""
    try:
        from lib import english_detector
    except Exception:
        return None
    tokens = _WORD_RE.findall(text)
    if not tokens:
        return 0.0
    try:
        return len(english_detector.find(text)) / len(tokens)
    except Exception:
        return None


def chrf_scores(hyps: list, refs: list):
    """(corpus_chrF, [cümle_chrF...]); sacrebleu yoksa net hata verir."""
    try:
        from sacrebleu.metrics import CHRF
    except ImportError:
        sys.exit("sacrebleu yüklü değil: pip install -r eval/requirements.txt")
    chrf = CHRF()
    corpus = chrf.corpus_score(hyps, [refs]).score
    per_item = [chrf.sentence_score(h, [r]).score for h, r in zip(hyps, refs)]
    return corpus, per_item


def _mean(values: list):
    values = [v for v in values if v is not None]
    return round(statistics.mean(values), 4) if values else None


# ── Çeviri ───────────────────────────────────────────────────────────────────

def _model_name() -> str:
    try:
        with open(os.path.join(ROOT, "scripts", "lib", "groq_client.py"), encoding="utf-8") as f:
            match = re.search(r'model="([^"]+)"', f.read())
        return match.group(1) if match else "?"
    except OSError:
        return "?"


def _git_sha() -> str:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"][:10]
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "?"


def make_translator():
    """Hattın kendi translate_chapter'ını saran fonksiyon döner."""
    import translate
    from lib import groq_client as gc, ner

    clients = gc.get_clients()
    key_index = [0]

    def run(item: dict):
        protected = item.get("protected") or []
        protected_str = ner.build_protected_str({}, set(n.lower() for n in protected)) if protected else ""
        chapter = {
            "title": item.get("origin") or "Değerlendirme",
            "text": item["source"],
        }
        return translate.translate_chapter(chapter, clients, key_index, "", protected_str, 0, 1)

    return run


# ── Rapor ────────────────────────────────────────────────────────────────────

def summarize(results: list) -> dict:
    hyps = [r["hyp"] or "" for r in results]
    refs = [r["reference"] for r in results]
    corpus, per_item = chrf_scores(hyps, refs)
    for r, score in zip(results, per_item):
        r["chrf"] = round(score if r["hyp"] else 0.0, 2)
        r["repeat_gap"] = round(repeat_rate(r["hyp"] or "") - repeat_rate(r["reference"]), 4)
        r["en_residue"] = english_residue(r["hyp"] or "") if r["hyp"] else None
        r["len_ratio"] = round(len(r["hyp"] or "") / max(len(r["reference"]), 1), 3)
    return {
        "n": len(results),
        "failed": sum(1 for r in results if not r["hyp"]),
        "chrf": round(corpus, 2),
        "repeat_gap": _mean([r["repeat_gap"] for r in results]),
        "en_residue": _mean([r["en_residue"] for r in results]),
        "len_ratio": _mean([r["len_ratio"] for r in results]),
    }


def format_report(label: str, summary: dict, baseline: dict = None) -> str:
    rows = [
        ("chrF (yüksek iyi)", "chrf", True),
        ("repeat_gap (0'a yakın iyi)", "repeat_gap", False),
        ("en_residue (düşük iyi)", "en_residue", False),
        ("len_ratio (~1 iyi)", "len_ratio", False),
        ("başarısız çift", "failed", False),
    ]
    lines = [f"## Eval: {label}  ({summary['n']} çift)", ""]
    lines.append("| metrik | değer | baseline | fark |" if baseline else "| metrik | değer |")
    lines.append("|---|---|---|---|" if baseline else "|---|---|")
    for title, key, _ in rows:
        value = summary.get(key)
        if baseline:
            base = baseline.get(key)
            diff = (value - base) if isinstance(value, (int, float)) and isinstance(base, (int, float)) else None
            lines.append(f"| {title} | {value} | {base} | {'' if diff is None else f'{diff:+.3f}'} |")
        else:
            lines.append(f"| {title} | {value} |")
    if summary["n"] < MIN_RELIABLE_ITEMS:
        lines += ["", f"Uyarı: yalnızca {summary['n']} çift var; {MIN_RELIABLE_ITEMS}'un altında "
                      f"farklar gürültü olabilir."]
    if baseline and isinstance(baseline.get("chrf"), (int, float)):
        drop = baseline["chrf"] - summary["chrf"]
        if drop > CHRF_REGRESSION_THRESHOLD:
            lines += ["", f"Gerileme: chrF baseline'dan {drop:.2f} puan düşük."]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", default="run")
    parser.add_argument("--limit", type=int, default=0, help="en fazla N çift (0 = hepsi)")
    parser.add_argument("--baseline", default="", help="önceki sonuç JSON'u (karşılaştırma için)")
    parser.add_argument("--sleep", type=float, default=3.0, help="çiftler arası bekleme (sn, TPM için)")
    parser.add_argument("--dry-run", action="store_true",
                        help="API çağırma; referansı çeviri say (veri + puanlama testi)")
    args = parser.parse_args()

    os.chdir(ROOT)  # common_pitfalls.json / fewshot.json göreli okunuyor

    items = load_gold()
    if args.limit > 0:
        items = items[:args.limit]
    if not items:
        print("Altın sette puanlanacak çift yok. Önce: python eval/add_pair.py add ...")
        return 1
    print(f"{len(items)} çift yüklendi.")

    translate_fn = None if args.dry_run else make_translator()

    results = []
    for n, item in enumerate(items, 1):
        if args.dry_run:
            hyp = item["reference"]
        else:
            print(f"[{n}/{len(items)}] {item['id']}")
            try:
                hyp = translate_fn(item)
            except Exception as e:
                print(f"  Hata: {e}")
                hyp = None
            if n < len(items):
                time.sleep(args.sleep)
        results.append({
            "id": item["id"],
            "origin": item.get("origin", ""),
            "source": item["source"],
            "reference": item["reference"],
            "hyp": hyp,
        })

    summary = summarize(results)

    from lib import fewshot, pitfalls
    config = {
        "label": args.label,
        "model": "dry-run" if args.dry_run else _model_name(),
        "git_sha": _git_sha(),
        "fewshot_examples": len(fewshot.pick_examples()),
        "fewshot_env": os.environ.get("EPTRAN_FEWSHOT", "1"),
        "pitfalls_chars": len(pitfalls._build_pitfalls_block()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    baseline = None
    if args.baseline and os.path.exists(args.baseline):
        with open(args.baseline, encoding="utf-8") as f:
            baseline = json.load(f).get("summary")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    safe_label = re.sub(r"[^\w\-]+", "_", args.label)
    out_path = os.path.join(RESULTS_DIR, f"{datetime.now(timezone.utc):%Y%m%d-%H%M%S}_{safe_label}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"config": config, "summary": summary, "items": results}, f,
                  ensure_ascii=False, indent=2)

    report = format_report(args.label, summary, baseline)
    print("\n" + report)
    print(f"\nAyrıntılı sonuç: {os.path.relpath(out_path, ROOT)}")

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(report + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
