---
title: "PINN ile Scramjet Nozul Akış Alanının Hızlı ve Güvenilir Tahmini"
date: 2026-06-27
tags:
  - "Deep Learning"
  - "Data-Driven Methods"
  - "Scramjet Propulsion"
  - "Hypersonic Flow"
  - "Surrogate Modeling"
summary: "Tong ve ekibi, scramjet nozul akış alanının hızlı, verimli ve güvenilir bir şekilde tahmin edilmesi için çift veri ve bilgi odaklı bir model..."
draft: false
paper_type: "ml_aerodynamics"
relevance_score: 65
ai_model: "Gemini 2.5 Flash"
---

**Type:** 🤖 MO/Aerodinamik | **Relevance:** 65/100

Tong ve ekibi, scramjet nozul akış alanının hızlı, verimli ve güvenilir bir şekilde tahmin edilmesi için çift veri ve bilgi odaklı bir model yaklaşımı sunuyor. Bu çalışma, geleneksel veri odaklı akış alanı tahmin modellerinin doğruluk ve fiziksel yorumlanabilirlik sınırlamalarını, ayrıca ham hesaplamalı akışkanlar dinamiği (HAD) verilerinin çarpık dağılım özelliklerinin model eğitimini kısıtlamasını ele alıyor. Bu sorunları gidermek amacıyla, HAD verilerinin dağılım özelliklerini etkili bir şekilde iyileştiren yapılandırılmış ızgara ikili veri geliştirme (SGBDE) yöntemi öneriliyor. Aynı zamanda, modelin genelleme yeteneğini artırmak için Euler denklemi kısıtlamalarını ve akış fiziksel nicelik vektör yapısı kısıtlamalarını içeren bir fizik tabanlı sinir ağı (PINN) çerçevesi oluşturuluyor.

SGBDE ve PINN'i entegre ederek DE-PINN adı verilen bir model geliştirilmiş. Deneysel doğrulamalar, DE-PINN tarafından yapılan fiziksel nicelik tahminleri için belirleme katsayısının (R²) 0.997'yi aştığını gösteriyor ve diğer modellere kıyasla önemli ölçüde daha iyi performans sergiliyor. Yapılan ablasyon deneyleri, SGBDE'nin ve fizik tabanlı kısıtlamaların bireysel etkinliğini ve sinerjik etkileşimini doğrulayarak, nozul optimizasyonu için yeni teknik destek sağlama ve akıllı akış alanı tahmini için önemli referanslar sunma potansiyelini ortaya koyuyor.

Bu yaklaşım, yüksek hızlı sistemlerde aerotermodinamik analizler için kritik öneme sahip olan doğru ve hızlı akış alanı verilerinin oluşturulmasında sağlam bir temel sunuyor. Doğrudan ısı akısı tahmini yapmasa da, scramjet gibi araçlarda termal tasarım ve performans optimizasyonu için gerekli olan akış koşullarının güvenilir bir şekilde belirlenmesine yardımcı oluyor.

---

*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v3.0.0 tarafindan duzenlenmistir.*

---

## Kaynak

1. Shuhong Tong, Ye Tian, Xue Deng et al., "Physics-Informed-Neural-Network-Based Fast Prediction Method for Scramjet Nozzle Flow," *AIAA Journal*, 2026-06-24. [Link](https://doi.org/10.2514/1.j067324)
