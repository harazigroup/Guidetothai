#!/usr/bin/env python3
"""Optional: copy the site photos from the old Webflow CDN into assets/img/
and point site.yml at the local copies. Run on your own computer:
    python3 tools/download-images.py
"""
import os, re, urllib.request, yaml
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg_path = os.path.join(ROOT, 'site.yml')
cfg = yaml.safe_load(open(cfg_path, encoding='utf-8'))
text = open(cfg_path, encoding='utf-8').read()
css_path = os.path.join(ROOT, 'assets', 'css', 'site.css')
css = open(css_path, encoding='utf-8').read()
os.makedirs(os.path.join(ROOT, 'assets', 'img', 'photos'), exist_ok=True)
for key, url in cfg['images'].items():
    if not url.startswith('http'):
        continue
    local = '/assets/img/photos/%s.jpg' % key
    print('downloading', key)
    urllib.request.urlretrieve(url, os.path.join(ROOT, local.lstrip('/')))
    text = text.replace(url, local)
    css = css.replace(url, local)
open(cfg_path, 'w', encoding='utf-8').write(text)
open(css_path, 'w', encoding='utf-8').write(css)
print('done - commit the new files in assets/img/photos')
