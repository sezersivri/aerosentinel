---
title: "LES ve Gauss Süreçleri Kullanılarak Yol Aracı Sürüklemesi Optimizasyonu"
date: 2026-03-14
tags:
  - "Gaussian Process Surrogates"
  - "Design Optimization"
  - "Data-Driven Methods"
  - "Surrogate Modeling"
summary: "Kacper Janczuk ve ekibi, basitleştirilmiş bir yol aracı olan Windsor gövdesinin arka tavan uzantısının/spoilerının optimizasyonu yoluyla sürüklemeyi..."
draft: false
paper_type: "ml_aerodynamics"
relevance_score: 25
ai_model: "Gemini 2.5 Flash"
---

**Type:** 🤖 MO/Aerodinamik | **Relevance:** 25/100

Kacper Janczuk ve ekibi, basitleştirilmiş bir yol aracı olan Windsor gövdesinin arka tavan uzantısının/spoilerının optimizasyonu yoluyla sürüklemeyi azaltmayı amaçlayan bir çalışma sunuyor. Yaklaşım, yüksek doğruluklu duvar çözümlü büyük girdap simülasyonlarını (LES) Gauss süreci tabanlı vekil modelleme ve Bayes optimizasyonu (Kriging) ile birleştiriyor. Optimizasyon süreci, beklenen iyileşme kriterini kullanarak tavan uzantısının konik penetrasyon mesafesi, geliş açısı ve uzunluğu gibi geometrik parametrelerini belirliyor.

Optimizasyon, altı iterasyonda (60 simülasyon) %6.5'lik bir sürükleme azalması elde etti. Çalışma, difüzör kaynaklı basınç geri kazanımı, taban boyutu küçültme, dikey iz denge modifikasyonu, ayrılma etkileri, geri dolaşım bölgesi çekirdek yer değiştirmesi ve açıklık yönünde yeniden simetrizasyon olmak üzere altı farklı sürükleme azaltma mekanizması tanımladı. Optimal konfigürasyon, ayrılmanın başlangıcına karşılık gelen bir tavan uzantısı geliş açısında, analiz edilen etki alanı içindeki maksimum konik penetrasyon mesafesi ve uzantı uzunluğunda bulundu.

Bu çalışma, Bayes optimizasyonunun hesaplamalı akışkanlar dinamiği tabanlı tasarımda etkinliğini gösteren sağlam bir çerçeve sunuyor. Yüksek hızlı füzelerdeki aerotermodinamik optimizasyon problemlerinde de benzer vekil modelleme ve optimizasyon yaklaşımlarının kullanılabileceği metodolojik bir örnek teşkil etse de, fiziksel uygulama alanı ve ele alınan akış rejimi benim doğrudan araştırma alanımın dışındadır.

---

*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v3.0.0 tarafindan duzenlenmistir.*

---

## Kaynak

1. Kacper Janczuk, Adrian Gaylard, Aimee S. Morgans, "Bayesian optimisation of a roof extension/spoiler on a simplified vehicle, employing wall-resolved large eddy simulation," *Journal of Fluid Mechanics*, 2026-03-09. [Link](https://doi.org/10.1017/jfm.2026.11244)
