---
title: "Hipersonik Füzelerde Termal Yük Belirsizliğini Azaltan Vekil Modeller"
date: 2026-07-11
tags:
  - "Gaussian Process Surrogates"
  - "Aerothermodynamics"
  - "Hypersonic Aerodynamics"
  - "Heat Flux Prediction"
  - "Surrogate Modeling"
summary: "C. El Khoury ve Jean-Pierre Hickey, hipersonik konik-flare konfigürasyonları için deterministik HAD tahminlerindeki büyük varyasyon ve..."
draft: false
paper_type: "multi_method"
relevance_score: 90
ai_model: "Gemini 2.5 Flash"
---

**Type:** 🔬 Coklu Yontem | **Relevance:** 90/100

C. El Khoury ve Jean-Pierre Hickey, hipersonik konik-flare konfigürasyonları için deterministik HAD tahminlerindeki büyük varyasyon ve belirsizlikleri ele alıyor. Çalışma, serbest akış koşulları, duvar sıcaklığı, taşıma parametreleri ve burun kütlüğü gibi girdilerdeki aleatorik değişkenliğin tasarım açısından önemli niceliklere (termal yükler ve ayrılma davranışı dahil) nasıl yayıldığını nicel olarak belirliyor. Bu amaçla, SU2 çözücüsünü (kararlı sıkıştırılabilir RANS ve SST türbülans modeli ile) DAKOTA ile birleştiren, müdahaleci olmayan bir belirsizlik yayılımı çerçevesi kullanılıyor. Latin Hiperküp Örneklemesi ile yedi boyutlu girdi uzayından 238 gerçekleştirim üretiliyor ve bunlar Bayesci adaptif örnekleme ile toplam 269 simülasyona çıkarılıyor.

Her bir simülasyondan altı adet ilgi niceliği çıkarılıyor ve bir Kriging vekil modelini eğitmek için kullanılıyor. Model doğrulamasının ardından, vekil modelin 75.000 Monte Carlo değerlendirmesi, ilgi niceliklerinin olasılık dağılımlarının ve Sobol küresel hassasiyet indekslerinin verimli bir şekilde tahmin edilmesini sağlıyor. Sonuçlar, sınır tabakası termodinamiğinin termal yükler ve ayrılma davranışı üzerindeki baskın etkilerini vurguluyor. Bu çalışma, hipersonik konik-flare RANS simülasyonları için tekrarlanabilir, vekil tabanlı bir belirsizlik nicelendirme iş akışını gösteriyor.

Bu iş akışı, çalışma koşullarındaki ve geometrideki belirsizliklerin önemli olduğu hipersonik araçların sağlam tasarımı ve analizi için hayati önem taşıyor. Termal yükler ve akış ayrılması gibi kritik performans metrikleri üzerindeki girdi değişkenliğinin etkisini anlamak için hesaplama açısından verimli bir yol sunarak, daha güvenilir tahminlere ve tasarımlara zemin hazırlıyor.

---

*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v3.0.0 tarafindan duzenlenmistir.*

---

## Kaynak

1. C. El Khoury, Jean-Pierre Hickey, "Surrogate-based uncertainty quantification framework for Reynolds-averaged Navier-Stokes simulations of hypersonic large cone-flares," *Aerospace Science and Technology*, 2026-07-07. [Link](https://doi.org/10.1016/j.ast.2026.113130)
