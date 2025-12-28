class Scheduler:
    def __init__(self, courses, instructors, rooms):
        self.courses = courses
        self.instructors = instructors
        self.rooms = rooms
        
        self.days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        self.hours = list(range(9, 18)) # 09, 10, ... 17
        self.schedule = {} 

    def clear_schedule(self):
        self.schedule = {}
        for day in self.days:
            self.schedule[day] = {}
            for hour in self.hours:
                self.schedule[day][hour] = {}
                # Oda isimlerini string olarak almayı garantiye al
                for room in self.rooms:
                    r_name = str(room.get('name', 'Unknown'))
                    self.schedule[day][hour][r_name] = None

    def check_conflict(self, course, day, hour, room):
        r_name = str(room.get('name', 'Unknown'))
        
        # 1. Sınıf Doluluk Kontrolü
        if self.schedule[day][hour].get(r_name) is not None:
            return False

        # Diğer odaları kontrol et
        current_instructor = course.get('instructor_id')
        current_year = course.get('year')

        for other_room_name in self.schedule[day][hour]:
            other_course = self.schedule[day][hour][other_room_name]
            if other_course:
                # 2. Hoca Çakışması
                if other_course.get('instructor_id') == current_instructor:
                    return False
                
                # 3. Yıl/Grup Çakışması (Opsiyonel, veri varsa)
                if current_year and other_course.get('year') == current_year:
                    return False
        return True

    def solve(self):
        self.clear_schedule()
        return self.backtrack(0)

    def backtrack(self, course_index):
        if course_index == len(self.courses):
            return True

        course = self.courses[course_index]
        
        # --- KRİTİK DÜZELTME: Veri Tipi Dönüşümü ---
        try:
            duration = int(course.get('duration', 1)) # Sayıya çevir
        except:
            duration = 1 # Hata olursa varsayılan 1 saat
            
        course_is_lab = course.get('is_lab', False)
        # JSON'da "true"/"false" string gelebilir, onu bool yapalım
        if isinstance(course_is_lab, str):
            course_is_lab = course_is_lab.lower() == 'true'

        for day in self.days:
            for hour in self.hours:
                if hour + duration > 18:
                    continue

                for room in self.rooms:
                    # Oda lab mı?
                    room_is_lab = room.get('is_lab', False)
                    if isinstance(room_is_lab, str):
                        room_is_lab = room_is_lab.lower() == 'true'

                    # Lab dersi labda, teori sınıfta
                    if course_is_lab != room_is_lab:
                        continue
                    
                    # Kapasite kontrolü (varsa)
                    try:
                        capacity = int(room.get('capacity', 999))
                        # JSON'da öğrenci sayısı yoksa varsayılan 0 kabul et
                        student_count = int(course.get('student_count', 0)) 
                        if student_count > capacity:
                            continue
                    except:
                        pass # Veri yoksa kontrolü geç

                    # Çakışma Kontrolü
                    is_slot_available = True
                    for t in range(duration):
                        if (hour + t) not in self.hours: # Saat 17'yi geçerse
                            is_slot_available = False
                            break
                        if not self.check_conflict(course, day, hour + t, room):
                            is_slot_available = False
                            break
                    
                    if is_slot_available:
                        r_name = str(room.get('name', 'Unknown'))
                        for t in range(duration):
                            self.schedule[day][hour + t][r_name] = course
                        
                        if self.backtrack(course_index + 1):
                            return True
                        
                        # Backtrack (Geri Al)
                        for t in range(duration):
                            self.schedule[day][hour + t][r_name] = None
                            
        return False