WAGNER PDKS - IoT Tabanlı Akıllı Personel Takip Sistemi
WAGNER PDKS, endüstriyel tesisler, ofisler ve fabrikalar için Raspberry Pi üzerinde çalışmak üzere geliştirilmiş, "Fişe Tak-Çalıştır" mantığıyla tasarlanan otonom bir Personel Devam Kontrol Sistemidir.

Geleneksel imza föylerini ve manuel takibi ortadan kaldırarak; fiziksel bir Kiosk Ekranı ile personelin saniyeler içinde işlem yapmasını, Canlı Web Paneli ile de yöneticilerin anlık durum takibi ve raporlama yapmasını sağlar.

Öne Çıkan Özellikler
Otonom Kiosk Modu: Cihaz fişe takıldığı an tam ekran (fullscreen) açılır. Sistemin saatine göre otonom olarak "GİRİŞ" veya "ÇIKIŞ" moduna geçer.

Akıllı Karar Mekanizması:

Saat 09:00 sonrası işlemleri otomatik olarak GEÇ GİRİŞ kaydeder.

Saat 17:00 öncesi çıkışları otomatik olarak YARIM GÜN ÇIKIŞ olarak işaretler.

Gün sonu (saat 12:00 sonrası kontrolüyle) gelmeyen personeli otomatik DEVAMSIZ yazar.

Canlı Dashboard (Web Paneli): Yerel ağ üzerinden (IP adresi ile) erişilebilen, Chart.js destekli grafiklerle anlık içerideki kişi sayısını ve departman doluluklarını gösteren yönetim paneli.

Çoklu Yönetici (Multi-Admin): Farklı departman yöneticileri için bağımsız şifreleme ve web paneli üzerinden yeni yönetici/şifre belirleme altyapısı.

 KVKK Uyumlu Arayüz: Fiziksel ekranın loglarında (Son 10 Hareket) personel isimleri otomatik olarak maskelenir (Örn: Ah* Yıl***).

Tek Tıkla Raporlama: İstenilen tarih aralığında tüm hareket dökümlerini saniyeler içinde Excel / CSV formatında dışa aktarabilme.

 Kullanılan Teknolojiler
Yazılım Mimarisi:

Arka Plan (Backend): Python 3, Flask (Web Sunucusu)

Veritabanı: SQLite3

Fiziksel Arayüz (Kiosk): Tkinter

Web Arayüzü (Frontend): HTML5, CSS3, Chart.js

Donanım Mimarisi:

Raspberry Pi (İşletim Merkezi)

Dokunmatik veya harici monitör (Kiosk Ekranı)

4x4 Matrix Tuş Takımı (GPIO Pinleri ile entegre donanımsal şifre girişi)

Kurulum ve Çalıştırma
Proje, "Açık Kaynak" güvenlik standartlarına uygun olarak izole edilmiştir. Kendi donanımınızda çalıştırmak için:

Depoyu bilgisayarınıza/cihazınıza klonlayın:

Bash
git clone https://github.com/KULLANICI_ADIN/personel-takip.git
Gerekli kütüphaneleri yükleyin:

Bash
pip install Flask RPi.GPIO
Sistemi başlatın:

Bash
export DISPLAY=:0
python pdks_v31.py
Web Paneline Erişim: Tarayıcınızdan http://<Cihaz_IP_Adresi>:5000 adresine gidin.

Varsayılan Yönetici Girişi: Kullanıcı Adı: admin | Şifre: Admin1234! (Sisteme ilk girişte ayarlar menüsünden değiştirilmesi önerilir).


[ ] E-Posta ile günlük otomatik rapor gönderimi

Bu proje, donanım ve yazılımın harmanlandığı uçtan uca bir IoT çözümü olarak geliştirilmiştir.
