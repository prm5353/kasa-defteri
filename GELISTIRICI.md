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
- Sekmeler: Ana Sayfa, Kartlar, **Analiz** (`viewAnaliz`: özet, öne çıkanlar, kategori halkası, ay içi birikimli çizgi, son 12 ay, ortalamaya göre farklar, işyerleri), **Hareketler** (`viewSpend` + `fillTxList`; Money Pro ayında arşiv kayıtlarını salt okunur gösterir, arama arşivi de tarar), Fişler. Ayrı Arşiv sekmesi kaldırıldı
- Analiz ekleri: `vizFlow` (12 ay gelir/harcama ve ay sonunda kalan; `incP`/`spendP` ticari hariç), `catDetail` (kategoriye dokununca: 12 ay `vizCols`, alt başlıklar, yerler, kayıtlar), `cmpSheet` (iki ay karşılaştırma, `cmpA`/`cmpB`). `vizCols` genel 12 ay sütun grafiği
- Varlık ve kredi: harcama sayılmayan kategoriler `__non` (açılışta bir kez `Araçlarım|Araç`, `Banka|Kredi`, `Banka|Kredi Kartı` eklenir, `kd_non2`); gelir sayılmayan gelir türleri `catIcons.__nonInc` (varsayılan `Araba taksiti`), Gelir türleri ekranındaki gelir/varlık düğmesi. Sabit kalemde `asset` (yoksa adından tahmin: kredi, araç, araba, taşıt, konut). Ana Sayfa tablosunda `asset` kalemler ayrı grupta ama nakit akışı toplamında kalır; analizde `incP`/`mineCats` dışında
- Analize dahil olanlar: `inclSheet` (Analiz'in üstündeki "Hariç / Değiştir" satırı) kategori, alt kategori (`__non`) ve gelir türü (`__nonInc`) işaretleri. Halka `vizDonut`: dış etiketler, en az 5° dilim, geniş dokunma alanı; ilk dokunuş `DSEL` seçer, ikincisi ayrıntı açar
- Kategori taşıma/ad değiştirme Money Pro arşivini değiştirmez; `catIcons.__alias` eşlemesi `archMap` ile `derive()` sırasında uygulanır, böylece analiz ve Hareketler yeni adları gösterir. Eşleme kaydı olmayan eski taşımalarda: arşivdeki alt başlık eski ana başlığın altında artık yoksa ve ilk ağaçta (`CAT_TREE`) oradaysa, ağaçta tek bulunduğu ana başlığa (ya da ana başlık olduysa kendisine) konur
- Abonelikler (`subscriptions`): aynı işyeri, tutar ±%6, en az 3 ayrı ay, işyerindeki harcamaların ≥%60'ı bu tutarda (Abonelik kategorisi her zaman). Ayda ≤2,5 ödeme yapılan işyerinde (ör. Apple) farklı tutarlar ayrı abonelik. Kullanıcı düzeltmesi `catIcons.__subs` {hide: "anahtar@tutar", items: [{id,name,amt,note}]}: tanım, adı içeren ve ±%6 tutarlı ödemelerle eşleşir; açıklama (note) başlık olur. `subsEditSheet`, `subForm`. Testlerde bekleme `wait_loaded` (wait_for_function CSP'ye takılıyordu)
- Ticari veriler arşiv + uygulama birlikte (genel "yeni kaydı olan ayda arşiv kullanılmaz" kuralının istisnası): `ticariItems`/`ticariInc`, `tcDedupe` (±3 gün, ±1 ₺ aynı işlem). `ticariSheet`: gün gün tarih aralığı (`TCR={from,to}` YYYY-AA-GG, `tcRange`), hazır aralıklar; grafik ≤45 gün günlük, ≤150 gün haftalık, üstü aylık; tablo ve kayıt listesi. Önbellek `_dv` (derive sayacı)
- Ticari: `isTic` adı "ticari" içeren kategori/gelir türü; `ticariItems`/`ticariOf` analize dahil olsun olmasın tüm ticari kayıtları sayar, sadece alt başlık düzeyinde çıkarılanlar varlık alımı. - Ticari bölüm (`ticariSec`) Analiz'de ayrı; Ticari Gider altında analizden çıkarılan alt başlıklar "ticari varlık alımı" olarak ayrı gösterilir, kârdan düşmez
- Ana Sayfa tablosu tek sütun: üstte Hesaplarımda / + Gelecek / − Ödenecek ve AY SONU KALAN; altında Gelecek gelirler ve Ödenecekler grupları. `planRow`: gün rozeti (gecikti kırmızı, bugün yeşil), ad, durum, tutar
- Fazla ödeme (`excessSheet`): verilecek tarih `excessDue` (tahsilat kaydında), Tamamı/Bir kısmı "Verdim", verilenler listesi ve Sil
- Hariç tutulanları görme: `mineCats(mk, true)` hariçleri de sayar; `catPart`/`catDetail(c,{sub})` hariç kategori ve alt başlıkları uyarıyla gösterir; Analiz'de `excludedSec` ("Hesaba katmadıkların", 12 ay mini grafik); aramada kategori adı eşleşince `gcat` düğmeleri; arama arşivi varsayılan tarar
- Ekran geçmişi: HER ekranda başlıkta ‹ (`openSheet` ekler). Önceki ekran `shReg(anahtar, yenidenAç)` ile kayıtlıysa güncel hâliyle yeniden açılır, değilse son görüntüsü (HTML) geri konur; önceki yoksa ‹ sayfaya döner. Aynı başlıklı yeniden çizim geçmişe eklenmez; geri dönerken (`SHBACK`) eklenmez. `closeSheet()` kayıtlı önceki ekrana döner, değilse kapatır; ✕ ve `goTab` `closeAll()`
- Analiz üstü: tıklanabilir Gelir/Gider satırları (`vgg`) → `gdetSheet('gelir'|'gider')`: dağılım (gelir türleri `incByA` / kategoriler), 12 ay. Gelir türü → `incSrcSheet`. Halka/çubuk seçimi `kd_vmode` (`vModeSw`, `vizDonut` çubuk modu). Analizde gelir `incA` ve gider `mineTotal` tamamen "Analize dahil olanlar"a göre (ticari dahil, istenirse çıkarılır); `incP`/`spendP` bunlara eşit
- Ortak tarih aralığı: `RG` {search, tx, an} (null = aylık), `rgBox(anahtar)` hazır aralıklar + gün seçimi, `rgRefresh`. `mineCatsR`/`incomeByR`/`incByAR` aralık toplamları (ay kuralları aynen). `an` aralığı Analiz'deki Gelir/Gider satırları, `gdetSheet`, `catDetail`, `incSrcSheet` için ortak; `tx` Hareketler; `search` Arama
- Grafik renkleri: `--v1..--v6` (doğrulanmış, renk körlüğüne uygun dizi), `--v0` Diğerleri; renk sıraya değil kategoriye bağlı (`vizColors`: son 12 ayın ilk 6 kategorisi). Fark grafiği `--vup` (fazla, kırmızı) / `--vdown` (az, mavi). `data-tip` taşıyan her öğe dokununca/üstüne gelince bilgi kutusu gösterir
- Ana Sayfa tablosunda gider kalemine dokununca öde ekranı (`payOutUI`): tamamı ya da bir kısmı. Sabit gider kısmi ödemesi `recPart:true` işaretli işlem; işaretsiz bir işlem kalemi kapatır (`recOcc` → `paid`, `plan`, `txs`). İleri tarihli ödemede kısmi ödeme kaydı ikiye böler. Borç ödemesi hem `payments`'a hem hesaptan `odeme` işlemine (`debtId`) yazılır. Kart: `formPayCard(id, tablodakiTutar)`. Gelirler de aynı ekranı kullanır (sabit gelir, ileri tarihli gelir, alacak `tahsilat` işlemiyle, taksitli alacak `planMonth` ile ait olduğu aya yazılır, Kişiler öder → `formPay(pid, tutar)`). Erken gelen: ileri ayın kalemine bugünkü tarihle girilir
- Örnek veri: `tests/ornek_veri.py` (13 ay, kişisel değil) — testler ve ekran denemeleri için
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
