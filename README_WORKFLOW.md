# Reddit Otomasyon Sistemi - Mevcut Durum ve İş Akışı (SKILL)

Bu dosya, projenin geldiği noktayı, kurulan altyapıyı ve gelecek adımları özetler. Yeni bir oturumda bu dosyayı referans alarak devam edebilirsiniz.

## 🛠️ Mevcut Altyapı
Sistem, WordPress `wpblog.csv` dosyasından içerik çekip NVIDIA AI (Llama 3.1 405B) ile Reddit gönderileri üretmek üzere kurgulanmıştır.

- **Veri Kaynağı:** `data/wpblog.csv` (WordPress'ten çekilen yaklaşık 800+ yayınlanmış blog yazısı).
- **AI Model:** `meta/llama-3.1-405b-instruct` (NVIDIA Build API).
- **Prompt Stratejisi:** "Konuşarak Öğren Ekibi" kurumsal kimliği ile, öğrenci verileri ve analizlerine dayanan, Markdown formatında içerik üretimi.
- **Veritabanı:** `data/reddit_automation.db` (SQLite). Tüm ham içerikler, üretilen postlar ve durumları burada tutulur.

## 📋 Tamamlanan Adımlar
1.  **CSV Parser Geliştirildi:** HTML temizliği yapan ve blog yazılarını SQLite'a `post_name` (slug) bilgisiyla yükleyen modül hazır.
2.  **AI Generator Kuruldu:** NVIDIA API üzerinden streaming destekli, kurumsal tonlu post üretici aktif.
3.  **CLI Güncellendi:** `--csv` parametresi ile toplu yükleme ve `status`, `review` komutları optimize edildi.
4.  **Test Başarılı:** İlk post kurumsal dilde üretildi ve el ile paylaşıldı.

## 🚀 Gelecek İş Akışı (Workflow)

### 1. Adım Adım Post Üretimi (Yarı-Otomatik)
Kullanıcı "Sıradaki 3 postu ver" dediğinde:
1.  SQLite'tan `status = 'pending'` olan en eski `N` post (`ORDER BY id ASC`) çekilir.
2.  `AIGenerator` üzerinden Markdown formatında içerikler üretilir.
3.  Sonuçlar `reddit_templates_[tarih].md` gibi bir dosyaya stilize edilerek kaydedilir.
4.  Üretilen postlar `status = 'generated'` olarak güncellenir.

### 2. Tam Otomasyon (Gelecek Planı)
- **Hermes AI Agent Entegrasyonu:** Onay mekanizmasını bir agent üzerinden veya belirli kurallarla aşarak otomatikleştirme.
- **Cron Job:** `cli.py post` komutunu günlük 1-2 kez tetikleyecek şekilde planlama.
- **Reddit API (PRAW):** PRAW modülü hazır, `.env` dosyasındaki API bilgileri doldurulduğunda direkt gönderim yapabilir.

## 📑 Dosya Yapısı Hatırlatıcı
- `cli.py`: Ana kontrol paneli.
- `core/csv_parser.py`: Veri temizleme ve yükleme.
- `core/ai_generator.py`: Prompt ve AI mantığı.
- `reddit_company_insight.md`: En son üretilen taslak dosyası.
