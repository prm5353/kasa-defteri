# Fibabanka FX Market gram gümüş (XAG/TRY) kurunu çekip gumus.json yazar.
# Fibabanka başka sitelerin tarayıcıdan okumasına izin vermediği için bu iş GitHub'da çalışır; uygulama dosyayı okur.
import json, urllib.request, datetime
r = urllib.request.urlopen(urllib.request.Request("https://www.fibabanka.com.tr/servisler/ListFXPrice",
    headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}), timeout=30)
rows = json.loads(r.read().decode("utf-8"))["TABLE"]
x = next(t for t in rows if t.get("EXCHANGETYPESYMBOL") == "XAG/TRY")
out = {"source": "Fibabanka FX Market · alış", "alis": x["BID"], "satis": x["ASK"],
       "updated": datetime.datetime.fromtimestamp(x["LASTUPDATED"] / 1000, datetime.timezone.utc).isoformat(timespec="seconds"),
       "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
json.dump(out, open("gumus.json", "w"), ensure_ascii=False)
print(out)
