"""
eptran — lib/series.py

SERİ GENELİ HAFIZA (elle doldurulan glossary).

Neden bu var: knh-10'da "Lahan'ın Kardeşi" karakteri baştan yanlış
öğrenildi ("Lakan'ın Kardeşi" diye), memory.json'a öyle işlendi ve
sonra hem çeviri hem review bunu "doğru/tutarlı" sanıp 10 bölüm boyunca
165 yerde tekrarladı — sistem kendi hatasını kendi kendine büyüttü.
Bunun kökü: her kitap hafızayı SIFIRDAN, o kitabın kendi metninden
tahmin ederek öğreniyordu. Bir seri hakkında (karakterler, ilişkiler,
"bunu bununla karıştırma" gibi) zaten bilinen bir gerçek varsa, bunu
her kitapta yeniden keşfetmeye/tahmin etmeye zorlamak yerine, admin'in
BİR KEZ elle yazdığı bir dosyadan doğrudan vermek çok daha güvenli.

TASARIM İLKESİ — otomatik keşif OLUR, otomatik YAZMA OLMAZ: Bu modül
seriye ait bilgiyi kitabın memory.json'ına "besler" (seed + overlay),
ama TERSİNE hiçbir şey yapmaz — yani bir kitaptaki çeviri, seri
dosyasını KENDİLİĞİNDEN güncellemez. Otomatik iki yönlü senkronizasyon
knh-10'daki hatayı çözmek yerine artık TÜM seriye yayardı (blast radius
küçülmek yerine büyürdü). Seri dosyasını güncellemek her zaman admin'in
elle yapacağı, bilinçli bir adım olarak kalıyor.

DOSYA FORMATI (series/<slug>.json) — admin için mümkün olduğunca basit:

    {
      "series": "Kusuriya no Hitorigoto (Zehir Ustası)",
      "characters": {
        "Jinshi": "Jinshi",
        "Lahan's Brother": "Lahan'ın Kardeşi"
      },
      "terms": {
        "Red Plum Village": "Kızıl Erik Köyü"
      },
      "notes": [
        "Lakan'ın evlatlık oğlu Lahan'dır. 'Lahan'ın Kardeşi' diye anılan kişi Lahan'ın çiftçi kardeşidir — İmparator'un kardeşi Jinshi ile KARIŞTIRILMAMALI."
      ]
    }

Sadece "characters" ve "terms" zorunlu değil, ikisi de opsiyonel;
"notes" da opsiyonel. Admin sadece bildiği kadarını yazar, geri kalanı
kitaplar biriktirdikçe zamanla eklenir. Şema esnektir: bilinmeyen ekstra
alanlar (örn. ileride "relationships" gibi) sessizce yok sayılır, hata
vermez.
"""
import json
import os

SERIES_DIR = "series"


def _path(slug: str) -> str:
    safe = "".join(c for c in slug if c.isalnum() or c in "-_")
    return os.path.join(SERIES_DIR, f"{safe}.json")


def load(slug: str) -> dict:
    """
    series/<slug>.json'ı oku. Dosya yoksa (henüz o seri için bir
    glossary yazılmamışsa) sessizce boş sözlük döner — series alanı
    olan ama glossary'si olmayan bir kitap, eskisi gibi sıfırdan
    öğrenmeye devam eder, hata almaz.
    """
    path = _path(slug)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  Uyarı: series/{slug}.json okunamadı ({e}), göz ardı ediliyor.")
        return {}
    return {
        "characters": data.get("characters", {}) or {},
        "terms": data.get("terms", {}) or {},
        "notes": data.get("notes", []) or [],
    }


def apply_overlay(memory: dict, series_data: dict) -> dict:
    """
    Seri glossary'sini kitabın memory'sine uygula. Seri verisi HER ZAMAN
    KAZANIR — yani bir karakter hem kitabın kendi NER/review sürecinde
    hem seri dosyasında varsa, seri dosyasındaki değer geçerli olur.
    Bu fonksiyon, kitap ilerledikçe (update_from_translation sonrası
    dahil) TEKRAR TEKRAR çağrılmalı — böylece kitabın kendi öğrenme
    süreci seri düzeyinde zaten doğrulanmış bir bilgiyi YANLIŞLIKLA
    ezemez (knh-10'daki hatanın tam olarak önlenmesi istenen türü).
    """
    if not series_data:
        return memory
    memory.setdefault("characters", {}).update(series_data.get("characters", {}))
    memory.setdefault("terms", {}).update(series_data.get("terms", {}))
    if series_data.get("notes"):
        # notes tekrar tekrar eklenip şişmesin diye sıralı+tekilleştirilmiş tutuyoruz.
        existing = set(memory.get("series_notes", []))
        existing.update(series_data["notes"])
        memory["series_notes"] = sorted(existing)
    return memory
