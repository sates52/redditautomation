# Reddit Otomasyon Sistemi: Analiz ve Geliştirme Raporu

Mevcut `redditautomation` projesi üzerinde yapılan teknik analiz sonucunda tespit edilen iyileştirme noktaları ve çözüm önerileri aşağıdadır.

---

## 🛠️ Düzeltilmesi Gereken Kritik Hatalar

### 1. Subreddit Dağıtım Hatası (Rotation)
*   **Mevcut Durum:** `cli.py` içindeki `parse` ve `process_all` komutlarında tüm postlar varsayılan olarak `konusarak_ogren` subreddit'ine atanmaktadır.
*   **Risk:** `r/IngilizceKonusma` kanalına hiç post gitmez ve veritabanına manuel müdahale gerekir.
*   **Çözüm:** Postlar eklenirken veritabanına ya bir "boş" (null) subreddit atanmalı ya da sıra ile (A/B testi gibi) dağıtılmalıdır.

### 2. Subreddit İsim Eşleşmesi
*   **Mevcut Durum:** Post gönderme sırasında `konusarak_ogren.replace('_', '')` mantığı kullanılıyor.
*   **Risk:** Reddit'teki gerçek isimler (`KonusarakOgren`, `IngilizceKonusma`) büyük-küçük harf veya özel karakter nedeniyle tam eşleşmeyebilir.
*   **Çözüm:** `.env` dosyasındaki `SUBREDDIT_1` ve `SUBREDDIT_2` değişkenleri doğrudan kullanılmalı.

---

## ✨ Önerilen Geliştirmeler (Features)

### 1. İçerik Çeşitliliği (Smart Prompting)
*   Sadece düz metin çevirisi yerine, Hermes AI'ya şu rolleri otomatik atayan bir yapı:
    *   "Bir İngilizce öğretmeni gibi anlat."
    *   "Bir öğrenciyle günlük diyalog kuruyormuş gibi yaz."
    *   "İş hayatı senaryosu üret."

### 2. Görsel Metin Desteği (Markdown Table)
*   Word'den gelen tablo verilerini Reddit'in kendi tablo formatına (`| Header | Column |`) dönüştüren bir parser geliştirilmeli. Bu, özellikle sayı ve telaffuz listeleri için çok daha profesyonel görünür.

### 3. Akıllı Zamanlayıcı (Smart Scheduler)
*   Sabit 6 saat beklemek yerine, Reddit'in yoğun olduğu saatlere (Sabah 09:00, Akşam 19:30) göre otomatik zamanlama kuyruğu oluşturulmalı.

---

## 📝 Hazırlık Kontrol Listesi (Checklist)

- [ ] `.env` dosyasındaki `NVIDIA_API_KEY` ve Reddit bilgilerini doldur.
- [ ] `data/word_files` klasörüne en az 5 adet Word dosyası yükle.
- [ ] `python cli.py process_all` komutunu çalıştır.
- [ ] `python cli.py generate --count 5` ile postları üret.
- [ ] `python cli.py review` ile ilk postlarını onayla.

---

> [!TIP]
> **Önemli Hatırlatma:** İlk paylaşımları yapmadan önce mutlaka bir "Test Subreddit" (kendinize özel) açıp orada deneme yapmanızı öneririm. Her şeyin düzgün göründüğünden emin olduktan sonra ana kanallara geçilmelidir.
