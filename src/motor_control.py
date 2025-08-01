import pygame
import time
import threading
from serial_comm import SerialComm

class MotorControl:
    """
    Enhanced motor control system that integrates the working joystick code
    with the existing project structure.
    """
    
    def __init__(self, serial_comm=None, port="COM14", protocol="text"):
        # Use shared serial connection if provided, otherwise create new one
        if serial_comm:
            self.serial = serial_comm
        else:
            self.serial = SerialComm(port=port, protocol=protocol)
        
        self.protocol = protocol
        
        # Motor control parameters (from working code)
        self.servo_min = 0
        self.servo_max = 60
        self.stepper_min = 0
        self.stepper_max = 300
        
        # Control states (from working code)
        self.servo_active = True
        self.stepper_active = True
        
        # Button state tracking (from working code)
        self.prev_b = self.prev_y = self.prev_lb = self.prev_rb = False
        
        # Angle tracking (from working code)
        self.last_sent_servo = -1
        self.last_sent_stepper = -1
        self.last_servo_time = time.time()
        self.last_stepper_time = time.time()
        
        # Command definitions
        self.SERVO_CMD = 0x01
        self.STEPPER_CMD = 0x02
        self.LASER_CMD = 0x03
        
        # Button definitions (from working code)
        self.BUTTON_B = 2    # Laser aç
        self.BUTTON_Y = 3    # Laser kapat
        self.BUTTON_LB = 4   # Servo toggle
        self.BUTTON_RB = 5   # Stepper toggle
        
        # Joystick initialization
        pygame.init()
        pygame.joystick.init()
        self.joystick = None
        
        if pygame.joystick.get_count() == 0:
            print("[MotorControl] ❌ Joystick bulunamadı!")
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"[MotorControl] ✅ Joystick başlatıldı: {self.joystick.get_name()}")
        
        # Control thread
        self.control_thread = None
        self.running = False
        
    def start_control_loop(self):
        """Start the motor control loop in a separate thread."""
        if self.control_thread and self.control_thread.is_alive():
            print("[MotorControl] ⚠️ Control loop already running")
            return
            
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        print("[MotorControl] 🚀 Motor control loop started")
    
    def stop_control_loop(self):
        """Stop the motor control loop."""
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
        print("[MotorControl] 🛑 Motor control loop stopped")
    
    def _control_loop(self):
        """Main control loop (from working code)."""
        while self.running:
            try:
                self._process_joystick_input()
                time.sleep(0.01)  # 10ms delay (from working code)
            except Exception as e:
                print(f"[MotorControl] ❌ Error in control loop: {e}")
                time.sleep(0.1)
    
    def _process_joystick_input(self):
        """Process joystick input (from working code)."""
        if not self.joystick:
            return
            
        pygame.event.pump()

        # === Buton Durumlarını Oku (from working code) ===
        current_b = self.joystick.get_button(self.BUTTON_B)
        current_y = self.joystick.get_button(self.BUTTON_Y)
        current_lb = self.joystick.get_button(self.BUTTON_LB)
        current_rb = self.joystick.get_button(self.BUTTON_RB)

        # === Lazer Kontrolleri (from working code) ===
        if current_b and not self.prev_b:
            self.serial.send_command(self.LASER_CMD, 1)
            print("[MotorControl] Lazer AÇ")

        if current_y and not self.prev_y:
            self.serial.send_command(self.LASER_CMD, 0)
            print("[MotorControl] Lazer KAPAT")

        # === Servo Aktif/Pasif Toggle (LB) ===
        if current_lb and not self.prev_lb:
            self.servo_active = not self.servo_active
            print("[MotorControl] Servo:", "Açık" if self.servo_active else "Kilitli")

        # === Stepper Aktif/Pasif Toggle (RB) ===
        if current_rb and not self.prev_rb:
            self.stepper_active = not self.stepper_active
            print("[MotorControl] Stepper:", "Açık" if self.stepper_active else "Kilitli")

        # === Önceki Butonları Güncelle ===
        self.prev_b, self.prev_y, self.prev_lb, self.prev_rb = current_b, current_y, current_lb, current_rb

        now = time.time()

        # === Servo Açı Gönderimi (from working code) ===
        if self.servo_active:
            angle_servo = self.get_servo_angle()
            if angle_servo != self.last_sent_servo and (now - self.last_servo_time) > 0.1:
                self.serial.send_command(self.SERVO_CMD, angle_servo)
                print(f"[MotorControl] Servo açı: {angle_servo}")
                self.last_sent_servo = angle_servo
                self.last_servo_time = now

        # === Stepper Açı Gönderimi (from working code) ===
        if self.stepper_active:
            angle_stepper = self.get_stepper_angle()
            if angle_stepper != self.last_sent_stepper and (now - self.last_stepper_time) > 0.1:
                self.serial.send_command(self.STEPPER_CMD, angle_stepper)
                print(f"[MotorControl] Stepper açı: {angle_stepper}")
                self.last_sent_stepper = angle_stepper
                self.last_stepper_time = now
    
    def get_servo_angle(self):
        """Get servo angle from left analog vertical (Axis 1) - from working code"""
        if not self.joystick:
            return 0
        pygame.event.pump()
        y = -self.joystick.get_axis(1)  # Yukarı pozitif
        if abs(y) < 0.05:  # Deadzone
            y = 0
        y = max(0.0, y)
        return int(y * 60)

    def get_stepper_angle(self):
        """Get stepper angle from right analog horizontal (Axis 2) - from working code"""
        if not self.joystick:
            return 0
        pygame.event.pump()
        x = self.joystick.get_axis(2)  # -1.0 to +1.0 (full range)
        # Map full joystick range to 0-300 degrees
        x_normalized = (x + 1.0) / 2.0  # Convert -1..1 to 0..1
        return int(x_normalized * 300)
    
    def set_servo_angle(self, angle):
        """Set servo angle directly."""
        angle = max(self.servo_min, min(self.servo_max, angle))
        self.serial.send_command(self.SERVO_CMD, angle)
        print(f"[MotorControl] Servo açısı ayarlandı: {angle}")
    
    def set_stepper_angle(self, angle):
        """Set stepper angle directly."""
        angle = max(self.stepper_min, min(self.stepper_max, angle))
        self.serial.send_command(self.STEPPER_CMD, angle)
        print(f"[MotorControl] Stepper açısı ayarlandı: {angle}")
    
    def fire_laser(self):
        """Fire laser."""
        self.serial.send_command(self.LASER_CMD, 1)
        print("[MotorControl] Lazer ateşlendi")
    
    def stop_laser(self):
        """Stop laser."""
        self.serial.send_command(self.LASER_CMD, 0)
        print("[MotorControl] Lazer durduruldu")
    
    def toggle_servo(self):
        """Toggle servo active state."""
        self.servo_active = not self.servo_active
        print("[MotorControl] Servo:", "Açık" if self.servo_active else "Kilitli")
    
    def toggle_stepper(self):
        """Toggle stepper active state."""
        self.stepper_active = not self.stepper_active
        print("[MotorControl] Stepper:", "Açık" if self.stepper_active else "Kilitli")
    
    def get_status(self):
        """Get current motor control status."""
        return {
            'servo_active': self.servo_active,
            'stepper_active': self.stepper_active,
            'servo_angle': self.last_sent_servo,
            'stepper_angle': self.last_sent_stepper,
            'joystick_connected': self.joystick is not None,
            'protocol': self.protocol
        }
    
    def emergency_stop(self):
        """Emergency stop - stop all motors and laser."""
        self.serial.send_command(self.LASER_CMD, 0)
        self.serial.send_command(self.SERVO_CMD, 0)
        self.serial.send_command(self.STEPPER_CMD, 0)
        print("[MotorControl] 🚨 Emergency stop executed")
    
    def close(self):
        """Close motor control system."""
        self.stop_control_loop()
        pygame.quit()
        print("[MotorControl] 🔌 Motor control system closed") 