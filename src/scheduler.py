import json
from pathlib import Path

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
HOURS = ["08:30", "09:20", "10:10", "11:00", "11:50", "12:40", "13:30", "14:20", "15:10", "16:00", "16:50"]

FRIDAY_EXAM_BLOCK = ["13:30", "14:20"]  # Cuma sınav saatleri

class BeeScheduler:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.curriculum = self._load("curriculum.json")
        self.instructors = self._load("instructors.json")
        self.rooms = self._load("rooms.json")
        self.schedule = {day: {h: None for h in HOURS} for day in DAYS}
        self.violations = []

    def _load(self, filename):
        path = self.data_dir / filename
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate(self):
        # 1) Teori derslerini yerleştir
        theory_courses = [c for c in self.curriculum if c.get("type") == "theory"]
        for course in theory_courses:
            self._place_theory(course)

        # 2) Lab derslerini teori sonrasına yerleştir
        lab_courses = [c for c in self.curriculum if c.get("type") == "lab"]
        for lab in lab_courses:
            self._place_lab(lab)

        return self.schedule, self.violations

    # --- Teori derslerini yerleştirme ---
    def _place_theory(self, course):
        instr = course["instructor"]
        instr_info = next((i for i in self.instructors if i["name"] == instr), None)
        if not instr_info:
            self.violations.append(f"Instructor not found: {instr} for {course['code']}")
            return

        for day in DAYS:
            # Cuma sınav bloğu hariç
            if day == "Friday":
                allowed_hours = [h for h in HOURS if h not in FRIDAY_EXAM_BLOCK]
            else:
                allowed_hours = HOURS

            available = set(instr_info.get("availability", {}).get(day, []))
            for hour in allowed_hours:
                if hour in available and self.schedule[day][hour] is None:
                    # Günlük max 4 saat kontrolü
                    if self._count_daily_theory(instr, day) >= instr_info.get("maxDailyTheoryHours", 4):
                        continue

                    # --- Ek kurallar ---
                    if not self._check_elective_conflicts(course, day, hour):
                        continue

                    room = self._find_room("theory")
                    if room:
                        self.schedule[day][hour] = {
                            "course": course,
                            "room": room,
                            "type": "theory",
                            "instructor": instr
                        }
                        return
        self.violations.append(f"No slot for theory: {course['code']}")

    # --- Lab derslerini yerleştirme ---
    def _place_lab(self, lab):
        linked = lab.get("linkedTheory")
        if not linked:
            self.violations.append(f"Lab without linked theory: {lab['code']}")
            return

        # Teori saatini bul
        theory_slot = self._find_course_slot(linked)
        if not theory_slot:
            self.violations.append(f"Lab cannot find theory slot: {lab['code']}")
            return

        day, hour_idx = theory_slot
        # Tercihen ardışık saat
        for offset in [1, 2]:  # teori sonrası
            next_idx = hour_idx + offset
            if next_idx < len(HOURS):
                next_hour = HOURS[next_idx]
                if self.schedule[day][next_hour] is None:
                    room = self._find_room("lab", max_capacity=40)
                    if room:
                        self.schedule[day][next_hour] = {
                            "course": lab,
                            "room": room,
                            "type": "lab",
                            "instructor": lab["instructor"]
                        }
                        return
        self.violations.append(f"No slot for lab after theory: {lab['code']}")

    # --- Ek kurallar kontrolü ---
    def _check_elective_conflicts(self, course, day, hour):
        slot = self.schedule[day][hour]
        if slot is None:
            return True

        other_course = slot["course"]

        # 3. sınıf zorunlu ders vs seçmeli
        if course.get("year") == 3 and not course.get("elective", False):
            if other_course.get("elective", False):
                self.violations.append(f"Conflict: {course['code']} overlaps with elective {other_course['code']}")
                return False

        # CENG vs SENG seçmeli çakışması
        if course.get("elective", False) and other_course.get("elective", False):
            if course.get("dept") == "CENG" and other_course.get("dept") == "SENG":
                self.violations.append(f"Conflict: CENG elective {course['code']} overlaps with SENG elective {other_course['code']}")
                return False

        return True

    # --- Yardımcı fonksiyonlar ---
    def _count_daily_theory(self, instructor, day):
        count = 0
        for h in HOURS:
            slot = self.schedule[day][h]
            if slot and slot.get("type") == "theory" and slot.get("instructor") == instructor:
                count += 1
        return count

    def _find_course_slot(self, code):
        for day in DAYS:
            for i, h in enumerate(HOURS):
                slot = self.schedule[day][h]
                if slot and slot.get("course", {}).get("code") == code and slot.get("type") == "theory":
                    return day, i
        return None

    def _find_room(self, room_type, max_capacity=None):
        candidates = [r for r in self.rooms if r["type"] == room_type]
        if max_capacity is not None:
            candidates = [r for r in candidates if r.get("capacity", 0) <= max_capacity]
        return candidates[0] if candidates else None