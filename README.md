# Eitaa Shop Crawler (Technical Assessment Project)

## Run with Docker
```bash
cp .env.example .env
docker compose up --build
```
## Run with python
```bash
cp .env.example .env
fill GROQ_API_KEY and EITAAYAR_TOKEN in .env
python main.py
```

## Architecture Overview

Global Search در ایتا به‌صورت URL-based در دسترس نیست.
بنابراین این پروژه از پکیج https://github.com/bistcuite/eitaapykit استفاده میکند
---


## Rate Limit Strategy

- Multi-session rotation round-robin
روش round-robin: به جای انتخاب تصادفی، هر بار pool.get() توکن بعدی را برمی‌گرداند و اندیس داخلی افزایش می‌یابد. این باعث توزیع یکنواخت استفاده از توکن‌ها می‌شود.
سلامت توکن: اگر توکنی خطای احراز هویت بدهد، fail_count آن افزایش می‌یابد و برای مدت زمانی براساس backoff (30s → 60s → 120s → ...) از استفاده بعدی کنار گذاشته می‌شود. اگر توکن موفقیت‌آمیز باشد، شمارش شکست آن ریست می‌شود.
دلیل: این رویکرد باعث می‌شود توکن‌های خراب یا موقتا محدودشده کمتر مورد استفاده قرار گیرند و سیستم بتواند خودبه‌خود واکنش نشان دهد.

همچنین با استفاده از ردیس:
جلوگیری از پردازش تکراری
کاهش بار API ایتا
کنترل Rate Limit
و آماده‌سازی پروژه برای Scale
بدون Redis، سیستم Stateless است و رفتار Crawl غیرقابل‌کنترل می‌شود.

---

## AI Usage (Groq)

- تولید هشتگ‌های هدفمند
- تشخیص فروشگاهی بودن کانال
- تمام Promptها و پاسخ‌ها فارسی هستند


