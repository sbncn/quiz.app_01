import time
import time

class Timer:
    def __init__(self, time_limit):
        self.time_limit = time_limit
        self.start_time = None
        self.end_time = None
        self.is_running = False

    def start_timer(self):
        self.start_time = time.time()
        self.end_time = self.start_time + self.time_limit
        self.is_running = True
        print("Timer started.\n Exam time 30 minutes")

    def check_time(self):
        if not self.is_running:
            return False
        remaining_time = self.end_time - time.time()
        if remaining_time <= 0:
            self.is_running = False
            return False
        return True
    
    def get_remaining_time(self):
        if self.start_time is None:
            return self.time_limit  # Zaman başlamadıysa tüm süre verilir
        elapsed_time = time.time() - self.start_time
        remaining_time = max(0, self.time_limit - elapsed_time)  # Kalan zamanı hesapla
        return int(remaining_time)  # Geriye kalan süreyi saniye cinsinden döndür
    

    def stop_timer(self):
        self.is_running = False