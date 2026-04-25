# Reddit Otomasyon Sistemi - Konuşarak Öğren

Word dosyalarından içerik analiz ederek Reddit'e otomatik post paylaşan sistem.

## Kurulum

1. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

2. `.env` dosyasını oluşturun:
```bash
copy .env.example .env
```

3. `.env` dosyasını düzenleyin:
- Reddit API bilgilerini ekleyin
- NVIDIA API key ekleyin

## Kullanım

### 1. Word Dosyası Parse Etme
```bash
python cli.py parse --file "data/word_files/sayilar.docx"
```

### 2. AI ile Post Üretme
```bash
python cli.py generate --count 5
```

### 3. Postları İnceleme
```bash
python cli.py review
```

### 4. Reddit'e Gönderme
```bash
python cli.py post
```

### 5. Durum Kontrolü
```bash
python cli.py status
```

## Komutlar

| Komut | Açıklama |
|-------|----------|
| `parse` | Word dosyasını parse et |
| `generate` | AI ile post üret |
| `review` | Postları manuel incele |
| `post` | Onaylı postları gönder |
| `status` | Sistem durumunu göster |
| `process_all` | Tüm Word dosyalarını işle |

## Proje Yapısı

```
redditautomation/
├── config/          # Ayarlar ve promptlar
├── core/            # Ana modüller (parser, AI, Reddit)
├── models/          # Veritabanı modelleri
├── utils/           # Yardımcı araçlar
├── data/            # Word dosyaları ve veritabanı
└── cli.py           # Ana CLI arayüzü
```

## Reddit API Kurulumu

1. https://www.reddit.com/prefs/apps adresine gidin
2. "Create App" butonuna tıklayın
3. "script" türünü seçin
4. client_id ve client_secret bilgilerini alın

## NVIDIA API

https://build.nvidia.com adresinden API key alın.
