#!/usr/bin/env python3
"""
Builds the guidetothai website into the _site/ folder.

    python3 build.py            -> builds _site/
    python3 build.py --serve    -> builds and serves on http://localhost:8000

Content lives in content/:
  pages/<lang>/<slug>.html   service pages (HTML with a small YAML header)
  posts/<date>-<slug>.<lang>.md   blog articles (Markdown with a YAML header)
  partials/                  menu, footer and booking band per language
  data/                      translations (i18n.yml) and the Our Work gallery
"""
import datetime as dt
import html
import json
import math
import os
import re
import shutil
import sys

import markdown
import yaml

ROOT = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(ROOT, 'content')
OUT = os.path.join(ROOT, '_site')
LANGS = ['en', 'ar', 'th']
PREFIX = {'en': '', 'ar': '/ar', 'th': '/th'}
HREFLANG = {'en': 'en', 'ar': 'ar', 'th': 'th'}

SITE = yaml.safe_load(open(os.path.join(ROOT, 'site.yml'), encoding='utf-8'))
I18N = yaml.safe_load(open(os.path.join(C, 'data', 'i18n.yml'), encoding='utf-8'))
WORK = yaml.safe_load(open(os.path.join(C, 'data', 'our-work.yml'), encoding='utf-8'))
BASE = (SITE.get('base_path') or '').rstrip('/')
SITE_URL = SITE['site_url'].rstrip('/')
IMAGES = SITE.get('images', {})
WA = 'https://wa.me/' + str(SITE['whatsapp'])
TODAY = dt.date.today().isoformat()


def esc(s):
    return html.escape(str(s), quote=True)


def img(key):
    """Image key from site.yml -> URL (or pass a path/URL straight through)."""
    if not key:
        return IMAGES.get('hero-bangkok')
    return IMAGES.get(key, key)


def abs_url(path):
    if path.startswith('http'):
        return path
    return SITE_URL + BASE + path


def read(path):
    return open(path, encoding='utf-8').read()


def split_front(text):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def partial(name, lang):
    return read(os.path.join(C, 'partials', '%s.%s.html' % (name, lang)))


def lang_path(lang, rest):
    """rest is '/' or '/medical/' -> language specific path."""
    return (PREFIX[lang] + rest) if rest != '/' else (PREFIX[lang] + '/' if lang != 'en' else '/')


def lang_switch(lang, alternates):
    links = []
    for l in LANGS:
        href = alternates.get(l) or lang_path(l, '/')
        cls = ' class="on"' if l == lang else ''
        links.append('<a href="%s" hreflang="%s" lang="%s"%s>%s</a>' % (href, l, l, cls, esc(I18N[l]['short'])))
    return '<nav class="gt-lang" aria-label="Language">%s</nav>' % ''.join(links)


WA_SVG = ('<svg width="30" height="30" viewBox="0 0 24 24" fill="#fff" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.3 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.6-4-4.7-4.2-.1-.2-1.1-1.5-1.1-2.9s.7-2.1 1-2.4c.3-.3.6-.3.8-.3h.6c.2 0 .4 0 .6.5l.9 2.1c.1.2.1.4 0 .6l-.4.6-.4.4c-.1.1-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.3 2.4 1.5.3.1.5.1.6-.1l.9-1.1c.2-.3.4-.2.7-.1l2 1c.3.1.5.2.5.3.1.2.1.7-.1 1.3z"/></svg>')

ORG = {
    "@type": "TravelAgency",
    "@id": SITE_URL + "/#org",
    "name": "guidetothai",
    "legalName": SITE['company'],
    "url": SITE_URL + "/",
    "logo": SITE_URL + "/assets/img/logo.webp",
    "image": SITE_URL + "/assets/img/logo.webp",
    "telephone": "+" + str(SITE['whatsapp']),
    "foundingDate": str(SITE['founded']),
    "areaServed": "TH",
    "address": {"@type": "PostalAddress", "addressCountry": "TH"},
    "knowsLanguage": ["ar", "en", "th"],
    "sameAs": ["https://instagram.com/" + SITE['instagram'], "https://www.tiktok.com/@" + SITE['tiktok']],
}


