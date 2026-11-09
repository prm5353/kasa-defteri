# Harem Altın fiyatlarını çekip prices.json yazar (GitHub Actions'ta çalışır).
# Uygulama bu dosyayı okur; tarayıcı Harem'e doğrudan erişemediği için ara adımdır.
import json, sys, urllib.request, urllib.parse, datetime

URL = "https://www.haremaltin.com/dashboard/ajax/doviz"
HDR = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.haremaltin.com/",
    "Origin": "https://www.haremaltin.com",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}

def num(v):
    if v is None: return None
    s = str(v).strip()
    if not s: return None
    if "," in s and "." in s: s = s.replace(".", "").replace(",", ".")
    elif "," in s: s = s.replace(",", ".")
    try: return float(s)
    except ValueError: return None

req = urllib.request.Request(URL, data=urllib.parse.urlencode({"dil_kodu": "tr"}).encode(), headers=HDR, method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    body = json.loads(r.read().decode("utf-8"))
d = body.get("data", body)

def alis(*codes):
    for c in codes:
        x = d.get(c)
        if isinstance(x, dict):
            v = num(x.get("alis"))
            if v: return v, c
    return None, None

out = {"source": "Harem Altın · alış", "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
for key, codes in {"gram": ("KULCEALTIN", "ALTIN"), "ceyrek": ("CEYREK_YENI", "CEYREK_ESKI"), "usd": ("USDTRY",), "eur": ("EURTRY",)}.items():
    v, c = alis(*codes)
    if v: out[key] = v; out[key + "_kod"] = c
missing = [k for k in ("gram", "ceyrek", "usd", "eur") if k not in out]
if len(missing) == 4:
    print("Fiyat bulunamadı. Gelen kodlar:", list(d.keys())[:60]); sys.exit(1)
out["codes"] = sorted(d.keys())
json.dump(out, open("prices.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:600])
