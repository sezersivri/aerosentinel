---
title: "Akustik Tahrikli Yarıkta Enerji Dağılım Mekanizmaları ve Viskoz Kayıplar"
date: 2026-08-15
tags:
  - "High-Performance Computing"
  - "Reduced-Order Modeling"
  - "Data-Driven Methods"
  - "Laminar Heating"
summary: "Yu ve arkadaslari, genis en-boy oranina sahip yarık geometrilerinden gecen duzlemsel bir dalga icin gelen akustik enerjinin girdap hareketine ve..."
draft: false
paper_type: "numerical_cfd"
relevance_score: 10
ai_model: "Gemini 2.5 Flash"
---

**Type:** 💻 Sayisal/HAD | **Relevance:** 10/100

Yu ve arkadaslari, genis en-boy oranina sahip yarık geometrilerinden gecen duzlemsel bir dalga icin gelen akustik enerjinin girdap hareketine ve viskoz dagilima donusumunu nicel olarak belirlemislerdir. Dogrudan sayisal simulasyonlar (DNS), gelen ses basinci seviyesi (ISPL), Strouhal sayisi (St) ve Reynolds sayisi (Re) gibi genis bir parametre uzayinda gerceklestirilmistir. Spektral ozgun dik ayrısım (SPOD), her frekansta enerjiye gore siralanmis tutarli yapilar elde etmek icin kullanilmis ve bu yapilardan spektral kinetik enerji (KE) ve viskoz kayip (VL) icin mod bazinda alanlar olusturularak akustik sogurma mekanizmalari incelenmistir.

ISPL 150 dB oldugunda, akustik-hidrodinamik enerji donusumu, St <= 4 St0 (etkin Keulegan-Carpenter sayisi Kc > 40'a karsilik gelir) kosulunda en yuksek seviyeye ulasmaktadir. Bu rejimde, uc boyutlu simulasyonlar, baskin akis tepkisinin iki boyutlu oldugunu ve yarık kosesi yakinindaki salinimli kesme tabakasinin ayrilan girdaplara donustugunu gostermektedir. Viskoz kayip, kinetik enerji katkisinin %20 ila %60'ini olusturmaktadir. Daha buyuk St degerleri icin, Stokes tabakasi sinirlamasi X seklinde yarık yakinindaki modlar olusturarak enerji girisini yaklasik %50 azaltmaktadir. Reynolds sayisinin etkisi de degerlendirilmistir.

Bu calisma, akustik-akis etkilesimleri ve enerji dagilimi uzerine temel bir bakis sunsa da, hipersonik fuzelerde aerodinamik isinmanin Gauss sureci tabanli vekil modellerle tahmini gibi benim uzmanlik alanima dogrudan bir uygulama veya iliski tasimamaktadir.

---

*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v3.0.0 tarafindan duzenlenmistir.*

---

## Kaynak

1. Haocheng Yu, Tianyi Chu, Spencer H. Bryngelson, "Energy dissipation mechanisms in an acoustically driven slit," *Journal of Fluid Mechanics*, 2026-08-10. [Link](https://doi.org/10.1017/jfm.2026.11896)
