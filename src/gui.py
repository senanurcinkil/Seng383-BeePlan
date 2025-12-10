from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor 
from scheduler import BeeScheduler, DAYS, HOURS
import os # Dosya işlemleri için

# --- Ders Seçim Penceresi ---
class CourseSelectionDialog(QDialog):
    def __init__(self, courses, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ders Seçimi")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        # Liste widget
        self.list_widget = QListWidget()
        for course in courses:

            text = f"{course['code']} - {course['name']} | Year {course.get('year')} | {course.get('type')} | {course.get('instructor')}"


            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setData(Qt.UserRole, course)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

        # Onay butonu
        self.ok_btn = QPushButton("Seçilenleri Uygula")
        self.ok_btn.clicked.connect(self.accept)
        layout.addWidget(self.ok_btn)

    def get_selected_courses(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected


# --- Ana Pencere ---
class BeePlanWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BeePlan - Course Scheduler")
        self.setMinimumSize(1000, 600)

        central = QWidget()
        layout = QVBoxLayout(central)

        # Bilgi etiketi (Hizalama PyQt6 stili)
        self.info = QLabel("Hazır: Henüz program oluşturulmadı.")
        self.info.setAlignment(Qt.AlignmentFlag.AlignLeading | Qt.AlignmentFlag.AlignVCenter)

        self.table = QTableWidget(len(HOURS), len(DAYS))
        self.table.setHorizontalHeaderLabels(DAYS)
        self.table.setVerticalHeaderLabels(HOURS)

        # Butonlar
        self.generate_btn = QPushButton("Generate Schedule (Full)")
        self.select_btn = QPushButton("Select Courses & Generate")
        self.report_btn = QPushButton("View Report")

        layout.addWidget(self.info)
        layout.addWidget(self.table)
        layout.addWidget(self.generate_btn)
        layout.addWidget(self.select_btn)
        layout.addWidget(self.report_btn)
        self.setCentralWidget(central)

        # Olay bağlama
        self.generate_btn.clicked.connect(self.on_generate)
        self.select_btn.clicked.connect(self.on_select_courses)
        self.report_btn.clicked.connect(self.on_report)

    def on_generate(self):
        # Tüm dersler ile program oluştur
        sched = BeeScheduler(data_dir="data")
        schedule, violations = sched.generate()
        self._fill_table(schedule, violations)

    def on_select_courses(self):
        # Sadece seçilen dersler ile program oluştur
        sched = BeeScheduler(data_dir="data")
        courses = sched.curriculum

        dialog = CourseSelectionDialog(courses, self)
        # exec_() yerine exec() kullanılır
        if dialog.exec():
            selected = dialog.get_selected_courses()
            if not selected:
                QMessageBox.warning(self, "Uyarı", "Hiç ders seçmediniz!")
                return
            
            # Seçilen dersleri scheduler'a yükle
            sched.curriculum = selected
            schedule, violations = sched.generate()
            self._fill_table(schedule, violations)

    def on_report(self):
        try:
            # Basitlik için ana dizine bakıyoruz
            with open("validation.txt", "r", encoding="utf-8") as f:
                content = f.read().strip() or "İhlal bulunamadı."
        except FileNotFoundError:
            content = "Henüz rapor oluşturulmadı."
        QMessageBox.information(self, "Validation Report", content)

    def _fill_table(self, schedule, violations):
        self.table.clearContents()
        
        # İhlal listesini düz bir metin listesine çevirelim (kolay arama için)
        violation_strings = " ".join(violations)

        for col, day in enumerate(DAYS):
            for row, hour in enumerate(HOURS):
                slot = schedule[day][hour]
                if slot:
                    code = slot['course']['code']
                    text = f"{code}\n{slot['room']['name']}\n{slot['instructor']}"
                    item = QTableWidgetItem(text)
                    
                    # Lab dersleri sarı
                    if slot["type"] == "lab":
                        item.setBackground(QColor("yellow"))
                    
                    # Çakışma varsa kırmızı (Basit kontrol)
                    if code in violation_strings:
                         item.setBackground(QColor("#FFCCCC")) # Açık kırmızı

                    self.table.setItem(row, col, item)

        if violations:
            self.info.setText(f"Rapor: {len(violations)} ihlal bulundu.")
            try:
                with open("validation.txt", "w", encoding="utf-8") as f:
                    for v in violations:
                        f.write(v + "\n")
            except Exception as e:
                print(f"Rapor yazılamadı: {e}")
        else:
            self.info.setText("Çakışma yok. Program başarıyla oluşturuldu.")