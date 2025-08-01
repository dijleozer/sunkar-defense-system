#!/usr/bin/env python3
"""
Test script for motor movement functionality.
This script tests the camera movement and coordinate mapping.
"""

import time
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from camera_manager import CameraManager
from serial_comm import SerialComm

def test_motor_movement():
    """Test motor movement functionality."""
    print("🧪 Testing Motor Movement Functionality")
    print("=" * 50)
    
    # Initialize components
    try:
        serial_comm = SerialComm(port="COM14", baudrate=9600, protocol="text")
        camera_manager = CameraManager(serial_comm)
        
        print("[Test] ✅ Components initialized successfully")
        
        # Test 1: Basic movement commands
        print("\n1. Testing basic movement commands:")
        
        # Test horizontal movement (stepper)
        print("   Moving right (dx=0.1)...")
        camera_manager.move_camera_smooth(0.1, 0)
        time.sleep(1)
        
        print("   Moving left (dx=-0.1)...")
        camera_manager.move_camera_smooth(-0.1, 0)
        time.sleep(1)
        
        # Test vertical movement (servo)
        print("   Moving up (dy=0.1)...")
        camera_manager.move_camera_smooth(0, 0.1)
        time.sleep(1)
        
        print("   Moving down (dy=-0.1)...")
        camera_manager.move_camera_smooth(0, -0.1)
        time.sleep(1)
        
        # Test 2: Get current position
        print("\n2. Testing position tracking:")
        position = camera_manager.get_camera_position()
        print(f"   Current position: Servo={position['servo_angle']:.1f}°, Stepper={position['stepper_angle']:.1f}°")
        print(f"   Target position: Servo={position['target_servo']:.1f}°, Stepper={position['target_stepper']:.1f}°")
        
        # Test 3: Reset to center
        print("\n3. Testing reset to center:")
        camera_manager.reset_position()
        time.sleep(2)
        
        position = camera_manager.get_camera_position()
        print(f"   After reset: Servo={position['servo_angle']:.1f}°, Stepper={position['stepper_angle']:.1f}°")
        
        # Test 4: Movement statistics
        print("\n4. Testing movement statistics:")
        stats = camera_manager.get_movement_statistics()
        print(f"   Total movements: {stats.get('total_movements', 0)}")
        print(f"   Average servo change: {stats.get('avg_servo_change', 0):.3f}")
        print(f"   Average stepper change: {stats.get('avg_stepper_change', 0):.3f}")
        
        print("\n✅ Motor movement test completed!")
        
    except Exception as e:
        print(f"[Test] ❌ Error during testing: {e}")
        print("[Test] Make sure Arduino is connected and motors are working")
    
    finally:
        # Cleanup
        if 'serial_comm' in locals():
            serial_comm.close()
        print("[Test] 🔌 Cleanup completed")

if __name__ == "__main__":
    test_motor_movement() 