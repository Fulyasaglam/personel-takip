#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import threading
import time
import RPi.GPIO as GPIO
import socket 
import csv 

class PersonelSistemi:
    def __init__(self, root):
        self.root = root
        self.root.title("PDKS Blue Enterprise")
        self.root.geometry("1024x600")
        self.root.configure(bg="#f0f9ff")

        # Ayarlar
        self.ADMIN_SIFRE = "1234"
        self.input_buffer = ""
        self.db_yolu = "personel_takip.db"
        self.running = True
        self.secili_islem = None 
        self.yoklama_tarihi = "" # Otomatik yoklama kontrolü için eklendi

        # Mavi Renk Paleti (Kesinlikle Korundu)
        self.c_bg = "#f0f9ff"
        self.c_light = "#e0f2fe"
        self.c_primary = "#0ea5e9"
        self.c_dark = "#0369a1"
        self.c_deep = "#0c4a6e"
        self.c_alert = "#1e40af"
        self.c_white = "#ffffff"

        # GPIO
        self.rows = [5, 6, 13, 19]
        self.cols = [1, 7, 8, 25]

        self.veritabani_kontrol()
        self.setup_gpio()
        self.arayuz_olustur()
        self.dongu_guncelle()

        self.thread = threading.Thread(target=self.keypad_dongusu, daemon=True)
        self.thread.start()

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except: return "127.0.0.1"

    def maskele(self, metin):
        if not metin: return ""
        parcalar = metin.split()
        maskeli_parcalar = []
        for p in parcalar:
            if len(p) > 2: maskeli_parcalar.append(p[:2] + "*" * (len(p) - 2))
            else: maskeli_parcalar.append(p + "*")
        return " ".join(maskeli_parcalar)

    def veritabani_kontrol(self):
        with sqlite3.connect(self.db_yolu) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS personeller 
                            (rfid_id TEXT PRIMARY KEY, ad TEXT, soyad TEXT, departman TEXT, durum TEXT DEFAULT 'Aktif')''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS hareketler 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, rfid_id TEXT, 
                             tarih TEXT, saat TEXT, islem_tipi TEXT)''')
            conn.commit()

    def setup_gpio(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        for r in self.rows: GPIO.setup(r, GPIO.OUT, initial=GPIO.LOW)
        for c in self.cols: GPIO.setup(c, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def yoklama_al(self, bugun):
        """Gelmeyen personelleri tespit eder ve DEVAMSIZ olarak işaretler."""
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                # 1. Tüm aktif personelleri bul
                cursor.execute("SELECT rfid_id FROM personeller WHERE durum='Aktif'")
                aktifler = [r[0] for r in cursor.fetchall()]
                
                # 2. Bugün 'GİRİŞ' yapanları bul
                cursor.execute("SELECT DISTINCT rfid_id FROM hareketler WHERE tarih=? AND islem_tipi='GİRİŞ'", (bugun,))
                girenler = [r[0] for r in cursor.fetchall()]
                
                # 3. Kümeleri birbirinden çıkararak gelmeyenleri bul (Aktifler - Girenler)
                gelmeyenler = set(aktifler) - set(girenler)
                simdi_saat = datetime.now().strftime("%H:%M:%S")
                
                # 4. Gelmeyenleri veritabanına 'DEVAMSIZ' olarak kaydet
                for pid in gelmeyenler:
                    cursor.execute("INSERT INTO hareketler (rfid_id, tarih, saat, islem_tipi) VALUES (?, ?, ?, ?)",
                                   (pid, bugun, simdi_saat, "DEVAMSIZ"))
                conn.commit()
        except Exception:
            pass

    def dongu_guncelle(self):
        simdi = datetime.now()
        saat = simdi.hour
        bugun = simdi.strftime("%d.%m.%Y")
        
        # OTOMATİK YOKLAMA KONTROLÜ (Saat 12:00 veya sonrasında günde 1 kez çalışır)
        if saat >= 12 and getattr(self, 'yoklama_tarihi', '') != bugun:
            self.yoklama_al(bugun)
            self.yoklama_tarihi = bugun

        # Zaman Bazlı Mod
        if 7 <= saat < 12:
            self.secili_islem = "GİRİŞ"
            self.lbl_mode.config(text="OTOMATİK GİRİŞ MODU", bg=self.c_primary)
        elif 13 <= saat < 19:
            self.secili_islem = "ÇIKIŞ"
            self.lbl_mode.config(text="OTOMATİK ÇIKIŞ MODU", bg=self.c_dark)
        else:
            if not self.secili_islem:
                self.lbl_mode.config(text="MANUEL MOD (A: GİRİŞ | B: ÇIKIŞ)", bg="#475569")
        
        self.lbl_big_clock.config(text=simdi.strftime("%H:%M:%S"))
        self.lbl_date.config(text=simdi.strftime("%d %B %Y | %A").upper())
        self.son_hareketleri_cek()
        self.root.after(1000, self.dongu_guncelle)

    def son_hareketleri_cek(self):
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT p.ad, p.soyad, h.islem_tipi, h.saat 
                                  FROM hareketler h JOIN personeller p ON h.rfid_id = p.rfid_id 
                                  ORDER BY h.id DESC LIMIT 3""")
                logs = cursor.fetchall()
                log_text = ""
                for l in logs:
                    log_text += f"• {self.maskele(l[0])} {self.maskele(l[1])}\n  {l[2]} - {l[3]}\n\n"
                self.lbl_log.config(text=log_text if log_text else "Kayıt yok.")
        except: pass

    def arayuz_olustur(self):
        self.left_frame = tk.Frame(self.root, bg=self.c_deep, width=380)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(self.root, bg=self.c_bg)
        self.right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        tk.Label(self.left_frame, text="SİSTEM ZAMANI", font=("Arial", 10, "bold"), bg=self.c_deep, fg="#7dd3fc").pack(pady=(40, 5))
        self.lbl_big_clock = tk.Label(self.left_frame, text="00:00:00", font=("Helvetica", 55, "bold"), bg=self.c_deep, fg=self.c_white)
        self.lbl_big_clock.pack()
        self.lbl_date = tk.Label(self.left_frame, text="", font=("Arial", 11), bg=self.c_deep, fg="#38bdf8")
        self.lbl_date.pack(pady=10)

        tk.Frame(self.left_frame, bg="#075985", height=2, width=300).pack(pady=30)
        tk.Label(self.left_frame, text="SON 3 HAREKET", font=("Arial", 10, "bold"), bg=self.c_deep, fg="#7dd3fc").pack()
        self.lbl_log = tk.Label(self.left_frame, text="", font=("Arial", 11), bg=self.c_deep, fg="#e0f2fe", justify=tk.LEFT)
        self.lbl_log.pack(pady=20, padx=40, anchor="w")
        tk.Label(self.left_frame, text=f"SİSTEM IP: {self.get_ip()}", font=("Courier", 10), bg=self.c_deep, fg="#334155").pack(side=tk.BOTTOM, pady=20)

        self.lbl_mode = tk.Label(self.right_frame, text="SİSTEM HAZIR", font=("Arial", 12, "bold"), fg="white", pady=20)
        self.lbl_mode.pack(fill=tk.X)

        self.card = tk.Frame(self.right_frame, bg="white", padx=40, pady=40, highlightthickness=1, highlightbackground="#e2e8f0")
        self.card.place(relx=0.5, rely=0.45, anchor=tk.CENTER, width=620, height=480)

        self.lbl_title = tk.Label(self.card, text="PERSONEL GİRİŞİ", font=("Arial", 16, "bold"), bg="white", fg=self.c_deep)
        self.lbl_title.pack(pady=(0, 10))
        
        self.disp_frame = tk.Frame(self.card, bg=self.c_bg, padx=15, pady=10, highlightthickness=2, highlightbackground=self.c_primary)
        self.disp_frame.pack()
        self.lbl_display = tk.Label(self.disp_frame, text="", font=("Courier", 55, "bold"), bg=self.c_bg, fg=self.c_primary, width=8)
        self.lbl_display.pack()

        self.lbl_info = tk.Label(self.card, text="Lütfen şifrenizi girin.", font=("Arial", 14), bg="white", fg="#64748b", justify=tk.CENTER)
        self.lbl_info.pack(pady=40, fill=tk.BOTH, expand=True)

        tk.Button(self.right_frame, text="⚙️ YÖNETİCİ AYARLARI", command=self.admin_onay_penceresi, 
                  bg=self.c_light, fg=self.c_deep, relief=tk.FLAT, font=("Arial", 10, "bold")).pack(side=tk.BOTTOM, pady=25)

    def tus_basildi(self, tus):
        if tus == 'A':
            self.secili_islem = "GİRİŞ"
            self.lbl_mode.config(text="MANUEL MOD: GİRİŞ", bg=self.c_primary)
        elif tus == 'B':
            self.secili_islem = "ÇIKIŞ"
            self.lbl_mode.config(text="MANUEL MOD: ÇIKIŞ", bg=self.c_dark)
        elif tus == '#':
            self.personel_islem(self.input_buffer)
            self.input_buffer = ""
            self.lbl_display.config(text="")
        elif tus == '*':
            self.input_buffer = ""
            self.lbl_display.config(text="")
        elif tus.isdigit() and len(self.input_buffer) < 8:
            self.input_buffer += tus
            self.lbl_display.config(text="•" * len(self.input_buffer))

    def personel_islem(self, kid):
        if not self.secili_islem: return
        with sqlite3.connect(self.db_yolu) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ad, soyad, departman, durum FROM personeller WHERE rfid_id=?", (kid,))
            p = cursor.fetchone()
            if p:
                ad, soyad, dep, durum = p
                if durum != "Aktif":
                    self.lbl_info.config(text=f"DİKKAT: {ad} {soyad}\nPERSONEL {durum.upper()} DURUMDA", fg=self.c_alert, font=("Arial", 16, "bold"))
                    return
                simdi_saat = datetime.now().strftime("%H:%M:%S")
                cursor.execute("INSERT INTO hareketler (rfid_id, tarih, saat, islem_tipi) VALUES (?, ?, ?, ?)",
                               (kid, datetime.now().strftime("%d.%m.%Y"), simdi_saat, self.secili_islem))
                conn.commit()
                success_text = f"İŞLEM BAŞARILI\n\n{ad.upper()} {soyad.upper()}\n{dep.upper()}\nSAAT: {simdi_saat}"
                self.lbl_info.config(text=success_text, fg=self.c_dark, font=("Arial", 18, "bold"))
                self.root.after(4000, lambda: self.lbl_info.config(text="Lütfen şifrenizi girin.", fg="#64748b", font=("Arial", 14)))
            else: 
                self.lbl_info.config(text="HATA: KAYITSIZ ŞİFRE\nLütfen tekrar deneyiniz.", fg=self.c_alert, font=("Arial", 16, "bold"))
                self.root.after(3000, lambda: self.lbl_info.config(text="Lütfen şifrenizi girin.", fg="#64748b", font=("Arial", 14)))

    def keypad_dongusu(self):
        keys = [['1','2','3','A'], ['4','5','6','B'], ['7','8','9','C'], ['*','0','#','D']]
        while self.running:
            for i, row_pin in enumerate(self.rows):
                GPIO.output(row_pin, GPIO.HIGH)
                for j, col_pin in enumerate(self.cols):
                    if GPIO.input(col_pin) == GPIO.HIGH:
                        self.tus_basildi(keys[i][j])
                        while GPIO.input(col_pin) == GPIO.HIGH: time.sleep(0.1)
                GPIO.output(row_pin, GPIO.LOW)
            time.sleep(0.05)

    def admin_onay_penceresi(self):
        win = tk.Toplevel(self.root)
        win.title("Güvenlik")
        win.geometry("300x180")
        win.configure(bg=self.c_bg)
        tk.Label(win, text="Yönetici Şifresi:", bg=self.c_bg, fg=self.c_deep).pack(pady=15)
        ent = tk.Entry(win, show="*", justify='center', font=("Arial", 12))
        ent.pack()
        tk.Button(win, text="Giriş", command=lambda: self.sifre_kontrol(ent.get(), win), bg=self.c_primary, fg="white", padx=20).pack(pady=15)

    def sifre_kontrol(self, s, w):
        if s == self.ADMIN_SIFRE:
            w.destroy()
            self.admin_paneli_ac()
        else: messagebox.showerror("Hata", "Yanlış Şifre!")

    def admin_paneli_ac(self):
        self.adm = tk.Toplevel(self.root)
        self.adm.title("Yönetici Kontrol Paneli")
        self.adm.geometry("900x550")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="white", foreground=self.c_deep, fieldbackground="white", borderwidth=0)
        style.map("Treeview", background=[('selected', self.c_primary)])

        tabs = ttk.Notebook(self.adm)
        tabs.pack(expand=True, fill=tk.BOTH)
        
        f1 = tk.Frame(tabs, bg="white")
        tabs.add(f1, text=" Personel Listesi ")
        
        cols = ("Şifre", "Ad", "Soyad", "Bölüm", "Durum")
        self.tree = ttk.Treeview(f1, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c); self.tree.column(c, width=100, anchor=tk.CENTER)
        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        btn_bar = tk.Frame(f1, bg="white")
        btn_bar.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_bar, text="AKTİF ET", bg=self.c_primary, fg="white", command=lambda: self.durum_guncelle("Aktif")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_bar, text="İZİNLİ YAP", bg=self.c_dark, fg="white", command=lambda: self.durum_guncelle("İzinli")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_bar, text="EXCEL RAPORU AL 📥", bg=self.c_deep, fg="white", command=self.rapor_olustur).pack(side=tk.LEFT, padx=20)
        
        tk.Button(btn_bar, text="KAYDI SİL", bg=self.c_alert, fg="white", command=self.personel_sil).pack(side=tk.RIGHT, padx=5)
        
        f2 = tk.Frame(tabs, bg="white")
        tabs.add(f2, text=" Yeni Kayıt ")
        form = tk.Frame(f2, bg="white")
        form.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
        self.entries = []
        labels = ["Şifre:", "Ad:", "Soyad:", "Bölüm:"]
        for i, t in enumerate(labels):
            tk.Label(form, text=t, bg="white", fg=self.c_deep).grid(row=i, column=0, pady=10)
            e = tk.Entry(form, highlightthickness=1, highlightbackground=self.c_light); e.grid(row=i, column=1, padx=10); self.entries.append(e)
        tk.Button(f2, text="KAYDET", bg=self.c_deep, fg="white", width=20, command=self.yeni_kaydet).place(relx=0.5, rely=0.8, anchor=tk.CENTER)
        self.personel_listele()

    def rapor_olustur(self):
        dosya_adi = f"PDKS_Rapor_{datetime.now().strftime('%d_%m_%Y')}.csv"
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT p.ad, p.soyad, p.departman, h.tarih, h.saat, h.islem_tipi 
                                  FROM hareketler h JOIN personeller p ON h.rfid_id = p.rfid_id 
                                  ORDER BY h.tarih DESC, h.saat DESC""")
                veriler = cursor.fetchall()
                
                with open(dosya_adi, mode='w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Ad', 'Soyad', 'Departman', 'Tarih', 'Saat', 'İşlem Tipi'])
                    writer.writerows(veriler)
            messagebox.showinfo("Başarılı", f"Rapor oluşturuldu!\nDosya Adı: {dosya_adi}")
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulamadı: {e}")

    def personel_listele(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        with sqlite3.connect(self.db_yolu) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM personeller")
            for r in cursor.fetchall(): self.tree.insert("", tk.END, values=r)

    def yeni_kaydet(self):
        v = [e.get() for e in self.entries]
        if "" in v: return
        with sqlite3.connect(self.db_yolu) as conn:
            try:
                conn.cursor().execute("INSERT INTO personeller VALUES (?,?,?,?,?)", (v[0], v[1], v[2], v[3], "Aktif"))
                conn.commit()
                self.personel_listele()
                for e in self.entries: e.delete(0, tk.END)
            except: messagebox.showerror("Hata", "Şifre Çakışması!")

    def durum_guncelle(self, d):
        sel = self.tree.selection(); 
        if not sel: return
        pid = self.tree.item(sel[0])['values'][0]
        with sqlite3.connect(self.db_yolu) as conn:
            conn.cursor().execute("UPDATE personeller SET durum=? WHERE rfid_id=?", (d, pid)); conn.commit()
        self.personel_listele()

    def personel_sil(self):
        sel = self.tree.selection(); 
        if not sel: return
        pid = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Onay", "Silinsin mi?"):
            with sqlite3.connect(self.db_yolu) as conn:
                conn.cursor().execute("DELETE FROM personeller WHERE rfid_id=?", (pid,)); conn.commit()
            self.personel_listele()

if __name__ == "__main__":
    root = tk.Tk()
    app = PersonelSistemi(root)
    root.mainloop()
