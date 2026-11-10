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

def wait_loaded(page, timeout=10000):
    """S.loaded olana kadar bekler (wait_for_function sayfanın CSP'sine takılabildiği için evaluate ile yoklanır)"""
    for _ in range(timeout // 100):
        try:
            if page.evaluate("typeof S!=='undefined'&&!!S.loaded"): return
        except Exception: pass
        page.wait_for_timeout(100)
    raise TimeoutError("uygulama yüklenmedi")

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
        page.goto(url); wait_loaded(page)

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
        for t in ["ana", "kart", "analiz", "harcama", "fis"]:
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

        print("Analiz ve Hareketler (13 aylık örnek veri)")
        import ornek_veri
        page.evaluate("j=>restoreFrom(new File([JSON.stringify(j)],'o.json'))", ornek_veri.build()); page.wait_for_timeout(300)
        page.click("[data-act=restoreok]"); page.wait_for_timeout(600)
        page.evaluate("viewMonth='2026-10';goTab('analiz')"); page.wait_for_timeout(300)
        tot = page.evaluate("mineTotal('2026-10')")
        check("Analiz: ayın toplamı büyük rakamla görünür", page.evaluate("document.querySelector('.vbig').textContent") == page.evaluate("TL(mineTotal('2026-10'))"))
        segs = page.evaluate("[...document.querySelectorAll('.vdonut2 .dseg')].length")
        check("Analiz: halka en çok 7 dilim (6 kategori + Diğerleri)", 2 <= segs <= 7, segs)
        legsum = page.evaluate("[...document.querySelectorAll('.vlegs > .vleg b, .vrest summary .vleg b')].reduce((a,b)=>a+Number(b.textContent.replace(/[^0-9,]/g,'').replace(',','.')),0)")
        check("Analiz: liste toplamı ay toplamına eşit", abs(legsum - tot) < 2, (legsum, tot))
        check("Analiz: 12 sütun", page.evaluate("document.querySelector('.vyear').querySelectorAll('[data-act=vmonth]').length") == 12)
        check("Analiz: renkler sıraya değil kategoriye bağlı (ay değişince Market aynı renk)", page.evaluate("(()=>{const a=vizColors().Market;viewMonth='2026-07';render();const b=vizColors().Market;viewMonth='2026-10';render();return a&&a===b})()"))
        page.locator(".vyear").first.locator("[data-act=vmonth]").nth(3).scroll_into_view_if_needed(); page.wait_for_timeout(400)
        box = page.locator(".vyear").first.locator("[data-act=vmonth]").nth(3).bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] - 30); page.wait_for_timeout(100)
        check("Analiz: grafik üstüne gelince bilgi kutusu çıkar", page.evaluate("!!document.querySelector('.vtip')&&!document.querySelector('.vtip').hidden"))
        page.locator(".vyear").first.locator("[data-act=vmonth]").nth(3).click(); page.wait_for_timeout(200)
        check("Analiz: sütuna dokununca o aya geçer", page.evaluate("viewMonth") != "2026-10", page.evaluate("viewMonth"))
        page.evaluate("viewMonth='2026-10';goTab('harcama')"); page.wait_for_timeout(300)
        n = page.evaluate("document.querySelectorAll('#txList .row').length")
        check("Hareketler: Money Pro ayında arşiv kayıtları listelenir", n > 20, n)
        page.fill("#txSearch", "shell"); page.wait_for_timeout(200)
        check("Hareketler: arama arşivi de tarar", page.evaluate("document.querySelectorAll('#txList .row').length") > 5)
        page.fill("#txSearch", "")
        page.evaluate("viewMonth='2026-10';goTab('analiz')"); page.wait_for_timeout(300)
        check("Gelir-harcama grafiği: 12 ay, her ay gelir ve harcama sütunu", page.evaluate("document.querySelectorAll('.vstat3').length") == 1 and page.evaluate("[...document.querySelectorAll('.vyear')].length") >= 3)
        page.evaluate("catDetail('Market')"); page.wait_for_timeout(300)
        check("Kategori ayrıntısı: toplam doğru", page.evaluate("document.querySelector('#sheetBody .total').textContent") == page.evaluate("TL(mineCats('2026-10').Market.v)"))
        check("Kategori ayrıntısı: 12 aylık grafik", page.evaluate("document.querySelectorAll('#sheetBody [data-act=catmonth]').length") == 12)
        page.locator("#sheetBody [data-act=catmonth]").nth(9).click(); page.wait_for_timeout(300)
        check("Kategori ayrıntısı: sütuna dokununca o aya geçer", page.evaluate("viewMonth") == "2026-09" and "Eylül" in page.inner_text("#sheetBody h1, #sheetBody .shead, #sheetBody"))
        page.evaluate("closeSheet();cmpA='2026-10';cmpB='2026-08';cmpSheet()"); page.wait_for_timeout(300)
        rows = page.evaluate("document.querySelectorAll('#sheetBody .vcmp').length")
        check("Karşılaştırma: kategoriler listelenir", rows >= 6, rows)
        page.select_option("#sheetBody select[data-cmp=b]", "2026-09"); page.wait_for_timeout(300)
        check("Karşılaştırma: ay değişince yenilenir", page.evaluate("cmpB") == "2026-09")
        page.evaluate("closeSheet()")
        print("Halka, dahil edilenler, kategori düzenleme")
        page.evaluate("viewMonth='2026-10';DSEL=null;goTab('analiz')"); page.wait_for_timeout(300)
        labs = page.evaluate("[...document.querySelectorAll('.vdonut2 .dl1')].map(t=>t.textContent)")
        check("halkada kategori adları yazılı", len(labs) >= 5 and "Market" in labs, labs)
        small = page.evaluate("(()=>{const s=[...document.querySelectorAll('.vdonut2 .dseg')].map(e=>e.dataset.c);return s[s.length-2]})()")
        page.locator(f'.vdonut2 rect[data-c="{small}"]').click(); page.wait_for_timeout(300)
        check("küçük dilimin yazısına dokununca seçilir", page.evaluate("DSEL") == small, (small, page.evaluate("DSEL")))
        page.locator(f'.vdonut2 rect[data-c="{small}"]').click(); page.wait_for_timeout(300)
        check("ikinci dokunuşta ayrıntı açılır", small in page.inner_text("#sheetBody"))
        page.evaluate("closeSheet();DSEL=null")
        before = page.evaluate("mineTotal('2026-10')"); mk = page.evaluate("mineCats('2026-10').Market.v")
        page.evaluate("inclSheet()"); page.wait_for_timeout(200)
        page.locator('#sheetBody input[data-incl="Market"]').uncheck(); page.wait_for_timeout(400)
        check("Market işareti kalkınca analizden çıkar", abs(page.evaluate("mineTotal('2026-10')") - (before - mk)) < 1)
        page.locator('#sheetBody input[data-incl="Market"]').check(); page.wait_for_timeout(400)
        check("işaret geri konunca geri gelir", abs(page.evaluate("mineTotal('2026-10')") - before) < 1)
        fv = page.evaluate("mineCats('2026-10').Araçlarım.subs.Yakıt||0")
        page.evaluate("document.querySelector('#sheetBody [data-incl=\"Araçlarım\"]').closest('.ic').querySelector('.icx').click()"); page.wait_for_timeout(100)
        page.locator('#sheetBody input[data-incl="Araçlarım|Yakıt"]').uncheck(); page.wait_for_timeout(400)
        check("alt kategori (Araçlarım › Yakıt) çıkarılabilir", abs(page.evaluate("mineTotal('2026-10')") - (before - fv)) < 1 and fv > 0)
        page.locator('#sheetBody input[data-incl="Araçlarım|Yakıt"]').check(); page.wait_for_timeout(300)
        page.locator('#sheetBody input[data-incli="Maaş"]').uncheck(); page.wait_for_timeout(300)
        check("gelir türü çıkarılabilir", page.evaluate("incP('2026-10')") < 1)
        page.locator('#sheetBody input[data-incli="Maaş"]').check(); page.wait_for_timeout(300)
        page.evaluate("closeSheet()")
        dy = page.evaluate("mineCats('2026-10')['Dışarıda Yemek'].v")
        page.evaluate("catRename('Dışarıda Yemek','','Restoran')"); page.wait_for_timeout(400)
        check("ad değişince arşivdeki (Money Pro) aylar da yeni adla görünür", abs(page.evaluate("mineCats('2026-10').Restoran?.v||0") - dy) < 1 and not page.evaluate("mineCats('2026-10')['Dışarıda Yemek']"))
        check("arşivin kendisi değişmez", page.evaluate("Object.values(S.amonths['a-2026-10']).some(t=>t.category==='Dışarıda Yemek')"))
        smk = page.evaluate("(()=>{for(let i=1;i<13;i++){const k=shiftMonth('2026-11',-i);if(mineCats(k).Kişisel?.subs?.Spor)return k}})()")
        sh = page.evaluate(f"mineCats('{smk}').Kişisel.subs.Spor")
        page.evaluate("catMove('Kişisel','Spor','Sağlık')"); page.wait_for_timeout(400)
        check("alt kategori taşınınca arşiv de yeni yerinde", abs((page.evaluate(f"mineCats('{smk}').Sağlık?.subs?.Spor||0")) - sh) < 1 and not page.evaluate(f"mineCats('{smk}').Kişisel?.subs?.Spor"), (smk, sh))
        # eşleme kaydı olmadan (eski sürümde) taşınmış alt başlıklar: ağaçtan bulunur
        hd = page.evaluate("(()=>{let v=0;for(let i=1;i<13;i++){v+=mineCats(shiftMonth('2026-11',-i)).Alışveriş?.subs?.Hediye||0}return v})()")
        page.evaluate("""(async()=>{const t=catTree();t['Alışveriş']=t['Alışveriş'].filter(x=>x!=='Hediye');t['Diğer']=[...(t['Diğer']||[]),'Hediye'];const I={...S.catIcons};delete I.__alias;await saveCatAll(t,I)})()"""); page.wait_for_timeout(400)
        hd2 = page.evaluate("(()=>{let v=0,o=0;for(let i=1;i<13;i++){const m=mineCats(shiftMonth('2026-11',-i));v+=m['Diğer']?.subs?.Hediye||0;o+=m.Alışveriş?.subs?.Hediye||0}return [v,o]})()")
        check("eski sürümde taşınan Hediye arşivde de Diğer altında", hd > 0 and abs(hd2[0] - hd) < 1 and hd2[1] == 0, (hd, hd2))
        page.evaluate("""(async()=>{const t=catTree();t['Araçlarım']=t['Araçlarım'].filter(x=>x!=='Yakıt');t['Yakıt']=[];const I={...S.catIcons};delete I.__alias;await saveCatAll(t,I)})()"""); page.wait_for_timeout(400)
        check("ana başlık yapılan alt başlık (Yakıt) arşivde kendi başına", page.evaluate("(mineCats('2026-10').Yakıt?.v||0)>0&&!mineCats('2026-10').Araçlarım?.subs?.Yakıt"))
        check("ağaçta hiç olmamış alt başlık yerinde kalır", page.evaluate("archMap({type:'gider',category:'Sağlık',sub:'Eczane'}).category") == "Sağlık")
        print("Abonelikleri düzenle")
        subs = page.evaluate("subscriptions().map(x=>x.k)")
        check("abonelikler algılanır, marketler abonelik sayılmaz", len(subs) >= 1 and not any(s in ("MIGROS","BIM","A101","MANAV") for s in subs), subs)
        page.evaluate("subsEditSheet()"); page.wait_for_timeout(200)
        page.locator(f'#sheetBody [data-act=subhide][data-k="{subs[0]}"]').first.click(); page.wait_for_timeout(400)
        check("'Değil' denen listeden çıkar", subs[0] not in page.evaluate("subscriptions().map(x=>x.k)"))
        page.locator('#sheetBody [data-act=subunhide]').first.click(); page.wait_for_timeout(400)
        check("geri alınınca geri gelir", subs[0] in page.evaluate("subscriptions().map(x=>x.k)"))
        page.evaluate("closeSheet()")
        page.evaluate("""saveTx(['2026-08','2026-09','2026-10','2026-11'].flatMap((m,i)=>[
          {id:'ap'+i,type:'gider',amount:159.99,date:m+'-03',account:'Banka',personId:'me',category:'Eğlence',sub:'',merchant:'APPLE.COM/BILL',ts:i},
          {id:'aq'+i,type:'gider',amount:39.99,date:m+'-05',account:'Banka',personId:'me',category:'Eğlence',sub:'',merchant:'APPLE.COM/BILL',ts:i}]))"""); page.wait_for_timeout(300)
        ap = page.evaluate("subscriptions().filter(x=>/APPLE/i.test(x.name)).map(x=>Math.round(x.amt*100)/100).sort((a,b)=>a-b)")
        check("Apple'dan iki ayrı tutar iki ayrı abonelik", ap == [39.99, 159.99], ap)
        page.evaluate("subsEditSheet()"); page.wait_for_timeout(200)
        page.click("#sheetBody >> text=+ Abonelik ekle"); page.wait_for_timeout(200)
        page.fill("#sheetBody input[name=name]", "Apple"); page.fill("#sheetBody input[name=amount]", "159.99"); page.fill("#sheetBody input[name=note]", "YouTube")
        page.click("#sheetBody button[type=submit]"); page.wait_for_timeout(400)
        yt = page.evaluate("subscriptions().filter(x=>/APPLE/i.test(x.name)).map(x=>[x.note||'',Math.round(x.amt*100)/100,x.months]).sort()")
        check("Apple 159,99 'YouTube' açıklamasıyla, 4 ay ödenmiş; 39,99 ayrı kalır", yt == [["", 39.99, 4], ["YouTube", 159.99, 4]], yt)
        page.locator('#sheetBody [data-act=subform][data-amt^="39.99"]').first.click(); page.wait_for_timeout(200)
        page.fill("#sheetBody input[name=note]", "iCloud"); page.click("#sheetBody button[type=submit]"); page.wait_for_timeout(400)
        notes = page.evaluate("subscriptions().filter(x=>/APPLE/i.test(x.name)).map(x=>x.note).sort()")
        check("otomatik bulunana açıklama yazılabilir (iCloud)", notes == ["YouTube", "iCloud"] or notes == ["iCloud", "YouTube"], notes)
        page.evaluate("closeSheet();viewMonth='2026-11';goTab('analiz')"); page.wait_for_timeout(300)
        check("Analiz listesinde açıklama başlık olarak görünür", page.evaluate("(()=>{const t=document.getElementById('view').textContent;return t.includes('YouTube')&&t.includes('iCloud')})()"))

        print("Ticari bölüm")
        page.evaluate("""saveTx([{id:'tc1',type:'gider',amount:20000,date:'2026-11-03',account:'Banka',personId:'me',category:'Ticari Gider',sub:'Medikal',merchant:'Cihaz',ts:1},
          {id:'tc2',type:'gider',amount:5000,date:'2026-11-04',account:'Banka',personId:'me',category:'Ticari Gider',sub:'Sarf Malzeme',merchant:'Sarf',ts:2},
          {id:'tc3',type:'gelir',amount:40000,date:'2026-11-05',account:'Banka',source:'Ticari Gelir',ts:3}])"""); page.wait_for_timeout(300)
        page.evaluate("(async()=>{const I={...S.catIcons};I.__non=[...(I.__non||[]),'Ticari Gider|Medikal'];await saveCatAll(catTree(),I)})()"); page.wait_for_timeout(300)
        page.evaluate("viewMonth='2026-11';goTab('analiz')"); page.wait_for_timeout(400)
        tsec = page.evaluate("[...document.querySelectorAll('#view section')].find(s=>s.querySelector('h2')?.textContent.startsWith('Ticari'))?.innerText||''")
        check("Ticari ayrı bölüm: gider 5 bin, kâr 35 bin", "5 bin" in tsec and "35 bin" in tsec, tsec[:200])
        check("Ticari varlık alımı ayrı gösterilir, kârdan düşmez", "Ticari varlık alımı" in tsec and "20.000" in tsec)
        page.evaluate("saveTx([{id:'tc4',type:'gider',amount:4000,date:'2026-11-10',account:'Halkbank',personId:'me',category:'Ticari Gider',sub:'',merchant:'Halkbank ödeme',ts:4},{id:'tc5',type:'gider',amount:1000,date:'2026-11-10',account:'Halkbank',personId:'me',category:'Ticari Gider',sub:'Diğer',merchant:'Başka yer',ts:5}])"); page.wait_for_timeout(300)
        check("bugün girilen 4.000 + 1.000 ticari gider sayılır", page.evaluate("ticariOf('2026-11').g") == 10000, page.evaluate("ticariOf('2026-11').g"))
        page.evaluate("(async()=>{const I={...S.catIcons};I.__non=[...(I.__non||[]),'Ticari Gider'];await saveCatAll(catTree(),I)})()"); page.wait_for_timeout(300)
        check("Ticari Gider analizden çıkarılmış olsa da ticari bölümde gider sayılır", page.evaluate("ticariOf('2026-11').g") == 10000, page.evaluate("ticariOf('2026-11')"))
        page.evaluate("(async()=>{const I={...S.catIcons};I.__non=(I.__non||[]).filter(k=>k!=='Ticari Gider');await saveCatAll(catTree(),I);await catRename('Ticari Gider','','Ticari Giderler')})()"); page.wait_for_timeout(500)
        check("kategori adı değişse de (Ticari Giderler) bulunur", page.evaluate("ticariOf('2026-11').g") == 10000, page.evaluate("ticariOf('2026-11').g"))
        page.evaluate("goTab('analiz')"); page.wait_for_timeout(300)
        check("ticari bölümde bu ayın kayıtları listelenir", page.evaluate("[...document.querySelectorAll('#view details')].some(d=>d.textContent.includes('Bu ayki ticari kayıtlar (4)'))"))
        vk = page.evaluate("[...document.querySelectorAll('details.vmore')].find(d=>d.innerText.includes('Varlık, kredi'))?.innerText||''")
        check("'Varlık, kredi ve toplama girmeyenler'de Ticari yok", "Ticari" not in vk, vk[:200])
        check("Analiz ve Hareketler hatasız", not errors, errors[:3])

        print("Ana Sayfa tablosundan öde: tamamı ya da bir kısmı")
        pay = json.loads(json.dumps(SAMPLE))
        pay["recs"] = [{"id": "r1", "name": "Kira", "amount": 20000, "day": 25, "dir": "gider", "account": "Banka", "ts": 1}]
        pay["debts"] = [{"id": "d1", "who": "Komşu", "dir": "borc", "amount": 5000, "dueDate": "2026-11-28", "ts": 1}]
        pay["months"]["m-2026-11"]["s1"] = {"type": "gider", "amount": 3000, "date": "2026-11-26", "account": "Banka", "personId": "me", "category": "Faturalar", "sub": "", "merchant": "Okul taksiti", "ts": 9}
        page.evaluate("j=>restoreFrom(new File([JSON.stringify(j)],'p.json'))", pay); page.wait_for_timeout(300)
        page.click("[data-act=restoreok]"); page.wait_for_timeout(500)
        page.evaluate("planMonth='2026-11';goTab('ana')"); page.wait_for_timeout(300)
        bal0 = page.evaluate("accBalance(S.accounts[0])")
        def open_item(k, i):
            page.evaluate(f"planItemSheet('{k}','{i}')"); page.wait_for_timeout(250)
        def submit(amount):
            page.fill("#sheetBody input[name=amount]", str(amount)); page.click("#sheetBody button[type=submit]"); page.wait_for_timeout(400)
        open_item("rec", "r1")
        check("sabit gider: Tamamı / Bir kısmı seçenekleri var", page.locator("#sheetBody .payopts button").count() == 2)
        submit(8000)
        rec = page.evaluate("(()=>{const o=recOcc(S.recs[0],'2026-11');return {left:o.amount,done:o.done,paid:o.paid}})()")
        check("sabit gider: 8.000 ödenince 12.000 kalır, kalem açık", rec == {"left": 12000, "done": False, "paid": 8000}, rec)
        outs = page.evaluate("monthPlan('2026-11').outs.filter(x=>x.k==='rec').map(x=>[x.amount,x.done])")
        check("sabit gider: tabloda ödenen kısım gerçekleşen, kalan bekleyen", sorted(outs) == [[8000, True], [12000, False]], outs)
        check("sabit gider: banka bakiyesinden 8.000 düşer", abs(page.evaluate("accBalance(S.accounts[0])") - (bal0 - 8000)) < 0.01)
        open_item("rec", "r1"); submit(12000)
        check("sabit gider: kalan ödenince kapanır", page.evaluate("recOcc(S.recs[0],'2026-11').done"))
        open_item("rec", "r1")
        check("sabit gider: ödenmiş kalemde iki ödeme listelenir", page.locator("#sheetBody [data-act=recundo]").count() == 2)
        page.evaluate("closeSheet()")
        open_item("sched", "s1"); submit(1000)
        sch = page.evaluate("S.tx.filter(t=>t.merchant==='Okul taksiti').map(t=>[t.amount,t.date]).sort()")
        check("ileri tarihli ödeme: 1.000 bugün, 2.000 eski tarihte bekler", sch == [[1000, "2026-11-10"], [2000, "2026-11-26"]], sch)
        open_item("debt", "d1"); submit(2000)
        d = page.evaluate("(()=>{const d=S.debts[0];return {left:debtLeft(d),paid:!!d.paid}})()")
        check("borç: 2.000 ödenince 3.000 kalır", d == {"left": 3000, "paid": False}, d)
        open_item("debt", "d1"); submit(3000)
        check("borç: kalan ödenince kapanır", page.evaluate("!!S.debts[0].paid"))
        open_item("card", "c1")
        check("kart: tablodaki tutar hazır gelir", page.evaluate("+document.querySelector('#sheetBody input[name=amount]').value") > 0)
        before = page.evaluate("monthPlan('2026-11').outs.find(x=>x.k==='card'&&!x.done)?.amount||0")
        submit(500)
        after = page.evaluate("monthPlan('2026-11').outs.find(x=>x.k==='card'&&!x.done)?.amount||0")
        check("kart: kısmi ödeme sonrası tablodaki tutar azalır", after < before - 1, (before, after))
        check("öde ekranları hatasız", not errors, errors[:3])

        print("Gelirler: erken ya da bir kısmı geldi")
        inc = json.loads(json.dumps(SAMPLE))
        inc["recs"] = [{"id": "g1", "name": "Maaş", "amount": 80000, "day": 15, "dir": "gelir", "account": "Banka", "ts": 1}]
        inc["debts"] = [{"id": "d2", "who": "Arkadaş", "dir": "alacak", "amount": 4000, "dueDate": "2026-11-20", "ts": 1}]
        inc["plans"] = [{"id": "pl1", "name": "Araba", "who": "Alıcı", "total": 30000, "installment": 10000, "day": 5, "account": "Banka", "ts": 1}]
        inc["months"]["m-2026-11"]["s2"] = {"type": "gelir", "amount": 6000, "date": "2026-11-27", "account": "Banka", "source": "Diğer", "merchant": "Kira geliri", "ts": 9}
        page.evaluate("j=>restoreFrom(new File([JSON.stringify(j)],'g.json'))", inc); page.wait_for_timeout(300)
        page.click("[data-act=restoreok]"); page.wait_for_timeout(500)
        b0 = page.evaluate("accBalance(S.accounts[0])")
        open_item("rec", "g1")
        check("sabit gelir: düğme 'Geldi'", page.inner_text("#sheetBody button[type=submit]").strip() == "Geldi")
        submit(50000)
        g = page.evaluate("(()=>{const o=recOcc(S.recs[0],'2026-11');return [o.amount,o.done]})()")
        check("sabit gelir: 50.000 gelince 30.000 bekler", g == [30000, False], g)
        page.evaluate("planMonth='2026-12'"); open_item("rec", "g1"); submit(80000); page.evaluate("planMonth='2026-11'")
        early = page.evaluate("(()=>{const o=recOcc(S.recs[0],'2026-12');const t=S.tx.find(x=>x.recMonth==='2026-12');return [o.done,t.date]})()")
        check("sabit gelir: Aralık maaşı erken (bugün) geldi, Aralık'ta kapanır", early == [True, "2026-11-10"], early)
        check("sabit gelir: gelenler hesaba eklenir", abs(page.evaluate("accBalance(S.accounts[0])") - (b0 + 130000)) < 0.01)
        open_item("sched", "s2"); submit(2000)
        sg = page.evaluate("S.tx.filter(t=>t.merchant==='Kira geliri').map(t=>[t.amount,t.date]).sort()")
        check("ileri tarihli gelir: 2.000 bugün geldi, 4.000 bekler", sg == [[2000, "2026-11-10"], [4000, "2026-11-27"]], sg)
        open_item("debt", "d2"); submit(1500)
        check("alacak: 1.500 gelince 2.500 kalır", page.evaluate("debtLeft(S.debts[0])") == 2500)
        open_item("plan", "pl1"); submit(4000)
        pp = page.evaluate("monthPlan('2026-11').ins.filter(x=>x.k==='plan').map(x=>[x.amount,x.done]).sort()")
        check("taksitli alacak: 4.000 gelince 6.000 bekler", sorted(pp) == [[4000, True], [6000, False]], pp)
        page.evaluate("planMonth='2026-12'"); open_item("plan", "pl1"); submit(10000); page.evaluate("planMonth='2026-11'")
        dec = page.evaluate("monthPlan('2026-12').ins.filter(x=>x.k==='plan'&&!x.done).length")
        check("taksitli alacak: Aralık taksiti erken geldi, Aralık'ta bekleyen kalmaz", dec == 0, dec)
        check("gelir ekranları hatasız", not errors, errors[:3])

        print("Varlık ve kredi: harcama/gelir sayılmaz, tabloda ayrı grupta")
        va = json.loads(json.dumps(SAMPLE))
        va["recs"] = [{"id": "k1", "name": "Konut kredisi", "amount": 15000, "day": 20, "dir": "gider", "account": "Banka", "ts": 1},
                      {"id": "k2", "name": "Kira", "amount": 10000, "day": 21, "dir": "gider", "account": "Banka", "ts": 1}]
        va["plans"] = [{"id": "pl1", "name": "Araba", "who": "Alıcı", "total": 30000, "installment": 10000, "day": 25, "account": "Banka", "ts": 1}]
        va["months"]["m-2026-11"]["v1"] = {"type": "gider", "amount": 9000, "date": "2026-11-04", "cardId": "c1", "personId": "me", "category": "Araçlarım", "sub": "Araç", "merchant": "Araç taksiti", "ts": 9}
        va["months"]["m-2026-11"]["v2"] = {"type": "gelir", "amount": 10000, "date": "2026-11-05", "account": "Banka", "source": "Araba taksiti", "planId": "pl1", "ts": 9}
        va["months"]["m-2026-11"]["v3"] = {"type": "gelir", "amount": 50000, "date": "2026-11-05", "account": "Banka", "source": "Maaş", "ts": 9}
        page.evaluate("ls.set('kd_non2','')")
        page.evaluate("j=>restoreFrom(new File([JSON.stringify(j)],'v.json'))", va); page.wait_for_timeout(300)
        page.click("[data-act=restoreok]"); page.wait_for_timeout(500)
        page.reload(); wait_loaded(page); page.wait_for_timeout(300)
        check("araç taksiti harcamaya girmez", page.evaluate("!mineCats('2026-11')['Araçlarım']"), page.evaluate("Object.keys(mineCats('2026-11'))"))
        check("araç satışı taksiti gelire girmez (analiz)", page.evaluate("incP('2026-11')") == 50000, page.evaluate("incP('2026-11')"))
        page.evaluate("planMonth='2026-11';goTab('ana')"); page.wait_for_timeout(300)
        grp = page.evaluate("[...document.querySelectorAll('.pgrp.asset')].map(g=>g.innerText)")
        check("tabloda konut kredisi 'Varlık ve kredi' grubunda", any("Konut kredisi" in g and "VARLIK / KREDİ" in g.upper() for g in grp), grp)
        check("kira sabit giderlerde kalır", not any("Kira" in g for g in grp))
        check("kalan hesabı değişmez (kredi yine nakit çıkışı)", page.evaluate("monthPlan('2026-11').outs.some(x=>x.title==='Konut kredisi'&&x.asset)"))
        check("varlık ekranları hatasız", not errors, errors[:3])

        print("Fazla ödeme: tarih ve yanlış kaydı geri alma")
        page.evaluate("saveTx([{id:'ex1',type:'tahsilat',amount:11929,cardAlloc:600,date:'2026-11-08',account:'Banka',personId:'p1',merchant:'Ödeme aldım',ts:4}])"); page.wait_for_timeout(300)
        page.evaluate("planMonth='2026-11';planItemSheet('personout','ex1')"); page.wait_for_timeout(300)
        page.fill("#sheetBody input[name=due]", "2026-11-25"); page.click("#sheetBody form[data-form=excessdue] button[type=submit]"); page.wait_for_timeout(400)
        po = page.evaluate("monthPlan('2026-11').outs.find(x=>x.k==='personout'&&x.id==='ex1')")
        check("fazla ödemenin verilecek tarihi değişir, tutar aynı kalır", po and po["date"] == "2026-11-25" and abs(po["amount"] - 11329) < 1, po)
        page.evaluate("planItemSheet('personout','ex1')"); page.wait_for_timeout(300)
        page.click("#sheetBody form[data-form=excessback] button[type=submit]"); page.wait_for_timeout(400)
        check("Verdim deyince kapanır", page.evaluate("monthPlan('2026-11').outs.some(x=>x.k==='personout'&&x.id==='ex1'&&x.done)"))
        page.evaluate("planItemSheet('personout','ex1')"); page.wait_for_timeout(300)
        page.locator("#sheetBody [data-act=recundo]").first.click(); page.locator("#sheetBody [data-act=recundo]").first.click(); page.wait_for_timeout(400)
        po = page.evaluate("monthPlan('2026-11').outs.find(x=>x.k==='personout'&&x.id==='ex1')")
        check("yanlış 'verdim' kaydı silinince borç geri gelir", po and not po["done"] and abs(po["amount"] - 11329) < 1, po)
        page.evaluate("closeSheet();goTab('ana')"); page.wait_for_timeout(300)
        check("tablo tek sütun, satırlarda gün rozeti", page.evaluate("document.querySelectorAll('.plan .pl2 .pday').length") > 3)
        check("tablo hatasız", not errors, errors[:3])

        print("Hesaba katılmayanlar görünür")
        import ornek_veri
        page.evaluate("j=>restoreFrom(new File([JSON.stringify(j)],'o.json'))", ornek_veri.build()); page.wait_for_timeout(300)
        page.click("[data-act=restoreok]"); page.wait_for_timeout(500)
        page.evaluate("(async()=>{const I={...S.catIcons};I.__non=['Araçlarım|Yakıt'];await saveCatAll(catTree(),I)})()"); page.wait_for_timeout(300)
        page.evaluate("viewMonth='2026-10';goTab('analiz')"); page.wait_for_timeout(300)
        check("Analiz'de 'Hesaba katmadıkların' bölümü var", "Hesaba katmadıkların" in page.inner_text("#view"))
        yv = page.evaluate("mineCats('2026-10',true).Araçlarım.subs.Yakıt")
        page.locator("#view [data-act=exdet]").first.click(); page.wait_for_timeout(300)
        check("dokununca hariç alt başlığın ayrıntısı açılır, tutar doğru", page.evaluate("document.querySelector('#sheetBody .total').textContent") == page.evaluate(f"TL({yv})") and "analize dahil değil" in page.inner_text("#sheetBody"))
        check("hariç alt başlıkta 12 aylık grafik", page.evaluate("document.querySelectorAll('#sheetBody [data-act=catmonth]').length") == 12)
        page.evaluate("closeSheet();gsQuery='araç';gsFilter='all';searchSheet()"); page.wait_for_timeout(300)
        check("aramada 'araç' yazınca kategori grafiği düğmesi çıkar", page.evaluate("document.querySelectorAll('#gResults .gcat').length") >= 1)
        check("arama Money Pro arşivini de tarar", page.evaluate("gsArch") is True)
        page.evaluate("closeSheet()")

        print("Güvenlik")
        check("içerik güvenlik politikası ihlali yok", not csp, csp[:2])
        check("sayfa hatası yok", not errors, errors[:3])
        b.close()
    srv.shutdown()
    print(f"\n{'HEPSİ GEÇTİ' if not fails else str(len(fails)) + ' TEST BAŞARISIZ'}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
