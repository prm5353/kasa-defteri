import re, urllib.request
H={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1","Accept":"text/html,application/json,*/*","Accept-Language":"tr-TR,tr"}
def get(u,extra=None,data=None):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,data=data,headers={**H,**(extra or {})}),timeout=25);return r.status,r.read().decode('utf-8','replace'),dict(r.headers)
    except Exception as e: return getattr(e,'code',0),str(e)[:200],{}
s,t,h=get("https://www.fibabanka.com.tr/piyasa-verileri/doviz");print("PAGE",s,len(t))
for m in sorted(set(re.findall(r'.{0,150}(?:XAG|Gümüş|GUMUS).{0,250}',t)))[:12]: print("  HIT",m.replace('\n',' ')[:400])
for m in sorted(set(re.findall(r'(?:url|fetch|ajax|action|data-url|src)\s*[:=(]\s*["\']([^"\']+)["\']',t)))[:40]: print("  REF",m[:200])
js=sorted(set(re.findall(r'src=["\']([^"\']+\.js[^"\']*)',t)))
print("JS",js[:40])
for u in js:
    if u.startswith('/'): u='https://www.fibabanka.com.tr'+u
    if 'fibabanka' not in u: continue
    s2,t2,_=get(u)
    for m in sorted(set(re.findall(r'.{0,100}(?:/api/|ajax|Exchange|exchange|Currency|currency|Kur|XAG).{0,140}',t2)))[:10]: print("  JS",u.split('/')[-1][:40],"|",m.replace('\n',' ')[:240])
