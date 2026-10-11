# guidetothai website

The guidetothai website in English, Arabic and Thai. It runs free on GitHub Pages and is built automatically every time you save a change.

Arabic instructions come first; the English version follows below.

## بالعربي

### النشر أول مرة

1. **أنشئ مستودعاً جديداً** على GitHub باسم مثل `guidetothai-site`.
   - اجعله **Public**، لأن GitHub Pages مجاني للمستودعات العامة.
2. **ارفع كل ملفات هذا المجلد** إلى المستودع.
   - تأكد أن مجلد `.github` ارتفع معها، لأنه هو الذي ينشر الموقع تلقائياً.
3. **فعّل النشر:** افتح **Settings ← Pages**، واختر في **Source** خيار **GitHub Actions**.
4. **انتظر دقيقة أو دقيقتين:** تابع التقدم في تبويب **Actions**، وبعدها يكون الموقع جاهزاً.

**تجربة الموقع قبل ربط الدومين:** إذا أردت فتح الموقع على `https://اسمك.github.io/guidetothai-site/` قبل ربط الدومين، اكتب في ملف `site.yml` السطر التالي:

```yaml
base_path: "/guidetothai-site"
```

### ربط الدومين guidetothai.co.th

1. **في ملف `site.yml`** غيّر السطرين:
   - `custom_domain: "guidetothai.co.th"`
   - `base_path: ""`
2. **في لوحة الدومين عند المسجّل** أضف هذه السجلات:

   | النوع | الاسم | القيمة |
   |---|---|---|
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | اسمك.github.io |

3. **في GitHub** افتح **Settings ← Pages**، واكتب الدومين، ثم فعّل **Enforce HTTPS** بعد ما يشتغل.

### إضافة مقال جديد في المدونة

1. افتح مجلد `content/posts` على GitHub.
2. انسخ أي مقال موجود وسمّه بهذا الشكل:
   - `2026-11-01-عنوان-بالانجليزي.ar.md` (اكتب التاريخ كما هو في البداية)
   - في نهاية الاسم استخدم `.ar.md` للعربي، أو `.en.md` للإنجليزي، أو `.th.md` للتايلندي.
   - أعطِ نسخ اللغات الثلاث **نفس الاسم** عشان يربط الموقع بينها.
3. عدّل الحقول في أعلى الملف:
   - `title`
   - `description`
   - `category`: واحد من `news` أو `visas` أو `medical` أو `business` أو `travel`
   - `image`
   - `sources`
4. اكتب المقال تحتها.
5. اضغط **Commit**، وبعد دقيقة يظهر المقال في الموقع وفي خريطة الموقع (sitemap) تلقائياً.

### تغيير الصور

- **صور صفحة "أعمالنا":** موجودة في `content/data/our-work.yml`.
- **روابط باقي الصور:** موجودة في `site.yml`.
- **لاستخدام صورة من صورك:** ارفعها إلى `assets/img/`، ثم ضع مسارها مكان الرابط، مثل `/assets/img/airport.jpg`.

### الصفحات والنصوص

| ماذا تريد أن تعدّل | مكانه |
|---|---|
| صفحات الخدمات | `content/pages/en/` و`content/pages/ar/` و`content/pages/th/` |
| القائمة | `content/partials/nav.*.html` |
| الفوتر | `content/partials/footer.*.html` |
| شريط الحجز | `content/partials/cta.*.html` |
| نصوص المدونة والأزرار | `content/data/i18n.yml` |

---

## English

### Publish for the first time

1. Create a **public** GitHub repository and upload all of these files, including the `.github` folder.
2. Open **Settings → Pages** and set **Source** to **GitHub Actions**.
3. Every push to `main` builds the site with `build.py` and publishes it.

### Build and preview locally

```bash
pip install -r requirements.txt
python3 build.py --serve     # http://localhost:8000
```

### Custom domain

1. Set `custom_domain: "guidetothai.co.th"` in `site.yml`.
2. Add the four A records listed above, plus a `www` CNAME pointing to `USERNAME.github.io`.
3. Enable **Enforce HTTPS** in **Settings → Pages**.

### New blog post

1. Add `content/posts/YYYY-MM-DD-slug.<en|ar|th>.md`.
2. Give the language versions of one article the same slug so they link to each other.

### Photos

- The photos still load from the old Webflow CDN.
- To move them into the repository, run `python3 tools/download-images.py` on your own computer and commit the files it adds.

### Layout of the project

| Path | Contents |
|---|---|
| `build.py` | The generator: pages, Our Work, blog, sitemap, hreflang, JSON-LD |
| `content/` | All text |
| `assets/` | CSS, JS, logo |
| `site.yml` | Settings |
