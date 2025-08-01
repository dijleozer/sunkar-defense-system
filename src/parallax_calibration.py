import cv2
import numpy as np
import time
from camera_manager import CameraManager
from serial_comm import SerialComm
from laser_control import LaserControl

class ParallaxCalibration:
    """
    Enhanced utility for calibrating the parallax offset between camera and laser.
    Camera is mounted parallel to laser (both pointing forward) - minimal parallax error.
    """
    
    def __init__(self, com_port="COM14", protocol="text"):
        self.serial = SerialComm(port=com_port, protocol=protocol)
        self.camera = CameraManager(serial_comm=self.serial)
        self.laser = LaserControl(self.serial)
        
        # Physical setup parameters (parallel mounting)
        self.camera_laser_gap = 0.025  # 2.5 cm gap (adjust this to your actual gap)
        self.camera_fov_horizontal = 60  # degrees (typical webcam FOV)
        self.camera_fov_vertical = 45    # degrees (typical webcam FOV)
        
        # Calibration parameters (much smaller offsets for parallel mounting)
        self.calibration_targets = []
        self.current_offset = 0.05  # Much smaller default offset for parallel mounting
        self.test_fire_count = 0
        self.max_test_fires = 10  # Increased for better calibration
        
        # Distance-based calibration
        self.calibration_distances = [0.5, 1.0, 2.0, 3.0]  # meters
        self.current_distance = 1.0  # Current calibration distance
        self.distance_index = 0
        
    def calculate_parallax_offset(self, distance_meters):
        """
        Calculate parallax offset for parallel-mounted camera and laser.
        Since both are pointing forward, parallax error is much smaller.
        
        Args:
            distance_meters: Distance to target in meters
            
        Returns:
            parallax_offset: Normalized offset (0-1)
        """
        # Convert camera FOV to radians
        fov_vertical_rad = np.radians(self.camera_fov_vertical)
        
        # For parallel mounting, the parallax error is much smaller
        # The camera and laser are both pointing forward, so the error is minimal
        # We use a much smaller factor for parallel mounting
        parallax_factor = 0.1  # Much smaller factor for parallel mounting
        
        # Calculate the small parallax angle
        angle_rad = np.arctan(self.camera_laser_gap / distance_meters) * parallax_factor
        
        # Convert angle to normalized offset in frame coordinates
        parallax_offset = angle_rad / (fov_vertical_rad / 2)
        
        # Ensure offset is within reasonable bounds (much smaller range)
        parallax_offset = max(0.0, min(0.1, parallax_offset))  # Max 10% for parallel mounting
        
        return parallax_offset
    
    def start_calibration(self):
        """Start the enhanced parallax calibration process for parallel mounting."""
        print("\n" + "="*60)
        print("🎯 PARALLEL-MOUNT PARALLAX CALIBRATION UTILITY")
        print("="*60)
        print(f"Physical Setup: {self.camera_laser_gap*1000:.1f}mm gap, camera parallel to laser")
        print(f"Camera FOV: {self.camera_fov_horizontal}° horizontal, {self.camera_fov_vertical}° vertical")
        print("\nInstructions:")
        print("1. Place a target at a known distance (0.5m, 1m, 2m, 3m)")
        print("2. Use +/- to adjust the calculated offset (small adjustments)")
        print("3. Test fire to verify accuracy")
        print("4. Press 'D' to cycle through different distances")
        print("5. Save the calibration when satisfied")
        print("Note: Parallel mounting means very small parallax errors")
        print("="*60)
        
        # Start camera
        self.camera.start()
        time.sleep(1)
        
        # Calculate initial offset for current distance
        self.current_offset = self.calculate_parallax_offset(self.current_distance)
        
        # Run calibration
        self._run_calibration_loop()
        
    def _run_calibration_loop(self):
        """Enhanced calibration loop with distance-based calculations."""
        while True:
            frame, tracks = self.camera.get_frame()
            if frame is None:
                continue
                
            # Display calibration interface
            display_frame = self._create_calibration_display(frame)
            
            # Show frame
            cv2.imshow("Enhanced Parallax Calibration", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('f'):
                self._test_fire()
            elif key == ord('+'):
                self._adjust_offset(0.005)  # Smaller increments for precision
            elif key == ord('-'):
                self._adjust_offset(-0.005)
            elif key == ord('d'):
                self._cycle_distance()
            elif key == ord('s'):
                self._save_calibration()
            elif key == ord('r'):
                self._reset_calibration()
                
        cv2.destroyAllWindows()
        self.camera.stop()
        
    def _cycle_distance(self):
        """Cycle through different calibration distances."""
        self.distance_index = (self.distance_index + 1) % len(self.calibration_distances)
        self.current_distance = self.calibration_distances[self.distance_index]
        
        # Recalculate theoretical offset for new distance
        theoretical_offset = self.calculate_parallax_offset(self.current_distance)
        self.current_offset = theoretical_offset
        
        print(f"📏 Distance changed to {self.current_distance}m, theoretical offset: {theoretical_offset:.3f}")
        
    def _create_calibration_display(self, frame):
        """Create enhanced calibration display with parallel mounting info."""
        display = frame.copy()
        height, width = display.shape[:2]
        
        # Draw crosshair at center
        center_x, center_y = width // 2, height // 2
        cv2.line(display, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
        cv2.line(display, (center_x, center_y - 20), (center_x, center_y + 20), (0, 255, 0), 2)
        
        # Draw laser firing point (compensated for parallax)
        laser_y = int(center_y + (self.current_offset * height))
        cv2.circle(display, (center_x, laser_y), 5, (0, 0, 255), -1)
        cv2.line(display, (center_x - 15, laser_y), (center_x + 15, laser_y), (0, 0, 255), 2)
        
        # Calculate theoretical offset for comparison
        theoretical_offset = self.calculate_parallax_offset(self.current_distance)
        theoretical_laser_y = int(center_y + (theoretical_offset * height))
        cv2.circle(display, (center_x, theoretical_laser_y), 3, (255, 255, 0), -1)
        
        # Add comprehensive text overlay
        cv2.putText(display, f"Distance: {self.current_distance}m", 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, f"Current Offset: {self.current_offset:.3f}", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, f"Theoretical: {theoretical_offset:.3f}", 
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(display, f"Test Fires: {self.test_fire_count}/{self.max_test_fires}", 
                    (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add physical setup info
        cv2.putText(display, f"Gap: {self.camera_laser_gap*1000:.1f}mm", 
                    (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(display, f"FOV: {self.camera_fov_vertical}°", 
                    (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(display, f"Mount: Parallel", 
                    (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add instructions
        cv2.putText(display, "Controls:", (10, height - 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, "F - Test Fire", (10, height - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, "+/- - Adjust Offset", (10, height - 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, "D - Change Distance", (10, height - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, "S - Save Calibration", (10, height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, "R - Reset", (10, height - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display, "Q - Quit", (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return display
        
    def _test_fire(self):
        """Perform a test fire to check calibration."""
        if self.test_fire_count >= self.max_test_fires:
            print("⚠️ Maximum test fires reached. Reset to continue testing.")
            return
            
        print(f"🔥 Test fire #{self.test_fire_count + 1} at {self.current_distance}m with offset {self.current_offset:.3f}")
        self.laser.fire_laser(0.1)  # Short test fire
        self.test_fire_count += 1
        
        # Record calibration data with distance information
        self.calibration_targets.append({
            'offset': self.current_offset,
            'distance': self.current_distance,
            'test_fire': self.test_fire_count,
            'timestamp': time.time()
        })
        
    def _adjust_offset(self, delta):
        """Adjust the parallax offset with precision (smaller increments for parallel mounting)."""
        new_offset = self.current_offset + delta
        if 0.0 <= new_offset <= 0.1:  # Much smaller range for parallel mounting
            self.current_offset = new_offset
            print(f"📏 Offset adjusted to: {self.current_offset:.3f}")
        else:
            print(f"⚠️ Offset {new_offset:.3f} out of range (0.0-0.1)")
            
    def _save_calibration(self):
        """Save the enhanced calibration with distance information."""
        print(f"💾 Saving calibration with offset: {self.current_offset:.3f}")
        
        # Calculate theoretical offset for comparison
        theoretical_offset = self.calculate_parallax_offset(self.current_distance)
        
        # Save to file with enhanced data
        calibration_data = {
            'camera_laser_offset': self.current_offset,
            'camera_laser_gap_mm': self.camera_laser_gap * 1000,
            'camera_fov_vertical': self.camera_fov_vertical,
            'calibration_distance': self.current_distance,
            'theoretical_offset': theoretical_offset,
            'calibration_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_fires': self.calibration_targets
        }
        
        try:
            import json
            with open('parallax_calibration.json', 'w') as f:
                json.dump(calibration_data, f, indent=2)
            print("✅ Enhanced calibration saved to parallax_calibration.json")
            print(f"📊 Theoretical vs Actual: {theoretical_offset:.3f} vs {self.current_offset:.3f}")
        except Exception as e:
            print(f"❌ Error saving calibration: {e}")
            
    def _reset_calibration(self):
        """Reset calibration data."""
        self.test_fire_count = 0
        self.calibration_targets.clear()
        self.distance_index = 0
        self.current_distance = self.calibration_distances[0]
        self.current_offset = self.calculate_parallax_offset(self.current_distance)
        print("🔄 Calibration reset")
        
    def load_calibration(self):
        """Load saved calibration."""
        try:
            import json
            with open('parallax_calibration.json', 'r') as f:
                data = json.load(f)
                self.current_offset = data.get('camera_laser_offset', 0.15)
                self.camera_laser_gap = data.get('camera_laser_gap_mm', 25) / 1000  # Convert mm to m
                print(f"📂 Loaded calibration: offset={self.current_offset:.3f}, gap={self.camera_laser_gap*1000:.1f}mm")
                return self.current_offset
        except FileNotFoundError:
            print("📂 No saved calibration found, using default")
            return 0.15
        except Exception as e:
            print(f"❌ Error loading calibration: {e}")
            return 0.15

def main():
    """Main function to run enhanced parallax calibration."""
    print("🎯 Starting Enhanced Parallax Calibration Utility")
    
    # Get COM port from user
    com_port = input("Enter COM port (default: COM14): ").strip()
    if not com_port:
        com_port = "COM14"
    
    # Get actual gap measurement from user
    gap_input = input("Enter camera-laser gap in mm (default: 25): ").strip()
    if gap_input:
        try:
            gap_mm = float(gap_input)
            gap_m = gap_mm / 1000
        except ValueError:
            print("Invalid gap value, using default 25mm")
            gap_m = 0.025
    else:
        gap_m = 0.025  # Default 25mm
    
    # Create calibration utility
    cal = ParallaxCalibration(com_port=com_port)
    cal.camera_laser_gap = gap_m
    
    # Load existing calibration if available
    cal.load_calibration()
    
    # Start calibration
    cal.start_calibration()
    
    print("🎯 Enhanced calibration complete!")

if __name__ == "__main__":
    main() 