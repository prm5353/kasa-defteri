"""Kasa Defteri otomatik testleri.

Çalıştırma (depo kökünde):  python3 tests/test_app.py
Gerekenler: Python Playwright + Chromium (pip install playwright && playwright install chromium)

Uygulamayı yerel bir sunucudan açar, tarihi 10 Kasım 2026 12:00'ye sabitler,
örnek bir yedek yükler ve kart/kişi hesaplarının, yedek-geri yükleme akışının,
silip geri almanın beklendiği gibi çalıştığını denetler. Kişisel veri kullanılmaz.
"""
import json, os, sys, threading, http.server, functools, socketserver
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOW = datetime(2026, 11, 10, 12, 0, tzinfo=timezone(timedelta(hours=3)))

SAMPLE = {
    "exportedAt": "2026-11-09T20:00:00.000Z",
    "cards": [{"id": "c1", "name": "Test Kart", "limit": 100000, "cutDay": 20, "dueDay": 30, "ts": 1}],
    "accounts": [{"id": "a1", "name": "Banka", "balance": 50000, "balanceAt": 1, "ts": 1}],
    "persons": [{"id": "p1", "name": "Deneme Kişi", "opening": 0, "since": "2026-11-01", "ts": 1}],
    "months": {"m-2026-11": {
        "t1": {"type": "gider", "amount": 1000, "date": "2026-11-05", "cardId": "c1", "personId": "me", "category": "Market", "sub": "", "merchant": "Market A", "ts": 1},
        "t2": {"type": "gider", "amount": 600, "date": "2026-11-06", "cardId": "c1", "personId": "p1", "category": "", "sub": "", "merchant": "Mağaza B", "ts": 2},
        "t3": {"type": "gider", "amount": 3000, "inst": 3, "date": "2026-11-07", "cardId": "c1", "personId": "me", "category": "Alışveriş", "sub": "Elektronik", "merchant": "Teknoloji C", "ts": 3},
        "t4": {"type": "tahsilat", "amount": 200, "date": "2026-11-08", "account": "Banka", "personId": "p1", "merchant": "Ödeme aldım", "ts": 4},
    }},
    "meta": {"start": "2026-11-01"},
    "catplan": {"months": {"2026-12": {"Market": 1234}}},
    "networth": {"hist": {"2026-10": 40000}, "day": "2026-11-01"},
}

fails = []
def check(name, cond, detail=""):
    print(("  ✓ " if cond else "  ✗ ") + name + ("" if cond else f"  → {detail}"))
    if not cond: fails.append(name)

def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    h.log_message = lambda *a: None
    s = socketserver.TCPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s

