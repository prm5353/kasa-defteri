# Fibabanka kurlarını (bankanın alış ve satış fiyatı) çekip gumus.json yazar: gram altın (XAU), gram gümüş (XAG), dolar, euro.
# Fibabanka başka sitelerin tarayıcıdan okumasına izin vermediği için bu iş GitHub'da çalışır; uygulama dosyayı okur.
# Kasım 2026'da eski ListFXPrice adresi kalktı; sitenin çevirici servisi kullanılıyor (X→TRY = banka alış, TRY→X = banka satış).
import json, urllib.request, datetime
URL = "https://www.fibabanka.com.tr/api/services/currency-convert"
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Content-Type": "application/json",
     "Origin": "https://www.fibabanka.com.tr", "Referer": "https://www.fibabanka.com.tr/yatirim/fx-market"}
def rate(src, dst):
    body = json.dumps({"amount": "1", "currency": src, "targetCurrency": dst}).encode()
    r = urllib.request.urlopen(urllib.request.Request(URL, data=body, headers=H, method="POST"), timeout=30)
    v = json.loads(r.read().decode("utf-8"))["data"]["tryrate"][0]["rate"]
    if not v or v <= 0: raise ValueError(f"{src}->{dst} boş")
    return round(float(v), 4)
now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
codes = {"gram": "XAU", "gumus": "XAG", "usd": "USD", "eur": "EUR"}
fiba = {k: {"alis": rate(c, "TRY"), "satis": rate("TRY", c)} for k, c in codes.items()}
out = {"source": "Fibabanka · alış", "alis": fiba["gumus"]["alis"], "satis": fiba["gumus"]["satis"],
       "fiba": fiba, "updated": now, "at": now}
json.dump(out, open("gumus.json", "w"), ensure_ascii=False)
print(out)
