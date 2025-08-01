#!/usr/bin/env python3
"""
Active Scanning Autonomous Mode
- Starts at center position (not top)
- When no target: slowly scans the area
- When target found: tracks and fires
- Uses ByteTrack for stable tracking
"""

import time
import math
import threading

class ActiveScanningAutonomousMode:
    """
    Active scanning autonomous mode that:
    1. Starts at center position (servo=30°, stepper=150°)
    2. When no target: slowly scans the area
    3. When target found: tracks and fires
    4. Uses ByteTrack for stable tracking
    """
    
    def __init__(self, serial_comm, laser_control, camera_manager):
        self.serial = serial_comm
        self.laser = laser_control
        self.camera = camera_manager
        
        # === CORE STATE ===
        self.is_active = False
        self.current_target_id = None
        self.target_lock_start = 0
        self.last_target_position = None
        self.target_history = []
        
        # === SCANNING PARAMETERS ===
        self.scan_mode = True  # Start in scan mode
        self.scan_start_time = 0
        self.scan_direction = 1  # 1 = right, -1 = left
        self.scan_speed = 0.05  # Faster scanning speed
        self.scan_range = 0.3  # Scan 30% of range
        self.scan_interval = 0.05  # 50ms between scan movements (daha hızlı)
        
        # === TARGETING PARAMETERS ===
        self.lock_duration = 1.5  # 1.5 seconds to build lock
        self.center_threshold = 0.1  # 10% of frame size
        self.min_target_size = 100  # Minimum target area
        self.max_target_distance = 0.8  # Maximum normalized distance
        self.fire_duration = 0.3  # 300ms laser fire
        
        # === MOVEMENT PARAMETERS ===
        self.movement_speed = 0.1  # Moderate movement speed
        self.max_movement = 0.2  # Maximum movement per frame
        self.movement_cooldown = 0.05  # 50ms between movements
        
        # === TRACKING PARAMETERS ===
        self.target_timeout = 5.0  # Lose target after 5 seconds (daha uzun)
        self.history_length = 15  # Keep last 15 positions (daha fazla geçmiş)
        
        # === CAMERA-MOTOR OFFSET ===
        self.camera_motor_offset_y = 0.1  # 10% offset - camera sees higher than laser aims
        self.camera_motor_offset_x = 0.0  # No horizontal offset
        
        # === SAFETY STATE ===
        self.emergency_stop_active = False
        self.last_movement_time = 0
        self.last_scan_time = 0
        
        print("[ActiveScanning] 🚀 Active scanning autonomous mode initialized")
        print("[ActiveScanning] 📡 Will scan when no target, track when target found")
        
    def activate(self):
        """Activate autonomous mode with center position."""
        if self.emergency_stop_active:
            print("[ActiveScanning] ❌ Cannot activate - emergency stop active")
            return False
            
        self.is_active = True
        self.scan_mode = True  # Start in scan mode
        self.scan_start_time = time.time()
        self._reset_state()
        
        # Move to bottom position (not top)
        if self.camera:
            print("[ActiveScanning] 🎯 Moving to bottom position (servo=0°, stepper=150°)")
            self.camera.reset_position()
            time.sleep(0.5)  # Wait for camera to settle
            
        print("[ActiveScanning] ✅ Active scanning mode activated")
        return True
        
    def deactivate(self):
        """Deactivate autonomous mode safely."""
        self.is_active = False
        self.scan_mode = False
        self._reset_state()
        
        # Stop laser if active
        if self.laser:
            self.laser.turn_off()
            
        print("[ActiveScanning] ⏹️ Active scanning mode deactivated")
        
    def emergency_stop(self):
        """Emergency stop - immediately halt all operations."""
        self.emergency_stop_active = True
        self.is_active = False
        self.scan_mode = False
        
        # Stop laser immediately
        if self.laser:
            self.laser.emergency_stop()
            
        # Reset camera to center position
        if self.camera:
            self.camera.reset_position()
            
        print("[ActiveScanning] 🚨 EMERGENCY STOP ACTIVATED")
        
    def _reset_state(self):
        """Reset all tracking state."""
        self.current_target_id = None
        self.target_lock_start = 0
        self.last_target_position = None
        self.target_history.clear()
        self.last_movement_time = 0
        self.last_scan_time = 0
        
    def process_frame(self, frame, detections):
        """
        Main processing function with active scanning.
        Returns: (target_bbox, target_id, status_message)
        """
        if not self.is_active or self.emergency_stop_active:
            return None, None, "Autonomous mode inactive"
            
        # === STEP 1: FIND RED BALLOONS ===
        red_balloons = self._find_red_balloons(detections)
        
        if not red_balloons:
            # No targets found - handle target loss
            self._handle_no_targets()
            
            # Switch to scan mode if not already scanning
            if not self.scan_mode:
                print("[ActiveScanning] 🔄 No targets - switching to scan mode")
                self.scan_mode = True
                self.scan_start_time = time.time()
                
            # Perform scanning
            self._perform_scanning()
            return None, None, "Scanning for targets"
            
        # === STEP 2: TARGET FOUND - SWITCH TO TRACKING ===
        if self.scan_mode:
            print("[ActiveScanning] 🎯 Target found - switching to tracking mode")
            self.scan_mode = False
            
        # === STEP 3: SELECT BEST TARGET ===
        target = self._select_target(red_balloons, frame.shape)
        if not target:
            return None, None, "No suitable target"
            
        # === STEP 4: UPDATE TARGET TRACKING ===
        self._update_target_tracking(target, frame.shape)
        
        # === STEP 5: CHECK IF READY TO FIRE ===
        if self._is_target_ready_to_fire(target, frame.shape):
            return self._fire_at_target(target)
            
        # === STEP 6: MOVE TOWARD TARGET ===
        self._move_toward_target(target, frame.shape)
        return target['bbox'], target['track_id'], "Tracking target"
        
    def _find_red_balloons(self, detections):
        """Find all red balloons in detections."""
        red_balloons = []
        print(f"[ActiveScanning] 🔍 Processing {len(detections)} detections")
        
        for det in detections:
            label = det['label'].lower()
            confidence = det.get('confidence', 0)
            print(f"[ActiveScanning] 📋 Detection: {label} (confidence: {confidence:.2f})")
            
            # Check for red balloon labels - more flexible matching
            if any(keyword in label for keyword in ['red', 'balloon', 'balon', 'kirmizi', 'ballon', 'kırmızı']):
                red_balloons.append(det)
                print(f"[ActiveScanning] ✅ Added red balloon: {label}")
            elif 'balloon' in label or 'balon' in label:
                # If it's any balloon, also consider it
                red_balloons.append(det)
                print(f"[ActiveScanning] ✅ Added balloon (any color): {label}")
            elif confidence > 0.7:  # High confidence detection
                red_balloons.append(det)
                print(f"[ActiveScanning] ✅ Added high-confidence detection: {label}")
                
        if red_balloons:
            print(f"[ActiveScanning] 🎯 Found {len(red_balloons)} red balloons")
        else:
            print(f"[ActiveScanning] ❌ No red balloons found in {len(detections)} detections")
        return red_balloons
        
    def _perform_scanning(self):
        """Perform slow scanning when no targets are found."""
        current_time = time.time()
        
        # Rate limiting for scanning
        if current_time - self.last_scan_time < self.scan_interval:
            return
            
        if not self.camera:
            return
            
        # Calculate scan movement
        scan_movement = self.scan_speed * self.scan_direction
        
        # Move camera slowly
        print(f"[ActiveScanning] 📡 Scanning {'RIGHT' if self.scan_direction > 0 else 'LEFT'}")
        self.camera.move_camera_smooth(scan_movement, 0)  # Only horizontal scanning
        self.last_scan_time = current_time
        
        # Check if we need to reverse direction
        # This would need camera position feedback to work properly
        # For now, use time-based direction change
        scan_duration = current_time - self.scan_start_time
        if scan_duration > 3.0:  # Change direction every 3 seconds
            self.scan_direction *= -1
            self.scan_start_time = current_time
            print(f"[ActiveScanning] 🔄 Reversing scan direction")
            
    def _select_target(self, red_balloons, frame_shape):
        """Select the best target based on simple criteria."""
        
        print(f"[ActiveScanning] 🎯 Selecting target from {len(red_balloons)} red balloons")
        print(f"[ActiveScanning] 📍 Current target ID: {self.current_target_id}")
        
        # Priority 1: Continue tracking current target if it exists
        if self.current_target_id:
            for target in red_balloons:
                if target['track_id'] == self.current_target_id:
                    print(f"[ActiveScanning] ✅ Continuing to track target {self.current_target_id}")
                    return target
            print(f"[ActiveScanning] ⚠️ Current target {self.current_target_id} not found in detections")
                    
        # Priority 2: Select new target based on center proximity
        center_x = frame_shape[1] / 2
        center_y = frame_shape[0] / 2
        print(f"[ActiveScanning] 📍 Frame center: ({center_x:.1f}, {center_y:.1f})")
        
        best_target = None
        best_distance = float('inf')
        
        # Priority 2: Select new target - just pick the first one for now
        if red_balloons:
            best_target = red_balloons[0]  # Pick the first detected balloon
            self.current_target_id = best_target['track_id']
            
            bbox = best_target['bbox']
            target_x = (bbox[0] + bbox[2]) / 2
            target_y = (bbox[1] + bbox[3]) / 2
            
            print(f"[ActiveScanning] ✅ Selected first target: ID={best_target['track_id']}, pos=({target_x:.1f}, {target_y:.1f})")
            return best_target
        else:
            print(f"[ActiveScanning] ❌ No red balloons to select from")
            return None
        
    def _update_target_tracking(self, target, frame_shape):
        """Update target position history and tracking."""
        bbox = target['bbox']
        current_pos = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
        
        # Add to history
        self.target_history.append({
            'position': current_pos,
            'time': time.time(),
            'bbox': bbox
        })
        
        # Keep only recent history
        while len(self.target_history) > self.history_length:
            self.target_history.pop(0)
            
        # Update last position
        self.last_target_position = current_pos
        
        # Start lock timer if not already started
        if self.target_lock_start == 0:
            self.target_lock_start = time.time()
            print(f"[ActiveScanning] 🔒 Started locking target {target['track_id']}")
            
    def _is_target_ready_to_fire(self, target, frame_shape):
        """Check if target is ready to fire with comprehensive safety checks."""
        
        # Check 1: Target size
        bbox = target['bbox']
        target_size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if target_size < self.min_target_size:
            print(f"[ActiveScanning] ⚠️ Target too small: {target_size} < {self.min_target_size}")
            return False
            
        # Check 2: Lock duration
        lock_time = time.time() - self.target_lock_start
        if lock_time < self.lock_duration:
            remaining = self.lock_duration - lock_time
            print(f"[ActiveScanning] ⏳ Building lock: {remaining:.1f}s remaining")
            return False
            
        # Check 3: Target centering
        if not self._is_target_centered(target, frame_shape):
            print("[ActiveScanning] ⚠️ Target not centered")
            return False
            
        # Check 4: Target distance (safety)
        center_x = frame_shape[1] / 2
        center_y = frame_shape[0] / 2
        target_x = (bbox[0] + bbox[2]) / 2
        target_y = (bbox[1] + bbox[3]) / 2
        
        distance = math.sqrt((target_x - center_x)**2 + (target_y - center_y)**2)
        max_distance = min(frame_shape[0], frame_shape[1]) * self.max_target_distance
        
        if distance > max_distance:
            print(f"[ActiveScanning] ⚠️ Target too far: {distance:.1f} > {max_distance:.1f}")
            return False
            
        # Check 5: Target stability (not moving too fast)
        if len(self.target_history) >= 3:
            recent_positions = [h['position'] for h in self.target_history[-3:]]
            total_movement = 0
            for i in range(1, len(recent_positions)):
                dx = recent_positions[i][0] - recent_positions[i-1][0]
                dy = recent_positions[i][1] - recent_positions[i-1][1]
                total_movement += math.sqrt(dx*dx + dy*dy)
                
            if total_movement > 50:  # Threshold for movement
                print(f"[ActiveScanning] ⚠️ Target moving too fast: {total_movement:.1f} pixels")
                return False
                
        print(f"[ActiveScanning] ✅ Target ready to fire - all checks passed")
        return True
        
    def _is_target_centered(self, target, frame_shape):
        """Check if target is centered within threshold, accounting for camera-motor offset."""
        bbox = target['bbox']
        center_x = frame_shape[1] / 2
        center_y = frame_shape[0] / 2
        target_x = (bbox[0] + bbox[2]) / 2
        target_y = (bbox[1] + bbox[3]) / 2
        
        # Apply camera-motor offset compensation for centering check
        compensated_center_y = center_y + (center_y * self.camera_motor_offset_y)
        
        # Calculate distance from compensated center
        distance_x = abs(target_x - center_x)
        distance_y = abs(target_y - compensated_center_y)
        
        # Use adaptive threshold based on target size
        target_size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        adaptive_threshold = max(25, target_size * 0.12)  # At least 25 pixels, or 12% of target size
        
        is_centered = distance_x < adaptive_threshold and distance_y < adaptive_threshold
        
        if is_centered:
            print(f"[ActiveScanning] 🎯 Target centered (threshold: {adaptive_threshold:.1f})")
        else:
            print(f"[ActiveScanning] 📍 Target offset: dx={distance_x:.1f}, dy={distance_y:.1f}")
            
        return is_centered
        
    def _move_toward_target(self, target, frame_shape):
        """Move camera toward target with clear direction mapping."""
        
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_movement_time < self.movement_cooldown:
            return
            
        bbox = target['bbox']
        center_x = frame_shape[1] / 2
        center_y = frame_shape[0] / 2
        target_x = (bbox[0] + bbox[2]) / 2
        target_y = (bbox[1] + bbox[3]) / 2
        
        # Calculate normalized movement (-1 to 1)
        dx = (target_x - center_x) / center_x
        dy = (center_y - target_y) / center_y  # Inverted because camera Y is inverted
        
        # Apply camera-motor offset compensation
        dy -= self.camera_motor_offset_y
        
        # Apply limits
        dx = max(-self.max_movement, min(self.max_movement, dx))
        dy = max(-self.max_movement, min(self.max_movement, dy))
        
        # Apply movement speed
        dx *= self.movement_speed
        dy *= self.movement_speed
        
        # Move camera
        if self.camera and (abs(dx) > 0.005 or abs(dy) > 0.005):
            print(f"[ActiveScanning] 🎯 SENDING MOVEMENT COMMAND: dx={dx:.3f}, dy={dy:.3f}")
            self.camera.move_camera_smooth(dx, dy)
            self.last_movement_time = current_time
            
            # Clear direction mapping
            direction_x = "RIGHT" if dx > 0 else "LEFT" if dx < 0 else "CENTER"
            direction_y = "UP" if dy > 0 else "DOWN" if dy < 0 else "CENTER"
            
            print(f"[ActiveScanning] 📡 Moving: {direction_x} ({dx:.3f}), {direction_y} ({dy:.3f})")
            print(f"[ActiveScanning] 🎯 Target at ({target_x:.1f}, {target_y:.1f}), Center at ({center_x:.1f}, {center_y:.1f})")
        else:
            print(f"[ActiveScanning] ⏸️ No movement needed: dx={dx:.3f}, dy={dy:.3f}")
            
    def _fire_at_target(self, target):
        """Fire laser at target with safety."""
        target_id = target['track_id']
        
        print(f"[ActiveScanning] 🔥 FIRING at target {target_id}")
        
        # Fire laser
        if self.laser:
            self.laser.fire_laser(self.fire_duration)
            
        # Reset tracking and return to scan mode
        self._reset_state()
        self.scan_mode = True
        self.scan_start_time = time.time()
        
        print(f"[ActiveScanning] ✅ Target {target_id} fired at - returning to scan mode")
        
        return target['bbox'], target_id, "FIRED!"
        
    def _handle_no_targets(self):
        """Handle situation when no targets are found."""
        current_time = time.time()
        
        # Check if we should lose current target
        if (self.current_target_id and 
            self.target_lock_start > 0 and 
            current_time - self.target_lock_start > self.target_timeout):
            
            print(f"[ActiveScanning] 🔄 Lost target {self.current_target_id} (timeout: {self.target_timeout}s)")
            self._reset_state()
        elif self.current_target_id:
            # Still have a target but no detections - keep trying
            remaining_time = self.target_timeout - (current_time - self.target_lock_start)
            if remaining_time > 0:
                print(f"[ActiveScanning] ⏳ Target {self.current_target_id} temporarily lost, {remaining_time:.1f}s remaining")
            else:
                print(f"[ActiveScanning] 🔄 Target {self.current_target_id} lost permanently")
                self._reset_state()
        
    def get_status(self):
        """Get current status for debugging."""
        return {
            'active': self.is_active,
            'scan_mode': self.scan_mode,
            'emergency_stop': self.emergency_stop_active,
            'current_target': self.current_target_id,
            'lock_time': time.time() - self.target_lock_start if self.target_lock_start > 0 else 0,
            'target_history_length': len(self.target_history),
            'last_position': self.last_target_position,
            'scan_direction': self.scan_direction
        }
        
    def reset(self):
        """Reset autonomous mode completely."""
        self._reset_state()
        self.emergency_stop_active = False
        self.scan_mode = True
        
        # Reset camera position
        if self.camera:
            self.camera.reset_position()
            
        print("[ActiveScanning] �� Complete reset") 