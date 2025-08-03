#!/usr/bin/env python3
"""
Stepper Motor Smoothness Test Script
Tests the anti-jitter improvements for stepper motor control
"""

import time
import serial
from joystick_controller import JoystickController

def test_stepper_smoothness():
    """Test stepper motor smoothness with anti-jitter improvements"""
    
    print("=== Stepper Motor Smoothness Test ===")
    print("Bu test, stepper motorun titreşim sorunlarını çözmek için yapılan iyileştirmeleri test eder.")
    print()
    
    # Initialize serial communication
    try:
        serial_comm = SerialComm(port="COM4", protocol="binary")
        if not serial_comm.is_connected():
            print("❌ Arduino bağlantısı kurulamadı!")
            return False
    except Exception as e:
        print(f"❌ Seri port hatası: {e}")
        return False
    
    # Initialize joystick controller
    joystick = JoystickController(serial_comm=serial_comm)
    if not joystick.joystick:
        print("❌ Joystick bulunamadı!")
        return False
    
    print("✅ Sistem başlatıldı")
    print("🎮 Joystick sağ analog stick ile stepper motoru test edin")
    print("📊 Test sırasında konsol çıktılarını izleyin")
    print("⏹️ Testi durdurmak için Ctrl+C basın")
    print()
    
    # Test parameters
    test_duration = 30  # seconds
    start_time = time.time()
    command_count = 0
    last_command_time = 0
    
    try:
        while time.time() - start_time < test_duration:
            # Get current joystick position
            angle = joystick.get_stepper_angle()
            current_time = time.time()
            
            # Check if command would be sent (simulate the filtering logic)
            angle_diff = abs(angle - joystick.last_sent_stepper)
            time_since_last = current_time - joystick.last_stepper_time
            
            should_send = (angle_diff > 3.0 or time_since_last > 0.2) and time_since_last > 0.15
            
            if should_send and angle != joystick.last_sent_stepper:
                command_count += 1
                last_command_time = current_time
                print(f"📤 Komut #{command_count}: Açı={int(angle)}°, Fark={angle_diff:.1f}°, Zaman={time_since_last:.3f}s")
            
            # Manual control loop
            joystick.manual_mode_control()
            time.sleep(0.01)  # 10ms loop
            
    except KeyboardInterrupt:
        print("\n⏹️ Test kullanıcı tarafından durduruldu")
    
    # Test results
    elapsed_time = time.time() - start_time
    commands_per_second = command_count / elapsed_time if elapsed_time > 0 else 0
    
    print("\n=== Test Sonuçları ===")
    print(f"⏱️ Test süresi: {elapsed_time:.1f} saniye")
    print(f"📤 Toplam komut sayısı: {command_count}")
    print(f"📊 Saniyede ortalama komut: {commands_per_second:.2f}")
    print(f"⏰ Son komut zamanı: {last_command_time - start_time:.1f}s")
    
    if commands_per_second < 5:
        print("✅ Komut frekansı düşük - Titreşim azalması beklenir")
    else:
        print("⚠️ Komut frekansı yüksek - Daha fazla iyileştirme gerekebilir")
    
    # Cleanup
    joystick.close()
    serial_comm.close()
    
    return True

def test_manual_control():
    """Test manual control with anti-jitter improvements"""
    
    print("=== Manuel Kontrol Testi ===")
    print("Joystick ile manuel kontrolü test edin")
    print("Sağ analog stick: Stepper motor")
    print("Sol analog stick: Servo motor")
    print("B butonu: Lazer aç")
    print("Y butonu: Lazer kapat")
    print("LB butonu: Servo toggle")
    print("RB butonu: Stepper toggle")
    print("⏹️ Çıkmak için Ctrl+C")
    print()
    
    try:
        serial_comm = SerialComm(port="COM4", protocol="binary")
        joystick = JoystickController(serial_comm=serial_comm)
        
        if not joystick.joystick:
            print("❌ Joystick bulunamadı!")
            return False
        
        print("✅ Manuel kontrol başlatıldı")
        
        while True:
            joystick.manual_mode_control()
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n⏹️ Manuel kontrol durduruldu")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        if 'joystick' in locals():
            joystick.close()
        if 'serial_comm' in locals():
            serial_comm.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        test_manual_control()
    else:
        test_stepper_smoothness() 