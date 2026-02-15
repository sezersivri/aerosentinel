---
title: "Yüksek Hızlı Füzelerde Aerodinamik Isınma Tahmini için Araştırma Özeti"
date: 2026-02-15
tags:
  - "Aerothermodynamics"
  - "Heat Flux Prediction"
  - "Neural Network Surrogates"
  - "Data-Driven Methods"
  - "Hypersonic Flow"
  - "Thermal Protection Systems"
summary: "Bu araştırma özeti, yüksek hızlı füzelerde aerodinamik ısınma tahmini ve ilgili yapay zeka uygulamaları üzerine yapılan güncel çalışmaları..."
draft: false
papers_count: 6
core_papers: 3
peripheral_papers: 3
ai_model: "Gemini 2.5 Flash"
ShowToc: true
TocOpen: false
---

## Araştırma Özeti

Bu araştırma özeti, yüksek hızlı füzelerde aerodinamik ısınma tahmini ve ilgili yapay zeka uygulamaları üzerine yapılan güncel çalışmaları değerlendirmektedir. Makaleler, yüksek sıcaklık gaz dinamiklerinden yüzey sıcaklık kontrolüne, hipersonik akışlarda makine öğrenimi tabanlı tahmin modellerine ve sınır tabaka geçişi ile şok-sınır tabaka etkileşimlerinin karmaşık dinamiklerine kadar geniş bir yelpazeyi kapsamaktadır. Temel odak, aerodinamik ısınma tahmini ve bu alanda yapay zeka/makine öğrenimi yöntemlerinin kullanımına yöneliktir.

> **Araştırma Trendleri:** Bu makaleler, yüksek hızlı uçuş için doğru aerotermodinamik tahminlere artan bir vurgu olduğunu göstermektedir. Yüksek sıcaklık gaz dinamiklerinin temel anlayışı ve yüzey termal kontrolü için gelişmiş deneysel tekniklerin yanı sıra, hesaplama açısından verimli akış alanı ve ısıtma tahminleri için makine öğreniminin hızla benimsenmesi açık bir eğilimdir. Sınır tabaka geçişi ve şok etkileşimleri gibi karmaşık akış fenomenleri üzerine devam eden araştırmalar, hipersonik araçlar için sağlam tasarımlar elde etmedeki zorlukların altını çizmektedir.

---

## Temel Odak Analizi

### 1. Experimental Measurements and Mechanism Optimization Research on Dissociation of High-Temperature CO2
**Tip:** 🧪 Deneysel | **İlgililik:** 75/100

> **Bu çalışma, yüksek sıcaklık CO2 ayrışmasının deneysel ölçümlerini ve mekanizma optimizasyonunu sunarak Mars atmosferine yüksek hızlı giriş sırasındaki ısı transferi tahminleri için kritik veriler sağlamaktadır.**

**Temel Bulgular:**
CO2 ayrışma davranışları için 3000–6000 K aralığında ölçümler ile model tahminleri arasında belirgin sapmalar bulunmuştur. Güncellenmiş Arrhenius denklemi ile revize edilmiş mekanizma, 2980–6030 K sıcaklık aralığında daha doğru CO2 ayrışma davranışları öngörmektedir.

**Temel Sayılar:** Sıcaklık aralığı: 3030–5990 K (kalibrasyon), 2980–6030 K (güncellenmiş Arrhenius), 3000–6000 K (tahmin doğruluğu).

<details>
<summary><strong>Metodoloji Detayları</strong></summary>

CO2 ayrışma sürecinde sıcaklık, CO ve CO2 konsantrasyonlarını eş zamanlı ölçmek için CO2-TDLAS ve CO-TDLAS sistemleri kullanılarak deneysel ölçümler yapılmıştır. Anahtar reaksiyonları belirlemek için hassasiyet analizi uygulanmış ve reaksiyon hızı katsayısı güncellenmiştir.

</details>

> **Neden Önemli:** Yüksek sıcaklık gaz kimyasının doğru karakterizasyonu, hipersonik araçların ve yeniden giriş kapsüllerinin termal koruma sistemleri için kritik olan aerodinamik ısınma tahminlerinin hassasiyetini doğrudan etkiler. Bu çalışma, geniş bir sıcaklık aralığında düşük belirsizlikle reaksiyon hızı katsayılarını belirlemek için işlevsel bir metodoloji sunmaktadır.

*Bağlantı: Bu makale, yüksek sıcaklık gaz dinamiklerinin deneysel olarak anlaşılması ve modellenmesi yoluyla aerotermodinamik ısınma tahminlerinin temelini güçlendirmektedir. Makine öğrenimi tabanlı vekil modeller için doğru fiziksel verilerin ve mekanizmaların sağlanması açısından dolaylı ancak kritik bir bağlantı sunar.*

> ⚠️ **Limitations:** Çalışma, doğrudan bir ısı akısı tahmin modeli geliştirmek yerine, yüksek sıcaklık CO2 ayrışma mekanizmasının deneysel ölçümüne ve optimizasyonuna odaklanmıştır. Yalnızca CO2 kimyasına odaklanması, genel hava kimyası için ek araştırmalar gerektirebilir.

