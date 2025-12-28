import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QTableWidget, QTableWidgetItem, QMessageBox, QLabel, 
                             QTabWidget, QHBoxLayout, QHeaderView, QFileDialog, QPushButton)
from PyQt5.QtCore import Qt
from scheduler import Scheduler # Oluşturduğumuz scheduler dosyasını çağırıyoruz

class BeePlanApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("BeePlan - Ders Programı Oluşturucu")
        self.setGeometry(100, 100, 1200, 800)

        # Veri saklama alanları
        self.courses_data = []
        self.rooms_data = []
        self.instructors_data = []

        self.init_ui()
        self.load_all_data() 

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        
        # --- ÜST MENÜ VE BUTONLAR ---
        self.top_menu = QHBoxLayout()
        self.btn_generate = QPushButton("Program Oluştur (Generate)")
        self.btn_generate.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_generate.clicked.connect(self.run_scheduler) # Butona basınca çalışacak fonksiyon
        self.top_menu.addWidget(self.btn_generate)
        self.layout.addLayout(self.top_menu)

        # --- SEKMELER ---
        self.tabs = QTabWidget()
        self.tab1 = QWidget() 
        self.tab2 = QWidget() 
        
        self.tabs.addTab(self.tab1, "Ders Listesi")
        self.tabs.addTab(self.tab2, "Haftalık Program")
        
        # SEKME 1: Liste
        self.tab1_layout = QVBoxLayout()
        self.course_table = QTableWidget()
        self.course_table.setColumnCount(5)
        self.course_table.setHorizontalHeaderLabels(["Kod", "Ders Adı", "Hoca ID", "Süre", "Tip"])
        self.course_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tab1_layout.addWidget(self.course_table)
        self.tab1.setLayout(self.tab1_layout)
        
        # SEKME 2: Program
        self.tab2_layout = QVBoxLayout()
        self.schedule_table = QTableWidget()
        self.schedule_table.setRowCount(9) 
        self.schedule_table.setColumnCount(5)
        self.schedule_table.setHorizontalHeaderLabels(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
        self.schedule_table.setVerticalHeaderLabels([f"{h}:00" for h in range(9, 18)])
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.schedule_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tab2_layout.addWidget(self.schedule_table)
        self.tab2.setLayout(self.tab2_layout)

        self.layout.addWidget(self.tabs)
        self.central_widget.setLayout(self.layout)

    def load_all_data(self):
        """Tüm JSON dosyalarını (Dersler, Odalar, Hocalar) yükler"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Dosyaları bulmaya çalış (data veya ../data)
        base_path = os.path.join(script_dir, 'data')
        if not os.path.exists(base_path):
            base_path = os.path.join(script_dir, '..', 'data')

        try:
            # 1. Müfredat (Dersler)
            with open(os.path.join(base_path, 'ciricullum.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.courses_data = data if isinstance(data, list) else data.get("courses", [])
            
            # 2. Odalar
            with open(os.path.join(base_path, 'rooms.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.rooms_data = data if isinstance(data, list) else data.get("rooms", [])

            # 3. Hocalar (Dosya adı instructrs.json imiş)
            with open(os.path.join(base_path, 'instructrs.json'), 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.instructors_data = data if isinstance(data, list) else data.get("instructors", [])

            # Listeyi doldur
            self.fill_course_list()

        except Exception as e:
            QMessageBox.warning(self, "Veri Yükleme Hatası", f"Dosyalar otomatik yüklenemedi: {e}\nLütfen dosya yollarını kontrol edin.")

    def fill_course_list(self):
        self.course_table.setRowCount(len(self.courses_data))
        for i, c in enumerate(self.courses_data):
            self.course_table.setItem(i, 0, QTableWidgetItem(str(c.get("code"))))
            self.course_table.setItem(i, 1, QTableWidgetItem(str(c.get("name"))))
            self.course_table.setItem(i, 2, QTableWidgetItem(str(c.get("instructor_id"))))
            self.course_table.setItem(i, 3, QTableWidgetItem(str(c.get("duration"))))
            self.course_table.setItem(i, 4, QTableWidgetItem("Lab" if c.get("is_lab") else "Teori"))

    def run_scheduler(self):
        # 1. Veri Kontrolü: Listeler dolu mu?
        if not self.courses_data:
            QMessageBox.warning(self, "Eksik Veri", "Ders listesi (ciricullum.json) boş veya yüklenemedi!")
            return
        if not self.rooms_data:
            QMessageBox.warning(self, "Eksik Veri", "Sınıf listesi (rooms.json) boş veya yüklenemedi!")
            return

        try:
            # Algoritmayı Başlat
            print("Algoritma başlatılıyor...") # Terminale bilgi yaz
            scheduler = Scheduler(self.courses_data, self.instructors_data, self.rooms_data)
            success = scheduler.solve()
            print("Algoritma tamamlandı. Sonuç:", success)

            if success:
                QMessageBox.information(self, "Başarılı", "Ders programı başarıyla oluşturuldu!")
                self.display_schedule(scheduler.schedule)
                self.tabs.setCurrentIndex(1) # 2. sekmeye geç
            else:
                QMessageBox.critical(self, "Başarısız", "Mevcut kurallara göre uygun bir program oluşturulamadı!\nLütfen kısıtlamaları veya ders saatlerini kontrol edin.")

        except Exception as e:
            # HATA YAKALAYICI: Programın kapanmasını önler ve hatayı gösterir
            import traceback
            hata_detayi = traceback.format_exc()
            print(hata_detayi) # Terminale detaylı hata bas
            QMessageBox.critical(self, "Kritik Hata", f"Program oluşturulurken bir hata oluştu:\n{str(e)}\n\nDetay terminalde yazıyor.")
    def display_schedule(self, schedule_data):
        """Hesaplanan programı tabloya yazar"""
        self.schedule_table.clearContents()
        
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        
        for d_idx, day in enumerate(days):
            for h_idx in range(9): # 9 saat (9-17)
                hour = h_idx + 9
                
                # O saatteki dersleri bul
                cell_text = ""
                # O saatteki tüm odalara bak, dolu olanları yaz
                if day in schedule_data and hour in schedule_data[day]:
                    for room_name, course in schedule_data[day][hour].items():
                        if course:
                            cell_text += f"{course['code']} ({room_name})\n"
                
                if cell_text:
                    item = QTableWidgetItem(cell_text.strip())
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setToolTip(cell_text) # Mouse üzerine gelince detay göster
                    self.schedule_table.setItem(h_idx, d_idx, item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BeePlanApp()
    window.show()
    sys.exit(app.exec_())