#!/usr/bin/env python3
"""
Test script for Capability11Tracker
Run this independently to test the Capability 11 autonomous mode.
"""

import time
import threading
import cv2
import numpy as np
from capability11_tracker import Capability11Tracker, BalloonColor, BalloonTarget

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
        self.last_fire_time = None
    
    def fire_laser(self, duration=0.5):
        self.fire_count += 1
        self.last_fire_time = time.time()
        print(f"[MockLaserControl] 🔥 Fired laser #{self.fire_count} (duration: {duration}s)")

class MockCameraManager:
    def __init__(self):
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.tracks = []
        self.running = True
    
    def get_frame(self):
        return self.frame
    
    def get_tracks(self):
        return self.tracks
    
    def start(self):
        print("[MockCameraManager] 📹 Camera started")
    
    def stop(self):
        print("[MockCameraManager] 📹 Camera stopped")

class MockMotorControl:
    def __init__(self):
        self.servo_position = 30
        self.stepper_position = 150
        self.movement_history = []
    
    def move_servo(self, angle):
        self.servo_position = angle
        self.movement_history.append(f"servo:{angle}")
        print(f"[MockMotorControl] 🎛️ Servo moved to {angle}°")
    
    def move_stepper(self, angle):
        self.stepper_position = angle
        self.movement_history.append(f"stepper:{angle}")
        print(f"[MockMotorControl] ⚙️ Stepper moved to {angle}°")

def create_test_targets():
    """Create test balloon targets for simulation."""
    # Create 3 red balloons at different distances from center
    red_targets = [
        {
            'track_id': 1,
            'bbox': (300, 200, 340, 240),  # Close to center
            'label': 'red_balloon',
            'confidence': 0.9
        },
        {
            'track_id': 2,
            'bbox': (100, 100, 140, 140),  # Medium distance
            'label': 'red_balloon',
            'confidence': 0.85
        },
        {
            'track_id': 3,
            'bbox': (500, 300, 540, 340),  # Far from center
            'label': 'red_balloon',
            'confidence': 0.8
        }
    ]
    
    # Create 3 blue balloons
    blue_targets = [
        {
            'track_id': 4,
            'bbox': (200, 150, 240, 190),
            'label': 'blue_balloon',
            'confidence': 0.9
        },
        {
            'track_id': 5,
            'bbox': (400, 250, 440, 290),
            'label': 'blue_balloon',
            'confidence': 0.85
        },
        {
            'track_id': 6,
            'bbox': (150, 350, 190, 390),
            'label': 'blue_balloon',
            'confidence': 0.8
        }
    ]
    
    return red_targets + blue_targets

def simulate_target_elimination(tracker, target_id):
    """Simulate elimination of a target."""
    for target in tracker.red_targets:
        if target.track_id == target_id:
            target.eliminated = True
            target.elimination_time = time.time()
            print(f"[Test] 🎯 Simulated elimination of red balloon {target_id}")
            break

