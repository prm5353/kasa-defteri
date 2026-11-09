import re, urllib.request
H={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1","Accept":"*/*","Accept-Language":"tr-TR,tr"}
def get(u,extra=None):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={**H,**(extra or {})}),timeout=25);return r.status,r.read().decode('utf-8','replace'),dict(r.headers)
    except Exception as e: return getattr(e,'code',0),str(e)[:200],{}
s,t,h=get("https://www.fibabanka.com.tr/ResourcePackages/Fibabanka/assets/js/piyasa-verileri.js")
for m in re.findall(r'.{0,200}api\.ashx[^"\']*.{0,40}',t): print("API",m.replace('\n',' ')[:300])
for m in re.findall(r'\$\("#(\w+Table)"\)',t): pass
print("TABLES",sorted(set(re.findall(r'#(\w+Table)',t))))
i=t.find('XAG/TRY');print("CTX",t[max(0,i-1500):i+600].replace('\n',' ')[:2200])
s,p,h=get("https://www.fibabanka.com.tr/piyasa-verileri/doviz")
for m in re.findall(r'<h\d[^>]*>[^<]{2,80}</h\d>|id="\w+Table"',p)[:40]: print("H",m)
