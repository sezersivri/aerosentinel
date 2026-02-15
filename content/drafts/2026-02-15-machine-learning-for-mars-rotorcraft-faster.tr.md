---
title: "Makine Ogrenmesiyle Uzun Menzilli Mars Rotorlu Arac Tasarim Optimizasyonu"
date: 2026-02-15
tags:
  - "Gaussian Process Surrogates"
  - "Neural Network Surrogates"
  - "Design Optimization"
  - "Flight Vehicle Design"
  - "Data-Driven Methods"
summary: "Bu makale, uzun menzilli bir Mars rotorlu aracinin tasarim optimizasyonu icin coklu dogruluk seviyelerindeki simülasyon verilerinin ve makine..."
draft: false
paper_type: "ml_aerodynamics"
relevance_score: 40
ai_model: "Gemini 2.5 Flash"
---

**Type:** 🤖 MO/Aerodinamik | **Relevance:** 40/100

Bu makale, uzun menzilli bir Mars rotorlu aracinin tasarim optimizasyonu icin coklu dogruluk seviyelerindeki simülasyon verilerinin ve makine ogrenmesi tekniklerinin kullanilmasini detaylandirmaktadir. Yaklasim, bir heksa-rotorlu cift kanatli kuyruk-oturucu ucagin geometrik pertürbasyonlari ve ucus kosullari araligi icin GPU hizlandirmali OVERFLOW kullanarak iki buyuk aerodinamik simülasyon veritabani olusturmayi iceriyordu. Bu yuksek dogruluklu HAD sonuclari, kanat profili ve govde aerodinamik performansini tahmin etmek icin Gauss Surec Regresyonu (GSR) ve cesitli Yapay Sinir Aglari (YSA) dahil olmak uzere vekil modelleri egitmek icin kullanildi.

3.000'den fazla tam ucak aerodinamik simülasyonu, bir aktüatör disk modeliyle GPU destekli OVERFLOW kullanilarak gerceklestirildi ve bu simülasyonlar 32 GPU dügümünde (128 NVIDIA V100 GPU) yaklasik 1.5 haftada tamamlandi. Gelistirilen vekil modeller, kütle ve ataleti tahmin eden ek Python modülleriyle birlestirilerek, 240 Merkezi Islem Birimi (CPU) cekirdegi kullanilarak CAMRAD-II'de alti saatten daha kisa sürede 3.000 ek ucak simülasyonunun yapilmasini sagladi. Bu, tasarim sürecini önemli olcude hizlandirarak stabilite ve kontrol türevlerinin hizli bir sekilde degerlendirilmesine olanak tanidi. Cerceve artik ucagi maksimum menzil, dayaniklilik veya faydali yük gibi hedefler icin kontrol edilebilirlik kisitlamalarina uyarak optimize edebilmektedir.

Yuksek hizli aerotermodinamigi dogrudan ele almasa da, bu calisma, yuksek dogruluklu HAD verilerini kavramsal tasarimin erken asamalarina entegre etmek icin saglam bir metodoloji sergilemektedir. Vekil modelleme yoluyla elde edilen hizlanma, ozellikle karmasik aerodinamik olaylari temsil etmek icin GSR ve YSA kullanimi, aerotermodinamik gibi daha karmasik fizik icerenler de dahil olmak uzere cesitli havacilik uygulamalarinda tasarim optimizasyonu icin daha genis cikarimlar tasimaktadir. Bu yaklasim, sonuclarin dogrulugunu artirarak ve tasarim iterasyon süresini azaltarak kritik tasarim sorunlarinin gözden kacirilmasi riskini azaltabilir.

---

*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v2.5.0 tarafindan duzenlenmistir.*

---

## Kaynak

1. , "Long-Range Mars Rotorcraft Design Optimization using Machine Learning," *NASA Technical Report*, Unknown. [Link](https://ntrs.nasa.gov/citations/20250003721)
