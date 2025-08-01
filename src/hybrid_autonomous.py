import time
import math

class HybridAutonomousMode:
    def __init__(self, serial_comm, laser_control, camera_manager):
        self.serial = serial_comm
        self.laser = laser_control
        self.camera = camera_manager
        
        # === CORE STATE TRACKING ===
        self.current_target_id = None      # Currently tracked target ID
        self.fired_target_ids = set()     # IDs of destroyed targets
        self.lock_start_time = 0          # When current target was first locked
        
        # === SIMPLIFIED PARALLAX COMPENSATION ===
        # For parallel mounting, use minimal offset
        self.camera_laser_offset = 0.02   # Very small offset (2% of frame height)
        self.parallax_calibrated = False  # Whether parallax has been calibrated
        self.target_distance_estimate = 0.5  # Estimated target distance (0-1, normalized)
        
        # === ENHANCED SAFETY PARAMETERS ===
        self.lock_duration = 1.5          # Increased to 1.5s for better safety
        self.center_margin = 0.08         # Increased to 8% for easier centering in Skill 9
        self.min_target_size = 50         # Reduced for better detection
        self.max_target_distance = 0.8    # Maximum normalized distance for safe firing
        
        # === PID CONTROL PARAMETERS - Optimized for Skill 9 ===
        self.pid_kp = 0.20               # Increased proportional gain for faster response
        self.pid_ki = 0.01               # Reduced integral gain to prevent overshooting
        self.pid_kd = 0.08               # Increased derivative gain for better damping
        self.pid_integral_x = 0.0
        self.pid_integral_y = 0.0
        self.pid_prev_error_x = 0.0
        self.pid_prev_error_y = 0.0
        
        # === CAMERA LIMITS ===
        self.servo_min, self.servo_max = 0, 60
        self.stepper_min, self.stepper_max = 0, 300
        
        # === ENHANCED TRACKING ===
        self.target_history = []          # Track target movement for velocity estimation
        self.last_target_position = None
        self.target_velocity = (0, 0)     # Target velocity for predictive aiming
        
        # Check camera connection
        self._check_camera_connection()
        
        print("[HybridAutonomous] 🚀 Enhanced autonomous mode initialized with simplified parallax compensation")
        
    def _check_camera_connection(self):
        """Check if camera manager is properly connected and has serial communication."""
        if not self.camera:
            print("[HybridAutonomous] ⚠️ Camera manager not provided!")
            return False
            
        if not hasattr(self.camera, 'serial') or not self.camera.serial:
            print("[HybridAutonomous] ⚠️ Camera manager has no serial connection!")
            return False
            
        print("[HybridAutonomous] ✅ Camera manager connected with serial communication")
        return True
        
    def calculate_parallax_offset(self, distance_meters):
        """
        Calculate parallax offset for parallel-mounted camera and laser.
        Since both are pointing forward, parallax error is much smaller.
        
        Args:
            distance_meters: Distance to target in meters
            
        Returns:
            parallax_offset: Normalized offset (0-1)
        """
        import math
        
        # For parallel mounting, the parallax error is much smaller
        # The error is approximately: gap / distance * (small angle factor)
        
        # Convert camera FOV to radians
        fov_vertical_rad = math.radians(self.camera_fov_vertical)
        
        # For parallel mounting, the parallax angle is very small
        # The camera and laser are both pointing forward, so the error is minimal
        # We use a much smaller factor for parallel mounting
        parallax_factor = 0.1  # Much smaller factor for parallel mounting
        
        # Calculate the small parallax angle
        angle_rad = math.atan(self.camera_laser_gap / distance_meters) * parallax_factor
        
        # Convert angle to normalized offset in frame coordinates
        parallax_offset = angle_rad / (fov_vertical_rad / 2)
        
        # Ensure offset is within reasonable bounds (much smaller range)
        parallax_offset = max(0.0, min(0.1, parallax_offset))  # Max 10% for parallel mounting
        
        return parallax_offset
        
    def calibrate_parallax(self, target_distance=0.5):
        """
        Simplified parallax calibration for parallel mounting.
        target_distance: Estimated distance to target (0-1, normalized)
        """
        self.target_distance_estimate = target_distance
        self.parallax_calibrated = True
        
        # Use minimal offset for parallel mounting
        self.camera_laser_offset = 0.02  # 2% offset - very small
        
        print(f"[HybridAutonomous] 🎯 Simplified parallax calibrated: offset={self.camera_laser_offset:.3f}")
    
    def _apply_parallax_compensation(self, target_x, target_y, frame_shape):
        """
        Apply minimal parallax compensation for parallel mounting.
        Returns compensated target position.
        """
        if not self.parallax_calibrated:
            # Use default calibration if not calibrated
            self.calibrate_parallax()
        
        # For parallel mounting, minimal compensation
        # The laser fires slightly below where the camera sees the target
        compensated_y = target_y + self.camera_laser_offset
        
        # No horizontal parallax for parallel mounting
        compensated_x = target_x
        
        # Ensure compensated position is within frame bounds
        compensated_y = max(0.0, min(1.0, compensated_y))
        compensated_x = max(0.0, min(1.0, compensated_x))
        
        return compensated_x, compensated_y
    
    def _estimate_target_distance(self, target, frame_shape):
        """
        Estimate target distance based on apparent size.
        Larger targets are closer, smaller targets are farther.
        """
        bbox = target['bbox']
        target_size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        
        # Normalize size relative to frame
        frame_area = frame_shape[0] * frame_shape[1]
        normalized_size = target_size / frame_area
        
        # Convert size to distance estimate (larger = closer)
        # This is a simplified model - in practice you'd need more sophisticated ranging
        distance = max(0.1, min(1.0, 1.0 - normalized_size * 10))
        
        return distance
    
    def process_frame(self, frame, detections):
        """
        Enhanced processing function with improved targeting, safety, and simplified parallax compensation
        Returns: (target_bbox, target_id, status_message)
        """
        
        # === STEP 1: DETECTION ===
        red_balloons = self._detect_red_balloons(detections)
        if not red_balloons:
            self._reset_tracking()
            return None, None, "No red balloons detected"
            
        # === STEP 2: ENHANCED TARGET SELECTION ===
        target = self._select_best_target(red_balloons, frame.shape)
        if not target:
            return None, None, "No suitable targets"
            
        # === STEP 3: VELOCITY TRACKING ===
        self._update_target_velocity(target, frame.shape)
        
        # === STEP 4: ENHANCED AIMING & LOCKING WITH SIMPLIFIED PARALLAX ===
        if self._is_target_centered_enhanced(target, frame.shape):
            # Target is centered - check if ready to fire
            if self._can_fire_at_target_enhanced(target, frame.shape):
                return self._fire_at_target(target)
            else:
                # Still building lock time
                remaining = self.lock_duration - (time.time() - self.lock_start_time)
                return target['bbox'], target['track_id'], f"Locking: {remaining:.1f}s"
        else:
            # Target not centered - move camera with PID control
            print(f"[HybridAutonomous] 🎯 Target {target['track_id']} not centered - moving camera...")
            self._aim_at_target_pid(target, frame.shape)
            return target['bbox'], target['track_id'], "Aligning camera"
    
    def _detect_red_balloons(self, detections):
        """Step 1: Find all red balloons in frame"""
        red_balloons = []
        for det in detections:
            label = det['label'].lower()
            # Check for various red balloon labels
            if 'red' in label or 'balloon' in label or 'balon' in label:
                red_balloons.append(det)
        
        print(f"[HybridAutonomous] 🔍 Detected {len(red_balloons)} red balloons")
        return red_balloons
    
    def _select_best_target(self, red_balloons, frame_shape):
        """Enhanced target selection with multiple criteria - Optimized for Skill 9"""
        
        # Filter out already-fired targets
        available_targets = [b for b in red_balloons if b['track_id'] not in self.fired_target_ids]
        
        if not available_targets:
            print("[HybridAutonomous] ✅ All targets have been destroyed")
            return None
            
        # Priority 1: Continue tracking current target if it exists (Skill 9 requirement)
        if self.current_target_id:
            for target in available_targets:
                if target['track_id'] == self.current_target_id:
                    print(f"[HybridAutonomous] 🎯 Continuing to track target {self.current_target_id} (Skill 9: Single target focus)")
                    return target
        
        # Priority 2: Enhanced target selection based on multiple criteria
        best_target = self._find_optimal_target(available_targets, frame_shape)
        if best_target:
            print(f"[HybridAutonomous] 🎯 Selected new target {best_target['track_id']} (Skill 9: Ignoring other balloons)")
            # Set current target for continuity
            self.current_target_id = best_target['track_id']
            self.lock_start_time = time.time()  # Start lock timer
            
        return best_target
    
    def _find_optimal_target(self, targets, frame_shape):
        """Find optimal target based on distance, size, and velocity - Optimized for Skill 9"""
        center_x = frame_shape[1] / 2
        center_y = frame_shape[0] / 2
        
        best_target = None
        best_score = float('-inf')
        
        for target in targets:
            bbox = target['bbox']
            target_x = (bbox[0] + bbox[2]) / 2
            target_y = (bbox[1] + bbox[3]) / 2
            
            # Calculate distance from center
            distance = ((target_x - center_x) ** 2 + (target_y - center_y) ** 2) ** 0.5
            
            # Calculate target size
            target_size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
            
            # Calculate velocity (if available)
            velocity_magnitude = 0
            if self.target_velocity != (0, 0):
                velocity_magnitude = math.sqrt(self.target_velocity[0]**2 + self.target_velocity[1]**2)
            
            # Enhanced scoring for Skill 9 - prioritize center targets
            distance_score = 1.0 / (1.0 + distance / 50.0)  # Stronger center preference
            size_score = min(target_size / 1000.0, 1.0)  # Normalize size
            velocity_score = max(0, 1.0 - velocity_magnitude / 30.0)  # Prefer slower targets
            
            # Combined score with enhanced weights for Skill 9
            score = distance_score * 0.6 + size_score * 0.3 + velocity_score * 0.1
            
            if score > best_score:
                best_score = score
                best_target = target
                
        return best_target
    
    def _update_target_velocity(self, target, frame_shape):
        """Update target velocity tracking"""
        bbox = target['bbox']
        current_pos = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
        
        if self.last_target_position:
            # Calculate velocity
            dx = current_pos[0] - self.last_target_position[0]
            dy = current_pos[1] - self.last_target_position[1]
            self.target_velocity = (dx, dy)
        
        self.last_target_position = current_pos
        
        # Keep history for velocity smoothing
        self.target_history.append(current_pos)
        if len(self.target_history) > 10:  # Keep last 10 positions
            self.target_history.pop(0)
    
    def _aim_at_target_pid(self, target, frame_shape):
        """PID-controlled aiming at actual laser firing position"""
        bbox = target['bbox']
        frame_width = frame_shape[1]
        frame_height = frame_shape[0]
        
        # Calculate normalized target position (0-1) in camera coordinates
        target_x = (bbox[0] + bbox[2]) / 2 / frame_width
        target_y = (bbox[1] + bbox[3]) / 2 / frame_height
        
        # Get current laser firing position based on motor angles
        if self.camera:
            camera_pos = self.camera.get_camera_position()
            servo_angle = camera_pos['servo_angle']
            stepper_angle = camera_pos['stepper_angle']
            
            # Convert motor angles to normalized position (0-1) - FIXED MAPPING
            current_laser_x = stepper_angle / 300.0  # Stepper controls horizontal (X)
            current_laser_y = servo_angle / 60.0     # Servo controls vertical (Y)
        else:
            # Fallback to center if camera not available
            current_laser_x = 0.5
            current_laser_y = 0.5
        
        # Calculate error from target to current laser position
        error_x = target_x - current_laser_x
        error_y = target_y - current_laser_y
        
        # PID control for X-axis (horizontal - affects stepper)
        self.pid_integral_x += error_x
        self.pid_integral_x = max(-1.0, min(1.0, self.pid_integral_x))  # Anti-windup
        derivative_x = error_x - self.pid_prev_error_x
        
        move_x = (self.pid_kp * error_x + 
                   self.pid_ki * self.pid_integral_x + 
                   self.pid_kd * derivative_x)
        
        # PID control for Y-axis (vertical - affects servo)
        self.pid_integral_y += error_y
        self.pid_integral_y = max(-1.0, min(1.0, self.pid_integral_y))  # Anti-windup
        derivative_y = error_y - self.pid_prev_error_y
        
        move_y = (self.pid_kp * error_y + 
                   self.pid_ki * self.pid_integral_y + 
                   self.pid_kd * derivative_y)
        
        # Apply limits to prevent overshooting
        move_x = max(-0.3, min(0.3, move_x))
        move_y = max(-0.3, min(0.3, move_y))
        
        # Update previous errors
        self.pid_prev_error_x = error_x
        self.pid_prev_error_y = error_y
        
        # Move camera - FIXED: dx affects stepper (horizontal), dy affects servo (vertical)
        if self.camera:
            # Correct mapping: move_x (horizontal error) -> stepper, move_y (vertical error) -> servo
            self.camera.move_camera_smooth(move_x, move_y)
            print(f"[HybridAutonomous] 📡 PID movement: dx={move_x:.3f}, dy={move_y:.3f}")
            print(f"[HybridAutonomous] 🎯 Target: ({target_x:.3f}, {target_y:.3f}), Laser: ({current_laser_x:.3f}, {current_laser_y:.3f})")
            print(f"[HybridAutonomous] 📊 Error: dx={error_x:.3f}, dy={error_y:.3f}")
    
    def _is_target_centered_enhanced(self, target, frame_shape):
        """Enhanced centering check using actual laser firing position"""
        bbox = target['bbox']
        frame_width = frame_shape[1]
        frame_height = frame_shape[0]
        
        # Calculate target center in camera coordinates
        target_x = (bbox[0] + bbox[2]) / 2 / frame_width
        target_y = (bbox[1] + bbox[3]) / 2 / frame_height
        
        # Get current laser firing position based on motor angles - FIXED MAPPING
        if self.camera:
            camera_pos = self.camera.get_camera_position()
            servo_angle = camera_pos['servo_angle']
            stepper_angle = camera_pos['stepper_angle']
            
            # Convert motor angles to normalized position (0-1) - CORRECTED
            current_laser_x = stepper_angle / 300.0  # Stepper controls horizontal (X)
            current_laser_y = servo_angle / 60.0     # Servo controls vertical (Y)
        else:
            # Fallback to center if camera not available
            current_laser_x = 0.5
            current_laser_y = 0.5
        
        # Calculate normalized distance from laser firing position (0-1)
        distance_x = abs(target_x - current_laser_x)
        distance_y = abs(target_y - current_laser_y)
        
        # Adaptive margin based on target size and velocity
        target_size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        size_factor = min(target_size / 5000.0, 1.0)  # Larger targets get tighter margin
        
        velocity_magnitude = math.sqrt(self.target_velocity[0]**2 + self.target_velocity[1]**2)
        velocity_factor = max(0.5, 1.0 - velocity_magnitude / 100.0)  # Faster targets get larger margin
        
        adaptive_margin = self.center_margin * size_factor * velocity_factor
        
        # Check if within adaptive margin
        is_centered = distance_x < adaptive_margin and distance_y < adaptive_margin
        
        if is_centered:
            print(f"[HybridAutonomous] 🎯 Target {target['track_id']} is centered (margin: {adaptive_margin:.3f})")
            print(f"[HybridAutonomous] 📍 Target: ({target_x:.3f}, {target_y:.3f}), Laser: ({current_laser_x:.3f}, {current_laser_y:.3f})")
        else:
            print(f"[HybridAutonomous] 📍 Target {target['track_id']} offset: dx={distance_x:.3f}, dy={distance_y:.3f}")
            
        return is_centered
    
    def _can_fire_at_target_enhanced(self, target, frame_shape):
        """Enhanced safety checks before firing with parallax consideration"""
        
        # Check 1: Target size
        bbox = target['bbox']
        target_size = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if target_size < self.min_target_size:
            print(f"[HybridAutonomous] ⚠️ Target too small: {target_size} < {self.min_target_size}")
            return False
        
        # Check 2: Lock duration
        lock_time = time.time() - self.lock_start_time
        if lock_time < self.lock_duration:
            print(f"[HybridAutonomous] ⏳ Building lock: {lock_time:.1f}s < {self.lock_duration}s")
            return False
        
        # Check 3: Target distance (safety check) - use laser firing position
        target_x = (bbox[0] + bbox[2]) / 2 / frame_shape[1]
        target_y = (bbox[1] + bbox[3]) / 2 / frame_shape[0]
        laser_x, laser_y = self._apply_parallax_compensation(target_x, target_y, frame_shape)
        distance_from_center = math.sqrt((laser_x - 0.5)**2 + (laser_y - 0.5)**2)
        
        if distance_from_center > self.max_target_distance:
            print(f"[HybridAutonomous] ⚠️ Target too far: {distance_from_center:.3f} > {self.max_target_distance}")
            return False
        
        # Check 4: Target still exists and is centered (using laser position)
        if not self._is_target_centered_enhanced(target, frame_shape):
            print("[HybridAutonomous] ⚠️ Target no longer centered")
            return False
        
        # Check 5: Target velocity (prefer stationary targets)
        velocity_magnitude = math.sqrt(self.target_velocity[0]**2 + self.target_velocity[1]**2)
        if velocity_magnitude > 20:  # Threshold for moving targets
            print(f"[HybridAutonomous] ⚠️ Target moving too fast: {velocity_magnitude:.1f} pixels/frame")
            return False
        
        print(f"[HybridAutonomous] ✅ All safety checks passed - ready to fire")
        return True
    
    def _fire_at_target(self, target):
        """Fire laser at target with enhanced safety and parallax compensation"""
        target_id = target['track_id']
        
        print(f"[HybridAutonomous] 🔥 FIRING at target {target_id}")
        
        # Fire laser with safety duration
        self.laser.fire_laser(0.3)  # 300ms duration
        
        # Mark target as destroyed
        self.fired_target_ids.add(target_id)
        self.current_target_id = None  # Reset tracking
        
        # Reset PID controllers
        self.pid_integral_x = 0.0
        self.pid_integral_y = 0.0
        self.pid_prev_error_x = 0.0
        self.pid_prev_error_y = 0.0
        
        print(f"[HybridAutonomous] ✅ Target {target_id} destroyed")
        
        return target['bbox'], target_id, "FIRING!"
    
    def _reset_tracking(self):
        """Reset tracking when no targets found"""
        if self.current_target_id:
            print(f"[HybridAutonomous] 🔄 Lost target {self.current_target_id}")
            self.current_target_id = None
            self.lock_start_time = 0
            self.target_history.clear()
            self.last_target_position = None
            self.target_velocity = (0, 0)
    
    def reset(self):
        """Reset autonomous mode completely"""
        self.current_target_id = None
        self.fired_target_ids.clear()
        self.lock_start_time = 0
        self.target_history.clear()
        self.last_target_position = None
        self.target_velocity = (0, 0)
        
        # Reset PID controllers
        self.pid_integral_x = 0.0
        self.pid_integral_y = 0.0
        self.pid_prev_error_x = 0.0
        self.pid_prev_error_y = 0.0
        
        # Ensure camera is at center position
        if self.camera:
            self.camera.reset_position()
        
        print("[HybridAutonomous] 🔄 Complete reset with PID reset and camera centering")
    
    def emergency_stop(self):
        """Emergency stop - immediately halt all operations"""
        self.current_target_id = None
        self.laser.emergency_stop()
        
        # Reset PID controllers
        self.pid_integral_x = 0.0
        self.pid_integral_y = 0.0
        self.pid_prev_error_x = 0.0
        self.pid_prev_error_y = 0.0
        
        print("[HybridAutonomous] 🚨 EMERGENCY STOP ACTIVATED")
    
    def get_status(self):
        """Get current status for debugging"""
        return {
            'current_target': self.current_target_id,
            'fired_count': len(self.fired_target_ids),
            'fired_targets': list(self.fired_target_ids),
            'lock_time': time.time() - self.lock_start_time if self.lock_start_time > 0 else 0,
            'target_velocity': self.target_velocity,
            'pid_integral': (self.pid_integral_x, self.pid_integral_y),
            'parallax_calibrated': self.parallax_calibrated,
            'camera_laser_offset': self.camera_laser_offset,
            'target_distance_estimate': self.target_distance_estimate
        }
    
    def set_parameters(self, lock_duration=1.5, center_margin=0.03, min_size=100, 
                      max_distance=0.8, kp=0.15, ki=0.02, kd=0.05, parallax_offset=0.15):
        """Update enhanced parameters including parallax compensation"""
        self.lock_duration = lock_duration
        self.center_margin = center_margin
        self.min_target_size = min_size
        self.max_target_distance = max_distance
        self.pid_kp = kp
        self.pid_ki = ki
        self.pid_kd = kd
        self.camera_laser_offset = parallax_offset
        print(f"[HybridAutonomous] ⚙️ Enhanced parameters updated: lock={lock_duration}s, margin={center_margin}, min_size={min_size}, max_dist={max_distance}, PID=({kp},{ki},{kd}), parallax={parallax_offset}") 