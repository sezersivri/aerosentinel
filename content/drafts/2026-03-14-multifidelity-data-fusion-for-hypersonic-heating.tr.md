---
title: "Hipersonik Isinma Tahmininde Coklu Dogrulukta Veri Birlestirme ve MF-UNet Yaklasimi"
date: 2026-03-14
tags:
  - "Aerothermodynamics"
  - "Deep Learning"
  - "Multi-Fidelity Modeling"
  - "Heat Flux Prediction"
  - "Hypersonic Flow"
summary: "Duan ve arkadaslari, hipersonik araclarin aerodinamik isinma tahmini icin coklu dogrulukta bir veri birlestirme cercevesi sunuyor. Mevcut yontemlerin..."
draft: false
paper_type: "ml_heating"
relevance_score: 92
ai_model: "Gemini 2.5 Flash"
---

**Type:** 🤖 MO/Isinma Tahmini | **Relevance:** 92/100

Duan ve arkadaslari, hipersonik araclarin aerodinamik isinma tahmini icin coklu dogrulukta bir veri birlestirme cercevesi sunuyor. Mevcut yontemlerin deneysel veri kitligi nedeniyle tum yuzey tahminini ve yeni ucus kosullarina guvenilir ekstrapolasyonu saglayamadigi zorlugunu ele aliyorlar. Yaklasimlari, sinirli deneysel veri setlerini genisletmek icin sistematik veri artirma stratejileri ile yenilikci bir coklu dogrulukta U-NET (MF-UNet) mimarisini birlestiriyor. Bu cerceve, veri artirma yoluyla ekstrapolasyon saglamligini artirmayi ve MF-UNet araciligiyla yuksek hassasiyetli isi akisi yeniden yapilandirmasi icin optimize edilmis bir coklu dogrulukta esleme mekanizmasi gelistirmeyi hedefliyor.

Calisma, hipersonik cift-elipsoid bir konfigürasyon uzerinde uc seyrek deneysel veri setini entegre ederek tam yuzey isinma profilleri olusturmada cercevenin etkinligini gosteriyor. Deneysel sonuclar, temel CFD cozumlerine kiyasla onemli iyilesmeler saglayarak, deneysel olcumlerle karsilastirildiginda yuzey ortalamali normalize kok-ortalama-kare hatasini %3'un altina dusuruyor. Bu metodoloji, coklu dogrulukta entegrasyon zorluklarini basariyla ele alirken, tam yuzey ekstrapolasyonunu mumkun kiliyor.

Bu calisma, aerodinamik isinma analizi icin muhendislik acisindan uygulanabilir bir cozum sunarak, ozellikle sinirli deneysel verilerle calisirken hipersonik arac tasariminda karsilasilan kritik bir zorlugu ele aliyor. Veri artirma ve MF-UNet'in entegrasyonu, hem tahmin dogrulugunu hem de yeni kosullara genellenebilirligi artirmak icin umut verici bir yol gosteriyor.

---

*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v3.0.0 tarafindan duzenlenmistir.*

---

## Kaynak

1. Zhiyu Duan, Wei Zhao, Wanshu Li et al., "Multifidelity Data Fusion Method for Aerodynamic Heating Prediction of Hypersonic Vehicles," *AIAA Journal*, 2026-03-08. [Link](https://doi.org/10.2514/1.j066092)
