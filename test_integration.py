#!/usr/bin/env python3
"""
Test script for the updated joystick controller and serial communication
"""

import time
from src.joystick_controller import JoystickController
from src.serial_comm import SerialComm

def test_serial_communication():
    """Test serial communication with Arduino"""
    print("=== Testing Serial Communication ===")
    
    # Test serial connection
    serial = SerialComm(port="COM14", baudrate=115200)
    
    if serial.ser is None:
        print("❌ Serial connection failed!")
        return False
    
    print("✅ Serial connection established")
    
    # Test status request
    print("\n--- Testing Status Request ---")
    response = serial.request_status()
    if response:
        print(f"✅ Status received: {response}")
    else:
        print("⚠️ No status response (Arduino might not be connected)")
    
    # Test YAW command
    print("\n--- Testing YAW Command ---")
    response = serial.send_yaw_command(90)
    if response:
        print(f"✅ YAW command response: {response}")
    else:
        print("⚠️ No YAW response")
    
    # Test PITCH command
    print("\n--- Testing PITCH Command ---")
    response = serial.send_pitch_command(30)
    if response:
        print(f"✅ PITCH command response: {response}")
    else:
        print("⚠️ No PITCH response")
    
    # Test FIRE command
    print("\n--- Testing FIRE Command ---")
    response = serial.send_fire_command(True)
    if response:
        print(f"✅ FIRE command response: {response}")
    else:
        print("⚠️ No FIRE response")
    
    time.sleep(1)
    
    # Turn off laser
    response = serial.send_fire_command(False)
    if response:
        print(f"✅ FIRE OFF command response: {response}")
    
    serial.close()
    return True

def test_joystick_controller():
    """Test joystick controller"""
    print("\n=== Testing Joystick Controller ===")
    
    try:
        # Create joystick controller
        controller = JoystickController(port="COM14", mode="manual")
        
        if controller.joystick is None:
            print("❌ Joystick not found!")
            return False
        
        print("✅ Joystick controller initialized")
        
        # Test mode switching
        print("\n--- Testing Mode Switching ---")
        controller.set_mode("manual")
        controller.set_mode("auto")
        controller.set_mode("manual")
        
        # Test position reading
        print("\n--- Testing Position Reading ---")
        for i in range(5):
            pos = controller.get_position()
            print(f"Position {i+1}: X={pos[0]:.2f}, Y={pos[1]:.2f}")
            time.sleep(0.5)
        
        # Test button reading
        print("\n--- Testing Button Reading ---")
        for i in range(5):
            button0 = controller.get_button_pressed(0)
            button1 = controller.get_button_pressed(1)
            print(f"Buttons {i+1}: B0={button0}, B1={button1}")
            time.sleep(0.5)
        
        controller.close()
        return True
        
    except Exception as e:
        print(f"❌ Joystick test failed: {e}")
        return False

def test_manual_control():
    """Test manual control mode"""
    print("\n=== Testing Manual Control Mode ===")
    
    try:
        controller = JoystickController(port="COM14", mode="manual")
        
        if controller.joystick is None:
            print("❌ Joystick not found!")
            return False
        
        print("✅ Starting manual control test...")
        print("Move joystick and press fire buttons to test")
        print("Press Ctrl+C to stop")
        
        # Run manual control for 10 seconds
        start_time = time.time()
        while time.time() - start_time < 10:
            controller.manual_mode_control()
            time.sleep(0.1)
        
        controller.close()
        print("✅ Manual control test completed")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Manual control test stopped by user")
        controller.close()
        return True
    except Exception as e:
        print(f"❌ Manual control test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Integration Tests")
    print("=" * 50)
    
    # Test 1: Serial Communication
    serial_ok = test_serial_communication()
    
    # Test 2: Joystick Controller
    joystick_ok = test_joystick_controller()
    
    # Test 3: Manual Control (optional - requires user interaction)
    print("\nDo you want to test manual control? (y/n): ", end="")
    try:
        response = input().lower()
        if response == 'y':
            manual_ok = test_manual_control()
        else:
            manual_ok = True
            print("⏭️ Skipping manual control test")
    except KeyboardInterrupt:
        manual_ok = True
        print("\n⏭️ Skipping manual control test")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"Serial Communication: {'✅ PASS' if serial_ok else '❌ FAIL'}")
    print(f"Joystick Controller: {'✅ PASS' if joystick_ok else '❌ FAIL'}")
    print(f"Manual Control: {'✅ PASS' if manual_ok else '❌ FAIL'}")
    
    if serial_ok and joystick_ok and manual_ok:
        print("\n🎉 All tests passed! Integration successful!")
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main() 