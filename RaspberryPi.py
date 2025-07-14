import pyrebase
import RPi.GPIO as gpio
from time import sleep

# ----------------- CẤU HÌNH FIREBASE -----------------
config = {
    "apiKey": "AIzaSyDh7evzo18VgSTXMQOBQmvPOpOIO87Gs2A",
    "authDomain": "iot-vuonrau.firebaseapp.com",
    "databaseURL": "https://iot-vuonrau-default-rtdb.firebaseio.com",
    "projectId": "iot-vuonrau",
    "storageBucket": "iot-vuonrau.firebasestorage.app",
    "messagingSenderId": "786889359852",
    "appId": "1:786889359852:web:9adb2a628c73a307fec0c9",
    "measurementId": "G-Z14B2QP8K9"
}

# ----------------- KHAI BÁO CHÂN GPIO -----------------
MOTOR_PINS = [17, 18, 27, 22]  # IN1, IN2, IN3, IN4
LIGHT = 5     # Đèn
FAN = 23       # Quạt
PUMP = 24      # Máy bơm

# -- --------------- KHỞI TẠO GPIO -----------------
gpio.setmode(gpio.BCM)
for pin in MOTOR_PINS:
    gpio.setup(pin, gpio.OUT)
    gpio.output(pin, 0)

gpio.setup(LIGHT, gpio.OUT)
gpio.setup(PUMP, gpio.OUT)
gpio.setup(FAN, gpio.OUT)

# ----------------- KHỞI TẠO FIREBASE -----------------
firebase = pyrebase.initialize_app(config)
db = firebase.database()

# ----------------- MA TRẬN NỬA BƯỚC -----------------
halfstep_seq = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1]
]

# ----------------- HÀM TIỆN ÍCH -----------------
def get_float_value(node):
    try:
        return float(db.child(node).get().val())
    except (ValueError, TypeError):
        print(f"[LỖI] Không thể chuyển {node} thành float.")
        return 0.0

def get_int_value(node):
    try:
        return int(db.child(node).get().val())
    except (ValueError, TypeError):
        print(f"[LỖI] Không thể chuyển {node} thành int.")
        return 0

# ----------------- HÀM ĐIỀU KHIỂN -----------------
def move_motor(direction, steps):
    """Điều khiển động cơ bước 28BYJ-48 với ULN2003"""
    if direction == 0:
        seq = halfstep_seq
    else:
        seq = list(reversed(halfstep_seq))

    for _ in range(steps):
        for halfstep in seq:
            for pin in range(4):
                gpio.output(MOTOR_PINS[pin], halfstep[pin])
            sleep(0.001)

def control_light():
    light_val = get_int_value("den")
    gpio.output(LIGHT, light_val)
    print("Đèn:", "Bật" if light_val else "Tắt")

def control_fan():
    fan_val = get_int_value("fan")
    gpio.output(FAN, fan_val)
    print("Quạt:", "Bật" if fan_val else "Tắt")

def control_pump():
    pump_val = get_int_value("pump")
    gpio.output(PUMP, pump_val)
    print("Bơm:", "Bật" if pump_val else "Tắt")

def manual_shield():
    desired_state = get_int_value("manchan")   # 1: mở, 0: đóng
    current_state = get_int_value("vtmc")
    if desired_state == 1 and current_state == 0:
        move_motor(0, 512)  # quay ngược (mở)
        db.update({"vtmc": 1})
        print("Màn chắn mở (thủ công)")
    elif desired_state == 0 and current_state == 1:
        move_motor(1, 512)  # quay thuận (đóng)
        db.update({"vtmc": 0})
        print("Màn chắn đóng (thủ công)")

# ----------------- CHẾ ĐỘ TỰ ĐỘNG -----------------
def auto_light():
    current_light = get_float_value("illu")
    light_threshold = get_float_value("illu_set_low")
    if current_light < light_threshold:
        gpio.output(LIGHT, 1)
        db.update({"den": 1})
        print("Đèn tự động bật")
    else:
        gpio.output(LIGHT, 0)
        db.update({"den": 0})
        print("Đèn tự động tắt")

def auto_fan():
    current_temp = get_float_value("Temperature")
    temp_threshold = get_float_value("temp_set")
    if current_temp > temp_threshold:
        gpio.output(FAN, 1)
        db.update({"fan": 1})
        print("Quạt tự động bật")
    else:
        gpio.output(FAN, 0)
        db.update({"fan": 0})
        print("Quạt tự động tắt")

def auto_pump():
    soil_moisture = get_float_value("moisture")
    moisture_threshold = get_float_value("moisture_set")
    if soil_moisture < moisture_threshold:
        gpio.output(PUMP, 1)
        db.update({"pump": 1})
        print("Bơm tự động bật")
    else:
        gpio.output(PUMP, 0)
        db.update({"pump": 0})
        print("Bơm tự động tắt")

def auto_shield():
    current_light = get_float_value("illu")
    light_high_threshold = get_float_value("illu_set_high")
    vtmc_val = get_int_value("vtmc")
    if current_light > light_high_threshold and vtmc_val == 0:
        move_motor(0, 512)
        db.update({"vtmc": 1})
        print("Màn chắn tự động mở")
    elif current_light <= light_high_threshold and vtmc_val == 1:
        move_motor(1, 4096)
        db.update({"vtmc": 0})
        print("Màn chắn tự động đóng")

# ----------------- CHƯƠNG TRÌNH CHÍNH -----------------
if __name__ == "__main__":
    print("Khởi động hệ thống IoT")
    try:
        while True:
            status = get_int_value("status")  # 0: thủ công, 1: tự động
            if status == 0:
                print("Chế độ THỦ CÔNG")
                control_light()
                control_fan()
                control_pump()
                manual_shield()
            elif status == 1:
                print("Chế độ TỰ ĐỘNG")
                auto_light()
                auto_fan()
                auto_pump()
                auto_shield()
            sleep(1)
    except KeyboardInterrupt:
        print("Dừng hệ thống, dọn dẹp GPIO")
        gpio.cleanup()