def layout(lang, path, title, description, body, alternates, image=None, jsonld=None, og_type='website'):
    t = I18N[lang]
    canonical = abs_url(path)
    alt_links = ''.join('<link rel="alternate" hreflang="%s" href="%s">' % (HREFLANG[l], esc(abs_url(p)))
                        for l, p in alternates.items())
    if 'en' in alternates:
        alt_links += '<link rel="alternate" hreflang="x-default" href="%s">' % esc(abs_url(alternates['en']))
    og_img = abs_url(img(image)) if image else SITE_URL + '/assets/img/logo.webp'
    ld = [ORG] + (jsonld or [])
    ld_html = '<script type="application/ld+json">%s</script>' % json.dumps(
        {"@context": "https://schema.org", "@graph": ld}, ensure_ascii=False)
    fonts = ('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800'
             + ('&family=Noto+Sans+Thai:wght@400;500;700;800' if lang == 'th' else '') + '&display=swap')
    doc = f'''<!doctype html>
<html lang="{t['html_lang']}" dir="{t['dir']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
{alt_links}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="guidetothai">
<meta property="og:locale" content="{t['locale']}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_img)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#16246b">
<link rel="icon" type="image/png" href="/assets/img/favicon.png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{fonts}">
<link rel="stylesheet" href="/assets/css/site.css">
{ld_html}
</head>
<body>
<a class="gt-skip" href="#main">{'تخطَّ إلى المحتوى' if lang == 'ar' else ('ข้ามไปยังเนื้อหา' if lang == 'th' else 'Skip to content')}</a>
{partial('nav', lang)}
<main id="main">
{body}
</main>
{partial('footer', lang)}
<a class="gt-wa" href="{WA}" target="_blank" rel="noopener" aria-label="WhatsApp">{WA_SVG}</a>
{lang_switch(lang, alternates)}
<script src="/assets/js/site.js" defer></script>
</body>
</html>
'''
    return doc


def finalize(doc):
    """Apply base_path to root-relative links when the site lives in a sub-folder."""
    if BASE:
        doc = re.sub(r'(href|src|action)="/(?!/)', r'\1="%s/' % BASE, doc)
        doc = doc.replace('url(/', 'url(%s/' % BASE)
    return doc


def write(path, doc):
    full = os.path.join(OUT, path.lstrip('/'))
    if path.endswith('/'):
        full = os.path.join(full, 'index.html')
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(finalize(doc))


SITEMAP = []  # (path, alternates, lastmod)


# ---------------------------------------------------------------- pages
def build_pages():
    slugs = sorted(os.listdir(os.path.join(C, 'pages', 'en')))
    for f in slugs:
        slug = f[:-5]
        rest = '/' if slug == 'index' else '/%s/' % slug
        alternates = {l: lang_path(l, rest) for l in LANGS if os.path.exists(os.path.join(C, 'pages', l, f))}
        for lang in alternates:
            meta, body = split_front(read(os.path.join(C, 'pages', lang, f)))
            body = body.replace('<!--cta-->', partial('cta', lang))
            jsonld = []
            if slug != 'index':
                jsonld.append(breadcrumbs(lang, [(I18N[lang]['home'], lang_path(lang, '/')), (meta.get('title', '').split('|')[0].strip(), alternates[lang])]))
            else:
                jsonld.append({"@type": "WebSite", "name": "guidetothai", "url": abs_url(lang_path(lang, '/')), "inLanguage": lang})
            write(alternates[lang], layout(lang, alternates[lang], meta.get('title', 'guidetothai'), meta.get('description', ''),
                                           body, alternates, image=meta.get('image'), jsonld=jsonld))
        SITEMAP.append((alternates, TODAY))


def breadcrumbs(lang, items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(p)} for i, (n, p) in enumerate(items)]}


