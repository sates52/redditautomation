# Reddit Otomasyon Sistemi — Konuşarak Öğren (Final V2 - CSV Destekli)

## Goal Description

Sistemin veri kaynağını, Word dosyaları yerine WordPress'ten dışa aktarılan `wpblog.csv` veritabanı yedeğine kaydırmak. Sistem, bu CSV dosyasındaki blog içeriklerini teker teker okuyacak ve NVIDIA Build API üzerinden verilen sistem promtuna sadık kalarak, organik, doğal ve "community-first" Reddit gönderileri üretecektir. Üretilen içeriklerin altına blog linki (`https://www.konusarakogren.com/blog/[post_name]`) eklenecek ve daha önce kurgulanan CLI onayı ile Reddit'e post edilebilecek duruma getirilecektir.

> [!NOTE]
> Önceki Word (`.docx`) okuma stratejisi yerine, artık yapısal olarak daha zengin olan veritabanı dışa aktarım (CSV) dosyası işlenecektir.

## Proposed Changes

### 1. `core/csv_parser.py` (YENİ)
- `data/wpblog.csv` dosyasını okuyacak modül.
- `post_status == 'publish'` ve `post_type == 'post'` olan satırları filtreleyecek.
- Her gönderi için `post_title`, `post_content` ve `post_name` sütunlarını parse edecek.
- HTML taglarını barındıran `post_content` alanını, token tasarrufu ve temiz bir prompt için düz metne (plaintext) çeviren bir temizleme (`beautifulsoup4` ile) fonksiyonu içerecek.

### 2. `core/ai_generator.py` (GÜNCELLEME)
- NVIDIA Build API (OpenAI uyumlu endpoint) entegrasyonu kurulacak. (Örn: `base_url="https://integrate.api.nvidia.com/v1"`)
- LLM'e gönderilecek **System Prompt** şu şekilde güncellenecektir:
  ```text
  You are a long-time Reddit user with high karma and deep familiarity with communities like r/SEO, r/Entrepreneur, r/Marketing, r/startups, and r/SideProject.
  Your task is to transform a given article into a Reddit post that feels completely natural, human, and community-first.
  Follow these strict rules:
  - Write in first-person voice (I, my experience, what I learned)
  - Sound like a real practitioner, not a brand
  - Do not use promotional or marketing language
  - Do not include links unless explicitly asked
  - Do not exaggerate results
  - Avoid fluff, be specific and grounded
  - Avoid unnecessary jargon unless relevant to subreddit context
  Structure your response EXACTLY like this:
  1. Title (Short, natural, curiosity-driven)
  2. Hook (first 2–3 lines)
  3. Context
  4. Core Insights (Most important section, natural bullet points)
  5. Mistakes / Challenges
  6. Practical Takeaways
  7. Closing + Discussion
  Tone: Intelligent but humble, Honest, Practical, No hype
  Return ONLY: Title and Reddit post body
  ```
- **User Prompt Formatting:** LLM'e şu formatta kullanıcı mesajı iletilecektir: 
  ```text
  Article:
  [post_title]
  [post_content]
  ```
- LLM'den dönen çıktı ayrıştırılacak ve postun en altına yönlendirme URL'si (`https://www.konusarakogren.com/blog/[post_name]`) otomatik eklenecektir.

### 3. `cli.py` (GÜNCELLEME)
- Word dosyalarını `parse` eden komut yapısı CSV'yi destekleyecek şekilde güncellenecektir:
  ```bash
  python cli.py parse --csv data/wpblog.csv
  ```

---

## Bağımlılıklar (Güncel)

```text
praw>=7.7.0             # Reddit API
openai>=1.30.0          # NVIDIA API (OpenAI-compat)
apscheduler>=3.10.0     # Zamanlama
python-dotenv>=1.0.0    # .env dosya okuma
rich>=13.0.0            # Etkileşimli CLI
click>=8.1.0            # CLI framework
pandas>=2.0.0           # CSV İşlemleri için (Opsiyonel ama verimli)
beautifulsoup4>=4.12.0  # HTML temizliği için
```

---

## Open Questions

> [!IMPORTANT]
> Lütfen aşağıdaki sorulara yanıt vererek uygulamanın geliştirme aşamasına yön verin.

1. **NVIDIA Model Seçimi ve Örnek Kod:** API kullanımı için `meta/llama-3.3-70b-instruct`, `deepseek-ai/deepseek-r1` veya `nvidia/nemotron-4-340b-instruct` modellerinden biri metin üretimi için mükemmel olacaktır. Bahsettiğiniz örnek kod parçasını ve belirlediğiniz spesifik model ismini paylaşabilir misiniz?
2. **HTML Temizliği:** Veritabanındaki `post_content` sütunu bolca HTML tagı ve satır içi iframe, image barındırıyor. AI sisteminin kafasını karıştırmaması için bunları süzüp ChatGPT'ye sadece saf metni vermemizi onaylıyor musunuz?

---

## Verification Plan

### Automated Tests
1. **Parser Test:** `wpblog.csv`'den en az 5 adet gönderinin (sadece yayınlananların) tam olarak title, content ve url (slug) değerleriyle başarılı parse edilip edilmediği test edilecek.
2. **API Bağlantı Testi:** NVIDIA API hedeflenen model adıyla tetiklenerek dönen sonucun "Title" ve "Hook" vb. yapılandırmalara uygun döndüğü teyit edilecek.

### Manual Verification
1. CLI üzerinden dry-run çalıştırılarak üretilen ilk Reddit post taslağı incelenecek.
2. Linkin doğru şekilde `https://www.konusarakogren.com/blog/[post_name]` yapısıyla alta eklenip eklenmediği gözle teyit edilecek.
