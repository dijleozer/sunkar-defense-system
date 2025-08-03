import pygame
import time
import math
from serial_comm import SerialComm

class JoystickController:
    def __init__(self, serial_comm=None, port="COM14", mode="manual", protocol="text"):
        # Use shared serial connection if provided, otherwise create new one
        if serial_comm:
            self.serial = serial_comm
        else:
            self.serial = SerialComm(port=port, protocol=protocol)
        self.mode = mode
        self.protocol = protocol

        # Joystick control parameters
        self.deadzone = 0.05  # Reduced deadzone for better control
        self.servo_min = 0
        self.servo_max = 60
        self.stepper_min = 0
        self.stepper_max = 300  # Updated to match working code

        # Control states (from working code)
        self.servo_active = True
        self.stepper_active = True
        
        # Button state tracking
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

        # Fire button state tracking
        self.last_fire_button_state = False
        self.fire_button_pressed = False

        # === IMPROVED ACCELERATION-BASED CONTROL PARAMETERS ===
        self.max_velocity_servo = 30.0   # degrees per second
        self.max_velocity_stepper = 120.0  # Reduced for smoother control
        self.acceleration_rate = 1.5    # Reduced for gentler acceleration
        self.deceleration_rate = 0.7    # Faster deceleration for better stopping
        
        # Current velocities and positions
        self.current_servo_velocity = 0.0
        self.current_stepper_velocity = 0.0
        self.current_servo_position = 30.0  # Start at center
        self.current_stepper_position = 150.0  # Start at center
        
        # Time tracking for velocity calculations
        self.last_update_time = time.time()
        
        # Improved response curve parameters
        self.response_curve_power = 1.8  # Reduced for less aggressive response
        self.min_velocity_threshold = 0.05  # Lower threshold for more responsive start
        
        # Position holding parameters
        self.stepper_holding_enabled = True
        self.last_joystick_input = 0.0
        self.stepper_movement_active = False

        pygame.init()
        pygame.joystick.init()
        self.joystick = None

        if pygame.joystick.get_count() == 0:
            print("[JoystickController] ❌ Joystick bulunamadı!")
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"[JoystickController] ✅ Joystick başlatıldı: {self.joystick.get_name()}")

    def apply_deadzone(self, value):
        if abs(value) < self.deadzone:
            return 0.0
        sign = 1 if value > 0 else -1
        normalized = (abs(value) - self.deadzone) / (1.0 - self.deadzone)
        return sign * normalized

    def apply_exponential_curve(self, value):
        """Apply exponential response curve for more sensitive control."""
        if abs(value) < 0.01:
            return 0.0
        
        sign = 1 if value > 0 else -1
        magnitude = abs(value)
        
        # Apply exponential curve: y = x^power
        curved_magnitude = math.pow(magnitude, self.response_curve_power)
        
        return sign * curved_magnitude

    def calculate_target_velocity(self, joystick_input, max_velocity):
        """Calculate target velocity based on joystick input with exponential response."""
        # Apply exponential curve for more sensitive control
        curved_input = self.apply_exponential_curve(joystick_input)
        
        # Map to target velocity
        target_velocity = curved_input * max_velocity
        
        return target_velocity

    def update_velocity_and_position(self, target_velocity, current_velocity, current_position, 
                                   max_velocity, min_position, max_position, dt):
        """Update velocity and position with acceleration/deceleration."""
        # Calculate acceleration based on target vs current velocity
        velocity_diff = target_velocity - current_velocity
        
        if abs(velocity_diff) > 0.1:  # Only accelerate if there's significant difference
            # Apply acceleration or deceleration
            if abs(target_velocity) > abs(current_velocity):
                # Accelerating
                acceleration = velocity_diff * self.acceleration_rate
            else:
                # Decelerating
                acceleration = velocity_diff * self.deceleration_rate
            
            # Update velocity
            new_velocity = current_velocity + acceleration * dt
            
            # Clamp velocity
            new_velocity = max(-max_velocity, min(max_velocity, new_velocity))
        else:
            # No significant change, apply gradual deceleration
            new_velocity = current_velocity * 0.9
        
        # Update position
        new_position = current_position + new_velocity * dt
        
        # Clamp position
        new_position = max(min_position, min(max_position, new_position))
        
        return new_velocity, new_position

    def get_servo_angle_acceleration(self):
        """Get servo angle using acceleration-based control."""
        if not self.joystick:
            return int(self.current_servo_position)
            
        pygame.event.pump()
        y = -self.joystick.get_axis(1)  # Yukarı pozitif
        y = self.apply_deadzone(y)
        
        # Calculate time delta
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Calculate target velocity from joystick input
        target_velocity = self.calculate_target_velocity(y, self.max_velocity_servo)
        
        # Update velocity and position
        self.current_servo_velocity, self.current_servo_position = self.update_velocity_and_position(
            target_velocity, self.current_servo_velocity, self.current_servo_position,
            self.max_velocity_servo, self.servo_min, self.servo_max, dt
        )
        
        return int(self.current_servo_position)

    def get_stepper_angle_acceleration(self):
        """Get stepper angle using improved acceleration-based control with position holding."""
        if not self.joystick:
            return int(self.current_stepper_position)
            
        pygame.event.pump()
        x = self.joystick.get_axis(2)  # -1.0 to +1.0 (full range)
        x = self.apply_deadzone(x)
        
        # Calculate time delta
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Check if joystick is being moved
        joystick_moving = abs(x) > 0.01
        self.stepper_movement_active = joystick_moving
        
        if joystick_moving:
            # Calculate target velocity based on joystick position
            # More proportional to joystick position
            target_velocity = self.calculate_target_velocity(x, self.max_velocity_stepper)
            
            # Update velocity and position with acceleration
            self.current_stepper_velocity, self.current_stepper_position = self.update_velocity_and_position(
                target_velocity, self.current_stepper_velocity, self.current_stepper_position,
                self.max_velocity_stepper, self.stepper_min, self.stepper_max, dt
            )
            
            self.last_joystick_input = x
        else:
            # Joystick released - gradually stop movement
            if abs(self.current_stepper_velocity) > 0.1:
                # Apply deceleration to stop smoothly
                self.current_stepper_velocity *= 0.8  # Gradual deceleration
                self.current_stepper_position += self.current_stepper_velocity * dt
                self.current_stepper_position = max(self.stepper_min, min(self.stepper_max, self.current_stepper_position))
            else:
                # Fully stopped - hold position
                self.current_stepper_velocity = 0.0
        
        return int(self.current_stepper_position)

    def get_servo_angle(self):
        """Get servo angle from left analog vertical (Axis 1) - acceleration-based control"""
        return self.get_servo_angle_acceleration()

    def get_stepper_angle(self):
        """Get stepper angle from right analog horizontal (Axis 2) - acceleration-based control"""
        return self.get_stepper_angle_acceleration()

    def set_acceleration_parameters(self, max_velocity_servo=None, max_velocity_stepper=None, 
                                  acceleration_rate=None, deceleration_rate=None, 
                                  response_curve_power=None):
        """Configure acceleration control parameters."""
        if max_velocity_servo is not None:
            self.max_velocity_servo = max_velocity_servo
        if max_velocity_stepper is not None:
            self.max_velocity_stepper = max_velocity_stepper
        if acceleration_rate is not None:
            self.acceleration_rate = acceleration_rate
        if deceleration_rate is not None:
            self.deceleration_rate = deceleration_rate
        if response_curve_power is not None:
            self.response_curve_power = response_curve_power
            
        print(f"[JoystickController] ⚙️ Acceleration parameters updated:")
        print(f"  Servo max velocity: {self.max_velocity_servo}°/s")
        print(f"  Stepper max velocity: {self.max_velocity_stepper}°/s")
        print(f"  Acceleration rate: {self.acceleration_rate}")
        print(f"  Response curve power: {self.response_curve_power}")

    def check_fire_button(self):
        """Check if fire button (usually button 0 or red button) is pressed."""
        if not self.joystick:
            return False
            
        pygame.event.pump()
        
        # Check multiple possible fire buttons (button 0 and 1 are common fire buttons)
        fire_buttons = [0, 1]  
        button_pressed = False
        
        for button in fire_buttons:
            if self.joystick.get_button(button):
                button_pressed = True
                break
        
        # Detect button press (rising edge)
        if button_pressed and not self.last_fire_button_state:
            self.fire_button_pressed = True
            print("[JoystickController] 🔥 Fire button pressed!")
        
        self.last_fire_button_state = button_pressed
        return button_pressed

    def get_fire_button_pressed(self):
        """Get and clear the fire button pressed state."""
        if self.fire_button_pressed:
            self.fire_button_pressed = False
            return True
        return False

    def manual_mode_control(self):
        """Enhanced manual control with working code logic"""
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
            print("[JoystickController] Lazer AÇ")

        if current_y and not self.prev_y:
            self.serial.send_command(self.LASER_CMD, 0)
            print("[JoystickController] Lazer KAPAT")

        # === Servo Aktif/Pasif Toggle (LB) ===
        if current_lb and not self.prev_lb:
            self.servo_active = not self.servo_active
            print("[JoystickController] Servo:", "Açık" if self.servo_active else "Kilitli")

        # === Stepper Aktif/Pasif Toggle (RB) ===
        if current_rb and not self.prev_rb:
            self.stepper_active = not self.stepper_active
            print("[JoystickController] Stepper:", "Açık" if self.stepper_active else "Kilitli")

        # === Önceki Butonları Güncelle ===
        self.prev_b, self.prev_y, self.prev_lb, self.prev_rb = current_b, current_y, current_lb, current_rb

        now = time.time()

        # === Servo Açı Gönderimi (from working code) ===
        if self.servo_active:
            angle_servo = self.get_servo_angle()
            if angle_servo != self.last_sent_servo and (now - self.last_servo_time) > 0.1:
                self.serial.send_command(self.SERVO_CMD, angle_servo)
                print(f"[JoystickController] Servo açı: {angle_servo}")
                self.last_sent_servo = angle_servo
                self.last_servo_time = now

        # === Stepper Açı Gönderimi (IMPROVED ACCELERATION CONTROL) ===
        if self.stepper_active:
            angle_stepper = self.get_stepper_angle()
            
            # Enhanced acceleration-based filtering
            angle_diff = abs(angle_stepper - self.last_sent_stepper)
            time_since_last = now - self.last_stepper_time
            
            # More responsive control with acceleration-based movement
            # Send command if:
            # 1. Angle changed significantly (> 2 degrees for more responsive control)
            # 2. OR enough time has passed (> 150ms for smooth updates)
            # 3. AND minimum time between commands (> 80ms for faster response)
            should_send = (angle_diff > 2.0 or time_since_last > 0.15) and time_since_last > 0.08
            
            if should_send and angle_stepper != self.last_sent_stepper:
                # Round to nearest integer to avoid floating point issues
                rounded_angle = int(round(angle_stepper))
                self.serial.send_command(self.STEPPER_CMD, rounded_angle)
                
                # Enhanced status reporting
                status_msg = f"Stepper: {rounded_angle}°"
                if self.stepper_movement_active:
                    status_msg += f" (Moving, Vel: {self.current_stepper_velocity:.1f}°/s)"
                else:
                    status_msg += " (Holding)"
                print(f"[JoystickController] {status_msg}")
                
                self.last_sent_stepper = angle_stepper
                self.last_stepper_time = now

    def get_position(self):
        if self.joystick:
            pygame.event.pump()
            x_axis = self.joystick.get_axis(0)
            y_axis = self.joystick.get_axis(1)
            return (x_axis, y_axis)
        else:
            return (0, 0)

    def get_button_pressed(self, button_index):
        if self.joystick:
            pygame.event.pump()
            return self.joystick.get_button(button_index)
        return False

    def get_control_status(self):
        """Get current control status including acceleration parameters."""
        return {
            'servo_velocity': self.current_servo_velocity,
            'stepper_velocity': self.current_stepper_velocity,
            'servo_position': self.current_servo_position,
            'stepper_position': self.current_stepper_position,
            'servo_active': self.servo_active,
            'stepper_active': self.stepper_active
        }

    def calibrate_deadzone(self):
        if not self.joystick:
            print("[JoystickController] ❌ Joystick bulunamadı, kalibrasyon yapılamıyor.")
            return
        print("\n[JoystickController] 🔧 Ölü Bölge Kalibrasyonu")
        print("[JoystickController] Joystick'i merkeze bırakın ve Enter'a basın...")
        input()
        pygame.event.pump()
        x = self.joystick.get_axis(0)
        y = self.joystick.get_axis(1)
        print(f"[JoystickController] 📊 Merkez değerleri: X={x:.3f}, Y={y:.3f}")
        max_offset = max(abs(x), abs(y))
        suggested_deadzone = max_offset + 0.05
        print(f"[JoystickController] 💡 Önerilen ölü bölge: {suggested_deadzone:.2f}")
        print(f"[JoystickController] ⚙ Ölü bölge: {self.deadzone:.2f}")
        if suggested_deadzone > self.deadzone:
            print("[JoystickController] ⚠ Ölü bölge artırılması önerilir.")
        else:
            print("[JoystickController] ✅ Mevcut ölü bölge yeterli.")

    def close(self):
        pygame.quit()
        print("[JoystickController] 🔌 Bağlantı kapatıldı.")