import urllib.request, json
H={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1","Accept":"application/json,*/*","Origin":"https://prm5353.github.io"}
for u in ["https://www.fibabanka.com.tr/servisler/ListFXPrice","https://www.fibabanka.com.tr/piyasalar/api.ashx?name=Altin/get/XAUXAG-XAGEURGR-XAGUSDKG-XAGTRY-XAGGR-SXAGGR-XAGEUR-XAGUSD-XAGUSDGR"]:
    try:
        r=urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=25);b=r.read().decode('utf-8','replace')
        print("URL",u,r.status,"ACAO=",r.headers.get('Access-Control-Allow-Origin'),"CT=",r.headers.get('Content-Type'))
        print("BODY",b[:2500])
    except Exception as e: print("URL",u,"ERR",getattr(e,'code',e))
