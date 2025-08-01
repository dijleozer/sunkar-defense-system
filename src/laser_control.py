import time
import threading

class LaserControl:
    def __init__(self, serial_comm):
        self.serial = serial_comm
        self.laser_active = False
        self.fire_duration = 0.3  # 300ms default fire duration
        self.fire_thread = None
        self.laser_lock = threading.Lock()  # Thread safety lock
        
        # Fire restriction zone settings
        self.fire_restriction_active = False
        self.restricted_start_angle = -15  # Default restricted zone
        self.restricted_end_angle = 15
        self.current_yaw_angle = 0  # Current turret yaw angle (horizontal)
        self.current_pitch_angle = 0  # Current turret pitch angle (vertical)

    def set_fire_restriction_zone(self, start_angle, end_angle):
        """Set the fire restriction zone angles."""
        self.restricted_start_angle = float(start_angle)
        self.restricted_end_angle = float(end_angle)
        self.fire_restriction_active = True
        print(f"[LaserControl] 🔒 Fire restriction zone set: ({start_angle}°, {end_angle}°)")

    def clear_fire_restriction_zone(self):
        """Clear the fire restriction zone."""
        self.fire_restriction_active = False
        print("[LaserControl] 🔓 Fire restriction zone cleared")

    def update_turret_position(self, yaw_angle, pitch_angle):
        """Update current turret position for restriction checking."""
        self.current_yaw_angle = float(yaw_angle)
        self.current_pitch_angle = float(pitch_angle)

    def is_in_restricted_zone(self):
        """Check if current turret position is in the restricted zone."""
        if not self.fire_restriction_active:
            return False
            
        # Normalize angles to handle wraparound
        current_angle = self.current_yaw_angle % 360
        start_angle = self.restricted_start_angle % 360
        end_angle = self.restricted_end_angle % 360
        
        # Handle angle ranges that cross 0°/360° boundary
        if start_angle <= end_angle:
            # Normal case: start < end (e.g., -15° to 15° becomes 345° to 15°)
            return start_angle <= current_angle <= end_angle
        else:
            # Wraparound case: start > end (e.g., 345° to 15°)
            return current_angle >= start_angle or current_angle <= end_angle

    def can_fire(self):
        """Check if firing is allowed at current turret position."""
        if not self.fire_restriction_active:
            return True  # No restrictions active
            
        if self.is_in_restricted_zone():
            print(f"[LaserControl] 🚫 Firing blocked - Turret in restricted zone: {self.current_yaw_angle}°")
            return False
        else:
            print(f"[LaserControl] ✅ Firing allowed - Turret position: {self.current_yaw_angle}°")
            return True

    def fire_laser(self, duration=None):
        """Fire the laser for a specified duration (default 300ms)."""
        if duration is None:
            duration = self.fire_duration
            
        # Check if firing is allowed
        if not self.can_fire():
            print("[LaserControl] 🚫 Fire command blocked - Turret in restricted zone")
            return
            
        # Thread safety - only one thread can fire at a time
        with self.laser_lock:
            if self.laser_active:
                print("[LaserControl] ⚠️ Laser already active, ignoring fire command")
                return
                
            # Start fire in a separate thread to avoid blocking
            if self.fire_thread and self.fire_thread.is_alive():
                return
                
            self.fire_thread = threading.Thread(target=self._fire_laser_thread, args=(duration,))
            self.fire_thread.daemon = True
            self.fire_thread.start()

    def _fire_laser_thread(self, duration):
        """Internal method to fire laser in a separate thread."""
        try:
            print(f"[LaserControl] 🔥 Firing laser for {duration}s")
            self.laser_active = True
            
            # Send trigger command - Arduino will handle the 300ms ON, 700ms OFF pattern
            self.serial.send_command(0x03, 1)
            
            # Wait for the pattern to complete (300ms + 700ms = 1000ms)
            time.sleep(1.0)
            
            print("[LaserControl] 🔇 Laser fire complete")
            self.laser_active = False
            # Don't send OFF command - let Arduino handle timing
            
        except Exception as e:
            print(f"[LaserControl] ❌ Error during laser fire: {e}")
            self.laser_active = False
            self.serial.send_command(0x03, 0)  # Emergency OFF

    def turn_on(self):
        """Turn laser ON - triggers 300ms ON, 700ms OFF pattern."""
        # Check if firing is allowed
        if not self.can_fire():
            print("[LaserControl] 🚫 Laser ON blocked - Turret in restricted zone")
            return
            
        with self.laser_lock:
            if not self.laser_active:
                self.laser_active = True
                # Send trigger command - Arduino handles the pattern timing
                self.serial.send_command(0x03, 1)
                print("[LaserControl] 🔴 Laser turned ON (300ms ON, 700ms OFF pattern)")
            else:
                print("[LaserControl] ⚠️ Laser already ON")
        
    def turn_off(self):
        """Turn laser OFF immediately."""
        with self.laser_lock:
            self.laser_active = False
            self.serial.send_command(0x03, 0)
            print("[LaserControl] ⚫ Laser turned OFF")

    def is_active(self):
        """Check if laser is currently active."""
        return self.laser_active

    def set_fire_duration(self, duration):
        """Set the default fire duration in seconds."""
        self.fire_duration = duration
        print(f"[LaserControl] ⚙️ Fire duration set to {duration}s")

    def emergency_stop(self):
        """Emergency stop - immediately turn off laser."""
        with self.laser_lock:
            self.laser_active = False
            self.serial.send_command(0x03, 0)
            print("[LaserControl] 🚨 Emergency stop - Laser OFF")

    def get_safety_info(self):
        """Get current safety settings."""
        return {
            'current_duration': self.fire_duration,
            'max_duration': 0.3,  # Fixed at 300ms for hardware compatibility
            'is_active': self.laser_active,
            'fire_restriction_active': self.fire_restriction_active,
            'restricted_zone': (self.restricted_start_angle, self.restricted_end_angle) if self.fire_restriction_active else None,
            'current_position': (self.current_yaw_angle, self.current_pitch_angle),
            'in_restricted_zone': self.is_in_restricted_zone()
        }