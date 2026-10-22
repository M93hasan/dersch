#!/usr/bin/env python3
"""Extract PDF text and candidate multiple-choice questions into app JSON."""
from __future__ import annotations
import json, re
from datetime import datetime, timezone
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf_kitaplar"
OUT_FILES = [ROOT / "data" / "dersler.json", ROOT / "public" / "data" / "dersler.json"]
UNIT_RE = re.compile(r"(?im)^\s*((?:ÜNİTE|UNIT)\s*[\dIVX]+[.: -]*.*|[\dIVX]+\.\s*ÜNİTE.*)$")
ANSWER_RE = re.compile(r"(?im)^\s*(\d{1,3})\s*[.)\-:]\s*([A-D])\s*$")

def slug(text: str) -> str:
    text = text.lower().translate(str.maketrans({"ı":"i","ğ":"g","ü":"u","ş":"s","ö":"o","ç":"c"}))
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
            questions.append({"id": f"q{number}_{len(questions)+1}",
                "soru": re.sub(r"\s+", " ", " ".join(stem)).strip(),
                "secenekler": [{"id": k, "metin": v} for k, v in options.items()],
                "dogru_cevap": answer,
                "aciklama": "PDF'te açık bir açıklama bulunamadı. Konu metninden kontrol edin.",
                "dogrulama_gerekli": answer is None})
        i = max(i + 1, j)
    return questions

def extract_pdf(path: Path) -> dict:
    with fitz.open(path) as doc:
        pages = [{"sayfa": n, "metin": p.get_text("text", sort=True).strip()}
                 for n, p in enumerate(doc, 1) if p.get_text("text", sort=True).strip()]
        page_count = len(doc)
    full_text = "\n\n".join(p["metin"] for p in pages)
    if not full_text.strip():
        print(f"UYARI: {path.name}: seçilebilir metin yok; OCR gerekebilir.")
    answer_key = {int(m.group(1)): m.group(2).upper() for m in ANSWER_RE.finditer(full_text)}
    matches = list(UNIT_RE.finditer(full_text))
    units = []
    if not matches:
        units.append({"baslik":"Genel İçerik", "ozet":make_summary(full_text),
                      "metin":full_text, "sayfalar":pages, "sorular":parse_questions(full_text, answer_key)})
    else:
        for i, m in enumerate(matches):
            chunk = full_text[m.start():matches[i+1].start() if i+1<len(matches) else len(full_text)].strip()
            units.append({"baslik":m.group(1).strip(), "ozet":make_summary(chunk), "metin":chunk,
                          "sayfalar":[p for p in pages if p["metin"] in chunk],
                          "sorular":parse_questions(chunk, answer_key)})
    return {"id":slug(path.stem), "ad":path.stem.replace("_"," ").replace("-"," ").title(),
            "kaynak_dosya":path.name, "sayfa_sayisi":page_count, "unite_sayisi":len(units), "uniter":units}

def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs: print(f"PDF bulunamadı. Kitapları buraya ekleyin: {PDF_DIR}")
    dersler = []
    for pdf in pdfs:
        try:
            lesson = extract_pdf(pdf); dersler.append(lesson)
            print(f"OK: {pdf.name} -> {lesson['unite_sayisi']} ünite")
        except Exception as exc: print(f"HATA: {pdf.name}: {exc}")
    result = {"schema_version":1, "olusturma_zamani":datetime.now(timezone.utc).isoformat(), "dersler":dersler}
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    for out in OUT_FILES:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="utf-8")
        print(f"Yazıldı: {out}")
    print(f"Toplam ders: {len(dersler)}")

if __name__ == "__main__":
    main()
