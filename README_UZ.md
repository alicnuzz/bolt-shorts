# YouTube Shorts avtomatik pipeline

Har kuni ertalab soat **08:17 da** (Toshkent vaqti) ishlaydi:

1. Navbatdagi mavzu bo'yicha 30–45 soniyalik inglizcha video yasaydi. Sahnalar kod bilan chiziladi, bola ovozi bilan o'qiladi, subtitr va musiqa qo'shiladi.
2. Videoni **Telegram botingizga** yuboradi, ostida **✅ Yuklash / ❌ Bekor** tugmalari bo'ladi.
3. ✅ ni bossangiz, 30 daqiqa ichida videoni sarlavha, tavsif va teglar bilan **YouTube'ga yuklaydi**. Keyin YouTube havolasini botga hisobot qilib yuboradi.
4. Har yakshanba kechqurun botga kanal statistikasini yuboradi. Botga `/report` yozib istalgan vaqtda ham olishingiz mumkin.

Tayyor 30 ta mavzu bor (`topics.json`). Ular tugagach, ro'yxat boshidan qayta boshlanadi. Yangi mavzular kerak bo'lsa, Claude'dan so'rang.

Hammasi **bepul**: GitHub Actions, Microsoft Edge ovozi va YouTube API.

---

## 1-qadam. Telegram bot (5 daqiqa)

1. Telegram'da **@BotFather** ga yozing va `/newbot` buyrug'ini yuboring.
2. Botga nom bering. BotFather sizga **token** beradi (masalan `7123456789:AAH...`). Uni saqlab qo'ying.
3. Chat ID'ingizni bilish uchun **@userinfobot** ga yozing. U sizga raqam qaytaradi, bu sizning **chat ID**ingiz.
4. O'zingizning yangi botingizga ham `/start` yozing. Busiz bot sizga xabar yubora olmaydi.

## 2-qadam. YouTube API (15 daqiqa)

1. https://console.cloud.google.com ga kiring va yangi loyiha (project) yarating.
2. **APIs & Services → Library** bo'limidan **YouTube Data API v3** ni topib **Enable** qiling.
3. **OAuth consent screen** sozlamalarida:
   - User type: **External**.
   - Ilova nomini yozing.
   - **Test users** ro'yxatiga YouTube kanalingiz ochilgan Gmail'ni qo'shing.
   - **Publishing status** ni **In production** ga o'tkazing. Aks holda token 7 kundan keyin ishlamay qoladi.
4. **Credentials → Create credentials → OAuth client ID** ni tanlang:
   - Turi: **Desktop app**.
   - **JSON yuklab olish** tugmasini bosing.
   - Faylni `client_secret.json` nomi bilan shu papkaga qo'ying.
5. Mac'da Terminal oching:
   ```
   cd ~/Desktop/"you tube shorts"
   pip3 install google-auth-oauthlib
   python3 get_token.py
   ```
   Brauzer ochiladi. Kanalingiz akkauntini tanlab ruxsat bering ("unverified app" ogohlantirishi chiqsa: **Advanced → Go to ...**). Terminalda 3 ta qiymat chiqadi: `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.

> ⚠️ **Muhim:** Google tekshiruvidan (audit) o'tmagan yangi API loyihalari orqali yuklangan videolar **private** holatda qulflanib qoladi. Buni hal qilishning ikki yo'li bor:
> - Bepul audit arizasini to'ldiring: https://support.google.com/youtube/contact/yt_api_form ("YouTube API Services – Audit and Quota Extension"). Odatda 1–3 hafta kutiladi.
> - Audit tasdiqlanguncha: agar yuklash muvaffaqiyatsiz bo'lsa yoki video private bo'lib qolsa, bot sarlavha va tavsifni nusxa olishga tayyor holda yuboradi. Videoni Telegram'dan saqlab, YouTube ilovasidan 30 soniyada o'zingiz yuklaysiz.

## 3-qadam. GitHub (10 daqiqa)

1. https://github.com da akkaunt oching.
2. **New repository** yarating. **Public** qilish tavsiya etiladi: public repo'da Actions cheksiz bepul. Kalitlar Secrets'da yashirin turadi, ular kodga kirmaydi.
3. **Add file → Upload files** orqali shu papkadagi barcha fayllarni yuklang. `client_secret.json` ni yuklamang! `.github` papkasi ham yuklanishi kerak; agar yashirin papka yuklanmasa, GitHub Desktop ilovasidan foydalaning.
4. **Settings → Secrets and variables → Actions → New repository secret** orqali quyidagilarni qo'shing:

   | Nomi | Qiymati |
   |---|---|
   | `TG_TOKEN` | BotFather bergan token |
   | `TG_CHAT_ID` | @userinfobot bergan raqam |
   | `YT_CLIENT_ID` | get_token.py natijasi |
   | `YT_CLIENT_SECRET` | get_token.py natijasi |
   | `YT_REFRESH_TOKEN` | get_token.py natijasi |

   Ixtiyoriy sozlamalar (**Variables** bo'limida):
   - `START_DATE`: birinchi mavzu qaysi kuni chiqishi, masalan `2026-11-15`.
   - `YT_PRIVACY`: `public`, `unlisted` yoki `private`.
5. **Actions** bo'limida workflow'larni yoqing. **Daily short → Run workflow** ni bosing. 3–5 daqiqadan keyin botingizga birinchi video keladi.

## Fayllar

| Fayl | Vazifasi |
|---|---|
| `make_video.py` | Videoni chizadi: sahnalar, ovoz, subtitr, musiqa |
| `topics.json` | 30 ta mavzu: ssenariy, sarlavha, tavsif, teglar, sahnalar |
| `bot.py` | Telegram bot, YouTube'ga yuklash va hisobot |
| `get_token.py` | YouTube kalitini olish uchun (bir marta ishga tushiriladi) |
| `.github/workflows/` | Kunlik jadval: render, tasdiqni tekshirish, haftalik hisobot |

Kompyuterda namuna ko'rish uchun (ovozsiz): `python3 make_video.py --topic 0 --out namuna.mp4 --no-tts`
