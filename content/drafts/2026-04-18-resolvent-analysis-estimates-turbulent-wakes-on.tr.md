---
title: "Düşük Mach Sayısında Türbülanslı Akış Tahmini İçin Resolvent Yaklaşımı"
date: 2026-04-18
tags:
  - "Reduced-Order Modeling"
  - "Data-Driven Methods"
  - "High-Performance Computing"
summary: "Jung ve Towne, Mach 0.3 ve Reynolds sayısı 23.000'deki bir NACA0012 kanat profilinin türbülanslı art izindeki hız dalgalanmalarını tahmin etmek için..."
draft: false
paper_type: "ml_aerodynamics"
relevance_score: 35
ai_model: "Gemini 2.5 Flash"
---

**Type:** 🤖 MO/Aerodinamik | **Relevance:** 35/100

Jung ve Towne, Mach 0.3 ve Reynolds sayısı 23.000'deki bir NACA0012 kanat profilinin türbülanslı art izindeki hız dalgalanmalarını tahmin etmek için resolvent tabanlı bir çerçeve sunuyor. Yaklaşım, büyük girdap simülasyonlarından (LES) elde edilen çapraz spektral yoğunluklardan nedensel resolvent tabanlı tahmin çekirdekleri oluşturmak için veri odaklı bir yöntem kullanıyor. Bu çekirdekler, nedenselliği en iyi şekilde uygulayarak gerçek zamanlı tahmin doğruluğunu artıran Wiener-Hopf yöntemiyle türetilmiştir. Çalışma, doğrusallaştırılmış Navier-Stokes operatöründeki küresel olarak kararsız modlar, çok ölçekli türbülanslı yapılar ve yüksek boyutlu veri kümeleri gibi türbülanslı art izi rejiminin getirdiği üç temel zorluğun üstesinden gelmeyi hedefliyor.

Çerçeve, tutarlı yapıların spektral imzalarını yakalamakta ve ampirik olarak belirlenen çapraz spektral yoğunluklar aracılığıyla doğrusal sistem üzerindeki doğrusal olmayan zorlamanın renkli istatistiklerini dolaylı olarak hesaba katmaktadır. Yüksek boyutlu tahmin probleminin hesaplama taleplerini karşılamak için paralel algoritmalar kullanılmıştır. Sonuçlar, kanat profilinin yüzeyindeki sınırlı kayma gerilmesi ölçümleri kullanılarak akış yönündeki hızın açıklık ortalamalı, açıklık-Fourier dönüşümlü ve orta açıklık akışı için doğru nedensel tahminini göstermektedir.

Bu çalışma, sıkıştırılabilir, türbülanslı ortamlarda akış özelliklerinin tahminine yönelik veri odaklı yöntemlerin potansiyelini göstermektedir. Ancak, Mach 0.3 gibi düşük hızlı bir rejimde türbülanslı art izi tahmini üzerine odaklanması ve aerodinamik ısınma veya hipersonik akış fiziği ile doğrudan ilişkili olmaması nedeniyle yüksek hızlı füze aerotermodinamiği alanındaki araştırmalarım için doğrudan uygulanabilirliği sınırlıdır.

---

*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v3.0.0 tarafindan duzenlenmistir.*

---

## Kaynak

1. Junoh Jung, Aaron Towne, "Resolvent-based estimation of a turbulent wake," *Journal of Fluid Mechanics*, 2026-04-16. [Link](https://doi.org/10.1017/jfm.2026.11444)
