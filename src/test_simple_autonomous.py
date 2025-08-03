#!/usr/bin/env python3
"""
Test script for simple autonomous mode functionality
"""

import time
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from simple_autonomous import SimpleAutonomousMode
from serial_comm import SerialComm
from laser_control import LaserControl
from camera_manager import CameraManager
from motor_control import MotorControl

def test_simple_autonomous():
    """Test simple autonomous mode functionality"""
    print("=== Testing Simple Autonomous Mode ===")
    
    try:
        # Initialize components
        print("1. Initializing components...")
        serial_comm = SerialComm(port="COM14", baudrate=9600, protocol="text")
        laser_control = LaserControl(serial_comm)
        camera_manager = CameraManager()
        motor_control = MotorControl(serial_comm=serial_comm, port="COM14", protocol="text")
        
        # Initialize autonomous mode
        autonomous = SimpleAutonomousMode(serial_comm, laser_control, camera_manager, motor_control)
        
        print("2. Testing autonomous mode parameters...")
        print(f"   - Servo limits: {autonomous.servo_min} to {autonomous.servo_max}")
        print(f"   - Stepper limits: {autonomous.stepper_min} to {autonomous.stepper_max}")
        print(f"   - Movement speed: {autonomous.movement_speed}")
        print(f"   - Movement interval: {autonomous.movement_interval}")
        print(f"   - Auto-fire enabled: {autonomous.auto_fire_enabled}")
        print(f"   - Auto-fire range: {autonomous.auto_fire_range}")
        
        print("3. Testing autonomous mode activation...")
        autonomous.activate()
        print("   ✅ Autonomous mode activated")
        
        print("4. Testing status methods...")
        status = autonomous.get_status()
        print(f"   Status: {status}")
        
        print("5. Testing target info...")
        target_info = autonomous.get_target_info()
        print(f"   Target info: {target_info}")
        
        print("6. Testing deactivation...")
        autonomous.deactivate()
        print("   ✅ Autonomous mode deactivated")
        
        print("7. Testing emergency stop...")
        autonomous.emergency_stop()
        print("   ✅ Emergency stop executed")
        
        print("8. Testing reset position...")
        autonomous.reset_position()
        print("   ✅ Position reset executed")
        
        print("✅ Simple autonomous mode test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during simple autonomous test: {e}")
        import traceback
        traceback.print_exc()

def test_gui_integration():
    """Test GUI integration methods"""
    print("\n=== Testing GUI Integration ===")
    
    try:
        # Initialize components
        serial_comm = SerialComm(port="COM14", baudrate=9600, protocol="text")
        laser_control = LaserControl(serial_comm)
        camera_manager = CameraManager()
        motor_control = MotorControl(serial_comm=serial_comm, port="COM14", protocol="text")
        
        # Initialize autonomous mode
        autonomous = SimpleAutonomousMode(serial_comm, laser_control, camera_manager, motor_control)
        
        print("1. Testing activate() method...")
        autonomous.activate()
        print("   ✅ activate() method works")
        
        print("2. Testing deactivate() method...")
        autonomous.deactivate()
        print("   ✅ deactivate() method works")
        
        print("3. Testing process_frame() method...")
        # Create dummy frame and tracks
        import numpy as np
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        dummy_tracks = []
        
        result = autonomous.process_frame(dummy_frame, dummy_tracks)
        print(f"   ✅ process_frame() method works: {result}")
        
        print("✅ GUI integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during GUI integration test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_autonomous()
    test_gui_integration() 