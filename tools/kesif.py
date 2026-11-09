# Harem sitesinin fiyatları nereden yüklediğini bulmak için tek seferlik inceleme.
import re, urllib.request
H={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1","Accept":"text/html,*/*"}
def get(u):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30);return r.status,r.read().decode('utf-8','replace')
    except Exception as e: return getattr(e,'code',0),str(e)
st,html=get("https://www.haremaltin.com/")
print("HOME",st,len(html))
for m in sorted(set(re.findall(r'["\'](/[^"\']*(?:ajax|api|doviz|fiyat|socket)[^"\']*)["\']',html,re.I)))[:40]: print("PATH",m)
for m in sorted(set(re.findall(r'(wss?://[^"\'\s]+|https?://[^"\'\s]*(?:api|socket|canli|doviz)[^"\'\s]*)',html,re.I)))[:40]: print("URL",m)
js=sorted(set(re.findall(r'src=["\']([^"\']+\.js[^"\']*)',html)))
print("JS",js[:30])
for u in js[:25]:
    if u.startswith('//'): u='https:'+u
    elif u.startswith('/'): u='https://www.haremaltin.com'+u
    if 'haremaltin' not in u: continue
    s,t=get(u)
    hits=set(re.findall(r'.{0,60}(?:ajax/|/api/|socket|wss://|doviz).{0,80}',t))
    for h in list(hits)[:12]: print("JSHIT",u.split('/')[-1][:40],"|",h.replace('\n',' ')[:160])
for p in ["/dashboard/ajax/doviz","/ajax/all_prices","/api/prices","/ajax/doviz"]:
    for meth in ("GET","POST"):
        try:
            req=urllib.request.Request("https://www.haremaltin.com"+p,data=(b"dil_kodu=tr" if meth=="POST" else None),headers={**H,"X-Requested-With":"XMLHttpRequest","Referer":"https://www.haremaltin.com/","Content-Type":"application/x-www-form-urlencoded"},method=meth)
            r=urllib.request.urlopen(req,timeout=20);b=r.read()[:300];print("TRY",meth,p,r.status,b)
        except Exception as e: print("TRY",meth,p,getattr(e,'code',e))
