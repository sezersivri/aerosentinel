---
title: "Veri Destekli PINN'ler ile RANS Turbulans Kapanımında Doğruluk Artışı"
date: 2026-05-02
tags:
  - "Neural Network Surrogates"
  - "Deep Learning"
  - "Data-Driven Methods"
  - "Turbulent Heating"
  - "Surrogate Modeling"
summary: "Zhang ve ekibi, geleneksel RANS kapanımlarının ortalama akış ve türbülans istatistiklerindeki yetersizliklerini gidermek amacıyla, dairesel bir..."
draft: false
paper_type: "ml_aerodynamics"
relevance_score: 35
ai_model: "Gemini 2.5 Flash"
---

**Type:** 🤖 MO/Aerodinamik | **Relevance:** 35/100

Zhang ve ekibi, geleneksel RANS kapanımlarının ortalama akış ve türbülans istatistiklerindeki yetersizliklerini gidermek amacıyla, dairesel bir silindir etrafındaki akışı ele alıyor. Çalışma, 3900 ila 100,000 Reynolds sayıları ve 0 ila 0.3 Mach sayıları aralığını kapsayan, sıkıştırılamaz ve zayıf sıkıştırılabilir rejimlerdeki akışları inceliyor. Araştırmacılar, hidrodinamik PIV, aerodinamik PIV ve yüksek doğruluklu DNS/LES verilerini bir araya getirerek çapraz doğrulanmış kapsamlı bir veri seti oluşturuyor. Bu veri seti, veri odaklı bir türbülans kapanımı geliştirmek için temel oluşturuyor. Yaklaşımları, sadece sınır bilgilerini kullanarak hız alanını ve Reynolds gerilimi zorlamasını çıkarmak için kapalı olmayan RANS denklemleriyle eğitilmiş Fizik-Bilgili Sinir Ağlarını (PINN'ler) kullanmak üzerine kurulu.

Toplanan verilerin analizi, incelenen parametre uzayında Reynolds gerilmelerinin evrensel bir dağılımını ortaya koyarak veri odaklı kapanımın temelini oluşturuyor. PINN'lerden türetilen kapanım, hem ileriye dönük bir PINN çözücüsüne hem de OpenFOAM sayısal çözücüsüne entegre edildiğinde, RANS tahminlerini geleneksel modellere kıyasla önemli ölçüde iyileştiriyor. Bu iyileşme, hem ortalama akış hem de türbülans istatistikleri için daha doğru sonuçlar sağlıyor.

Bu çalışma, yüksek hızlı aerotermodinamik veya ısı transferine doğrudan odaklanmasa da, PINN'ler aracılığıyla veri odaklı türbülans modellemesi kullanarak RANS doğruluğunu artırmak için sağlam bir metodoloji sunuyor. Seyrek deneysel ve yüksek doğruluklu simülasyon verilerini kullanarak akışkanlar dinamiğindeki tahmin yeteneklerini geliştiren bu yaklaşım, genel CFD topluluğu için, özellikle de yönetici denklemlerdeki kapalı olmayan terimleri çıkarmak için PINN'lerin kullanımı açısından değerlidir.

---

*Bu makale incelemesi [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v3.0.0 tarafindan duzenlenmistir.*

---

## Kaynak

1. Zhen Zhang, Khemraj Shukla, Zhicheng Wang et al., "Turbulence closure in Reynolds-averaged Navier–Stokes and flow inference around a cylinder using physics-informed neural networks and sparse experimental data," *Journal of Fluid Mechanics*, 2026-04-27. [Link](https://doi.org/10.1017/jfm.2026.11471)
