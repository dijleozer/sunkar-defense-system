import time
import threading
from radar_tracking_system import RadarTrackingSystem, ScanMode

class SimpleAutonomousMode:
    """
    Simple autonomous mode that integrates radar tracking with the existing system.
    Provides easy-to-use interface for radar scanning and target tracking.
    """
    
    def __init__(self, serial_comm, laser_control, camera_manager):
        self.serial_comm = serial_comm
        self.laser_control = laser_control
        self.camera_manager = camera_manager
        
        # Initialize radar tracking system
        self.radar_system = RadarTrackingSystem(
            motor_control=None,  # We'll use serial_comm directly
            camera_manager=camera_manager,
            serial_comm=serial_comm
        )
        
        # Autonomous mode state
        self.is_active = False
        self.auto_fire_enabled = False
        self.current_scan_mode = ScanMode.RADAR_SWEEP
        
        # Control parameters
        self.scan_speed = 2.0
        self.movement_speed = 3.0
        self.auto_fire_delay = 1.0  # seconds between auto-fires
        
        # Threading
        self.control_thread = None
        self.running = False
        
    def start_autonomous_mode(self):
        """Start autonomous mode with radar tracking."""
        if self.is_active:
            print("[SimpleAutonomous] ⚠️ Autonomous mode already active")
            return
            
        self.is_active = True
        self.running = True
        
        # Start radar tracking system
        self.radar_system.start()
        
        # Start control thread
        self.control_thread = threading.Thread(target=self._autonomous_loop, daemon=True)
        self.control_thread.start()
        
        print("[SimpleAutonomous] 🚀 Autonomous mode started with radar tracking")
        
    def stop_autonomous_mode(self):
        """Stop autonomous mode."""
        self.is_active = False
        self.running = False
        
        # Stop radar tracking system
        self.radar_system.stop()
        
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
            
        print("[SimpleAutonomous] 🛑 Autonomous mode stopped")
        
    def _autonomous_loop(self):
        """Main autonomous control loop."""
        last_auto_fire_time = time.time()
        
        while self.running and self.is_active:
            try:
                # Update radar system parameters
                self.radar_system.set_scan_speed(self.scan_speed)
                self.radar_system.set_movement_speed(self.movement_speed)
                
                # Auto-fire logic
                if self.auto_fire_enabled and self.radar_system.current_target:
                    current_time = time.time()
                    if current_time - last_auto_fire_time >= self.auto_fire_delay:
                        self._auto_fire_laser()
                        last_auto_fire_time = current_time
                
                time.sleep(0.1)  # 10 FPS control loop
                
            except Exception as e:
                print(f"[SimpleAutonomous] ❌ Error in autonomous loop: {e}")
                time.sleep(0.1)
                
    def _auto_fire_laser(self):
        """Auto-fire laser at current target."""
        if not self.laser_control:
            return
            
        try:
            # Fire laser briefly
            self.laser_control.fire_laser()
            time.sleep(0.1)  # Fire for 100ms
            self.laser_control.stop_laser()
            
            print(f"[SimpleAutonomous] 🔫 Auto-fired at target {self.radar_system.current_target.track_id}")
            
        except Exception as e:
            print(f"[SimpleAutonomous] ❌ Error auto-firing laser: {e}")
            
    def set_scan_mode(self, mode_name: str):
        """Set scanning mode by name."""
        mode_map = {
            'radar': ScanMode.RADAR_SWEEP,
            'spiral': ScanMode.SPIRAL_SCAN,
            'sector': ScanMode.SECTOR_SCAN,
            'tracking': ScanMode.TRACKING
        }
        
        if mode_name.lower() in mode_map:
            self.current_scan_mode = mode_map[mode_name.lower()]
            self.radar_system.set_scan_mode(self.current_scan_mode)
            print(f"[SimpleAutonomous] 🔄 Scan mode set to: {mode_name}")
        else:
            print(f"[SimpleAutonomous] ❌ Unknown scan mode: {mode_name}")
            
    def set_scan_speed(self, speed: float):
        """Set scanning speed."""
        self.scan_speed = max(0.5, min(10.0, speed))
        print(f"[SimpleAutonomous] ⚡ Scan speed set to: {self.scan_speed}°/s")
        
    def set_movement_speed(self, speed: float):
        """Set movement speed."""
        self.movement_speed = max(0.5, min(5.0, speed))
        print(f"[SimpleAutonomous] ⚡ Movement speed set to: {self.movement_speed}°/update")
        
    def toggle_auto_fire(self):
        """Toggle auto-fire mode."""
        self.auto_fire_enabled = not self.auto_fire_enabled
        status = "enabled" if self.auto_fire_enabled else "disabled"
        print(f"[SimpleAutonomous] 🔫 Auto-fire {status}")
        
    def emergency_stop(self):
        """Emergency stop all systems."""
        self.stop_autonomous_mode()
        self.radar_system.emergency_stop()
        if self.laser_control:
            self.laser_control.stop_laser()
        print("[SimpleAutonomous] 🚨 Emergency stop executed")
        
    def reset_position(self):
        """Reset to safe position."""
        self.radar_system.reset_position()
        print("[SimpleAutonomous] 🔄 Reset to safe position")
        
    def get_status(self):
        """Get current autonomous mode status."""
        radar_status = self.radar_system.get_status()
        
        return {
            'is_active': self.is_active,
            'auto_fire_enabled': self.auto_fire_enabled,
            'scan_mode': self.current_scan_mode.value,
            'scan_speed': self.scan_speed,
            'movement_speed': self.movement_speed,
            'radar_status': radar_status
        }
        
    def get_target_info(self):
        """Get current target information."""
        if not self.radar_system.current_target:
            return None
            
        target = self.radar_system.current_target
        return {
            'track_id': target.track_id,
            'label': target.label,
            'confidence': target.confidence,
            'center': target.center,
            'bbox': target.bbox,
            'priority': target.priority
        } 