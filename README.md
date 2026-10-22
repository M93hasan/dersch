# AÖL Cep Dersim

Açık Öğretim Lisesi için çevrimdışı çalışabilen ders, özet, günlük görev ve test uygulaması. Web arayüzü Android APK'ya Capacitor ile paketlenebilir.

## Proje yapısı

- `pdf_kitaplar/`: MEB PDF kitapları (git'e kitap eklemeyin; `.gitignore` kapsamındadır).
- `scripts/pdf_to_json.py`: PDF metnini ve olası çoktan seçmeli soruları `data/dersler.json` dosyasına çıkarır.
- `data/dersler.json`: Uygulamanın kullandığı ders/ünite/soru verisi.
- `app/`: React + Vite mobil uyumlu arayüz.

## 1. PDF verisini oluşturma (Windows)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/pdf_to_json.py
```

Tarama olarak kaydedilmiş (metin seçilemeyen) PDF'lerde OCR gerekir. Soru ayrıştırma sezgiseldir; oluşturulan soruları uygulamada kullanmadan önce kontrol edin. Cevap anahtarı PDF'te açıkça bulunmuyorsa sistem cevap uydurmaz.

## 2. Uygulamayı çalıştırma

```powershell
npm install
npm run dev
```

## 3. Android APK

Node.js LTS ve Android Studio (Android SDK) kurulu olmalı:

```powershell
npm run build
npx cap add android
npx cap sync android
npx cap open android
```

Android Studio'da **Build > Build Bundle(s) / APK(s) > Build APK(s)**. İlk `cap add android` komutu Android klasörünü bir kez oluşturur.

## Önemli notlar

- İlerleme, yanlış sorular, puan ve ayarlar cihazdaki localStorage'da saklanır; uygulama internet olmadan çalışabilir.
- PDF'ler ve çıkarılan içerik telifli olabilir. Yalnızca kullanma hakkınız olan kitapları kullanın ve içerikleri herkese açık şekilde dağıtmayın.
- Bu başlangıç sürümü PDF metnini ve soru kalıplarını çıkarır; görsel/tablo ağırlıklı veya OCR gerektiren sayfalar elle doğrulanmalıdır.
