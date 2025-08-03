import time
import threading
import math
import numpy as np
import cv2
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class TargetType(Enum):
    ENEMY = "red_balloon"  # Red balloon = enemy to destroy
    FRIENDLY = "blue_balloon"  # Blue balloon = friendly
    UNKNOWN = "unknown"

@dataclass
class BalloonTarget:
    track_id: int
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]  # x, y center
    target_type: TargetType
    confidence: float
    last_seen: float
    priority: int = 0

class SimpleAutonomousMode:
    """
    Simple autonomous mode for air defense system.
    Self-contained with built-in defaults - no user input required.
    Features: detect, scan, track, and act autonomously.
    """
    
    def __init__(self, serial_comm, laser_control, camera_manager, motor_control):
        self.serial_comm = serial_comm
        self.laser_control = laser_control
        self.camera_manager = camera_manager
        self.motor_control = motor_control
        
        # Motor control parameters (built-in defaults)
        self.servo_min = 5
        self.servo_max = 55
        self.stepper_min = 10
        self.stepper_max = 290
        
        # Current motor positions
        self.current_servo_angle = 30
        self.current_stepper_angle = 150
        
        # Camera frame dimensions (will be updated from camera)
        self.frame_width = 640
        self.frame_height = 480
        self.crosshair_x = 320
        self.crosshair_y = 240
        
        # Target tracking (built-in defaults)
        self.targets: List[BalloonTarget] = []
        self.current_target: Optional[BalloonTarget] = None
        self.target_lost_timeout = 2.0  # seconds
        self.tracking_threshold = 0.6  # confidence threshold
        
        # Spiral scanning parameters (MUCH SLOWER for YOLO detection)
        self.spiral_center_servo = 30  # Center servo position
        self.spiral_center_stepper = 150  # Center stepper position
        self.spiral_radius = 0  # Current spiral radius
        self.spiral_angle = 0  # Current spiral angle (radians)
        self.spiral_radius_step = 0.2  # MUCH SLOWER - reduced from 0.5
        self.spiral_angle_step = 0.05  # MUCH SLOWER - reduced from 0.1
        self.max_spiral_radius = 15  # Reduced from 20 - smaller scan area
        self.spiral_reset_threshold = 20  # Reduced from 25
        
        # Movement control (MUCH SLOWER for YOLO detection)
        self.movement_speed = 0.5  # MUCH SLOWER - reduced from 1.0
        self.movement_interval = 0.2  # MUCH SLOWER - increased from 0.05 (5x slower)
        self.last_movement_time = time.time()
        self.movement_tolerance = 0.3  # More precise positioning
        
        # Auto-fire settings (built-in defaults)
        self.auto_fire_enabled = True
        self.auto_fire_delay = 0.5  # seconds between shots
        self.last_auto_fire_time = time.time()
        self.auto_fire_range = 50  # pixels from crosshair center
        
        # Autonomous mode state
        self.is_active = False
        self.running = False
        self.control_thread = None
        
        # Performance tracking
        self.fps_counter = 0
        self.last_fps_time = time.time()
        
    def start_autonomous_mode(self):
        """Start autonomous mode - no configuration needed."""
        if self.is_active:
            print("[SimpleAutonomous] ⚠️ Autonomous mode already active")
            return
            
        self.is_active = True
        self.running = True
        
        # Initialize camera frame dimensions
        if self.camera_manager.frame is not None:
            self.frame_height, self.frame_width = self.camera_manager.frame.shape[:2]
            self.crosshair_x = self.frame_width // 2
            self.crosshair_y = self.frame_height // 2
        
        # Start control thread
        self.control_thread = threading.Thread(target=self._autonomous_loop, daemon=True)
        self.control_thread.start()
        
        print("[SimpleAutonomous] 🚀 Autonomous mode started")
        print(f"[SimpleAutonomous] 📐 Frame: {self.frame_width}x{self.frame_height}")
        print(f"[SimpleAutonomous] 🎯 Crosshair: ({self.crosshair_x}, {self.crosshair_y})")
        
    def stop_autonomous_mode(self):
        """Stop autonomous mode."""
        self.is_active = False
        self.running = False
        
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
            
        # Stop laser
        if self.laser_control:
            self.laser_control.stop_laser()
            
        print("[SimpleAutonomous] 🛑 Autonomous mode stopped")
        
    def _autonomous_loop(self):
        """Main autonomous control loop - makes all decisions automatically."""
        while self.running and self.is_active:
            try:
                # Update frame dimensions if needed
                self._update_frame_dimensions()
                
                # Process camera frame and detect targets
                self._process_camera_frame()
                
                # Execute appropriate action based on targets
                if self.current_target:
                    self._track_target()
                else:
                    self._execute_scanning()
                
                # Auto-fire logic
                if self.auto_fire_enabled and self.current_target:
                    self._auto_fire_logic()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # MUCH SLOWER loop for YOLO detection - 10 FPS instead of 50 FPS
                time.sleep(0.1)  # 10 FPS control loop (5x slower)
                
            except Exception as e:
                print(f"[SimpleAutonomous] ❌ Error in autonomous loop: {e}")
                time.sleep(0.2)  # Slower error recovery
                
    def _update_frame_dimensions(self):
        """Update frame dimensions from camera."""
        if self.camera_manager.frame is not None:
            height, width = self.camera_manager.frame.shape[:2]
            if width != self.frame_width or height != self.frame_height:
                self.frame_width = width
                self.frame_height = height
                self.crosshair_x = width // 2
                self.crosshair_y = height // 2
                print(f"[SimpleAutonomous] 📐 Updated frame: {width}x{height}")
                
    def _process_camera_frame(self):
        """Process camera frame and detect balloon targets."""
        if self.camera_manager.frame is None:
            return
            
        # Get current tracks from camera manager
        tracks = self.camera_manager.tracks
        
        # Update targets list
        current_time = time.time()
        new_targets = []
        
        for track in tracks:
            # Check if this is a balloon detection
            if 'label' in track and 'balloon' in track['label'].lower():
                bbox = track['bbox']
                center_x = (bbox[0] + bbox[2]) // 2
                center_y = (bbox[1] + bbox[3]) // 2
                
                # Determine target type based on color analysis
                target_type = self._classify_balloon_color(track)
                
                # Create balloon target
                balloon_target = BalloonTarget(
                    track_id=track['track_id'],
                    bbox=bbox,
                    center=(center_x, center_y),
                    target_type=target_type,
                    confidence=track.get('confidence', 0.0),
                    last_seen=current_time,
                    priority=1 if target_type == TargetType.ENEMY else 0
                )
                
                new_targets.append(balloon_target)
        
        # Update targets list and find current target
        self.targets = new_targets
        self._update_current_target()
        
    def _classify_balloon_color(self, track):
        """Classify balloon color based on detection results."""
        label = track.get('label', '').lower()
        
        if 'red' in label or 'kirmizi' in label:
            return TargetType.ENEMY
        elif 'blue' in label or 'mavi' in label:
            return TargetType.FRIENDLY
        else:
            return TargetType.UNKNOWN
            
    def _update_current_target(self):
        """Update current target based on priority and tracking status."""
        current_time = time.time()
        
        # Remove old targets
        self.targets = [t for t in self.targets if current_time - t.last_seen < self.target_lost_timeout]
        
        if not self.targets:
            self.current_target = None
            return
            
        # Find highest priority enemy target
        enemy_targets = [t for t in self.targets if t.target_type == TargetType.ENEMY]
        
        if enemy_targets:
            # Select closest enemy target to crosshair
            best_target = min(enemy_targets, key=lambda t: self._distance_to_crosshair(t.center))
            self.current_target = best_target
        else:
            self.current_target = None
            
    def _distance_to_crosshair(self, target_center):
        """Calculate distance from target center to crosshair."""
        dx = target_center[0] - self.crosshair_x
        dy = target_center[1] - self.crosshair_y
        return math.sqrt(dx*dx + dy*dy)
        
    def _track_target(self):
        """Track current target with smooth motor control."""
        if not self.current_target:
            return
            
        target_center = self.current_target.center
        dx = target_center[0] - self.crosshair_x
        dy = target_center[1] - self.crosshair_y
        
        # Calculate required motor movements
        servo_delta = self._calculate_servo_movement(dy)
        stepper_delta = self._calculate_stepper_movement(dx)
        
        # Apply smooth movement
        self._smooth_motor_movement(servo_delta, stepper_delta)
            
    def _calculate_servo_movement(self, dy):
        """Calculate servo movement based on vertical offset."""
        # Convert pixel offset to servo angle change
        servo_range = self.servo_max - self.servo_min
        pixel_to_angle = servo_range / self.frame_height
        
        return -dy * pixel_to_angle  # Negative because servo angle increases downward
        
    def _calculate_stepper_movement(self, dx):
        """Calculate stepper movement based on horizontal offset."""
        # Convert pixel offset to stepper angle change
        stepper_range = self.stepper_max - self.stepper_min
        pixel_to_angle = stepper_range / self.frame_width
        
        return dx * pixel_to_angle
        
    def _smooth_motor_movement(self, servo_delta, stepper_delta):
        """Apply smooth motor movement with acceleration."""
        current_time = time.time()
        
        if current_time - self.last_movement_time < self.movement_interval:
            return
            
        # Apply movement speed limiting
        max_delta = self.movement_speed
        servo_delta = max(-max_delta, min(max_delta, servo_delta))
        stepper_delta = max(-max_delta, min(max_delta, stepper_delta))
        
        # Update motor positions
        new_servo = self.current_servo_angle + servo_delta
        new_stepper = self.current_stepper_angle + stepper_delta
        
        # Apply limits
        new_servo = max(self.servo_min, min(self.servo_max, new_servo))
        new_stepper = max(self.stepper_min, min(self.stepper_max, new_stepper))
        
        # Send motor commands
        if abs(new_servo - self.current_servo_angle) > self.movement_tolerance:
            self.motor_control.set_servo_angle(int(new_servo))
            self.current_servo_angle = new_servo
            
        if abs(new_stepper - self.current_stepper_angle) > self.movement_tolerance:
            self.motor_control.set_stepper_angle(int(new_stepper))
            self.current_stepper_angle = new_stepper
            
        self.last_movement_time = current_time
        
    def _execute_scanning(self):
        """Execute spiral scanning pattern when no targets detected."""
        current_time = time.time()
        
        if current_time - self.last_movement_time < self.movement_interval:
            return
            
        # Spiral scanning pattern (MUCH SLOWER for YOLO detection)
        self._spiral_scan()
        
        # Add pause for YOLO detection after each movement
        time.sleep(0.3)  # 300ms pause for YOLO to process frame
        
    def _spiral_scan(self):
        """Execute spiral scanning pattern - covers both horizontal and vertical axes."""
        # Calculate spiral position
        servo_offset = self.spiral_radius * math.cos(self.spiral_angle)
        stepper_offset = self.spiral_radius * math.sin(self.spiral_angle)
        
        # Calculate target positions
        target_servo = self.spiral_center_servo + servo_offset
        target_stepper = self.spiral_center_stepper + stepper_offset
        
        # Apply limits
        target_servo = max(self.servo_min, min(self.servo_max, target_servo))
        target_stepper = max(self.stepper_min, min(self.stepper_max, target_stepper))
        
        # Smooth movement to target positions
        self._smooth_move_to_position(target_servo, target_stepper)
        
        # Update spiral parameters (MUCH SLOWER)
        self.spiral_angle += self.spiral_angle_step
        self.spiral_radius += self.spiral_radius_step
        
        # Reset spiral when it gets too large
        if self.spiral_radius >= self.spiral_reset_threshold:
            self._reset_spiral()
            
        # Add extra pause for YOLO detection
        time.sleep(0.2)  # 200ms pause for YOLO processing
            
    def _smooth_move_to_position(self, target_servo, target_stepper):
        """Smoothly move to target position with controlled speed."""
        # Calculate required movements
        servo_delta = target_servo - self.current_servo_angle
        stepper_delta = target_stepper - self.current_stepper_angle
        
        # Limit movement speed for controlled motion
        max_delta = self.movement_speed
        servo_delta = max(-max_delta, min(max_delta, servo_delta))
        stepper_delta = max(-max_delta, min(max_delta, stepper_delta))
        
        # Update positions
        new_servo = self.current_servo_angle + servo_delta
        new_stepper = self.current_stepper_angle + stepper_delta
        
        # Apply limits
        new_servo = max(self.servo_min, min(self.servo_max, new_servo))
        new_stepper = max(self.stepper_min, min(self.stepper_max, new_stepper))
        
        # Send motor commands only if movement is significant
        if abs(new_servo - self.current_servo_angle) > self.movement_tolerance:
            self.motor_control.set_servo_angle(int(new_servo))
            self.current_servo_angle = new_servo
            
        if abs(new_stepper - self.current_stepper_angle) > self.movement_tolerance:
            self.motor_control.set_stepper_angle(int(new_stepper))
            self.current_stepper_angle = new_stepper
            
        self.last_movement_time = time.time()
        
    def _reset_spiral(self):
        """Reset spiral to center and start over."""
        self.spiral_radius = 0
        self.spiral_angle = 0
        print("[SimpleAutonomous] 🔄 Spiral scan reset - returning to center")
        
        # Move back to center position
        self._smooth_move_to_position(self.spiral_center_servo, self.spiral_center_stepper)
        
    def _auto_fire_logic(self):
        """Auto-fire logic for enemy targets."""
        if not self.current_target or self.current_target.target_type != TargetType.ENEMY:
            return
            
        current_time = time.time()
        if current_time - self.last_auto_fire_time < self.auto_fire_delay:
            return
            
        # Check if target is close enough to crosshair
        distance = self._distance_to_crosshair(self.current_target.center)
        if distance <= self.auto_fire_range:
            self._fire_laser()
            self.last_auto_fire_time = current_time
            
    def _fire_laser(self):
        """Fire laser at current target."""
        if not self.laser_control:
            return
            
        try:
            self.laser_control.fire_laser()
            time.sleep(0.1)  # Fire for 100ms
            self.laser_control.stop_laser()
            
            print(f"[SimpleAutonomous] 🔫 Fired at enemy target {self.current_target.track_id}")
            
        except Exception as e:
            print(f"[SimpleAutonomous] ❌ Error firing laser: {e}")
            
    def _update_performance_metrics(self):
        """Update performance metrics."""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.last_fps_time >= 1.0:
            fps = self.fps_counter
            self.fps_counter = 0
            self.last_fps_time = current_time
            
            # Print performance info every 10 seconds
            if int(current_time) % 10 == 0:
                target_count = len(self.targets)
                current_target_id = self.current_target.track_id if self.current_target else "None"
                print(f"[SimpleAutonomous] 📊 FPS: {fps}, Targets: {target_count}, Current: {current_target_id}")
                
    def emergency_stop(self):
        """Emergency stop all systems."""
        self.stop_autonomous_mode()
        if self.laser_control:
            self.laser_control.stop_laser()
        if self.motor_control:
            self.motor_control.emergency_stop()
        print("[SimpleAutonomous] 🚨 Emergency stop executed")
        
    def reset_position(self):
        """Reset to safe position."""
        self.current_servo_angle = 30
        self.current_stepper_angle = 150
        
        self.motor_control.set_servo_angle(int(self.current_servo_angle))
        self.motor_control.set_stepper_angle(int(self.current_stepper_angle))
        
        print("[SimpleAutonomous] 🔄 Reset to safe position")
        
    def get_status(self):
        """Get current autonomous mode status."""
        return {
            'is_active': self.is_active,
            'current_target': self.current_target.track_id if self.current_target else None,
            'target_count': len(self.targets),
            'servo_angle': self.current_servo_angle,
            'stepper_angle': self.current_stepper_angle,
            'frame_dimensions': f"{self.frame_width}x{self.frame_height}"
        }
        
    def get_target_info(self):
        """Get current target information."""
        if not self.current_target:
            return None
            
        return {
            'track_id': self.current_target.track_id,
            'target_type': self.current_target.target_type.value,
            'confidence': self.current_target.confidence,
            'center': self.current_target.center,
            'bbox': self.current_target.bbox,
            'distance_to_crosshair': self._distance_to_crosshair(self.current_target.center)
        }
        
    # GUI Integration Methods (NEW - for GUI compatibility)
    def activate(self):
        """Activate autonomous mode - called by GUI."""
        self.start_autonomous_mode()
        
    def deactivate(self):
        """Deactivate autonomous mode - called by GUI."""
        self.stop_autonomous_mode()
        
    def process_frame(self, frame, tracks):
        """Process frame and return target information - called by GUI."""
        if not self.is_active:
            return None, None, "Autonomous mode not active"
            
        # Update camera frame in camera manager
        if hasattr(self.camera_manager, 'frame'):
            self.camera_manager.frame = frame
            
        # Update tracks in camera manager
        if hasattr(self.camera_manager, 'tracks'):
            self.camera_manager.tracks = tracks
            
        # Process the frame (this will update targets)
        self._process_camera_frame()
        
        # Get current target info
        if self.current_target:
            target_bbox = self.current_target.bbox
            target_id = self.current_target.track_id
            
            # Determine status based on target type and distance
            distance = self._distance_to_crosshair(self.current_target.center)
            
            if self.current_target.target_type == TargetType.ENEMY:
                if distance <= self.auto_fire_range:
                    status = f"FIRING at enemy {target_id}"
                else:
                    status = f"TRACKING enemy {target_id} - distance: {distance:.1f}px"
            else:
                status = f"TRACKING {self.current_target.target_type.value} {target_id}"
                
            return target_bbox, target_id, status
        else:
            # No target - show scanning status
            spiral_progress = (self.spiral_radius / self.spiral_reset_threshold) * 100
            status = f"SCANNING - spiral {spiral_progress:.1f}% complete"
            return None, None, status 