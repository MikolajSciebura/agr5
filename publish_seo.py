#!/usr/bin/env python3
"""Konfiguracja domeny przed publikacją: python publish_seo.py https://twoja-domena.pl
Działa bez instalowania pakietów. Można uruchamiać ponownie, także dla innej domeny.
"""
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
import json,re,sys
from html import escape
if len(sys.argv)!=2:
 raise SystemExit("Użycie: python publish_seo.py https://twoja-domena.pl")
base=sys.argv[1].strip().rstrip('/')
u=urlparse(base)
if u.scheme != 'https' or not u.hostname or u.path or u.query or u.fragment or u.username or u.password or 'twoja-domena' in u.netloc or 'example' in u.netloc:
 raise SystemExit('Podaj prawdziwy adres domeny HTTPS, bez ścieżki.')
root=Path(__file__).resolve().parent
pages=['index.html','noclegi-klobuck.html','noclegi-czestochowa.html','noclegi-pracownicze-kamyk.html','noclegi-dla-pielgrzymow.html']
old_base=None
for filename in pages:
 p=root/filename
 html=p.read_text(encoding='utf-8')
 # Replace only our explicit placeholder; external links remain unchanged.
 html=html.replace('SITE_ORIGIN',base)
 url=base+('/' if filename=='index.html' else '/'+filename)
 html=re.sub(r'<link\b(?=[^>]*\brel=["\']canonical["\'])[^>]*>', '',html, flags=re.I)
 html=re.sub(r'<meta\b(?=[^>]*\bproperty=["\'](?:og:url|og:image|og:image:alt)["\'])[^>]*>', '',html, flags=re.I)
 # Update JSON-LD URLs via JSON parsing, including domain changes on repeat runs.
 def fix_schema(m):
  data=json.loads(m.group(1))
  def transform(v):
   if isinstance(v,dict):
    return {k:transform_uri(k,x) if k in ('@id','url','image','item') else transform(x) for k,x in v.items()}
   if isinstance(v,list):return [transform(x) for x in v]
   return v
  def transform_uri(k,v):
   if isinstance(v,str) and (v.startswith('SITE_ORIGIN') or v.startswith('http://') or v.startswith('https://')):
    if v.startswith('SITE_ORIGIN'):
     return base+v[len('SITE_ORIGIN'):]
    if k=='item' or k in ('@id','url','image'):
     # Only site-owned fields on our schema objects; external maps url not rewritten.
     if 'google.com' in v or 'schema.org' in v:return v
     path=urlparse(v).path
     frag=('#'+urlparse(v).fragment) if urlparse(v).fragment else ''
     return base+path+frag
   return transform(v)
  return '<script type="application/ld+json">'+json.dumps(transform(data),ensure_ascii=False,separators=(',',':'))+'</script>'
 html=re.sub(r'<script type="application/ld\+json">(.*?)</script>',fix_schema,html,flags=re.S)
 og=(f'<link rel="canonical" href="{escape(url,quote=True)}"/>'
     f'<meta property="og:url" content="{escape(url,quote=True)}"/>'
     f'<meta property="og:image" content="{escape(base+"/assets/img/front-ogrod-v58.webp",quote=True)}"/>'
     '<meta property="og:image:alt" content="Budynek Pokoi Gościnnych w Kamyku – widok od frontu"/>')
 html=html.replace('</head>',og+'</head>',1)
 p.write_text(html,encoding='utf-8')
ns='http://www.sitemaps.org/schemas/sitemap/0.9'
ET.register_namespace('',ns)
rootnode=ET.Element('{%s}urlset'%ns)
for filename in pages:
 item=ET.SubElement(rootnode,'{%s}url'%ns)
 ET.SubElement(item,'{%s}loc'%ns).text=base+('/' if filename=='index.html' else '/'+filename)
ET.ElementTree(rootnode).write(root/'sitemap.xml',encoding='utf-8',xml_declaration=True)
(root/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+base+'/sitemap.xml\n',encoding='utf-8')
print('Gotowe: canonical, Open Graph, JSON-LD, sitemap.xml, robots.txt dla',base)