# ---------------------------------------------------------------- our work
def build_work():
    rest = '/our-work/'
    alternates = {l: lang_path(l, rest) for l in LANGS}
    cat_name = {f['key']: f for f in WORK['filters']}
    for lang in LANGS:
        t = WORK['text'][lang]
        stats = ''.join('<div class="gt-stat"><div class="gt-stat-n">%s</div><div class="gt-stat-t">%s</div></div>' % (esc(s['n']), esc(s['t'])) for s in t['stats'])
        filters = '<button class="gt-filter on" data-f="all" aria-pressed="true">%s</button>' % esc(I18N[lang]['all'])
        filters += ''.join('<button class="gt-filter" data-f="%s" aria-pressed="false">%s</button>' % (f['key'], esc(f[lang])) for f in WORK['filters'])
        tiles = ''
        for it in WORK['items']:
            tx = it[lang]
            tiles += ('<figure class="gt-tile %s" data-cat="%s"><img src="%s" alt="%s" loading="lazy" decoding="async">'
                      '<figcaption><span class="gt-tile-cat">%s</span><h3 class="gt-tile-h">%s</h3><p class="gt-tile-p">%s</p></figcaption></figure>'
                      ) % (it.get('size', ''), it['cat'], esc(img(it['image'])), esc(tx['title']), esc(cat_name[it['cat']][lang]), esc(tx['title']), esc(tx['text']))
        ig = 'https://instagram.com/' + SITE['instagram']
        tt = 'https://www.tiktok.com/@' + SITE['tiktok']
        body = f'''<section class="gt-ph gt-ph-work" style="--hero:url('{esc(img("bangkok-night"))}')"><div class="gt-ph-inner"><div class="gt-pill">{esc(t['pill'])}</div><h1 class="gt-ph-h">{esc(t['h1'])}</h1><p class="gt-ph-p">{esc(t['lead'])}</p></div></section>
<div class="gt-wrap"><div class="gt-stats">{stats}</div></div>
<section class="gt-sec"><div class="gt-wrap"><div class="gt-head"><div class="gt-eyebrow">{esc(t['gallery_eyebrow'])}</div><h2 class="gt-h2">{esc(t['gallery_h'])}</h2></div>
<div class="gt-filters" role="group">{filters}</div>
<div class="gt-gallery">{tiles}</div></div></section>
<section class="gt-sec gt-sec-soft"><div class="gt-wrap" style="text-align:center"><div class="gt-head"><div class="gt-eyebrow">@{esc(SITE['instagram'])}</div><h2 class="gt-h2">{esc(t['follow_h'])}</h2><p class="gt-sub">{esc(t['follow_p'])}</p></div>
<div class="gt-follow"><a class="gt-social ig" href="{ig}" target="_blank" rel="noopener">Instagram @{esc(SITE['instagram'])}</a><a class="gt-social tt" href="{tt}" target="_blank" rel="noopener">TikTok @{esc(SITE['tiktok'])}</a></div></div></section>
{partial('cta', lang)}'''
        jsonld = [breadcrumbs(lang, [(I18N[lang]['home'], lang_path(lang, '/')), (t['pill'], alternates[lang])])]
        write(alternates[lang], layout(lang, alternates[lang], t['title'], t['description'], body, alternates,
                                       image='bangkok-night', jsonld=jsonld))
    SITEMAP.append((alternates, TODAY))


# ---------------------------------------------------------------- blog
def load_posts():
    posts = []
    d = os.path.join(C, 'posts')
    for f in sorted(os.listdir(d)):
        m = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)\.(en|ar|th)\.md$', f)
        if not m:
            continue
        meta, md = split_front(read(os.path.join(d, f)))
        if meta.get('draft'):
            continue
        date = str(meta.get('date', m.group(1)))[:10]
        slug, lang = m.group(2), m.group(3)
        conv = markdown.Markdown(extensions=['extra', 'sane_lists', 'toc'])
        body = conv.convert(md)
        body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
        text = re.sub(r'<[^>]+>', ' ', body)
        if lang == 'th':
            minutes = max(1, math.ceil(len(re.sub(r'\s', '', text)) / 900))
        else:
            minutes = max(1, math.ceil(len(text.split()) / 200))
        posts.append(dict(meta, slug=slug, lang=lang, date=date, html=body, minutes=minutes,
                          path=lang_path(lang, '/blog/%s/' % slug)))
    posts.sort(key=lambda p: (p['date'], p.get('order', 0)), reverse=True)
    return posts


def fmt_date(d, lang):
    y, m, dd = [int(x) for x in d.split('-')]
    months = {
        'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        'ar': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
        'th': ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน', 'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'],
    }[lang]
    if lang == 'en':
        return '%d %s %d' % (dd, months[m - 1], y)
    if lang == 'th':
        return '%d %s %d' % (dd, months[m - 1], y + 543)
    return '%d %s %d' % (dd, months[m - 1], y)