---

### 2. Fast prediction of chemically reactive rarefied hypersonic flows using boundary condition-based machine learning algorithm
**Tip:** 🤖 MO/Isinma Tahmini | **İlgililik:** 88/100

> **Bu çalışma, yüksek irtifa, seyreltilmiş hipersonik yeniden giriş akışlarını hızlı bir şekilde tahmin etmek için sınır koşulu tabanlı makine öğrenimi (BCML) ve derin sinir ağı (ChemDNN) modellerini içeren bir makine öğrenimi çerçevesi geliştirmektedir.**

**Temel Bulgular:**
BCML modeli, Mach 8 ila 35 aralığındaki hipersonik akış koşulları için DSMC tahminleriyle iyi bir uyum sağlamakta ve hesaplama maliyetinin yalnızca bir kısmını gerektirmektedir. ChemDNN modeli, beş tür hava kimyası modeli için türlerin mol fraksiyonlarını etkili bir şekilde tahmin ederek denge dışı yüksek entalpili reaksiyonlu akışları verimli bir şekilde modellemektedir. Ayrıca, yeniden giriş geometrisinin yüzeyindeki ısı akısı ve basınç katsayılarını tahmin eden ayrı bir derin sinir ağı modeli de sunulmuştur.

**Temel Sayılar:** Mach aralığı: 8 ila 35. Hesaplama maliyeti: DSMC'nin 'bir kısmı'.

<details>
<summary><strong>Metodoloji Detayları</strong></summary>

Çalışma, akış alanlarını tahmin etmek için sınır koşulu tabanlı makine öğrenimi (BCML) algoritmasını ve çeşitli türlerin mol fraksiyonlarını hesaplamak için derin sinir ağı tabanlı bir model olan ChemDNN'i içeren bir makine öğrenimi çerçevesi kullanmaktadır. BCML modeli, DSMC kodu tarafından üretilen akış alanı verileri kullanılarak eğitilmiştir.

</details>

> **Neden Önemli:** Bu makine öğrenimi çerçevesi, hipersonik araçların termal koruma sistemlerinin tasarımı için kritik girdiler olan ısı akısı ve basınç katsayılarının hızlı ve doğru tahminini sağlayarak tasarım döngülerini önemli ölçüde hızlandırabilir. Geleneksel yöntemlere göre hesaplama maliyetinde büyük bir azalma sunar.

*Bağlantı: Bu makale, aerodinamik ısınma tahmini için makine öğrenimi ve derin öğrenme yöntemlerinin doğrudan bir uygulamasını sunarak tez alanımla yüksek düzeyde uyumludur. Özellikle ısı akısı katsayılarının tahminine odaklanması, Gauss süreci tabanlı vekil modellerin potansiyelini desteklemektedir.*

> ⚠️ **Limitations:** Model, doğrudan Gauss süreci vekil modelleri yerine sınır koşulu tabanlı makine öğrenimi ve derin sinir ağlarını kullanmaktadır. Seyreltilmiş akışlara odaklanması, yoğun akış rejimleri için ek doğrulamalar gerektirebilir.

---

### 3. Experimental generation of non-uniform surface temperature distributions in high-speed flow
**Tip:** 🧪 Deneysel | **İlgililik:** 78/100

> **Bu çalışma, yüksek hızlı akışta düz bir plaka üzerinde pasif olarak kontrol edilen, tekdüze olmayan yüzey sıcaklığı dağılımlarının deneysel olarak oluşturulmasını ve fiziksel olarak bilgilendirilmiş bir termal modelle tahminini sunmaktadır.**

**Temel Bulgular:**
Mach 2.75 süpersonik rüzgar tünelinde yapılan deneyler, farklı termal özelliklere sahip malzeme şeritleri (bakır ve MACOR) arasında sıcaklık değişimleri göstererek pasif yüzey sıcaklığı kontrolünü doğrulamıştır. Fiziksel olarak bilgilendirilmiş termal model, deneysel sonuçlarla nicel olarak uyumlu tekdüze olmayan yüzey sıcaklığı dağılımları tahmin etmiştir.

**Temel Sayılar:** Mach 2.75, 'şeritler arasında sıcaklık değişimleri'.

<details>
<summary><strong>Metodoloji Detayları</strong></summary>

Düz bir plaka test makalesinde, farklı termal özelliklere sahip malzeme şeritleri kullanılarak tekdüze olmayan yüzey sıcaklığı profilleri oluşturulmuştur. Yüzey sıcaklığı ölçümleri için kızılötesi termografi kullanılmış ve rüzgar tüneli koşullarından türetilen sınır koşullarına sahip fiziksel olarak bilgilendirilmiş bir termal model kullanılmıştır.

</details>

