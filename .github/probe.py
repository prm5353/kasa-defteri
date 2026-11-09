import re, urllib.request, json
H={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1","Accept":"text/html,application/json,*/*","Accept-Language":"tr-TR,tr"}
def get(u,extra=None):
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers={**H,**(extra or {})}),timeout=25);return r.status,r.read().decode('utf-8','replace'),dict(r.headers)
    except Exception as e: return getattr(e,'code',0),str(e)[:200],{}
pages=["https://www.fibabanka.com.tr/doviz-kurlari","https://www.fibabanka.com.tr/yatirim/fx-market","https://www.fibabanka.com.tr/faiz-ucret-ve-komisyonlar/doviz-kurlari","https://www.fibabanka.com.tr/","https://www.fibabanka.com.tr/mevduat/kiymetli-maden/gumus-hesabi"]
for u in pages:
    s,t,h=get(u);print("PAGE",u,s,len(t))
    for m in sorted(set(re.findall(r'.{0,80}(?:XAG|[Gg]ümüş|GUMUS|silver).{0,120}',t)))[:8]: print("  HIT",m.replace('\n',' ')[:220])
    for m in sorted(set(re.findall(r'["\']((?:https?://[^"\']+)?/[^"\']*(?:api|kur|rate|currency|doviz|Doviz|Kur|exchange)[^"\']*)["\']',t)))[:25]: print("  URL",m[:200])
