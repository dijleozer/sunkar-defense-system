#!/usr/bin/env python3
"""
Simple GUI integration for autonomous mode
"""

import time
import sys
import os
import threading

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from simple_autonomous import SimpleAutonomousMode
from serial_comm import SerialComm
from laser_control import LaserControl
from camera_manager import CameraManager
from motor_control import MotorControl

class SimpleGUIIntegration:
    """
    Simple GUI integration class for autonomous mode
    Provides easy interface for GUI to interact with autonomous system
    """
    
    def __init__(self, serial_comm, laser_control, camera_manager, motor_control):
        self.serial_comm = serial_comm
        self.laser_control = laser_control
        self.camera_manager = camera_manager
        self.motor_control = motor_control
        
        # Initialize autonomous mode
        self.autonomous = SimpleAutonomousMode(serial_comm, laser_control, camera_manager, motor_control)
        
        # GUI state
        self.is_autonomous_active = False
        self.last_frame_time = time.time()
        self.frame_interval = 0.033  # ~30 FPS
        
    def activate_autonomous_mode(self):
        """Activate autonomous mode from GUI"""
        try:
            self.autonomous.activate()
            self.is_autonomous_active = True
            print("[SimpleGUI] 🚀 Autonomous mode activated")
            return True
        except Exception as e:
            print(f"[SimpleGUI] ❌ Error activating autonomous mode: {e}")
            return False
            
    def deactivate_autonomous_mode(self):
        """Deactivate autonomous mode from GUI"""
        try:
            self.autonomous.deactivate()
            self.is_autonomous_active = False
            print("[SimpleGUI] 🛑 Autonomous mode deactivated")
            return True
        except Exception as e:
            print(f"[SimpleGUI] ❌ Error deactivating autonomous mode: {e}")
            return False
            
    def process_frame(self, frame, tracks):
        """Process frame from GUI and return target information"""
        if not self.is_autonomous_active:
            return None, None, "Autonomous mode not active"
            
        try:
            # Process frame through autonomous system
            target_bbox, target_id, status = self.autonomous.process_frame(frame, tracks)
            return target_bbox, target_id, status
        except Exception as e:
            print(f"[SimpleGUI] ❌ Error processing frame: {e}")
            return None, None, f"Error: {e}"
            
    def get_status(self):
        """Get current system status"""
        if not self.is_autonomous_active:
            return {
                'mode': 'manual',
                'autonomous_active': False,
                'status': 'Manual mode active'
            }
            
        try:
            autonomous_status = self.autonomous.get_status()
            return {
                'mode': 'autonomous',
                'autonomous_active': True,
                'status': autonomous_status
            }
        except Exception as e:
            return {
                'mode': 'error',
                'autonomous_active': False,
                'status': f'Error: {e}'
            }
            
    def emergency_stop(self):
        """Emergency stop all systems"""
        try:
            self.autonomous.emergency_stop()
            self.is_autonomous_active = False
            print("[SimpleGUI] 🚨 Emergency stop executed")
            return True
        except Exception as e:
            print(f"[SimpleGUI] ❌ Error during emergency stop: {e}")
            return False
            
    def reset_position(self):
        """Reset to safe position"""
        try:
            self.autonomous.reset_position()
            print("[SimpleGUI] 🔄 Position reset executed")
            return True
        except Exception as e:
            print(f"[SimpleGUI] ❌ Error resetting position: {e}")
            return False
            
    def get_target_info(self):
        """Get current target information"""
        if not self.is_autonomous_active:
            return None
            
        try:
            return self.autonomous.get_target_info()
        except Exception as e:
            print(f"[SimpleGUI] ❌ Error getting target info: {e}")
            return None

def test_simple_gui_integration():
    """Test simple GUI integration"""
    print("=== Testing Simple GUI Integration ===")
    
    try:
        # Initialize components
        print("1. Initializing components...")
        serial_comm = SerialComm(port="COM14", baudrate=9600, protocol="text")
        laser_control = LaserControl(serial_comm)
        camera_manager = CameraManager()
        motor_control = MotorControl(serial_comm=serial_comm, port="COM14", protocol="text")
        
        # Initialize GUI integration
        gui_integration = SimpleGUIIntegration(serial_comm, laser_control, camera_manager, motor_control)
        
        print("2. Testing autonomous mode activation...")
        success = gui_integration.activate_autonomous_mode()
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        print("3. Testing status retrieval...")
        status = gui_integration.get_status()
        print(f"   Status: {status}")
        
        print("4. Testing frame processing...")
        import numpy as np
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dummy_tracks = []
        
        result = gui_integration.process_frame(dummy_frame, dummy_tracks)
        print(f"   Result: {result}")
        
        print("5. Testing target info...")
        target_info = gui_integration.get_target_info()
        print(f"   Target info: {target_info}")
        
        print("6. Testing deactivation...")
        success = gui_integration.deactivate_autonomous_mode()
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        print("7. Testing emergency stop...")
        success = gui_integration.emergency_stop()
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        print("8. Testing position reset...")
        success = gui_integration.reset_position()
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        print("✅ Simple GUI integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during GUI integration test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_gui_integration() 