# Reddit Otomasyonu: Geliştirme Notları ve Çözümler (Shadow DOM & AI Formats)

Bu doküman, WordPress blog yazılarının otomatik olarak Reddit'e gönderilmesi projesinde (Reddit Automation) karşılaşılan engelleri ve ebediyen çözülen mantıksal hataları kayıt altına alır. Tekrar aynı sorunları yaşamamak amacıyla Hermes/AI asistanı tarafından derlenmiştir.

## Karşılaşılan Temel Sorunlar ve Çözümleri

### 1. Reddit "Shadow DOM" ve Playwright Tıkanması
**Sorun:** Reddit'in `new.reddit.com` ve ana sayfası tamamen Web Components (Shadow DOM) ve React tabanlıdır. Otomasyon araçları (Playwright/Browser-use vs.) `textarea` elementlerini bulamıyor, bulsa bile focus olamıyor ve timeout atıyordu. Klavye simülasyonları da eksik kalıyordu.
**Çözüm:** Gönderim platformu stabil form tabanlı **`old.reddit.com`** adresine çekildi. 
* Orijinal, temiz `<textarea name="title">` ve `<textarea name="text">` HTML formları sayesinde odaklanma sorunu %100 ortadan kalktı. (`core/browser_reddit_client.py` güncellendi).

### 2. Submit (Gönder) Butonunda Görünürlük Sorunu (Timeout)
**Sorun:** `old.reddit.com` üzerinde form doldurulsa dahi, Submit butonu bazen div altında kaldığı ya da scroll dışında olduğu için Playwright'ın `wait_for_selector` (görünür olmasını bekleme) komutuna takılarak `Timeout` atıyordu.
**Çözüm:** Butona direkt olarak **JavaScript Enjeksiyonu** ile tıklanması sağlandı. 
* Elementin Playwright gözündeki DOM stabilitesi kontrol edilmek yerine doğrudan sayfa içine JS inşaa edilip `btn.click()` gönderildi (Görünürlük ve Stabilite kontrolü atlandı).

### 3. AI Geliştiricisinin Metni Düz Vermesi (Wall of Text) ve Link Eksikliği
**Sorun:** Yapay zeka blog yazılarını özetliyordu ancak sonuçlar dümdüz, okunaksız, sıkıcı bir metin yığınıydı (Markdown yoktu). Ayrıca blogun orijinal bağlantısını metnin sonuna eklemiyordu.
**Çözüm:** `core/prompt_templates.py` içerisindeki `SYSTEM_PROMPT_BASE` baştan yazıldı:
* Katı kurallar eklendi: Önemli yerleri `**kalın (bold)**` yapması, `-` işaretleriyle okunabilir maddeler üretmesi emredildi.
* URL bağlantısı, `[Devamı için tıklayın](URL)` formatı ile standartlaştırıp AI tarafından unudulsa dahi Python parser'ı tarafından (%100 garanti olarak) metnin EN SONUNA eklenmesi işlemi (`core/ai_generator.py`) kodlandı.

### 4. Mantık Hatası: Ham Gönderilerin Onay Döngüsüne Düşmesi ve Eskiyi Paylaşması
**Sorun:** `python3 main.py review` komutu, hem orijinal WordPress ham yazısını (ID: 1) hem de AI tarafından zenginleştirilmiş yazıyı (ID: 767) `generated` statüsünde görüyordu. Kullanıcı tümünü approved yaptığında, script ID numarası küçük olmasından mütevellit bozuk ham yazıyı paylaşıyordu.
**Çözüm:** `cli.py` içerisinde `generate` adımındaki `update_post_status` kodu `processed` olarak değiştirildi. Böylece orijinal ham blog verisi döngüden çıkarıldı; ekrana (Review) sadece yapay zekanın yazdığı harika içerikler yansıması sağlandı.

---

## Rutin İşleyiş (Günlük İş Akışı)
Bilgisayarınızı veya sunucuyu her gün kendi kendine bırakırken şu sırayı takip edebilirsiniz:

1. **Parse:** `python3 main.py parse --csv data/wpblog.csv` (Varsa yeni CSV'yi veritabanına ekle)
2. **Generate:** `python3 main.py generate --count 5` (5 adet yeni okunaklı AI taslağı çıkart)
3. **Review:** `python3 main.py review` ("a" diyerek taslakları onayla)
4. **Post:** `python3 main.py browser-post --headful` (Otomatik olarak Reddit'e zımbala. Tam arka plan çalıştırmak için `--headful` etiketini kaldırabilirsiniz)

*Not: Gerektiği takdirde `scheduler.py` veya Linux `cron` ile 4. adımı günde 5 defa tetikletebilirsiniz.*
