import time
from hybrid_autonomous import HybridAutonomousMode

class AutonomousManager:
    """
    Clean autonomous mode manager that can be easily integrated.
    Separates autonomous logic from GUI concerns.
    """
    
    def __init__(self, serial_comm, laser_control, camera_manager):
        self.autonomous_mode = HybridAutonomousMode(serial_comm, laser_control, camera_manager)
        self.is_active = False
        self.status = "Ready"
        
    def activate(self):
        """Activate autonomous mode"""
        self.is_active = True
        self.autonomous_mode.reset()
        self.status = "Active"
        print("[AutonomousManager] 🚀 Autonomous mode activated")
        
    def deactivate(self):
        """Deactivate autonomous mode"""
        self.is_active = False
        self.status = "Inactive"
        print("[AutonomousManager] ⏹️ Autonomous mode deactivated")
        
    def process_frame(self, frame, detections):
        """Process frame if autonomous mode is active"""
        if not self.is_active:
            return None, None, "Autonomous mode inactive"
            
        return self.autonomous_mode.process_frame(frame, detections)
        
    def emergency_stop(self):
        """Emergency stop"""
        self.is_active = False
        self.autonomous_mode.emergency_stop()
        self.status = "EMERGENCY STOP"
        print("[AutonomousManager] 🚨 Emergency stop activated")
        
    def reset(self):
        """Reset autonomous mode"""
        self.autonomous_mode.reset()
        self.status = "Reset"
        print("[AutonomousManager] 🔄 Reset complete")
        
    def get_status(self):
        """Get current status"""
        return {
            'active': self.is_active,
            'status': self.status,
            'autonomous_status': self.autonomous_mode.get_status()
        }
        
    def set_parameters(self, **kwargs):
        """Set autonomous mode parameters"""
        self.autonomous_mode.set_parameters(**kwargs) 