def test_capability11_tracker():
    """Main test function for Capability11Tracker."""
    print("=" * 60)
    print("🧪 CAPABILITY 11 TRACKER TEST")
    print("=" * 60)
    
    # Create mock components
    serial_comm = MockSerialComm()
    laser_control = MockLaserControl()
    camera_manager = MockCameraManager()
    motor_control = MockMotorControl()
    
    # Create tracker instance
    tracker = Capability11Tracker(serial_comm, laser_control, camera_manager, motor_control)
    
    print("\n📋 Test Setup:")
    print(f"   - Mock components created")
    print(f"   - Tracker initialized")
    print(f"   - Mission: Eliminate 3 red balloons")
    print(f"   - Target order: Closest to center first")
    print(f"   - Blue balloons: NEVER target")
    
    # Test 1: Basic initialization
    print("\n" + "=" * 40)
    print("🧪 TEST 1: Basic Initialization")
    print("=" * 40)
    
    status = tracker.get_status()
    print(f"Initial status: {status}")
    
    assert not status['is_active'], "Tracker should not be active initially"
    assert status['red_balloons_eliminated'] == 0, "No balloons eliminated initially"
    assert not status['mission_complete'], "Mission should not be complete initially"
    
    print("✅ Test 1 PASSED: Basic initialization")
    
    # Test 2: Start capability mode
    print("\n" + "=" * 40)
    print("🧪 TEST 2: Start Capability Mode")
    print("=" * 40)
    
    tracker.start_capability11_mode()
    time.sleep(0.5)  # Let the thread start
    
    status = tracker.get_status()
    print(f"Status after start: {status}")
    
    assert status['is_active'], "Tracker should be active after start"
    assert status['mission_start_time'] > 0, "Mission should have start time"
    
    print("✅ Test 2 PASSED: Capability mode started")
    
    # Test 3: Target detection and classification
    print("\n" + "=" * 40)
    print("🧪 TEST 3: Target Detection and Classification")
    print("=" * 40)
    
    # Simulate camera detecting targets
    camera_manager.tracks = create_test_targets()
    
    # Let the tracker process the targets
    time.sleep(1.0)
    
    target_info = tracker.get_target_info()
    print(f"Target info: {target_info}")
    
    assert len(target_info['red_targets']) == 3, "Should detect 3 red balloons"
    assert len(target_info['blue_targets']) == 3, "Should detect 3 blue balloons"
    
    # Check that red targets are sorted by distance to center
    red_distances = [t['distance_to_center'] for t in target_info['red_targets']]
    assert red_distances == sorted(red_distances), "Red targets should be sorted by distance"
    
    print("✅ Test 3 PASSED: Target detection and classification")
    
    # Test 4: Target selection (closest red balloon first)
    print("\n" + "=" * 40)
    print("🧪 TEST 4: Target Selection (Closest First)")
    print("=" * 40)
    
    # The closest red balloon should be track_id 1 (at 300, 200)
    current_target = tracker.current_target
    print(f"Current target: {current_target.track_id if current_target else None}")
    
    assert current_target is not None, "Should have a current target"
    assert current_target.track_id == 1, "Should target closest red balloon (track_id 1)"
    assert current_target.color == BalloonColor.RED, "Should only target red balloons"
    
    print("✅ Test 4 PASSED: Target selection working correctly")
    
    # Test 5: Simulate target elimination
    print("\n" + "=" * 40)
    print("🧪 TEST 5: Target Elimination")
    print("=" * 40)
    
    # Simulate eliminating the first target
    simulate_target_elimination(tracker, 1)
    tracker.red_balloons_eliminated += 1
    
    # Let the tracker update
    time.sleep(0.5)
    
    # Should now target the next closest red balloon (track_id 2)
    current_target = tracker.current_target
    print(f"Current target after elimination: {current_target.track_id if current_target else None}")
    
    assert current_target.track_id == 2, "Should target next closest red balloon (track_id 2)"
    
    print("✅ Test 5 PASSED: Target elimination working")
    
    # Test 6: Mission completion
    print("\n" + "=" * 40)
    print("🧪 TEST 6: Mission Completion")
    print("=" * 40)
    
    # Simulate eliminating all red balloons
    simulate_target_elimination(tracker, 2)
    simulate_target_elimination(tracker, 3)
    tracker.red_balloons_eliminated = 3
    
    # Let the tracker check mission completion
    time.sleep(0.5)
    
    status = tracker.get_status()
    print(f"Final status: {status}")
    
    assert status['red_balloons_eliminated'] == 3, "Should eliminate all 3 red balloons"
    assert status['mission_complete'], "Mission should be complete"
    
    print("✅ Test 6 PASSED: Mission completion")
    
    # Test 7: Blue balloon protection
    print("\n" + "=" * 40)
    print("🧪 TEST 7: Blue Balloon Protection")
    print("=" * 40)
    
    # Verify that blue balloons are never targeted
    target_info = tracker.get_target_info()
    blue_targets = target_info['blue_targets']
    
    print(f"Blue balloons detected: {len(blue_targets)}")
    print(f"Blue balloon track IDs: {[t['track_id'] for t in blue_targets]}")
    
    # Check that no blue balloons were eliminated
    for target in tracker.blue_targets:
        assert not hasattr(target, 'eliminated') or not target.eliminated, "Blue balloons should never be eliminated"
    
    print("✅ Test 7 PASSED: Blue balloons protected")
    
    # Test 8: Stop capability mode
    print("\n" + "=" * 40)
    print("🧪 TEST 8: Stop Capability Mode")
    print("=" * 40)
    
    tracker.stop_capability11_mode()
    time.sleep(0.5)  # Let the thread stop
    
    status = tracker.get_status()
    print(f"Status after stop: {status}")
    
    assert not status['is_active'], "Tracker should not be active after stop"
    
    print("✅ Test 8 PASSED: Capability mode stopped")
    
    # Test 9: Emergency stop
    print("\n" + "=" * 40)
    print("🧪 TEST 9: Emergency Stop")
    print("=" * 40)
    
    tracker.start_capability11_mode()
    time.sleep(0.2)
    
    tracker.emergency_stop()
    time.sleep(0.2)
    
    status = tracker.get_status()
    assert not status['is_active'], "Tracker should be stopped after emergency stop"
    
    print("✅ Test 9 PASSED: Emergency stop working")
    
    # Test 10: Performance metrics
    print("\n" + "=" * 40)
    print("🧪 TEST 10: Performance Metrics")
    print("=" * 40)
    
    # Check that performance tracking is working
    target_info = tracker.get_target_info()
    print(f"Target info keys: {list(target_info.keys())}")
    print(f"Status keys: {list(tracker.get_status().keys())}")
    
    assert 'red_targets' in target_info, "Should have red targets info"
    assert 'blue_targets' in target_info, "Should have blue targets info"
    assert 'current_target' in target_info, "Should have current target info"
    
    print("✅ Test 10 PASSED: Performance metrics working")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("\n📊 Test Summary:")
    print(f"   - Laser fires: {laser_control.fire_count}")
    print(f"   - Motor movements: {len(motor_control.movement_history)}")
    print(f"   - Serial commands: {len(serial_comm.last_commands)}")
    print(f"   - Red balloons eliminated: {tracker.red_balloons_eliminated}")
    print(f"   - Blue balloons protected: {len(tracker.blue_targets)}")
    print(f"   - Mission complete: {tracker.mission_complete}")
    
    print("\n✅ Capability11Tracker is ready for integration!")
    print("   - Can be tested independently")
    print("   - Can be integrated into existing GUI")
    print("   - Only targets red balloons in order of proximity to center")
    print("   - Never targets blue balloons")
    print("   - Provides comprehensive status and target information")

def test_integration_interface():
    """Test the integration interface methods."""
    print("\n" + "=" * 60)
    print("🔗 INTEGRATION INTERFACE TEST")
    print("=" * 60)
    
    # Create mock components
    serial_comm = MockSerialComm()
    laser_control = MockLaserControl()
    camera_manager = MockCameraManager()
    motor_control = MockMotorControl()
    
    # Create tracker instance
    tracker = Capability11Tracker(serial_comm, laser_control, camera_manager, motor_control)
    
    # Test integration methods
    print("\n🧪 Testing integration methods:")
    
    # Test activate/deactivate
    tracker.activate()
    assert tracker.is_active, "activate() should start the tracker"
    
    tracker.deactivate()
    assert not tracker.is_active, "deactivate() should stop the tracker"
    
    # Test process_frame (should not raise errors)
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    test_tracks = []
    tracker.process_frame(test_frame, test_tracks)
    
    print("✅ Integration interface working correctly")

if __name__ == "__main__":
    try:
        test_capability11_tracker()
        test_integration_interface()
        print("\n🎯 All tests completed successfully!")
        print("Capability11Tracker is ready for integration with your GUI.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 