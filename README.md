# AÖL Cep Dersim

Açık Öğretim Lisesi için mobil uyumlu çalışma uygulaması. Ders kataloğu, okuma ekranı, konu testleri, yanlış sorular, günlük görevler, tema seçimi ve cihazda ilerleme kaydı içerir. React + Vite arayüzü Capacitor ile Android projesine paketlenebilir.

## Ders kataloğu

Uygulamada 34 derslik başlangıç kataloğu bulunur. Bir dersin gerçek konu içeriği, kitabı yerel PDF olarak eklendikten ve dönüştürme betiği çalıştırıldıktan sonra görünür.

## PDF kitapları nereye konur?

PDF kitaplarını GitHub'a yüklemek gerekmez. Windows bilgisayarında projenin içindeki `pdf_kitaplar/` klasörüne kaydet:

```text
dersch/
  pdf_kitaplar/
    Akaid.pdf
    Almanca.pdf
    Biyoloji.pdf
    Türk Dili ve Edebiyatı.pdf
```

Dosya adını mümkün olduğunca dersin tam adıyla eşleştir. Büyük PDF'ler `.gitignore` tarafından GitHub commit'lerinden hariç tutulur; kitap dosyaları yalnızca senin bilgisayarında kalır. Böylece GitHub'ın dosya boyutu sınırına takılmazsın.

## Windows 11: PDF kitaplarını dönüştür

Python 3.12 ve Node.js LTS kurulu olmalı. PowerShell'de proje klasöründe:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/pdf_to_json.py
```

Betik hem `data/dersler.json` hem de `public/data/dersler.json` dosyasını üretir. Kitabı olmayan dersler katalogda kalır. PDF'nin içindeki metin seçilemiyorsa (taranmış sayfa/görüntü PDF) OCR gerekir. Ünite ve çoktan seçmeli soru tespiti sezgiseldir; her kitapta doğru çalışacağı garanti edilmez. Cevap anahtarı açık biçimde tanınamazsa doğru cevap uydurulmaz ve doğrulama gerekir.

## Uygulamayı bilgisayarda çalıştır

```powershell
npm install
npm run dev
```

Vite'ın gösterdiği yerel adresi tarayıcıda aç.

## Android APK hazırlama

Node.js LTS, Android Studio ve Android SDK gerekir:

```powershell
npm install
npm run build
npx cap add android
npx cap sync android
npx cap open android
```

`npx cap add android` yalnızca Android projesi ilk kez oluşturulurken çalıştırılır. Sonraki güncellemelerde `npm run build` ve `npx cap sync android` yeterlidir. Android Studio'da **Build > Build Bundle(s) / APK(s) > Build APK(s)** seç.

## Büyük PDF kitaplarını ileride çevrimiçi sunmak

GitHub kod deposu büyük PDF arşivi olarak kullanılmamalı. Kitapların telefondan çevrimiçi indirilmesi istenirse ayrı bir nesne depolama alanı (ör. Cloudflare R2) yapılandırılabilir. Bu depo henüz bu repoda yapılandırılmış değildir. Çevrimdışı okuma için PDF veya içeriklerin cihaza indirilmesi gerekir.

## Veri ve telif notları

- İlerleme, yanlış sorular, puan ve tema ayarları cihazın yerel depolamasında tutulur.
- PDF'den çıkarılan metin, özet ve sorular doğruluk açısından kontrol edilmelidir; bu başlangıç betiği yapay zekâ ile özet üretmez.
- Yalnızca kullanım/dağıtım hakkına sahip olduğun kitapları kullan. MEB materyallerini herkese açık biçimde yeniden dağıtmadan önce ilgili kullanım koşullarını kontrol et.
- Bu depo için APK derlemesi ve gerçek cihaz testi ayrıca yapılmalıdır.
