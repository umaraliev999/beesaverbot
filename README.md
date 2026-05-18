# 📥 Media Downloader Bot v2.0

## ✨ Yangi funksiyalar
- 📊 Sifat tanlash: 360p / 720p / 1080p
- 👤 Foydalanuvchilar statistikasi (`/stats`)
- 🗂️ YouTube Playlist yuklab olish
- 💾 SQLite ma'lumotlar bazasi

---

## 🚀 O'rnatish (Windows)

```bash
cd beesaverbot_v2
pip install -r requirements.txt
```

`.env.example` → `.env` ga nusxalab, tokeningizni kiriting.

```bash
python bot.py
```

---

## ☁️ Railway ga deploy (24/7 bepul)

### 1. railway.app ga ro'yxatdan o'ting
https://railway.app → GitHub bilan kiring

### 2. Procfile yarating (papkaga)
```
worker: python bot.py
```

### 3. GitHub ga yuklang
```bash
git init
git add .
git commit -m "bot v2"
git push origin main
```

### 4. Railway da yangi loyiha
- New Project → Deploy from GitHub repo
- Repo ni tanlang
- Variables bo'limiga o'ting:
  - `BOT_TOKEN` = tokeningiz
  - `ADMIN_ID` = Telegram ID ingiz

### 5. Deploy!
Railway avtomatik ishga tushiradi ✅

---

## 📋 Buyruqlar

| Buyruq | Kim uchun | Tavsif |
|--------|-----------|--------|
| `/start` | Hammasi | Botni boshlash |
| `/help` | Hammasi | Yordam |
| `/stats` | Admin | Statistika |

---

## 📊 Statistika misoli
```
👥 Jami foydalanuvchilar: 142
📥 Jami yuklanmalar: 891
📺 YouTube: 654
📸 Instagram: 102
🎵 TikTok: 98
📌 Pinterest: 37
🎵 Audio: 201
🎬 Video: 690
```
