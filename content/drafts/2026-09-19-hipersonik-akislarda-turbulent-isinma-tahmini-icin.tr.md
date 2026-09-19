---
title: "Hipersonik Akislarda Turbulent Isinma Tahmini Icin Yeni RANS Kapatma Modeli"
date: 2026-09-19
tags:
  - "Aerothermodynamics"
  - "Hypersonic Aerodynamics"
  - "Turbulent Heating"
  - "Heat Flux Prediction"
summary: "Cheng ve arkadaslari, hipersonik turbulent sinir tabakalarindaki duvar sogutmasi durumunda ortaya cikan ve geleneksel k-omega modellerinin zorlandigi..."
draft: false
paper_type: "numerical_cfd"
relevance_score: 75
ai_model: "Gemini 2.5 Flash"
---

**Type:** 💻 Sayisal/HAD | **Relevance:** 75/100

Cheng ve arkadaslari, hipersonik turbulent sinir tabakalarindaki duvar sogutmasi durumunda ortaya cikan ve geleneksel k-omega modellerinin zorlandigi sicaklik maksimumunu daha dogru tahmin etmek icin Reynolds-ortalamali enerji denklemi icin yeni bir kapatma modeli sunuyor. Yaklasimlari, turbulent kinetik enerji (TKE) tasiniminin yerel olarak onemli hale geldigi durumlarda, k-omega cercevesi icinde cebirsel bir kapatma gelistirmeye odaklanmis. TKE icin tasinan k degiskeni turbulans denklemlerinde kalirken, momentum ve enerji denklemlerindeki fiziksel kinetik enerji terimlerinde cebirsel olarak yeniden yapilandirilmis bir K buyuklugu kullaniliyor.

Yazarlar, bu yeni K yeniden yapilandirmasinin, asiri tahmin edilen sicaklik maksimumundaki azalmanin buyuk bir kismini acikladigini gosteriyor. Ayrica, sikistirilabilir kanal dogrudan sayisal simulasyon (DNS) verilerinden duzenlenmis ensemble-Kalman ters cevirme yontemiyle elde edilen yerel bir turbulent Prandtl sayisi (Pr_t) iliskisi de sunmuslar. Bu Pr_t iliskisi, daha kucuk ama etkili ek bir duzeltme sagliyor. Model, Mach 2'den 14'e kadar serbest akis Mach sayilarina sahip sikistirilabilir kanallarda ve sifir basincli egimli sinir tabakalarinda test edilmis. SST-omega0 ve EARSM-omega0 modelleriyle yapilan testler, gelistirmelerin tutarli oldugunu gosteriyor.

Bu calisma, hipersonik akislarda aerotermodinamik isinma tahminlerinin dogrulugunu artirmak icin temel RANS modellerinin yeteneklerini gelistirme cabalarina onemli bir katki sagliyor. Ozellikle duvar sogutmasinin ve turbulent kinetik enerji tasiniminin kritik oldugu durumlarda, bu tur model iyilestirmeleri, termal koruma sistemlerinin tasarimi ve yuksek hizli fuzelerin performans analizi icin daha guvenilir CFD simulasyonlari saglayabilir.

---

*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v3.0.0 tarafindan duzenlenmistir.*

---

## Kaynak

1. Yuxiao Cheng, Sijie Wang, Yitong Fan et al., "Reynolds-averaged closure modelling of the energy equation for compressible wall turbulence based on the k-ω equations," *Journal of Fluid Mechanics*, 2026-09-17. [Link](https://doi.org/10.1017/jfm.2026.12029)
