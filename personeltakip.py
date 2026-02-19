#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RFID RC522 ile Personel Giriş-Çıkış Takip Sistemi
Raspberry Pi 4 için hazırlanmıştır.
Türkçe karakter desteği eklenmiştir.
"""

import sqlite3
from datetime import datetime
import time
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import sys

# Türkçe karakter desteği için encoding ayarı
if sys.version_info[0] < 3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

class PersonelTakipSistemi:
    def __init__(self, veritabani_adi="personel_takip.db"):
        """
        Personel takip sistemini başlatır.
        
        Args:
            veritabani_adi (str): SQLite veritabanı dosya adı
        """
        self.veritabani = veritabani_adi
        self.rfid_okuyucu = SimpleMFRC522()
        self.veritabani_olustur()
        
    def baglanti_olustur(self):
        """UTF-8 destekli veritabanı bağlantısı oluşturur."""
        conn = sqlite3.connect(self.veritabani)
        conn.text_factory = str  # UTF-8 desteği
        return conn
        
    def veritabani_olustur(self):
        """Gerekli veritabanı tablolarını oluşturur."""
        conn = self.baglanti_olustur()
        cursor = conn.cursor()
        
        # Personeller tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personeller (
                kart_id INTEGER PRIMARY KEY,
                ad_soyad TEXT NOT NULL,
                departman TEXT,
                kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Giriş-Çıkış kayıtları tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giris_cikis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kart_id INTEGER NOT NULL,
                islem_tipi TEXT NOT NULL,
                tarih_saat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kart_id) REFERENCES personeller(kart_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Veritabanı hazır.")
        
    def personel_ekle(self, kart_id, ad_soyad, departman=""):
        """
        Yeni personel kaydı oluşturur.
        
        Args:
            kart_id (int): RFID kart ID'si
            ad_soyad (str): Personel adı soyadı
            departman (str): Personelin departmanı
        """
        conn = self.baglanti_olustur()
        cursor = conn.cursor()
        
        try:
            # Türkçe karakterleri doğru şekilde kaydet
            ad_soyad = ad_soyad.strip()
            departman = departman.strip()
            
            cursor.execute('''
                INSERT INTO personeller (kart_id, ad_soyad, departman)
                VALUES (?, ?, ?)
            ''', (kart_id, ad_soyad, departman))
            conn.commit()
            print(f"✓ {ad_soyad} sisteme eklendi. (Kart ID: {kart_id})")
            return True
        except sqlite3.IntegrityError:
            print(f"⚠ Bu kart ID zaten kayıtlı: {kart_id}")
            return False
        except Exception as e:
            print(f"⚠ Kayıt hatası: {e}")
            return False
        finally:
            conn.close()
            
    def personel_bilgisi_al(self, kart_id):
        """
        Kart ID'sine göre personel bilgilerini getirir.
        
        Args:
            kart_id (int): RFID kart ID'si
            
        Returns:
            tuple: (kart_id, ad_soyad, departman) veya None
        """
        conn = self.baglanti_olustur()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT kart_id, ad_soyad, departman
            FROM personeller
            WHERE kart_id = ?
        ''', (kart_id,))
        
        sonuc = cursor.fetchone()
        conn.close()
        return sonuc
        
    def son_islem_tipi(self, kart_id):
        """
        Personelin son işlem tipini getirir (giriş veya çıkış).
        
        Args:
            kart_id (int): RFID kart ID'si
            
        Returns:
            str: 'giris' veya 'cikis' veya None
        """
        conn = self.baglanti_olustur()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT islem_tipi
            FROM giris_cikis
            WHERE kart_id = ?
            ORDER BY tarih_saat DESC
            LIMIT 1
        ''', (kart_id,))
        
        sonuc = cursor.fetchone()
        conn.close()
        return sonuc[0] if sonuc else None
        
    def islem_kaydet(self, kart_id, islem_tipi):
        """
        Giriş veya çıkış işlemini kaydeder.
        
        Args:
            kart_id (int): RFID kart ID'si
            islem_tipi (str): 'giris' veya 'cikis'
        """
        conn = self.baglanti_olustur()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO giris_cikis (kart_id, islem_tipi)
            VALUES (?, ?)
        ''', (kart_id, islem_tipi))
        
        conn.commit()
        conn.close()
        
    def kart_okut(self, kart_id):
        """
        Okutulan kartı işler ve giriş-çıkış kaydı oluşturur.
        
        Args:
            kart_id (int): RFID kart ID'si
        """
        personel_bilgisi = self.personel_bilgisi_al(kart_id)
        
        if personel_bilgisi is None:
            print(f"\n⚠ Tanınmayan kart! (ID: {kart_id})")
            print("Bu kartı sisteme eklemek ister misiniz? (e/h): ", end="", flush=True)
            
            try:
                cevap = input().lower().strip()
                
                if cevap == 'e':
                    print("Ad Soyad: ", end="", flush=True)
                    ad_soyad = input().strip()
                    
                    print("Departman (opsiyonel): ", end="", flush=True)
                    departman = input().strip()
                    
                    if self.personel_ekle(kart_id, ad_soyad, departman):
                        print("\n✓ Personel başarıyla eklendi!")
                        print("Tekrar kart okutarak giriş yapabilirsiniz.\n")
                    return
                else:
                    print("İşlem iptal edildi.\n")
                    return
            except Exception as e:
                print(f"\n⚠ Hata: {e}\n")
                return
        
        # Personel bilgileri
        _, ad_soyad, departman = personel_bilgisi
        
        # Son işlemi kontrol et
        son_islem = self.son_islem_tipi(kart_id)
        
        # Giriş-çıkış mantığı
        if son_islem is None or son_islem == 'cikis':
            islem_tipi = 'giris'
            mesaj = "GİRİŞ"
            emoji = "-->"
        else:
            islem_tipi = 'cikis'
            mesaj = "ÇIKIŞ"
            emoji = "<--"
        
        # İşlemi kaydet
        self.islem_kaydet(kart_id, islem_tipi)
        
        # Ekrana yazdır
        simdi = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(f"\n{emoji} {mesaj}")
        print(f"─────────────────────────────")
        print(f"Personel: {ad_soyad}")
        if departman:
            print(f"Departman: {departman}")
        print(f"Kart ID: {kart_id}")
        print(f"Tarih/Saat: {simdi}")
        print(f"─────────────────────────────\n")
        
    def calistir(self):
        """Ana döngüyü başlatır ve sürekli kart okur."""
        print("\n" + "="*50)
        print("PERSONEL GİRİŞ-ÇIKIŞ TAKİP SİSTEMİ")
        print("="*50)
        print("\nSistem hazır. Kartınızı okutun...")
        print("Çıkmak için CTRL+C tuşlayın.\n")
        
        try:
            while True:
                # Kart okumayı bekle
                print("Kart bekleniyor...", end="\r", flush=True)
                kart_id, metin = self.rfid_okuyucu.read()
                
                # Kartı işle
                self.kart_okut(kart_id)
                
                # Aynı kartın tekrar okumasını önlemek için kısa bekleme
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\nSistem kapatılıyor...")
        finally:
            try:
                GPIO.cleanup()
                print("Temizlik tamamlandı. İyi günler!")
            except:
                print("İyi günler!")
            
    def rapor_olustur(self, tarih=None):
        """
        Belirtilen tarih için giriş-çıkış raporunu gösterir.
        Tarih belirtilmezse bugünün raporunu verir.
        
        Args:
            tarih (str): 'YYYY-MM-DD' formatında tarih
        """
        if tarih is None:
            tarih = datetime.now().strftime("%Y-%m-%d")
            
        conn = self.baglanti_olustur()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                p.ad_soyad,
                p.departman,
                gc.islem_tipi,
                gc.tarih_saat
            FROM giris_cikis gc
            JOIN personeller p ON gc.kart_id = p.kart_id
            WHERE DATE(gc.tarih_saat) = ?
            ORDER BY gc.tarih_saat
        ''', (tarih,))
        
        kayitlar = cursor.fetchall()
        conn.close()
        
        print(f"\n{'='*70}")
        print(f"GİRİŞ-ÇIKIŞ RAPORU - {tarih}")
        print(f"{'='*70}")
        
        if not kayitlar:
            print("Bu tarih için kayıt bulunamadı.")
        else:
            print(f"{'Personel':<25} {'Departman':<15} {'İşlem':<10} {'Saat':<15}")
            print("-" * 70)
            for ad_soyad, departman, islem_tipi, tarih_saat in kayitlar:
                saat = tarih_saat.split()[1][:5]
                islem = "GİRİŞ" if islem_tipi == "giris" else "ÇIKIŞ"
                departman_str = departman if departman else '-'
                print(f"{ad_soyad:<25} {departman_str:<15} {islem:<10} {saat:<15}")
        
        print("="*70 + "\n")
        
    def tum_personeli_listele(self):
        """Sistemdeki tüm personelleri listeler."""
        conn = self.baglanti_olustur()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT kart_id, ad_soyad, departman, kayit_tarihi
            FROM personeller
            ORDER BY ad_soyad
        ''')
        
        personeller = cursor.fetchall()
        conn.close()
        
        print(f"\n{'='*70}")
        print("KAYITLI PERSONELLER")
        print(f"{'='*70}")
        
        if not personeller:
            print("Henüz kayıtlı personel yok.")
        else:
            print(f"{'Ad Soyad':<25} {'Departman':<15} {'Kart ID':<15} {'Kayıt':<15}")
            print("-" * 70)
            for kart_id, ad_soyad, departman, kayit_tarihi in personeller:
                departman_str = departman if departman else '-'
                kayit_tarih = kayit_tarihi.split()[0]
                print(f"{ad_soyad:<25} {departman_str:<15} {kart_id:<15} {kayit_tarih:<15}")
        
        print("="*70 + "\n")


def menu():
    """Ana menü gösterir."""
    sistem = PersonelTakipSistemi()
    
    while True:
        print("\n" + "="*50)
        print("PERSONEL TAKİP SİSTEMİ - ANA MENÜ")
        print("="*50)
        print("1. Sistem Başlat (Kart Okuma)")
        print("2. Yeni Personel Ekle")
        print("3. Personel Listesi")
        print("4. Günlük Rapor")
        print("5. Tarihli Rapor")
        print("6. Çıkış")
        print("="*50)
        
        secim = input("\nSeçiminiz (1-6): ").strip()
        
        if secim == "1":
            sistem.calistir()
            
        elif secim == "2":
            print("\nKartı okutun...")
            try:
                kart_id, _ = sistem.rfid_okuyucu.read()
                print(f"Kart ID: {kart_id}")
                
                print("Ad Soyad: ", end="", flush=True)
                ad_soyad = input().strip()
                
                print("Departman (opsiyonel): ", end="", flush=True)
                departman = input().strip()
                
                sistem.personel_ekle(kart_id, ad_soyad, departman)
                time.sleep(1)
            except KeyboardInterrupt:
                print("\n⚠ İşlem iptal edildi.")
            except Exception as e:
                print(f"⚠ Hata: {e}")
                
        elif secim == "3":
            sistem.tum_personeli_listele()
            input("\nDevam etmek için Enter'a basın...")
            
        elif secim == "4":
            sistem.rapor_olustur()
            input("\nDevam etmek için Enter'a basın...")
            
        elif secim == "5":
            tarih = input("Tarih (YYYY-MM-DD): ").strip()
            sistem.rapor_olustur(tarih)
            input("\nDevam etmek için Enter'a basın...")
            
        elif secim == "6":
            print("\nProgram sonlandırılıyor...")
            try:
                GPIO.cleanup()
            except:
                pass
            print("İyi günler!")
            break
            
        else:
            print("\n⚠ Geçersiz seçim! Lütfen 1-6 arası bir değer girin.")
            time.sleep(1)


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\n\nProgram sonlandırılıyor...")
        try:
            GPIO.cleanup()
        except:
            pass
        print("İyi günler!")
    except Exception as e:
        print(f"\n⚠ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        try:
            GPIO.cleanup()
        except:
            pass