def main():
    srv = serve(); url = f"http://127.0.0.1:{srv.server_address[1]}/index.html"
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, timezone_id="Europe/Istanbul", service_workers="block")
        page = ctx.new_page()
        errors, csp = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: csp.append(m.text) if "Content Security Policy" in m.text else None)
        page.clock.install(time=NOW)
        page.goto(url); page.wait_for_function("S.loaded", timeout=10000)

        print("Yedek yükleme")
        page.evaluate("j=>restoreFrom(new File([JSON.stringify(j)],'y.json'))", SAMPLE)
        page.wait_for_timeout(300)
        check("önce özet ekranı açılır, veri değişmez", page.evaluate("S.tx.length") == 0 and page.locator("[data-act=restoreok]").count() == 1)
        page.click("[data-act=restoreok]"); page.wait_for_timeout(500)
        check("onaydan sonra işlemler yüklenir", page.evaluate("S.tx.length") == 4, page.evaluate("S.tx.length"))
        check("kategori planı yüklenir", page.evaluate("S.catplan?.months?.['2026-12']?.Market") == 1234)
        check("net varlık geçmişi yüklenir", page.evaluate("S.nw?.hist?.['2026-10']") == 40000)

        print("Kart ve kişi hesapları")
        st = page.evaluate("(()=>{const s=cardState(cardById('c1'));return {cut:s.open.cut,due:s.open.due,total:s.open.total,debt:s.debt}})()")
        check("açık dönem kesimi 20 Kasım", st["cut"] == "2026-11-20", st)
        check("açık dönem son ödeme 30 Kasım", st["due"] == "2026-11-30", st)
        check("açık dönem toplamı 1000 + 600 + 1000 (1. taksit) = 2600", abs(st["total"] - 2600) < 0.01, st)
        check("toplam kart borcu taksitler dahil 4600", abs(st["debt"] - 4600) < 0.01, st)
        owed = page.evaluate("owedByDue().filter(o=>o.pid==='p1').reduce((a,o)=>a+o.left,0)")
        check("kişinin kalan payı 600 − 200 = 400", abs(owed - 400) < 0.01, owed)
        check("taksit tutarı kuruşa yuvarlanır", page.evaluate("r2(333.33*3)") == 999.99)

        print("Ekranlar")
        for t in ["ana", "kart", "harcama", "fis", "arsiv"]:
            page.evaluate(f"goTab('{t}')"); page.wait_for_timeout(150)
        page.evaluate("settingsSheet()"); page.wait_for_timeout(150)
        page.evaluate("closeSheet()")
        check("tüm sekmeler hatasız açılır", not errors, errors[:3])

        print("Yedek dosyası")
        page.evaluate("navigator.canShare=undefined")
        with page.expect_download() as dl:
            page.evaluate("backup('json')")
        data = json.loads(open(dl.value.path(), encoding="utf-8").read())
        check("yedekte kategori planı var", data.get("catplan", {}).get("months", {}).get("2026-12", {}).get("Market") == 1234)
        check("yedekte net varlık geçmişi var", "2026-10" in (data.get("networth") or {}).get("hist", {}))

        print("Eski yedek uyarısı ve geri dönüş")
        old = json.loads(json.dumps(SAMPLE)); old["months"]["m-2026-11"] = {k: v for k, v in old["months"]["m-2026-11"].items() if k == "t1"}
        page.evaluate("j=>restoreFrom(new File([JSON.stringify(j)],'eski.json'))", old); page.wait_for_timeout(300)
        check("daha eski yedekte uyarı çıkar", "daha eski" in page.inner_text("#sheetBody"))
        page.click("[data-act=restoreok]"); page.wait_for_timeout(600)
        check("eski yedek yüklenince 1 işlem kalır", page.evaluate("S.tx.length") == 1)
        page.evaluate("restoreUndo()"); page.wait_for_timeout(600)
        check("'önceki hâle dön' 4 işlemi geri getirir", page.evaluate("S.tx.length") == 4, page.evaluate("S.tx.length"))

        print("Silme ve geri alma")
        page.evaluate("goTab('kart')")
        page.evaluate("""(()=>{const b=document.createElement('button');b.dataset.act='delcard';b.dataset.id='c1';document.body.append(b);b.click();window._b=b})()""")
        page.wait_for_timeout(100)
        check("kart silmede bağlı kayıt sayısı söylenir", "3 kayıt" in page.evaluate("_b.textContent"), page.evaluate("_b.textContent"))
        page.evaluate("_b.click()"); page.wait_for_timeout(300)
        check("kart silinir", page.evaluate("!cardById('c1')"))
        page.click(".toastbtn"); page.wait_for_timeout(400)
        check("Geri al ile kart geri gelir", page.evaluate("!!cardById('c1')"))
        page.evaluate("""(()=>{const b=document.createElement('button');b.dataset.act='deltx';b.dataset.id='t2';document.body.append(b);b.click();b.click()})()""")
        page.wait_for_timeout(300)
        check("işlem silinir", page.evaluate("!S.tx.some(t=>t.id==='t2')"))
        page.click(".toastbtn"); page.wait_for_timeout(400)
        check("Geri al ile işlem geri gelir", page.evaluate("S.tx.some(t=>t.id==='t2')"))

        print("Güvenlik")
        check("içerik güvenlik politikası ihlali yok", not csp, csp[:2])
        check("sayfa hatası yok", not errors, errors[:3])
        b.close()
    srv.shutdown()
    print(f"\n{'HEPSİ GEÇTİ' if not fails else str(len(fails)) + ' TEST BAŞARISIZ'}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
