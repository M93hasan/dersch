#!/usr/bin/env python3
"""Extract searchable text and heuristic multiple-choice questions from PDFs."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf_kitaplar"
OUT_FILE = ROOT / "data" / "dersler.json"

UNIT_RE = re.compile(r"(?im)^\s*((?:ÜNİTE|UNIT)\s*[\dIVX]+[.: -]*.*|[\dIVX]+\.\s*ÜNİTE.*)$")
QUESTION_RE = re.compile(r"(?m)^\s*(\d{1,3})[.)]\s+(.+)")
OPTION_RE = re.compile(r"(?m)^\s*([A-Da-d])[).]\s*(.+?)\s*$")
ANSWER_RE = re.compile(r"(?im)^\s*(\d{1,3})\s*[.)\-:]\s*([A-D])\s*$")


def slug(text: str) -> str:
    text = text.lower().translate(str.maketrans({"ı":"i","ğ":"g","ü":"u","ş":"s","ö":"o","ç":"c"}))
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_") or "ders"


def extract_pdf(path: Path) -> dict:
    doc = fitz.open(path)
    pages = []
    for page_no, page in enumerate(doc, 1):
        text = page.get_text("text", sort=True).strip()
        if text:
            pages.append({"sayfa": page_no, "metin": text})
    full_text = "\n\n".join(p["metin"] for p in pages)
    if not full_text.strip():
        print(f"UYARI: {path.name}: seçilebilir metin bulunamadı; OCR gerekebilir.")

    # Answers are only used when a clear standalone answer-key pattern exists.
    answer_key: dict[int, str] = {}
    for match in ANSWER_RE.finditer(full_text):
        answer_key[int(match.group(1))] = match.group(2).upper()

    units = []
    matches = list(UNIT_RE.finditer(full_text))
    if not matches:
        units.append({"baslik": "Genel İçerik", "ozet": full_text[:1800].strip(),
                      "sayfalar": pages, "sorular": []})
    else:
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            chunk = full_text[start:end].strip()
            unit_title = match.group(1).strip()
            questions = parse_questions(chunk, answer_key)
            units.append({
                "baslik": unit_title,
                "ozet": make_summary(chunk),
                "sayfalar": [{"sayfa": p["sayfa"], "metin": p["metin"]} for p in pages
                             if p["metin"] and p["metin"] in chunk],
                "metin": chunk,
                "sorular": questions,
            })

    return {
        "id": slug(path.stem),
        "ad": path.stem.replace("_", " ").replace("-", " ").title(),
        "kaynak_dosya": path.name,
        "sayfa_sayisi": len(doc),
        "unite_sayisi": len(units),
        "uniter": units,
    }


def make_summary(text: str) -> str:
    # Safe baseline summary: a short, readable excerpt, not AI-generated claims.
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:1200] + ("…" if len(clean) > 1200 else "")


def parse_questions(text: str, answer_key: dict[int, str]) -> list[dict]:
    lines = text.splitlines()
    questions = []
    i = 0
    while i < len(lines):
        match = re.match(r"^\s*(\d{1,3})[.)]\s+(.+?)\s*$", lines[i])
        if not match:
            i += 1
            continue
        number = int(match.group(1))
        stem = [match.group(2).strip()]
        options: dict[str, str] = {}
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
                # Wrapped option text: append to the most recently seen option.
                last = list(options)[-1]
                options[last] += " " + line
            j += 1
        if len(options) >= 2 and len(" ".join(stem)) >= 8:
            answer = answer_key.get(number)
            questions.append({
                "id": f"q{number}_{len(questions)+1}",
                "soru": re.sub(r"\s+", " ", " ".join(stem)).strip(),
                "secenekler": [{"id": key, "metin": value} for key, value in options.items()],
                "dogru_cevap": answer,
                "aciklama": "PDF'te açık bir açıklama bulunamadı. Konu metninden kontrol edin.",
                "dogrulama_gerekli": answer is None,
            })
        i = max(i + 1, j)
    return questions


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"PDF bulunamadı. Kitapları şu klasöre ekleyin: {PDF_DIR}")
    dersler = []
    for pdf in pdfs:
        try:
            ders = extract_pdf(pdf)
            dersler.append(ders)
            print(f"OK: {pdf.name} -> {ders['unite_sayisi']} ünite")
        except Exception as exc:
            print(f"HATA: {pdf.name}: {exc}")
    result = {
        "schema_version": 1,
        "olusturma_zamani": datetime.now(timezone.utc).isoformat(),
        "dersler": dersler,
    }
    OUT_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Yazıldı: {OUT_FILE} ({len(dersler)} ders)")


if __name__ == "__main__":
    main()
