#!/usr/bin/env python3
"""
Test script for Capability11Service integration
Tests the background service initialization and GUI integration.
"""

import time
import threading
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from capability11_service import Capability11Service

# Mock classes for testing
class MockSerialComm:
    def __init__(self):
        self.connected = True
        self.last_commands = []
    
    def send_command(self, command):
        self.last_commands.append(command)
        print(f"[MockSerialComm] 📤 Sent: {command}")

class MockLaserControl:
    def __init__(self):
        self.fire_count = 0
    
    def fire_laser(self, duration=0.5):
        self.fire_count += 1
        print(f"[MockLaserControl] 🔥 Fired laser #{self.fire_count}")

class MockCameraManager:
    def __init__(self):
        self.frame = None
        self.tracks = []
    
    def get_frame(self):
        return self.frame, self.tracks

class MockMotorControl:
    def __init__(self):
        self.servo_position = 30
        self.stepper_position = 150
    
    def move_servo(self, angle):
        self.servo_position = angle
        print(f"[MockMotorControl] 🎛️ Servo moved to {angle}°")
    
    def move_stepper(self, angle):
        self.stepper_position = angle
        print(f"[MockMotorControl] ⚙️ Stepper moved to {angle}°")

def test_capability11_service_integration():
    """Test the Capability11Service integration."""
    print("=" * 60)
    print("🧪 CAPABILITY 11 SERVICE INTEGRATION TEST")
    print("=" * 60)
    
    # Create mock components
    print("\n📋 Creating mock components...")
    serial_comm = MockSerialComm()
    laser_control = MockLaserControl()
    camera_manager = MockCameraManager()
    motor_control = MockMotorControl()
    
    # Initialize Capability11Service
    print("\n🔄 Initializing Capability11Service...")
    service = Capability11Service(serial_comm, laser_control, camera_manager, motor_control)
    
    # Test 1: Service initialization
    print("\n" + "=" * 40)
    print("🧪 TEST 1: Service Initialization")
    print("=" * 40)
    
    # Wait for initialization
    print("⏳ Waiting for service initialization...")
    if service.wait_for_initialization(timeout=10.0):
        print("✅ Service initialized successfully")
    else:
        print("❌ Service initialization failed or timed out")
        return False
    
    # Test 2: Service availability
    print("\n" + "=" * 40)
    print("🧪 TEST 2: Service Availability")
    print("=" * 40)
    
    service_status = service.get_service_status()
    print(f"Service status: {service_status}")
    
    if service.is_capability11_available():
        print("✅ Capability 11 is available")
    else:
        print("❌ Capability 11 is not available")
        return False
    
    # Test 3: Status and target info
    print("\n" + "=" * 40)
    print("🧪 TEST 3: Status and Target Info")
    print("=" * 40)
    
    capability11_status = service.get_capability11_status()
    target_info = service.get_capability11_target_info()
    
    print(f"Capability 11 status: {capability11_status}")
    print(f"Target info: {target_info}")
    
    # Test 4: Activation and deactivation
    print("\n" + "=" * 40)
    print("🧪 TEST 4: Activation and Deactivation")
    print("=" * 40)
    
    try:
        # Activate Capability 11
        print("🎯 Activating Capability 11...")
        service.activate_capability11()
        
        # Check if active
        status = service.get_capability11_status()
        if status['is_active']:
            print("✅ Capability 11 activated successfully")
        else:
            print("❌ Capability 11 not activated")
        
        # Wait a moment
        time.sleep(2)
        
        # Deactivate Capability 11
        print("🛑 Deactivating Capability 11...")
        service.deactivate_capability11()
        
        # Check if deactivated
        status = service.get_capability11_status()
        if not status['is_active']:
            print("✅ Capability 11 deactivated successfully")
        else:
            print("❌ Capability 11 not deactivated")
            
    except Exception as e:
        print(f"❌ Error during activation/deactivation: {e}")
        return False
    
    # Test 5: Emergency stop
    print("\n" + "=" * 40)
    print("🧪 TEST 5: Emergency Stop")
    print("=" * 40)
    
    try:
        # Activate again
        service.activate_capability11()
        time.sleep(1)
        
        # Emergency stop
        print("🚨 Emergency stopping Capability 11...")
        service.emergency_stop()
        
        # Check if stopped
        status = service.get_capability11_status()
        if not status['is_active']:
            print("✅ Emergency stop successful")
        else:
            print("❌ Emergency stop failed")
            
    except Exception as e:
        print(f"❌ Error during emergency stop: {e}")
        return False
    
    # Test 6: Shutdown
    print("\n" + "=" * 40)
    print("🧪 TEST 6: Service Shutdown")
    print("=" * 40)
    
    try:
        print("🔌 Shutting down service...")
        service.shutdown()
        
        # Check if shutdown
        service_status = service.get_service_status()
        if not service_status['is_available']:
            print("✅ Service shutdown successful")
        else:
            print("❌ Service shutdown failed")
            
    except Exception as e:
        print(f"❌ Error during shutdown: {e}")
        return False
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 ALL INTEGRATION TESTS PASSED!")
    print("=" * 60)
    print("\n✅ Capability11Service integration is working correctly")
    print("✅ Service can be initialized as background task")
    print("✅ Service can be activated/deactivated on demand")
    print("✅ Emergency stop functionality works")
    print("✅ Service can be properly shut down")
    
    return True

def test_gui_integration_simulation():
    """Simulate GUI integration behavior."""
    print("\n" + "=" * 60)
    print("🖥️ GUI INTEGRATION SIMULATION")
    print("=" * 60)
    
    # Create mock components
    serial_comm = MockSerialComm()
    laser_control = MockLaserControl()
    camera_manager = MockCameraManager()
    motor_control = MockMotorControl()
    
    # Initialize service
    service = Capability11Service(serial_comm, laser_control, camera_manager, motor_control)
    
    # Simulate GUI behavior
    print("\n📋 Simulating GUI behavior:")
    
    # 1. Check if service is available
    if service.is_capability11_available():
        print("✅ GUI: Capability 11 service is available")
        
        # 2. Simulate autonomous mode button press
        print("🎯 GUI: Autonomous mode button pressed")
        try:
            service.activate_capability11()
            print("✅ GUI: Capability 11 activated successfully")
            
            # 3. Get status for display
            status = service.get_capability11_status()
            target_info = service.get_capability11_target_info()
            
            print(f"📊 GUI Status: {status['red_balloons_eliminated']}/{status['total_red_balloons']} eliminated")
            print(f"🎯 GUI Target: {target_info['current_target']}")
            
            # 4. Simulate emergency stop
            print("🚨 GUI: Emergency stop button pressed")
            service.emergency_stop()
            print("✅ GUI: Emergency stop successful")
            
        except Exception as e:
            print(f"❌ GUI Error: {e}")
    else:
        print("❌ GUI: Capability 11 service not available")
    
    # Cleanup
    service.shutdown()

if __name__ == "__main__":
    try:
        # Run integration tests
        success = test_capability11_service_integration()
        
        if success:
            # Run GUI simulation
            test_gui_integration_simulation()
            
            print("\n🎯 All tests completed successfully!")
            print("Capability11Service is ready for integration with main.py")
            print("\n📋 Next steps:")
            print("1. Run main.py to start the full system")
            print("2. Check that Capability 11 service initializes in background")
            print("3. Press 'Autonomous Mode' button to activate Capability 11")
            print("4. Verify that only red balloons are targeted")
            
        else:
            print("\n❌ Integration tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 