> **Neden Önemli:** Yüksek hızlı akışlarda yüzey sıcaklığı dağılımlarını doğru bir şekilde kontrol etme ve tahmin etme yeteneği, termal koruma sistemlerinin tasarımı ve akış kontrol yöntemlerinin geliştirilmesi için hayati öneme sahiptir. Bu çalışma, gelecekteki sınır tabaka geçiş geciktirme deneyleri için temel bir doğrulama sağlamaktadır.

*Bağlantı: Bu makale, aerodinamik ısınmanın bir sonucu olan yüzey sıcaklığı dağılımlarının deneysel ölçümüne ve fiziksel modellemesine odaklanmaktadır. Bu tür deneysel veriler, makine öğrenimi tabanlı vekil modellerin eğitimi ve doğrulaması için değerli bir zemin oluşturabilir, özellikle termal koruma sistemlerinin etkinliğini değerlendirmede.*

> ⚠️ **Limitations:** Çalışma, doğrudan ısı akısı tahmini yerine yüzey sıcaklığı dağılımlarının oluşturulmasına ve kontrolüne odaklanmıştır. Süpersonik akış (Mach 2.75) koşullarında yapılmış olup, hipersonik rejim için ek araştırmalar gerektirebilir.

---

## Geniş Bağlam

Hipersonik akış fiziği alanındaki çevresel çalışmalar, yüksek hızlı araçların aerodinamik performansını etkileyen temel fenomenlere ışık tutmaktadır. Örneğin, duvar eğriliğinin hipersonik sınır tabakalarındaki Mack modu evrimi üzerindeki etkileri, sınır tabaka geçişinin karmaşıklığını vurgulamaktadır [2]. Dışbükey yüzeylerin Mack modunu stabilize ettiği, içbükey yüzeylerin ise destabilize ettiği bulgusu, hipersonik konfigürasyonların tasarımında kritik öneme sahiptir. Benzer şekilde, hipersonik akışta şok salınımlarına maruz kalan geçişli şok/sınır tabaka etkileşiminin dinamikleri, türbülanslı sınır tabakasında dalga iletimi ve bozukluk amplifikasyonunun karmaşık mekanizmalarını ortaya koymaktadır [5]. Bu tür etkileşimler, hipersonik araçların aerodinamik yükleri ve yapısal bütünlüğü için önemli sonuçlar doğurabilir. Ayrıca, koni-silindir-flare konfigürasyonu üzerindeki serbest akış akustik bozukluklarının alıcılığı ve evrimi üzerine yapılan çalışmalar, sınır tabaka ayrılması, kararsızlık büyümesi ve doğrusal olmayan süreçlerin anlaşılmasına katkıda bulunmaktadır [6]. Özellikle, sıcak duvar koşullarının ayrılma kabarcığı boyutunu önemli ölçüde artırdığı ve kararsızlık amplifikasyonunu etkilediği gözlemlenmiştir. Bu çalışmalar, doğrudan aerodinamik ısınmaya odaklanmasa da, hipersonik araçların genel akış fiziği ve performansını anlamak için temel bir zemin oluşturmakta ve dolaylı olarak termal yönetim stratejilerini etkileyebilecek karmaşık akış olaylarını aydınlatmaktadır.

---

*Bu arastirma ozeti [Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) tarafindan olusturulmus ve AeroSentinel v2.4.0 tarafindan duzenlenmistir.*

---

## Kaynaklar

1. Tielou Liu, Yanfeng He, Ting Si et al., "Experimental Measurements and Mechanism Optimization Research on Dissociation of High-Temperature CO2," *AIAA Journal*, 2026-02-03. [Link](https://doi.org/10.2514/1.j066439)
2. Chunhui Liu, Shenghao Yu, Jisen Yuan et al., "Effects of Curvature on Mack Mode Evolution in Hypersonic Boundary Layer," *AIAA Journal*, 2026-02-12. [Link](https://doi.org/10.2514/1.j066641)
3. R. Prakash, Sumati Raghav, Tapan K. Mankodi et al., "Fast prediction of chemically reactive rarefied hypersonic flows using boundary condition-based machine learning algorithm," *Physics of Fluids*, 2026-02-01. [Link](https://doi.org/10.1063/5.0309330)
4. Kazuki Ozawa, Paul J. Bruce, "Experimental generation of non-uniform surface temperature distributions in high-speed flow," *Experiments in Fluids*, 2026-02-01. [Link](https://doi.org/10.1007/s00348-026-04177-3)
5. Adriano Cerminara, Deborah Levin, Vassilis Theofilis, "Receptivity of a Transitional Shock/Boundary-Layer Interaction to Shock Oscillations in Hypersonic Flow," *AIAA Journal*, 2026-02-01. [Link](https://doi.org/10.2514/1.j066062)
6. Chandan Kumar, S. Unnikrishnan, Datta V. Gaitonde, "Receptivity and evolution of free-stream acoustic disturbances in hypersonic flow over cone–cylinder–flare," *Journal of Fluid Mechanics*, 2026-02-06. [Link](https://doi.org/10.1017/jfm.2026.11156)
