import time
import threading
import math
from enum import Enum

class ScanMode(Enum):
    RADAR_SWEEP = "radar_sweep"
    TRACKING = "tracking"

class SimpleRadarTracker:
    """
    Simple and effective radar tracking system for balloon detection.
    - Scans horizontally like a radar when no target is found
    - Tracks red balloons smoothly when detected
    - Prevents overshooting with gentle movement
    """
    
    def __init__(self, serial_comm, camera_manager):
        self.serial = serial_comm
        self.camera = camera_manager
        
        # Motor limits
        self.servo_min = 0
        self.servo_max = 60
        self.stepper_min = 0
        self.stepper_max = 300
        
        # Current motor positions
        self.current_servo = 30  # Start at middle servo position
        self.current_stepper = 150  # Start at middle stepper position
        
        # Scanning parameters
        self.scan_mode = ScanMode.RADAR_SWEEP
        self.scan_speed = 1.0  # degrees per second (slow and smooth)
        self.scan_direction = 1  # 1 = right, -1 = left
        self.last_scan_time = time.time()
        
        # Target tracking
        self.current_target = None
        self.target_lost_timeout = 3.0  # seconds
        self.last_target_time = 0
        
        # Movement control (gentle to prevent overshooting)
        self.movement_speed = 1.5  # degrees per update (reduced from 3.0)
        self.movement_interval = 0.1  # 100ms between movements (slower)
        self.last_movement_time = time.time()
        
        # Center threshold for tracking
        self.center_threshold = 0.15  # 15% of frame size (increased for easier tracking)
        
        # Threading
        self.running = False
        self.control_thread = None
        
        print("[SimpleRadarTracker] 🚀 Simple radar tracker initialized")
        print("[SimpleRadarTracker] 📡 Will scan when no target, track when red balloon found")
        
    def start(self):
        """Start the radar tracking system."""
        if self.control_thread and self.control_thread.is_alive():
            print("[SimpleRadarTracker] ⚠️ System already running")
            return
            
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        print("[SimpleRadarTracker] 🚀 Radar tracking system started")
        
    def stop(self):
        """Stop the radar tracking system."""
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
        print("[SimpleRadarTracker] 🛑 Radar tracking system stopped")
        
    def _control_loop(self):
        """Main control loop."""
        while self.running:
            try:
                self._update_targets()
                self._execute_current_mode()
                time.sleep(0.05)  # 20 FPS control loop
            except Exception as e:
                print(f"[SimpleRadarTracker] ❌ Error in control loop: {e}")
                time.sleep(0.1)
                
    def _update_targets(self):
        """Update target list from camera detections."""
        if not hasattr(self.camera, 'tracks'):
            return
            
        current_time = time.time()
        tracks = self.camera.tracks if hasattr(self.camera, 'tracks') else []
        
        # Find red balloons (enemies)
        red_balloons = []
        for track in tracks:
            if track.get('label', '').lower() == 'red':
                red_balloons.append(track)
        
        # Select best target (largest and most centered)
        if red_balloons:
            best_target = self._select_best_target(red_balloons)
            if best_target:
                self.current_target = best_target
                self.last_target_time = current_time
                self.scan_mode = ScanMode.TRACKING
                print(f"[SimpleRadarTracker] 🎯 Target acquired: {best_target['track_id']}")
        else:
            # Check if we should lose current target
            if (self.current_target and 
                current_time - self.last_target_time > self.target_lost_timeout):
                print(f"[SimpleRadarTracker] 🔄 Lost target {self.current_target['track_id']}")
                self.current_target = None
                self.scan_mode = ScanMode.RADAR_SWEEP
                
    def _select_best_target(self, red_balloons):
        """Select the best target based on size and position."""
        if not red_balloons:
            return None
            
        best_target = None
        best_score = 0
        
        frame_height, frame_width = 480, 640  # Standard camera resolution
        
        for target in red_balloons:
            bbox = target['bbox']
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            # Calculate target size
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            area = width * height
            
            # Calculate distance from center
            center_distance = math.sqrt(
                ((center_x - frame_width/2) / frame_width) ** 2 +
                ((center_y - frame_height/2) / frame_height) ** 2
            )
            
            # Score based on size and center proximity
            # Larger targets and more centered targets get higher scores
            size_score = area / (frame_width * frame_height)  # Normalized area
            center_score = 1.0 - center_distance  # Closer to center = higher score
            
            total_score = size_score * 0.7 + center_score * 0.3
            
            if total_score > best_score:
                best_score = total_score
                best_target = target
                
        return best_target
        
    def _execute_current_mode(self):
        """Execute current scanning/tracking mode."""
        if self.scan_mode == ScanMode.RADAR_SWEEP:
            self._radar_sweep()
        elif self.scan_mode == ScanMode.TRACKING:
            self._track_target()
            
    def _radar_sweep(self):
        """Simple horizontal radar sweep."""
        current_time = time.time()
        if current_time - self.last_scan_time < 0.1:  # 100ms between scan movements
            return
            
        # Move stepper motor in a sweeping pattern
        self.current_stepper += self.scan_speed * self.scan_direction
        
        # Reverse direction at boundaries
        if self.current_stepper >= self.stepper_max:
            self.current_stepper = self.stepper_max
            self.scan_direction = -1
        elif self.current_stepper <= self.stepper_min:
            self.current_stepper = self.stepper_min
            self.scan_direction = 1
            
        # Send motor commands
        self._send_motor_commands()
        self.last_scan_time = current_time
        
        print(f"[SimpleRadarTracker] 📡 Scanning: Stepper={self.current_stepper:.1f}°")
        
    def _track_target(self):
        """Track current target smoothly."""
        if not self.current_target:
            return
            
        current_time = time.time()
        if current_time - self.last_movement_time < self.movement_interval:
            return
            
        # Get target center
        bbox = self.current_target['bbox']
        target_center_x = (bbox[0] + bbox[2]) / 2
        target_center_y = (bbox[1] + bbox[3]) / 2
        
        # Get frame dimensions
        frame_height, frame_width = 480, 640
        
        # Calculate normalized position (0-1)
        x_normalized = target_center_x / frame_width
        y_normalized = target_center_y / frame_height
        
        # Convert to motor angles
        target_stepper = self.stepper_min + x_normalized * (self.stepper_max - self.stepper_min)
        target_servo = self.servo_min + (1.0 - y_normalized) * (self.servo_max - self.servo_min)  # Invert Y
        
        # Calculate movement needed
        stepper_diff = target_stepper - self.current_stepper
        servo_diff = target_servo - self.current_servo
        
        # Apply gentle movement limits
        if abs(stepper_diff) > self.movement_speed:
            stepper_diff = self.movement_speed if stepper_diff > 0 else -self.movement_speed
            
        if abs(servo_diff) > self.movement_speed:
            servo_diff = self.movement_speed if servo_diff > 0 else -self.movement_speed
            
        # Update motor positions
        self.current_stepper += stepper_diff
        self.current_servo += servo_diff
        
        # Clamp to motor limits
        self.current_stepper = max(self.stepper_min, min(self.stepper_max, self.current_stepper))
        self.current_servo = max(self.servo_min, min(self.servo_max, self.current_servo))
        
        # Send motor commands
        self._send_motor_commands()
        self.last_movement_time = current_time
        
        print(f"[SimpleRadarTracker] 🎯 Tracking: Stepper={self.current_stepper:.1f}°, Servo={self.current_servo:.1f}°")
        print(f"[SimpleRadarTracker] 🎯 Target at ({target_center_x:.1f}, {target_center_y:.1f})")
        
    def _send_motor_commands(self):
        """Send motor commands to Arduino."""
        if not self.serial:
            return
            
        try:
            # Send servo command
            self.serial.send_command(0x01, int(self.current_servo))
            
            # Send stepper command
            self.serial.send_command(0x02, int(self.current_stepper))
            
        except Exception as e:
            print(f"[SimpleRadarTracker] ❌ Error sending motor commands: {e}")
            
    def set_scan_speed(self, speed):
        """Set scanning speed in degrees per second."""
        self.scan_speed = max(0.5, min(3.0, speed))
        print(f"[SimpleRadarTracker] ⚡ Scan speed set to: {self.scan_speed}°/s")
        
    def set_movement_speed(self, speed):
        """Set movement speed in degrees per update."""
        self.movement_speed = max(0.5, min(3.0, speed))
        print(f"[SimpleRadarTracker] ⚡ Movement speed set to: {self.movement_speed}°/update")
        
    def get_status(self):
        """Get current system status."""
        return {
            'scan_mode': self.scan_mode.value,
            'current_target': self.current_target['track_id'] if self.current_target else None,
            'servo_angle': self.current_servo,
            'stepper_angle': self.current_stepper,
            'scan_speed': self.scan_speed,
            'movement_speed': self.movement_speed
        }
        
    def emergency_stop(self):
        """Emergency stop - stop all movement."""
        if self.serial:
            self.serial.send_command(0x01, 30)  # Center servo
            self.serial.send_command(0x02, 150)  # Center stepper
        print("[SimpleRadarTracker] 🚨 Emergency stop executed")
        
    def reset_position(self):
        """Reset to safe starting position."""
        self.current_servo = 30
        self.current_stepper = 150
        self._send_motor_commands()
        print("[SimpleRadarTracker] 🔄 Reset to safe position") 