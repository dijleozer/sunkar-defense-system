from camera_manager import CameraManager
from gui import SunkarGUI
from joystick_controller import JoystickController
from serial_comm import SerialComm
from laser_control import LaserControl
from motor_control import MotorControl

if __name__ == "__main__":
    # Configuration
    COM_PORT = "COM14"
    PROTOCOL = "text"
    
    # Initialize components
    cam = CameraManager()
    serial_comm = SerialComm(port=COM_PORT, baudrate=9600, protocol=PROTOCOL)
    laser_control = LaserControl(serial_comm)
    
    # Initialize motor control system
    motor_control = MotorControl(serial_comm=serial_comm, port=COM_PORT, protocol=PROTOCOL)
    
    # Initialize joystick
    joystick = JoystickController(serial_comm=serial_comm, mode="manual", protocol=PROTOCOL)
    
    # Connect camera manager to serial communication
    cam.serial = serial_comm
    
    # Initialize radar tracking system (✅ motor_control parametresi eklendi)
    from simple_autonomous import SimpleAutonomousMode
    autonomous_manager = SimpleAutonomousMode(serial_comm, laser_control, cam, motor_control)
    
    # Start motor control loop
    motor_control.start_control_loop()
    
    # Initialize GUI
    app = SunkarGUI(cam, joystick, laser_control, autonomous_manager)
    
    try:
        print("[Main] 🚀 Sunkar Defense System başlatıldı")
        print("[Main] 📡 Motor control sistemi aktif")
        print("[Main] 🎮 Joystick kontrolü hazır")
        app.mainloop()
    except KeyboardInterrupt:
        print("\n[Main] ⚠ Program kapatılıyor...")
    finally:
        # Cleanup
        motor_control.close()
        serial_comm.close()
        print("[Main] 🔌 Tüm bağlantılar kapatıldı")
