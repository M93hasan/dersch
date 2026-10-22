#!/usr/bin/env python3
"""Build the AÖL app's lesson JSON from local PDF books."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf_kitaplar"
OUT_FILES = [ROOT / "data" / "dersler.json", ROOT / "public" / "data" / "dersler.json"]

CATALOG = [
    "Akaid", "Almanca", "Biyoloji", "Coğrafya", "Çağdaş Türk ve Dünya Tarihi",
    "Demokrasi ve İnsan Hakları", "Din Kültürü ve Ahlak Bilgisi", "Dinler Tarihi",
    "Ekonomi", "Felsefe", "Fıkıh", "Fizik", "Fransızca", "Girişimcilik",
    "İngilizce", "İslam Kültür ve Medeniyeti", "İşletme", "Kelam", "Kimya",
    "Mantık", "Matematik", "Mesleki Gelişim Atölyesi", "Osmanlı Türkçesi",
    "Peygamberimizin Hayatı", "Psikoloji", "Sağlık Bilgisi ve Trafik Kültürü",
    "Sanat Tarihi", "Seçmeli Ortak Türk Tarihi", "Siyer", "Sosyoloji", "Tarih",
    "Temel Dini Bilgiler", "Türk Dili ve Edebiyatı",
    "Türkiye Cumhuriyeti İnkılap Tarihi ve Atatürkçülük",
]
UNIT_RE = re.compile(r"(?im)^\s*((?:ÜNİTE|UNIT)\s*[\dIVX]+[.: -]*.*|[\dIVX]+\.\s*ÜNİTE.*)$")
ANSWER_RE = re.compile(r"(?im)^\s*(\d{1,3})\s*[.)\-:]\s*([A-D])\s*$")


def slug(text: str) -> str:
    text = text.lower().translate(str.maketrans({"ı": "i", "ğ": "g", "ü": "u", "ş": "s", "ö": "o", "ç": "c"}))
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_") or "ders"


def make_summary(text: str) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:1200] + ("…" if len(clean) > 1200 else "")


def parse_questions(text: str, answer_key: dict[int, str]) -> list[dict]:
    lines, questions, i = text.splitlines(), [], 0
    while i < len(lines):
        match = re.match(r"^\s*(\d{1,3})[.)]\s+(.+?)\s*$", lines[i])
        if not match:
            i += 1
            continue
        number, stem, options = int(match.group(1)), [match.group(2).strip()], {}
        j = i + 1
        while j < len(lines):
            line = lines[j].strip()
            opt = re.match(r"^([A-Da-d])[).]\s*(.+)$", line)
            if opt:
                options[opt.group(1).upper()] = opt.group(2).strip()
            elif not options and line and not re.match(r"^\d{1,3}[.)]\s+", line):
                stem.append(line)
            elif options and (not line or re.match(r"^\d{1,3}[.)]\s+", line)):
                break
            elif options and line:
                options[list(options)[-1]] += " " + line
            j += 1
        if len(options) >= 2 and len(" ".join(stem)) >= 8:
            answer = answer_key.get(number)
            questions.append({
                "id": f"q{number}_{len(questions)+1}",
                "soru": re.sub(r"\s+", " ", " ".join(stem)).strip(),
                "secenekler": [{"id": k, "metin": v} for k, v in options.items()],
                "dogru_cevap": answer,
                "aciklama": "PDF'te açık bir açıklama bulunamadı. Konu metninden kontrol edin.",
                "dogrulama_gerekli": answer is None,
            })
        i = max(i + 1, j)
    return questions


def extract_pdf(path: Path, lesson_name: str) -> dict:
    with fitz.open(path) as doc:
        page_count = len(doc)
        pages = []
        for number, page in enumerate(doc, 1):
            text = page.get_text("text", sort=True).strip()
            if text:
                pages.append({"sayfa": number, "metin": text})
    full_text = "\n\n".join(page["metin"] for page in pages)
    if not full_text.strip():
        print(f"UYARI: {path.name}: seçilebilir metin yok; OCR gerekebilir.")
    answer_key = {int(m.group(1)): m.group(2).upper() for m in ANSWER_RE.finditer(full_text)}
    matches = list(UNIT_RE.finditer(full_text))
    units = []
    if not matches:
        units.append({
            "baslik": "Genel İçerik",
            "ozet": make_summary(full_text),
            "metin": full_text,
            "sayfalar": pages,
            "sorular": parse_questions(full_text, answer_key),
        })
    else:
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(full_text)
            chunk = full_text[match.start():end].strip()
            units.append({
                "baslik": match.group(1).strip(),
                "ozet": make_summary(chunk),
                "metin": chunk,
                "sayfalar": [],
                "sorular": parse_questions(chunk, answer_key),
            })
    return {
        "id": slug(lesson_name),
        "ad": lesson_name,
        "kaynak_dosya": path.name,
        "sayfa_sayisi": page_count,
        "unite_sayisi": len(units),
        "uniter": units,
    }


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    # Keep every catalogue lesson visible even before its PDF is available.
    lessons = {
        slug(name): {
            "id": slug(name), "ad": name, "kaynak_dosya": None,
            "sayfa_sayisi": 0, "unite_sayisi": 0, "uniter": [],
        }
        for name in CATALOG
    }
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"Henüz PDF bulunamadı. Kitapları buraya koyun: {PDF_DIR}")
    for pdf in pdfs:
        stem_slug = slug(pdf.stem)
        canonical = next((name for name in CATALOG if slug(name) == stem_slug), None)
        lesson_name = canonical or pdf.stem.replace("_", " ").replace("-", " ").strip().title()
        try:
            lesson = extract_pdf(pdf, lesson_name)
            lessons[lesson["id"]] = lesson
            print(f"OK: {pdf.name} -> {lesson['unite_sayisi']} ünite")
        except Exception as exc:
            print(f"HATA: {pdf.name}: {exc}")
    result = {
        "schema_version": 1,
        "olusturma_zamani": datetime.now(timezone.utc).isoformat(),
        "dersler": sorted(lessons.values(), key=lambda item: item["ad"].casefold()),
    }
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    for output in OUT_FILES:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
        print(f"Yazıldı: {output}")
    print(f"Toplam ders kataloğu: {len(lessons)}; PDF bulunan ders: {sum(bool(x['kaynak_dosya']) for x in lessons.values())}")


if __name__ == "__main__":
    main()
