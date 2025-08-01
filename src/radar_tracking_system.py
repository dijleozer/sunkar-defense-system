import time
import threading
import math
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple

class ScanMode(Enum):
    RADAR_SWEEP = "radar_sweep"
    SPIRAL_SCAN = "spiral_scan"
    SECTOR_SCAN = "sector_scan"
    TRACKING = "tracking"

@dataclass
class Target:
    track_id: int
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    label: str
    confidence: float
    center: Tuple[int, int]  # x, y center of target
    last_seen: float
    priority: int = 0  # Higher number = higher priority

class RadarTrackingSystem:
    """
    Radar-like scanning system with balloon tracking and motor control.
    Implements multiple scanning patterns and continuous target tracking.
    """
    
    def __init__(self, motor_control, camera_manager, serial_comm=None):
        self.motor_control = motor_control
        self.camera_manager = camera_manager
        self.serial_comm = serial_comm
        
        # Motor control parameters
        self.servo_min = 0
        self.servo_max = 60
        self.stepper_min = 0
        self.stepper_max = 300
        
        # Current motor positions
        self.current_servo_angle = 0
        self.current_stepper_angle = 150
        
        # Scanning parameters
        self.scan_mode = ScanMode.RADAR_SWEEP
        self.scan_speed = 2.0  # degrees per second
        self.scan_direction = 1  # 1 for clockwise, -1 for counter-clockwise
        
        # Target tracking
        self.targets: List[Target] = []
        self.current_target: Optional[Target] = None
        self.target_lost_timeout = 3.0  # seconds
        self.tracking_threshold = 0.7  # confidence threshold for tracking
        
        # Control parameters
        self.movement_speed = 3.0  # degrees per update
        self.movement_interval = 0.05  # seconds between movements
        self.last_movement_time = time.time()
        
        # Threading
        self.running = False
        self.control_thread = None
        
        # Scanning patterns
        self.spiral_center = (150, 30)  # stepper, servo
        self.spiral_radius = 50  # degrees
        self.spiral_step = 5  # degrees per spiral step
        
        # Sector scanning
        self.sector_start = 0
        self.sector_end = 300
        self.sector_step = 30
        
    def start(self):
        """Start the radar tracking system."""
        if self.control_thread and self.control_thread.is_alive():
            print("[RadarTracking] ⚠️ System already running")
            return
            
        self.running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        print("[RadarTracking] 🚀 Radar tracking system started")
        
    def stop(self):
        """Stop the radar tracking system."""
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
        print("[RadarTracking] 🛑 Radar tracking system stopped")
        
    def _control_loop(self):
        """Main control loop for radar tracking."""
        while self.running:
            try:
                self._update_targets()
                self._execute_scanning()
                time.sleep(0.05)  # 20 FPS control loop
            except Exception as e:
                print(f"[RadarTracking] ❌ Error in control loop: {e}")
                time.sleep(0.1)
                
    def _update_targets(self):
        """Update target list from camera detections."""
        if not hasattr(self.camera_manager, 'tracks'):
            return
            
        current_time = time.time()
        new_targets = []
        
        # Get current detections
        tracks = self.camera_manager.tracks if hasattr(self.camera_manager, 'tracks') else []
        
        for track in tracks:
            if track.get('label', '').lower() == 'red':  # Only track red balloons (enemies)
                bbox = track['bbox']
                center = ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)
                
                # Calculate priority based on confidence and size
                confidence = track.get('confidence', 0.0)
                size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                
                # Higher confidence and larger size = higher priority
                priority = int(confidence * 100) + (size // 1000)
                
                target = Target(
                    track_id=track['track_id'],
                    bbox=bbox,
                    label=track['label'],
                    confidence=confidence,
                    center=center,
                    last_seen=current_time,
                    priority=priority
                )
                new_targets.append(target)
        
        # Update target list
        self.targets = new_targets
        
        # Select highest priority target
        if self.targets:
            self.current_target = max(self.targets, key=lambda t: t.priority)
            self.scan_mode = ScanMode.TRACKING
        else:
            self.current_target = None
            if self.scan_mode == ScanMode.TRACKING:
                self.scan_mode = ScanMode.RADAR_SWEEP
                
    def _execute_scanning(self):
        """Execute current scanning mode."""
        if self.scan_mode == ScanMode.RADAR_SWEEP:
            self._radar_sweep()
        elif self.scan_mode == ScanMode.SPIRAL_SCAN:
            self._spiral_scan()
        elif self.scan_mode == ScanMode.SECTOR_SCAN:
            self._sector_scan()
        elif self.scan_mode == ScanMode.TRACKING:
            self._track_target()
            
    def _radar_sweep(self):
        """Radar-like horizontal sweep pattern."""
        current_time = time.time()
        if current_time - self.last_movement_time < self.movement_interval:
            return
            
        # Move stepper motor in a sweeping pattern
        self.current_stepper_angle += self.scan_speed * self.scan_direction
        
        # Reverse direction at boundaries
        if self.current_stepper_angle >= self.stepper_max:
            self.current_stepper_angle = self.stepper_max
            self.scan_direction = -1
        elif self.current_stepper_angle <= self.stepper_min:
            self.current_stepper_angle = self.stepper_min
            self.scan_direction = 1
            
        # Send motor commands
        self._send_motor_commands()
        self.last_movement_time = current_time
        
    def _spiral_scan(self):
        """Spiral scanning pattern."""
        current_time = time.time()
        if current_time - self.last_movement_time < self.movement_interval:
            return
            
        # Calculate spiral position
        angle = (current_time * 30) % 360  # 30 degrees per second
        radius = self.spiral_radius * (angle / 360)  # Gradually increase radius
        
        # Convert to motor angles
        stepper_angle = self.spiral_center[0] + radius * math.cos(math.radians(angle))
        servo_angle = self.spiral_center[1] + radius * math.sin(math.radians(angle)) * 0.5
        
        # Clamp to motor limits
        self.current_stepper_angle = max(self.stepper_min, min(self.stepper_max, stepper_angle))
        self.current_servo_angle = max(self.servo_min, min(self.servo_max, servo_angle))
        
        # Send motor commands
        self._send_motor_commands()
        self.last_movement_time = current_time
        
    def _sector_scan(self):
        """Sector-based scanning pattern."""
        current_time = time.time()
        if current_time - self.last_movement_time < self.movement_interval:
            return
            
        # Move through sectors
        sector_angle = (int(current_time) % 10) * self.sector_step
        self.current_stepper_angle = self.sector_start + sector_angle
        
        # Oscillate servo within sector
        servo_oscillation = math.sin(current_time * 2) * 10
        self.current_servo_angle = 30 + servo_oscillation
        
        # Clamp to limits
        self.current_stepper_angle = max(self.stepper_min, min(self.stepper_max, self.current_stepper_angle))
        self.current_servo_angle = max(self.servo_min, min(self.servo_max, self.current_servo_angle))
        
        # Send motor commands
        self._send_motor_commands()
        self.last_movement_time = current_time
        
    def _track_target(self):
        """Track current target by adjusting motor positions."""
        if not self.current_target:
            return
            
        current_time = time.time()
        if current_time - self.last_movement_time < self.movement_interval:
            return
            
        # Calculate target center in image coordinates
        target_center = self.current_target.center
        frame_height, frame_width = 480, 640  # Assuming standard camera resolution
        
        # Convert image coordinates to motor angles
        # Horizontal movement (stepper) - map x position to stepper angle
        x_normalized = target_center[0] / frame_width  # 0 to 1
        target_stepper = self.stepper_min + x_normalized * (self.stepper_max - self.stepper_min)
        
        # Vertical movement (servo) - map y position to servo angle (inverted)
        y_normalized = 1.0 - (target_center[1] / frame_height)  # Invert Y axis
        target_servo = self.servo_min + y_normalized * (self.servo_max - self.servo_min)
        
        # Smooth movement towards target
        stepper_diff = target_stepper - self.current_stepper_angle
        servo_diff = target_servo - self.current_servo_angle
        
        # Apply movement speed limits
        if abs(stepper_diff) > self.movement_speed:
            stepper_diff = self.movement_speed if stepper_diff > 0 else -self.movement_speed
            
        if abs(servo_diff) > self.movement_speed:
            servo_diff = self.movement_speed if servo_diff > 0 else -self.movement_speed
            
        # Update motor positions
        self.current_stepper_angle += stepper_diff
        self.current_servo_angle += servo_diff
        
        # Clamp to motor limits
        self.current_stepper_angle = max(self.stepper_min, min(self.stepper_max, self.current_stepper_angle))
        self.current_servo_angle = max(self.servo_min, min(self.servo_max, self.current_servo_angle))
        
        # Send motor commands
        self._send_motor_commands()
        self.last_movement_time = current_time
        
        print(f"[RadarTracking] 🎯 Tracking target {self.current_target.track_id}: "
              f"Stepper={self.current_stepper_angle:.1f}°, Servo={self.current_servo_angle:.1f}°")
        
    def _send_motor_commands(self):
        """Send motor commands to Arduino."""
        if not self.serial_comm:
            return
            
        try:
            # Send servo command
            self.serial_comm.send_command(0x01, int(self.current_servo_angle))
            
            # Send stepper command
            self.serial_comm.send_command(0x02, int(self.current_stepper_angle))
            
        except Exception as e:
            print(f"[RadarTracking] ❌ Error sending motor commands: {e}")
            
    def set_scan_mode(self, mode: ScanMode):
        """Set scanning mode."""
        self.scan_mode = mode
        print(f"[RadarTracking] 🔄 Scan mode changed to: {mode.value}")
        
    def set_scan_speed(self, speed: float):
        """Set scanning speed in degrees per second."""
        self.scan_speed = max(0.5, min(10.0, speed))
        print(f"[RadarTracking] ⚡ Scan speed set to: {self.scan_speed}°/s")
        
    def set_movement_speed(self, speed: float):
        """Set movement speed in degrees per update."""
        self.movement_speed = max(0.5, min(5.0, speed))
        print(f"[RadarTracking] ⚡ Movement speed set to: {self.movement_speed}°/update")
        
    def get_status(self):
        """Get current system status."""
        return {
            'scan_mode': self.scan_mode.value,
            'current_target': self.current_target.track_id if self.current_target else None,
            'target_count': len(self.targets),
            'servo_angle': self.current_servo_angle,
            'stepper_angle': self.current_stepper_angle,
            'scan_speed': self.scan_speed,
            'movement_speed': self.movement_speed
        }
        
    def emergency_stop(self):
        """Emergency stop - stop all movement."""
        if self.serial_comm:
            self.serial_comm.send_command(0x01, 0)  # Stop servo
            self.serial_comm.send_command(0x02, 150)  # Center stepper
        print("[RadarTracking] 🚨 Emergency stop executed")
        
    def reset_position(self):
        """Reset to safe starting position."""
        self.current_servo_angle = 0
        self.current_stepper_angle = 150
        self._send_motor_commands()
        print("[RadarTracking] 🔄 Reset to safe position") 