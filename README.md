Personel Takip Sistemi - Blue Enterprise Edition

Raspberry Pi üzerinde çalışan, gelişmiş otomasyonlara ve modern bir kullanıcı arayüzüne sahip akıllı Personel Devam Kontrol Sistemi (PDKS). Bu proje, donanım ve yazılımın tam entegrasyonu ile gerçek bir endüstriyel çözüm sunmak üzere geliştirilmiştir.

Öne Çıkan Özellikler:

Akıllı Zaman Yönetimi:07:00-12:00 arası otomatik "GİRİŞ", 13:00-19:00 arası otomatik "ÇIKIŞ" moduna geçer.
Otomatik Yoklama Zekası:Her gün saat 12:00'da veritabanını tarar, o gün giriş yapmayan aktif personelleri tespit edip otomatik olarak "DEVAMSIZ" kaydı düşer.
KVKK Uyumlu Arayüz:Dış ekranda personellerin isim ve soyisimleri maskelenerek (Örn: Fu** Sa****) gösterilir.
Tek Tıkla Raporlama:Yönetici panelinden tüm giriş-çıkış hareketleri anında `.csv` (Excel) formatında raporlanabilir.
Gelişmiş Yönetici Paneli:Sadece şifre ile girilebilen, personel ekleme/silme ve "Aktif/İzinli" durumu ayarlayabilen kontrol merkezi.

Kullanılan Teknolojiler

Yazılım:Python 3, Tkinter (GUI), SQLite3 (Veritabanı), Threading
Donanım:Raspberry Pi, 4x4 Membran Tuş Takımı, GPIO Bağlantıları
Veri Çıktısı:Yerleşik CSV Modülü

Tasarım Dili

Proje, kurumsal ve göz yormayan bir deneyim sunmak için özel "Blue Enterprise" renk paleti (Buz Mavisi ve Gök Mavisi tonları) kullanılarak tasarlanmıştır. Cihaz uykuya geçmez, Threading yapısı sayesinde arka planda tuş takımını dinlerken arayüzdeki dijital saat kesintisiz akmaya devam eder.