def card(p, lang, feat=False):
    t = I18N[lang]
    cat = p.get('category', 'travel')
    return ('<a class="gt-post-card%s" href="%s" data-cat="%s"><img src="%s" alt="" loading="lazy" decoding="async">'
            '<div class="gt-post-b"><div class="gt-post-meta"><span class="gt-cat %s">%s</span><span>%s</span></div>'
            '<h3 class="gt-post-h">%s</h3><p class="gt-post-p">%s</p><span class="gt-post-more">%s</span></div></a>'
            ) % (' feat' if feat else '', p['path'], cat, esc(img(p.get('image'))), cat, esc(t['categories'].get(cat, cat)),
                 esc(fmt_date(p['date'], lang)), esc(p['title']), esc(p.get('description', '')), esc(t['read_more']))


def build_blog():
    posts = load_posts()
    by_slug = {}
    for p in posts:
        by_slug.setdefault(p['slug'], {})[p['lang']] = p
    rest = '/blog/'
    alternates = {l: lang_path(l, rest) for l in LANGS}
    for lang in LANGS:
        t = I18N[lang]
        mine = [p for p in posts if p['lang'] == lang]
        cats = []
        for p in mine:
            if p.get('category') not in cats:
                cats.append(p.get('category'))
        filt = '<div class="gt-filters"><button class="gt-filter gt-bfilter on" data-f="all">%s</button>%s</div>' % (
            esc(t['all']), ''.join('<button class="gt-filter gt-bfilter" data-f="%s">%s</button>' % (c, esc(t['categories'].get(c, c))) for c in cats))
        cards = ''.join(card(p, lang, feat=(i == 0)) for i, p in enumerate(mine))
        body = f'''<section class="gt-ph gt-ph-blog" style="--hero:url('{esc(img("bangkok-night"))}')"><div class="gt-ph-inner"><div class="gt-pill">{esc(t['blog_pill'])}</div><h1 class="gt-ph-h">{esc(t['blog_title'])}</h1><p class="gt-ph-p">{esc(t['blog_lead'])}</p></div></section>
<section class="gt-sec"><div class="gt-wrap">{filt}<div class="gt-posts">{cards}</div></div></section>
{partial('cta', lang)}'''
        jsonld = [{"@type": "Blog", "name": t['blog_title'], "url": abs_url(alternates[lang]), "inLanguage": lang,
                   "blogPost": [{"@type": "BlogPosting", "headline": p['title'], "url": abs_url(p['path']), "datePublished": p['date']} for p in mine]}]
        write(alternates[lang], layout(lang, alternates[lang], '%s | guidetothai' % t['blog_title'], t['blog_lead'], body,
                                       alternates, image='bangkok-night', jsonld=jsonld))
    SITEMAP.append((alternates, posts[0]['date'] if posts else TODAY))

    for slug, versions in by_slug.items():
        alternates = {l: versions[l]['path'] for l in LANGS if l in versions}
        for lang, p in versions.items():
            t = I18N[lang]
            cat = p.get('category', 'travel')
            sources = ''
            if p.get('sources'):
                sources = '<div class="gt-sources"><h4>%s</h4><ol>%s</ol></div>' % (esc(t['sources']), ''.join(
                    '<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (esc(s['url']), esc(s['title'])) for s in p['sources']))
            related = [q for q in posts if q['lang'] == lang and q['slug'] != slug][:3]
            rel_html = ''
            if related:
                rel_html = '<section class="gt-sec gt-sec-soft"><div class="gt-wrap"><div class="gt-head"><h2 class="gt-h2">%s</h2></div><div class="gt-posts">%s</div></div></section>' % (
                    esc(t['related']), ''.join(card(q, lang) for q in related))
            body = f'''<article>
<section class="gt-ph gt-art-hero" style="background-image:linear-gradient(180deg,rgba(10,18,60,.35),rgba(8,14,48,.92)),url('{esc(img(p.get('image')))}')"><div class="gt-ph-inner">
<div class="gt-crumbs"><a href="{lang_path(lang, '/')}">{esc(t['home'])}</a> / <a href="{lang_path(lang, '/blog/')}">{esc(t['blog_pill'])}</a></div>
<h1 class="gt-ph-h">{esc(p['title'])}</h1>
<div class="gt-art-meta"><span class="gt-cat">{esc(t['categories'].get(cat, cat))}</span><time datetime="{p['date']}">{esc(fmt_date(p['date'], lang))}</time><span>· {p['minutes']} {esc(t['min_read'])}</span></div>
</div></section>
<div class="gt-article">{p['html']}</div>
<div class="gt-art-box">{sources}<p class="gt-disclaimer">{esc(t['disclaimer'])}</p></div>
<div class="gt-art-box"><div class="gt-help"><div><h4>{esc(t['need_help'])}</h4><p>{esc(t['need_help_p'])}</p></div><a class="gt-btn" href="{WA}" target="_blank" rel="noopener">{esc(t['wa_btn'])}</a></div>
<p style="margin-top:24px"><a class="gt-back" href="{lang_path(lang, '/blog/')}">{esc(t['back_to_blog'])}</a></p></div>
</article>
{rel_html}'''
            jsonld = [{
                "@type": "BlogPosting", "headline": p['title'], "description": p.get('description', ''),
                "image": abs_url(img(p.get('image'))), "datePublished": p['date'], "dateModified": str(p.get('updated', p['date'])),
                "inLanguage": lang, "mainEntityOfPage": abs_url(p['path']),
                "author": {"@type": "Organization", "name": "guidetothai", "url": SITE_URL + "/"},
                "publisher": {"@id": SITE_URL + "/#org"},
            }, breadcrumbs(lang, [(t['home'], lang_path(lang, '/')), (t['blog_pill'], lang_path(lang, '/blog/')), (p['title'], p['path'])])]
            write(p['path'], layout(lang, p['path'], '%s | guidetothai' % p['title'], p.get('description', ''), body,
                                    alternates, image=p.get('image'), jsonld=jsonld, og_type='article'))
        SITEMAP.append((alternates, max(str(v.get('updated', v['date'])) for v in versions.values())))


# ---------------------------------------------------------------- extras
def build_extras():
    for lang in LANGS:
        t = I18N[lang]
        body = '<section class="gt-404"><div><h1>404</h1><h2 class="gt-h2">%s</h2><p class="gt-sub">%s</p><p><a class="gt-btn" href="%s">%s</a></p></div></section>' % (
            esc(t['not_found_title']), esc(t['not_found_p']), lang_path(lang, '/'), esc(t['not_found_btn']))
        doc = layout(lang, lang_path(lang, '/404.html') if lang != 'en' else '/404.html', t['not_found_title'], t['not_found_p'], body,
                     {l: lang_path(l, '/') for l in LANGS})
        doc = doc.replace('<head>', '<head>\n<meta name="robots" content="noindex">', 1)
        write('/404.html' if lang == 'en' else PREFIX[lang] + '/404.html', doc)
    # sitemap with language alternates
    urls = []
    for alternates, lastmod in SITEMAP:
        alts = ''.join('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (l, esc(abs_url(p))) for l, p in alternates.items())
        for l, p in alternates.items():
            urls.append('<url><loc>%s</loc><lastmod>%s</lastmod>%s</url>' % (esc(abs_url(p)), lastmod, alts))
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n%s\n</urlset>\n') % '\n'.join(urls)
    open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write(sm)
    open(os.path.join(OUT, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % (SITE_URL + BASE))
    open(os.path.join(OUT, '.nojekyll'), 'w').write('')
    if SITE.get('custom_domain'):
        open(os.path.join(OUT, 'CNAME'), 'w').write(SITE['custom_domain'].strip() + '\n')


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(ROOT, 'assets'), os.path.join(OUT, 'assets'))
    if BASE:
        css = os.path.join(OUT, 'assets', 'css', 'site.css')
        open(css, 'w').write(open(css).read().replace('url(/', 'url(%s/' % BASE))
    build_pages()
    build_work()
    build_blog()
    build_extras()
    n = sum(len(f) for _, _, f in os.walk(OUT))
    print('Built %d files into _site/' % n)
    if '--serve' in sys.argv:
        import http.server
        import functools
        os.chdir(OUT)
        print('Serving on http://localhost:8000')
        http.server.ThreadingHTTPServer(('', 8000), functools.partial(http.server.SimpleHTTPRequestHandler, directory=OUT)).serve_forever()


if __name__ == '__main__':
    main()
