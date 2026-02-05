# Özel Etiketler

* Yazarlar: Kefas Lungu

Not: Bu eklenti NVDA 2025.1 veya daha yeni bir sürümünü gerektirir.

## Genel Bakış

Özel Etiketler, etiketlenmemiş denetimler için özel etiketler eklemenizi ve mevcut olanları düzenlemenizi sağlayan bir NVDA eklentisidir. Bu özellik, üzerinde etiket bulunmayan veya NVDA’nın düzgün tanımlayamadığı düğmeler ya da denetimler içeren uygulamalar için özellikle kullanışlıdır.

## Özellikler

* Etiketlenmemiş denetimlere özel etiketler atama
* Mevcut özel etiketleri düzenleme
* Artık ihtiyaç duyulmadığında özel etiketleri kaldırma
* Tüm etiketleri bir ayarlar paneli üzerinden yönetme
* Etiketler, daha iyi düzenleme için uygulama bazında saklanır ve daha sonra paylaşmak üzere dışa aktarılıp içe aktarılabilir

## Desteklenen Denetim Türleri

Aşağıdaki denetim türleri etiketlenebilir:

* Düğmeler
* Menü düğmeleri
* Açma/kapatma düğmeleri
* Onay kutuları
* Radyo düğmeleri
* Açılır kutular
* Kaydırıcılar
* Sekmeler
* Menü öğeleri

## Kısayollar

* NVDA+Control+L: Geçerli denetim için özel etiket ayarla veya düzenle
* NVDA+Control+Delete: Geçerli denetimdeki özel etiketi kaldır
* NVDA+Control+J: Geçerli denetimde özel etiket olup olmadığını denetle
* NVDA+Control+; (noktalı virgül): Özel etiketler ayarlarını aç

## Kullanım

### Özel Etiket Ayarlama

1. Etiketlemek istediğiniz bir denetime odaklanın
2. NVDA+Control+L tuşlarına basın
3. Denetim hakkında bilgi gösteren bir iletişim kutusu açılacaktır
4. Metin alanına istediğiniz etiketi girin
5. Etiketi kaydetmek için Tamam’a basın

### Mevcut Bir Etiketi Düzenleme

1. Özel etiketi olan bir denetime odaklanın
2. NVDA+Control+L tuşlarına basın
3. Metin alanındaki etiketi değiştirin
4. Değişiklikleri kaydetmek için Tamam’a basın

### Etiketi Kaldırma

Bir etiketi iki şekilde kaldırabilirsiniz:

1. Denetime odaklanıp NVDA+Control+Delete tuşlarına basarak
2. Ya da etiket iletişim kutusunu açıp (NVDA+Control+L) Kaldır düğmesine basarak

### Tüm Etiketleri Yönetme

1. Özel Etiketler ayar panelini açmak için NVDA+Control+; tuşlarına basın
2. Uygulamaya göre düzenlenmiş etiketlere göz atın
3. Gerektikçe Düzenle, Kaldır, Uygulamayı Kaldır veya Tümünü Kaldır düğmelerini kullanın

## Ayarlar Paneli

Özel Etiketler ayar paneline şu yollarla erişebilirsiniz:

* Klavye kısayolu NVDA+Control+;
* NVDA menüsü > Tercihler > Ayarlar > Özel Etiketler

Panel, tüm özel etiketleri uygulamaya göre ağaç görünümünde gösterir. Şunları yapabilirsiniz:

* **Düzenle**: Seçili etiketi değiştir
* **Kaldır**: Seçili etiketi sil
* **Uygulamayı Kaldır**: Seçili uygulamaya ait tüm etiketleri sil
* **Tümünü Kaldır**: Tüm özel etiketleri sil

## Depolama

Etiketler, NVDA’nın yapılandırma dizininde `customLabels` klasörü altında JSON dosyaları olarak saklanır. Her uygulamanın kendi JSON dosyası vardır; bu da belirli uygulamalar için etiketleri yedeklemeyi veya paylaşmayı kolaylaştırır.

## Değişiklik Günlüğü

### Sürüm 2026.0

* İlk sürüm
