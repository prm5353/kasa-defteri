"""Testler ve ekran tasarımı için uydurma, kişisel olmayan örnek veri.

13 aylık geçmiş: Eki 2025 – Eki 2026 arşivde (Money Pro gibi), Kasım 2026 canlı kayıt.
Rastgelelik sabit tohumlu; her çalıştırmada aynı veri üretilir.
"""
import random
from datetime import date, timedelta

CATS = [  # kategori, alt kategoriler, aylık ortalama, işyeri örnekleri, ayda kaç kez
    ("Market", [""], 14000, ["Migros", "A101", "BİM", "Şok", "Manav"], 14),
    ("Dışarıda Yemek", [""], 6500, ["Kahveci", "Pideci", "Burgerci", "Lokanta"], 9),
    ("Araçlarım", ["Yakıt", "Otopark", "Yıkama"], 7000, ["Shell", "Opet", "Otopark", "Oto yıkama"], 6),
    ("Faturalar", ["Elektrik", "Doğalgaz", "İnternet", "Cep telefonu"], 5200, ["Elektrik", "Doğalgaz", "İnternet", "GSM"], 4),
    ("Alışveriş", ["Giyim", "Elektronik", "Hediye"], 6000, ["Giyim mağazası", "Teknoloji", "Hediyelik"], 3),
    ("Sağlık", [""], 1800, ["Eczane", "Klinik"], 2),
    ("Kişisel", ["Spor", "Saç bakımı"], 2200, ["Spor salonu", "Kuaför"], 2),
    ("Abonelik", [""], 900, ["Müzik", "Dizi", "Bulut"], 3),
    ("Gezi", [""], 0, ["Otel", "Uçak"], 0),
]
SEASON = {"Doğalgaz": [1.0, 1.4, 2.2, 2.6, 2.4, 1.8, 1.0, 0.5, 0.3, 0.3, 0.3, 0.4, 1.0]}


def build():
    rnd = random.Random(42)
    arch, months = {}, {}
    start = date(2025, 10, 1)
    for i in range(14):
        y, m = divmod(start.month - 1 + i, 12)
        y += start.year; m += 1
        mk = f"{y}-{m:02d}"
        live = mk == "2026-11"
        last_day = 10 if live else (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)).day
        items = {}
        n = 0
        trend = 1 + i * 0.02  # enflasyon
        for cat, subs, avg, shops, times in CATS:
            k = times
            if cat == "Gezi" and mk in ("2026-07", "2026-08"):
                k, avg = 3, 24000
            if cat == "Alışveriş" and mk in ("2025-12", "2026-11"):
                avg *= 2.2
            if live:
                k = max(1, round(k * last_day / 30))
            for _ in range(k):
                sub = rnd.choice(subs)
                f = SEASON.get(sub, [1] * 14)[i % 13] if sub else 1
                amt = round(avg * trend * f / max(times, 1) * rnd.uniform(0.6, 1.4), 2)
                if amt <= 0:
                    continue
                d = f"{mk}-{rnd.randint(1, last_day):02d}"
                n += 1
                items[f"x{i}-{n}"] = {"type": "gider", "amount": amt, "date": d, "personId": "me", "category": cat, "sub": sub,
                                       "merchant": rnd.choice(shops), "ts": n, **({"cardId": "c1"} if live else {"account": "Kart"})}
        # gelir
        for day, a in ((15, 80000), (25, 10000), (28, 10000)):
            if day <= last_day:
                n += 1
                items[f"x{i}-{n}"] = {"type": "gelir", "amount": a * trend, "date": f"{mk}-{day:02d}", "source": "Maaş", "account": "Banka", "ts": n}
        # kart kullanan kişi
        n += 1
        items[f"x{i}-{n}"] = {"type": "gider", "amount": round(rnd.uniform(3000, 9000), 2), "date": f"{mk}-{min(last_day, 9):02d}", "personId": "p1",
                               "category": "Market", "sub": "", "merchant": "Mağaza", "ts": n, **({"cardId": "c1"} if live else {"account": "Kart"})}
        (months if live else arch)[("m-" if live else "a-") + mk] = items
    return {
        "exportedAt": "2026-11-10T08:00:00.000Z",
        "cards": [{"id": "c1", "name": "Test Kart", "limit": 200000, "cutDay": 20, "dueDay": 30, "ts": 1}],
        "accounts": [{"id": "a1", "name": "Banka", "balance": 120000, "balanceAt": 1, "ts": 1}],
        "persons": [{"id": "p1", "name": "Deneme Kişi", "opening": 0, "since": "2026-11-01", "ts": 1}],
        "months": months, "archive": arch, "meta": {"start": "2026-11-01"},
    }


if __name__ == "__main__":
    import json, sys
    json.dump(build(), sys.stdout, ensure_ascii=False)
