# Kasa Defteri: geliştirici notları

Tek dosyalık PWA. Yayın: GitHub Pages (main dalı, kök). Kişisel veri bu depoda **yok**. Veriler telefondaki IndexedDB'de.

## Dosyalar
- `index.html`: bütün uygulama (HTML + CSS + JS)
- `sw.js`: service worker. Her yayında `CACHE` sürümünü artır (`kasa-defteri-vNN`)
- `.github/workflows/gumus.yml` + `.github/gumus.py`: 15 dakikada bir Fibabanka FX Market XAG/TRY kurunu `data` dalına `gumus.json` olarak yazar
- `manifest.webmanifest`, ikonlar

## Veri modeli (IndexedDB `kasaDefteri` / `docs`, artifact db API taklidi: `db.collection('kasa').doc(id).set/delete`, `onSnapshot`)
- Ay kovaları: `m-YYYY-MM` (canlı işlemler, `items` haritası), `a-YYYY-MM` (Money Pro arşivi, **salt okunur**), `r-YYYY-MM` (fişler)
- Tekil belgeler (k): card, account, person, budget, asset, debt, plan, stmt, rec, cattree (tree + icons + `icons.__non` = harcama sayılmayanlar), catplan (aylık kategori tahmini düzeltmeleri), incsrc (gelir türleri), networth, meta, merchants, products, market/prices
- İşlem türleri: gider, gelir, tahsilat, verdim, transfer, duzeltme, odeme
- Önemli alanlar: personId (ME='me' | kişi id), cardId | account, inst/instDone/nextDate (taksit), stmtCut (ekstreye sabitleme), lump ('stmt'|'open' toplu tutar), cardAlloc (tahsilatın karta sayılan kısmı), excessOf, feeOf, groupId (bölünmüş), recId
- İleri tarihli (date > bugün) hesap hareketleri bakiyeye dokunmaz, planda bekler

## Ana kavramlar ve fonksiyonlar
- Kart: `portions` (pcut = ait olduğu kesim), `cutFor/dueFor/prevCut/lastCut`, `card.cuts` {kesim: son ödeme} haritası, `stmt`, `cardState`, `cardTotals`, `debtSplit` (eski ekstreden kalan / bu dönem), `fixCuts`
- Kişiler: `owedByDue` (tüm dönemlerdeki kişi payları, tahsilat en eskiden düşülür), `heldMoney/heldTotal/heldByAcc`, `excessList`
- Plan: `monthPlan(mk)` → ins/outs; `cashFlow`, `projection`, `planTableFlow` (gruplar: kartlar, yatırım hedefi, gönderilecek, sabit, tahmini)
- Tahmin: `catHist`, `estCat/estCats` (mevsimsel: geçen yıl aynı ay; düzenli: 6 ay ortancası; Gezi: 0), `srcShares`, `estSpend`
- Kişi payları ve ticari giderler plana/rahat harcamaya girmez; `card.ticari` kartlar hiç girmez
- Harcama: `mineCats` (nonSpend hariç), `useArch(mk)` (o ayda canlı kayıt yoksa arşiv), `budgetUse/budgetCarry` (devirli bütçe)
- Analiz: `anData`, `analizSheet`, `yearSheet`
- Birikim: `aPrice/aVal` (yarım=2, tam=4 çeyrek; esya elle değer), `pnl`, `goalRows`, `netWorth`
- Kurlar: `autoPrices` → Harem websocket (`hrmsocketonly.haremaltin.com`, KULCEALTIN/CEYREK_YENI/USDTRY/EURTRY alış) + `gumus.json` (raw.githubusercontent)
- Yapay zekâ okuma: tarayıcıdan doğrudan Anthropic API (`anthropic-dangerous-direct-browser-access`), anahtar telefonda localStorage `kd_key`, model `kd_model` (varsayılan claude-haiku-5-5)

## Güvenlik ve yedek
- Sayfada içerik güvenlik politikası (CSP) var: yeni bir dış adrese bağlanılacaksa `index.html` başındaki `connect-src` (ya da ilgili) listesine eklenmeli, yoksa tarayıcı engeller
- Yedek yükleme iki adımlı (`restoreFrom` özet + onay → `restoreApply`). Yüklemeden önce şimdiki hâl ayrı IndexedDB'ye (`kasaDefteriOnce`) kopyalanır; `restoreUndo` geri döner
- Silmeler `delUndoable` / `toast(msg,0,geriAlFn)` ile geri alınabilir
- Kişisel isimler koda yazılmaz; veriden (kişiler, kategori ağacı) okunur

## Çalışma düzeni
- Otomatik testler: `python3 tests/test_app.py` (Playwright + Chromium; tarih 10 Kasım 2026'ya sabit, örnek veriyle). Her değişiklikten sonra çalıştır; hesap mantığı değişirse testteki beklenen tutarları bilerek güncelle
- Değişiklik → `node --check` (script'i ayıklayıp) → Playwright ile `restoreFrom(new File([JSON]))` ile örnek veri yükleyip test → `sw.js` sürümünü artır → commit → push
- Commit kimliği: Claude <noreply@anthropic.com>
