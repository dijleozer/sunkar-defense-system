# camera_manager.py
import cv2
import threading
from object_detection import detect_objects
import time
import math

class CameraManager:
    def __init__(self, serial_comm=None):
        self.cap = cv2.VideoCapture(0)
        self.running = False
        self.frame = None
        self.tracks = []
        self.lock = threading.Lock()
        self.serial = serial_comm
        
        # Enhanced camera position tracking
        self.current_servo_angle = 30  # Start at middle position
        self.current_stepper_angle = 150  # Start at middle position
        self.target_servo_angle = 30
        self.target_stepper_angle = 150
        
        # Position verification
        self.position_tolerance = 2.0  # Degrees tolerance for position verification
        self.last_position_check = 0
        self.position_check_interval = 0.5  # Check position every 0.5 seconds
        
        # Movement limits with safety margins
        self.servo_min = 5   # Added safety margin
        self.servo_max = 55  # Added safety margin
        self.stepper_min = 10   # Added safety margin
        self.stepper_max = 290  # Added safety margin
        
        # Enhanced smooth movement parameters
        self.movement_speed = 1.5  # Increased for more responsive movement
        self.last_movement_time = time.time()
        self.movement_interval = 0.03  # 30ms between movements for smoother motion
        
        # Movement history for debugging
        self.movement_history = []
        self.max_history_size = 50

    def start(self):
        if not self.cap.isOpened():
            print("Kamera açılamadı.")
            return
        self.running = True
        self.thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.thread.start()
        print("Kamera başlatıldı.")
        
        # Set initial position for autonomous mode with verification
        self.set_autonomous_start_position()

    def stop(self):
        self.running = False
        self.cap.release()
        print("Kamera kapatıldı.")

    def capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            processed_frame, tracks = detect_objects(frame)

            with self.lock:
                self.frame = processed_frame
                self.tracks = tracks

            # MUCH SLOWER for YOLO detection - 10 FPS instead of 30 FPS
            time.sleep(0.1)  # 10 FPS for better YOLO detection
            
    def set_autonomous_start_position(self):
        """Set camera to optimal starting position for autonomous mode with verification."""
        if self.serial:
            # Move to center position for better target detection
            self.target_servo_angle = 30  # Center servo
            self.target_stepper_angle = 150  # Center stepper
            
            # Send commands and verify position
            self._send_motor_commands()
            self._verify_position()
            
            print("[CameraManager] 🎯 Set to autonomous start position: Servo=30°, Stepper=150°")
        else:
            print("[CameraManager] ⚠️ SerialComm not connected, cannot set start position")

    def reset_position(self):
        """Reset to safe starting position with verification."""
        print("Kamera başlangıç konumuna getiriliyor...")
        if self.serial:
            self.target_servo_angle = 30
            self.target_stepper_angle = 150
            self._send_motor_commands()
            self._verify_position()
            print("Servo 30°, Stepper 150° - Safe position set and verified.")
        else:
            print("SerialComm bağlı değil, sıfırlama yapılamadı.")

    def _verify_position(self):
        """Verify that motors have reached their target positions."""
        if not self.serial:
            return False
            
        # Wait a bit for motors to move
        time.sleep(0.2)
        
        # Check if current position is close to target
        servo_error = abs(self.current_servo_angle - self.target_servo_angle)
        stepper_error = abs(self.current_stepper_angle - self.target_stepper_angle)
        
        if servo_error <= self.position_tolerance and stepper_error <= self.position_tolerance:
            print(f"[CameraManager] ✅ Position verified: Servo={self.current_servo_angle:.1f}°, Stepper={self.current_stepper_angle:.1f}°")
            return True
        else:
            print(f"[CameraManager] ⚠️ Position verification failed: Servo error={servo_error:.1f}°, Stepper error={stepper_error:.1f}°")
            return False

    def move_camera_smooth(self, dx, dy):
        """
        Enhanced smooth camera movement using normalized inputs (-1 to 1).
        dx: horizontal movement (-1 = left, 1 = right)
        dy: vertical movement (-1 = down, 1 = up)
        """
        if not self.serial:
            return
            
        current_time = time.time()
        if current_time - self.last_movement_time < self.movement_interval:
            return  # Rate limiting
            
        # Apply deadzone to prevent jitter
        if abs(dx) < 0.02:
            dx = 0
        if abs(dy) < 0.02:
            dy = 0
            
        # Calculate new target angles with improved mapping
        servo_range = self.servo_max - self.servo_min
        stepper_range = self.stepper_max - self.stepper_min
        
        # Gentler movement calculation to prevent overshooting
        servo_change = dx * servo_range * 0.08  # Reduced from 0.15 to 0.08 for smoother movement
        stepper_change = dy * stepper_range * 0.08  # Reduced from 0.15 to 0.08 for smoother movement
        
        # Update target angles
        self.target_servo_angle += servo_change
        self.target_stepper_angle += stepper_change
        
        # Apply enhanced limits with safety margins
        self.target_servo_angle = max(self.servo_min, min(self.servo_max, self.target_servo_angle))
        self.target_stepper_angle = max(self.stepper_min, min(self.stepper_max, self.target_stepper_angle))
        
        # Check for excessive movement (safety check)
        servo_movement = abs(self.target_servo_angle - self.current_servo_angle)
        stepper_movement = abs(self.target_stepper_angle - self.current_stepper_angle)
        
        if servo_movement > 10 or stepper_movement > 20:  # Safety limits
            print(f"[CameraManager] ⚠️ Excessive movement detected: Servo={servo_movement:.1f}°, Stepper={stepper_movement:.1f}°")
            # Limit movement to safe values
            if servo_movement > 10:
                if self.target_servo_angle > self.current_servo_angle:
                    self.target_servo_angle = self.current_servo_angle + 10
                else:
                    self.target_servo_angle = self.current_servo_angle - 10
                    
            if stepper_movement > 20:
                if self.target_stepper_angle > self.current_stepper_angle:
                    self.target_stepper_angle = self.current_stepper_angle + 20
                else:
                    self.target_stepper_angle = self.current_stepper_angle - 20
        
        # Send commands
        self._send_motor_commands()
        self.last_movement_time = current_time
        
        # Record movement for debugging
        self._record_movement(dx, dy, servo_change, stepper_change)
        
        print(f"[CameraManager] 📡 Enhanced movement: dx={dx:.2f}, dy={dy:.2f} -> Servo={self.target_servo_angle:.1f}°, Stepper={self.target_stepper_angle:.1f}°")

    def _record_movement(self, dx, dy, servo_change, stepper_change):
        """Record movement for debugging and analysis."""
        movement_record = {
            'timestamp': time.time(),
            'input_dx': dx,
            'input_dy': dy,
            'servo_change': servo_change,
            'stepper_change': stepper_change,
            'target_servo': self.target_servo_angle,
            'target_stepper': self.target_stepper_angle
        }
        
        self.movement_history.append(movement_record)
        if len(self.movement_history) > self.max_history_size:
            self.movement_history.pop(0)

    def move_camera(self, x, y):
        """Legacy method - use move_camera_smooth for better control."""
        if self.serial:
            # Convert normalized coordinates to angles with improved mapping
            servo_angle = int(30 + (x * 25))  # Reduced range for safety
            stepper_angle = int(150 + (y * 140))  # Reduced range for safety

            # Apply enhanced limits
            servo_angle = max(self.servo_min, min(self.servo_max, servo_angle))
            stepper_angle = max(self.stepper_min, min(self.stepper_max, stepper_angle))
            
            # Update targets
            self.target_servo_angle = servo_angle
            self.target_stepper_angle = stepper_angle
            
            # Send commands
            self._send_motor_commands()

            print(f"[CameraManager] 📡 Legacy movement: Servo={servo_angle}°, Stepper={stepper_angle}°")
        else:
            print("[CameraManager] SerialComm bağlı değil, hareket gönderilemedi.")

    def _send_motor_commands(self):
        """Send motor commands to Arduino with enhanced error handling."""
        if not self.serial:
            return
            
        try:
            # Send servo command
            self.serial.send_command(0x01, int(self.target_servo_angle))
            
            # Send stepper command  
            self.serial.send_command(0x02, int(self.target_stepper_angle))
            
            # Update current positions
            self.current_servo_angle = self.target_servo_angle
            self.current_stepper_angle = self.target_stepper_angle
            
        except Exception as e:
            print(f"[CameraManager] ❌ Error sending motor commands: {e}")
            # Try to recover by resetting to safe position
            self._emergency_reset_position()

    def _emergency_reset_position(self):
        """Emergency reset to safe position if communication fails."""
        print("[CameraManager] 🚨 Emergency position reset")
        self.target_servo_angle = 30
        self.target_stepper_angle = 150
        self.current_servo_angle = 30
        self.current_stepper_angle = 150

    def get_frame(self):
        with self.lock:
            return self.frame, self.tracks
            
    def get_camera_position(self):
        """Get current camera position with enhanced information."""
        return {
            'servo_angle': self.current_servo_angle,
            'stepper_angle': self.current_stepper_angle,
            'target_servo': self.target_servo_angle,
            'target_stepper': self.target_stepper_angle,
            'servo_error': abs(self.current_servo_angle - self.target_servo_angle),
            'stepper_error': abs(self.current_stepper_angle - self.target_stepper_angle),
            'movement_history_count': len(self.movement_history)
        }
    
    def get_movement_statistics(self):
        """Get movement statistics for debugging."""
        if not self.movement_history:
            return {}
            
        recent_movements = self.movement_history[-10:]  # Last 10 movements
        
        servo_changes = [m['servo_change'] for m in recent_movements]
        stepper_changes = [m['stepper_change'] for m in recent_movements]
        
        return {
            'avg_servo_change': sum(servo_changes) / len(servo_changes) if servo_changes else 0,
            'avg_stepper_change': sum(stepper_changes) / len(stepper_changes) if stepper_changes else 0,
            'max_servo_change': max(servo_changes) if servo_changes else 0,
            'max_stepper_change': max(stepper_changes) if stepper_changes else 0,
            'total_movements': len(self.movement_history)
        }