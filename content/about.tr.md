---
title: "AeroSentinel Hakkinda"
layout: "single"
url: "/tr/about/"
summary: "AeroSentinel nedir?"
translationKey: "about"
---

## AeroSentinel Nedir?

AeroSentinel, belirli bir tez alanina odaklanan yapay zeka destekli bir arastirma istihbarat platformudur: **"Yuksek Hizli Fuzelerde Aerodinamik Isinmanin Gauss Sureci Tabanli Vekil Modeller Kullanilarak Tahmini."**

Her hafta, sistem 7 ust duzey akademik veritabanini yeni yayinlar icin tarar, bunlari cok katmanli bir kalite filtresinden gecirir, makaleleri temel ve cevresel arastirma olarak siniflandirir ve yapilandirilmis analizle iki dilli istihbarat brifingleri yayinlar -- tumunu Telegram botu uzerinden tek dokunusla onay ile yonetir.

## Tez Odagi

Bu platform ozellikle asagidaki kesisim noktalarindaki arastirmalari takip etmek icin ayarlanmistir:

- **Aerodinamik isinma** -- yuksek hizli araclarda yuzey isi akisi tahmini, olcumu ve simulasyonu
- **CFD icin YZ/MO vekil modelleri** -- Gauss sureci regresyonu, sinir aglari, derin ogrenme ve aerodinamik/aerotermodinamik problemlerine uygulanan fizik bilgili yontemler
- **Hipersonik akis fizigi** -- sinir tabaka gecisi, sok-sinir tabaka etkilesimi, gercek gaz etkileri, durma noktasi isinmasi

Bu konulardaki makaleler tam bireysel derin inceleme aliyor (**temel makaleler**). Diger her sey -- genel HAD, genel havacilik, scramjet itisi, yeniden giris fizigi -- metin ici atiflarla akici bir akademik anlatima donusturuluyor (**cevresel makaleler**).

## Kaynaklar

Makaleler 7 akademik veritabanindan toplanir:

- **OpenAlex** -- genis akademik kapsam (200M+ eser), dergi kademesi ve kurum filtrelemesiyle
- **Crossref** -- 70M+ makale, DOI tabanli metadata, tez/doktora kesfi ile
- **CORE** -- 200M+ acik erisim makale, tezler ve gri literatur dahil
- **Semantic Scholar** -- atif hizi, etkili atif sayilari, ozet zenginlestirme
- **arXiv** -- en son on-baskilar, fizik ve hesaplama kategorileriyle sinirli, havacilik konu ilgilisi kontrolu ile
- **NASA NTRS** -- NASA teknik raporlari ve muhtiralar (her zaman 1. Kademe)
- **IEEE Xplore** -- IEEE konferans ve dergi makaleleri (opsiyonel, API anahtari gerektirir)

## Kalite Sistemi

### Dergi Kademeleri
- **1. Kademe** (her zaman tutulur): AIAA Journal, Journal of Fluid Mechanics, Physics of Fluids, Journal of Spacecraft and Rockets, Aerospace Science and Technology, Shock Waves ve digerleri
- **2. Kademe** (atif hizi veya elit kurumla tutulur): Computers & Fluids, Acta Astronautica, International Journal of Heat and Mass Transfer, Chinese Journal of Aeronautics ve digerleri
- **0. Kademe** (engellenir, tezler/doktora haric): derecelendirilmemis dergiler

### Puanlama
Makaleler dergi kademesi, kaynak, anahtar kelime onceligi, atif metrikleri, guncellik ve ozet varligina gore puanlanir (0-100+). Yalnizca 30+ puan alan makaleler dahil edilir. 20'nin altinda puan alan makaleler tamamen cikarilir.

### Tez Kesfi
Crossref doktora tezleri ve CORE tezleri 0. kademe filtresini atlar, tez alaniyla dogrudan ilgili doktora ve yuksek lisans calismalarina erisimi saglar. Bunlar yine de puanlamadan gecer, bu nedenle ilgisiz tezler dogal olarak filtrelenir.

## Yapay Zeka Analizi

Her brifing **Gemini 2.5 Flash** tarafindan olusturulur ve sunlari icerir:

- **Iki katmanli yapi** -- Temel makaleler tam analiz alir (metodoloji, temel bulgular, temel sayilar, sinirliliklar, makaleler arasi baglantilar); cevresel makaleler literatur taramasi tarzi bir anlatima dokunur
- **9 makale tipi siniflandirmasi** -- MO/Isinma, MO/Aerodinamik, MO/Gecis, Sayisal/HAD, Deneysel, Analitik, Derleme, Coklu Yontem, Tez
- **36 kuratoryel etiket** -- Arastirma alanlari, metodolojiler, fiziksel olgular, akis rejimleri, uygulamalar ve capraz konulari kapsayan siki Ingilizce kelime dagarciqi
- **Ilgililik puanlamasi** (0-100) tez alanina yakinliga dayali
- **Elestirel analiz** -- Sinirliliklar alani metodolojik zayifliklari ve kanit gucunu tanimlar
- **Yapay zeka dolgu filtresi** -- 24 yasakli YZ dolgu ifadesi istemde engellenir ve ciktidan temizlenir
- **Iki dilli cikti** -- Her brifing hem Ingilizce hem Turkce

## Telegram Botu

Her seyi Telegram'dan yonetin:

| Komut | Aciklama |
|-------|----------|
| `/scout` | Hemen bir makale avi baslatir |
| `/search` | Interaktif ozel arama -- 36 etiketten secin, tarih araligi belirleyin |
| `/bibtex` | Son ozeti BibTeX olarak disari aktarin |
| `/bookmarks` | Yer imlerine alinan ozetlerinizi goruntuler |
| `/status` | Son is akisi durumunu kontrol eder |
| `/help` | Kullanilabilir komutlari gosterir |

Taslak on izlemeler tek dokunusla **Yayinla / Duzenle / Cikar / Yer Imi** butonlariyla gelir.

## Teknik Detaylar

- **Tamamen otomatik** -- GitHub Actions, programli (haftalik) veya Telegram uzerinden talep uzerine calisir
- **Acik kaynak** -- [github.com/sezersivri/aerosentinel](https://github.com/sezersivri/aerosentinel)
- **Aylik $0** -- GitHub Actions, GitHub Pages, Cloudflare Worker, Gemini API, Telegram Bot API ve tum akademik API'ler ucretsiz katmandadir
- **Gizlilik oncelikli** -- Analitik yok, izleme yok, cerez yok
- **Kullanilanlar:** Hugo (PaperMod temasi), Python 3.11, Cloudflare Workers, Gemini 2.5 Flash
- **Guncel surum:** 2.4.0
