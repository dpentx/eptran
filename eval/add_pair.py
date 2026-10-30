#!/usr/bin/env python3
"""
eptran — eval/add_pair.py

Altın test setine (eval/gold/*.jsonl) lisansı belli bir "kaynak + iyi
Türkçe çeviri" çifti ekler, ya da bir çifti few-shot örneği olarak
fewshot.json'a kopyalar.

Kullanım (repo kökünden):

  python eval/add_pair.py add \
      --id gutenberg-pp-001 \
      --source @kaynak.txt --reference @ceviri.txt \
      --origin "Pride and Prejudice, Böl. 1" \
      --license public-domain \
      --source-url https://www.gutenberg.org/ebooks/1342 \
      --translator "Çevirmen adı (öl. 1950)"

  python eval/add_pair.py add ... --private      # eval/private/ (git'e girmez)
  python eval/add_pair.py list
  python eval/add_pair.py fewshot gutenberg-pp-001

--source/--reference: metnin kendisi, ya da '@dosya.txt' ile dosyadan.

LİSANS KURALI: Telifli çeviriyi (basılı roman, yayınevi çevirisi) public
repoya KOYMA. Böyle bir veriyi sadece kendi testin için tutacaksan
--private kullan; o klasör .gitignore'da. Emin değilsen ekleme.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD_DIR = os.path.join(ROOT, "eval", "gold")
PRIVATE_DIR = os.path.join(ROOT, "eval", "private")
FEWSHOT_FILE = os.path.join(ROOT, "fewshot.json")

# public repoya girebilecek lisanslar
PUBLIC_LICENSES = {"public-domain", "CC0", "CC-BY", "CC-BY-SA", "own", "permission"}
# own        = senin kendi çevirin/düzeltmen (kaynak metin de serbestse)
# permission = çevirmenden açık YAZILI izin (DATA_SOURCES.md'ye not düş)

MIN_CHARS, MAX_CHARS = 20, 2500  # paragraf düzeyi; TPM tavanı yüzünden uzun metin yok
MAX_FEWSHOT_SIDE = 600


def _read_value(value: str) -> str:
    if value.startswith("@"):
        with open(value[1:], encoding="utf-8") as f:
            return f.read().strip()
    return value.strip()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "genel"


def _iter_gold(include_private: bool = True):
    dirs = [GOLD_DIR] + ([PRIVATE_DIR] if include_private else [])
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".jsonl"):
                continue
            path = os.path.join(d, name)
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    try:
                        yield path, json.loads(line)
                    except json.JSONDecodeError:
                        print(f"Uyarı: {path} içinde bozuk satır atlandı", file=sys.stderr)


def cmd_add(args) -> int:
    source = _read_value(args.source)
    reference = _read_value(args.reference)

    if args.license not in PUBLIC_LICENSES:
        print(f"Hata: lisans {sorted(PUBLIC_LICENSES)} içinden biri olmalı "
              f"(verilen: {args.license!r}). Lisansı belirsiz veri eklenmez.")
        return 1
    if args.license != "own" and not args.source_url:
        print("Hata: --source-url zorunlu (lisansı doğrulayabilmek için). "
              "Sadece kendi çevirinse --license own kullan.")
        return 1
    if not (MIN_CHARS <= len(source) <= MAX_CHARS and MIN_CHARS <= len(reference) <= MAX_CHARS):
        print(f"Hata: kaynak ve çeviri {MIN_CHARS}-{MAX_CHARS} karakter arasında olmalı "
              f"(şu an {len(source)} / {len(reference)}). Paragraf düzeyinde tut.")
        return 1
    if source.strip() == reference.strip():
        print("Hata: kaynak ile çeviri aynı.")
        return 1

    existing_ids = {item.get("id") for _, item in _iter_gold()}
    if args.id in existing_ids:
        print(f"Hata: '{args.id}' zaten var.")
        return 1

    item = {
        "id": args.id,
        "source": source,
        "reference": reference,
        "origin": args.origin,
        "license": args.license,
        "source_url": args.source_url or "",
        "translator": args.translator or "",
    }
    if args.protected:
        item["protected"] = [n.strip() for n in args.protected.split(",") if n.strip()]
    if args.note:
        item["note"] = args.note

    out_dir = PRIVATE_DIR if args.private else GOLD_DIR
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{_slug(args.origin.split(',')[0])}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Eklendi: {args.id} -> {os.path.relpath(path, ROOT)}")
    if not args.private:
        print("Hatırlatma: DATA_SOURCES.md'ye bu kaynağı (url, lisans, tarih) da yaz.")
    return 0


def cmd_list(_args) -> int:
    rows = [(p, i) for p, i in _iter_gold()]
    if not rows:
        print("Altın sette hiç çift yok.")
        return 0
    by_origin = {}
    for path, item in rows:
        key = (item.get("origin", "?"), item.get("license", "?"),
               "private" if PRIVATE_DIR in path else "public")
        by_origin[key] = by_origin.get(key, 0) + 1
    for (origin, lic, vis), n in sorted(by_origin.items()):
        print(f"{n:3d}  {lic:14s} {vis:7s} {origin}")
    scored = sum(1 for p, i in rows if not os.path.basename(p).startswith("_"))
    print(f"\nToplam: {len(rows)} çift ({scored} tanesi puanlamaya katılıyor)")
    return 0


def cmd_fewshot(args) -> int:
    match = next((i for _, i in _iter_gold() if i.get("id") == args.id), None)
    if not match:
        print(f"Hata: '{args.id}' altın sette yok.")
        return 1
    if match.get("license") not in PUBLIC_LICENSES:
        print("Hata: lisansı belirsiz çift few-shot'a eklenmez.")
        return 1
    if len(match["source"]) > MAX_FEWSHOT_SIDE or len(match["reference"]) > MAX_FEWSHOT_SIDE:
        print(f"Hata: few-shot örneği her iki yanda da en fazla {MAX_FEWSHOT_SIDE} karakter "
              f"olmalı (TPM bütçesi). Daha kısa bir çift seç.")
        return 1

    with open(FEWSHOT_FILE, encoding="utf-8") as f:
        data = json.load(f)
    entries = data.setdefault("entries", [])
    if any(e.get("id") == args.id for e in entries):
        print(f"'{args.id}' zaten fewshot.json'da.")
        return 0
    entries.append({
        "id": match["id"],
        "source": match["source"],
        "target": match["reference"],
        "origin": match.get("origin", ""),
        "license": match.get("license", ""),
    })
    with open(FEWSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"fewshot.json'a eklendi: {args.id} (toplam {len(entries)}; "
          f"prompt'a en fazla 3 tanesi girer)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="altın sete çift ekle")
    p_add.add_argument("--id", required=True)
    p_add.add_argument("--source", required=True, help="metin ya da @dosya")
    p_add.add_argument("--reference", required=True, help="metin ya da @dosya")
    p_add.add_argument("--origin", required=True, help="kitap/kaynak adı")
    p_add.add_argument("--license", required=True)
    p_add.add_argument("--source-url", default="")
    p_add.add_argument("--translator", default="")
    p_add.add_argument("--protected", default="",
                       help="virgülle ayrılmış özel isimler (çeviri bunları korumalı)")
    p_add.add_argument("--note", default="")
    p_add.add_argument("--private", action="store_true",
                       help="eval/private/ içine yaz (git'e girmez)")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="altın seti özetle")
    p_list.set_defaults(func=cmd_list)

    p_fs = sub.add_parser("fewshot", help="bir çifti fewshot.json'a kopyala")
    p_fs.add_argument("id")
    p_fs.set_defaults(func=cmd_fewshot)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
