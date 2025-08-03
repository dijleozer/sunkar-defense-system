#!/usr/bin/env python3
"""
Improved Stepper Motor Control Test Script
Tests acceleration-based movement and position holding
"""

import time
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from joystick_controller import JoystickController
from serial_comm import SerialComm

def test_acceleration_control():
    """Test acceleration-based control and position holding"""
    
    print("=== Improved Stepper Motor Control Test ===")
    print("Bu test, hızlanma tabanlı kontrol ve pozisyon tutma özelliklerini test eder.")
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
    test_duration = 60  # seconds
    start_time = time.time()
    command_count = 0
    movement_phases = 0
    
    try:
        while time.time() - start_time < test_duration:
            # Get current joystick position and status
            angle = joystick.get_stepper_angle()
            current_time = time.time()
            
            # Check movement status
            if joystick.stepper_movement_active:
                if movement_phases == 0 or not hasattr(joystick, '_last_movement_state') or not joystick._last_movement_state:
                    movement_phases += 1
                    print(f"🔄 Hareket fazı #{movement_phases}: Başladı")
                joystick._last_movement_state = True
            else:
                if hasattr(joystick, '_last_movement_state') and joystick._last_movement_state:
                    print("⏸️ Hareket durdu - Pozisyon tutuluyor")
                joystick._last_movement_state = False
            
            # Manual control loop
            joystick.manual_mode_control()
            time.sleep(0.01)  # 10ms loop
            
    except KeyboardInterrupt:
        print("\n⏹️ Test kullanıcı tarafından durduruldu")
    
    # Test results
    elapsed_time = time.time() - start_time
    
    print("\n=== Test Sonuçları ===")
    print(f"⏱️ Test süresi: {elapsed_time:.1f} saniye")
    print(f"🔄 Toplam hareket fazı: {movement_phases}")
    print(f"📊 Ortalama hareket fazı süresi: {elapsed_time/movement_phases:.1f}s" if movement_phases > 0 else "📊 Hareket fazı yok")
    
    # Cleanup
    joystick.close()
    serial_comm.close()
    
    return True

def test_position_holding():
    """Test position holding behavior"""
    
    print("=== Position Holding Test ===")
    print("Joystick'i bırakın ve stepper motorun pozisyonu tutup tutmadığını gözlemleyin")
    print("⏹️ Çıkmak için Ctrl+C")
    print()
    
    try:
        serial_comm = SerialComm(port="COM4", protocol="binary")
        joystick = JoystickController(serial_comm=serial_comm)
        
        if not joystick.joystick:
            print("❌ Joystick bulunamadı!")
            return False
        
        print("✅ Pozisyon tutma testi başlatıldı")
        print("🎮 Joystick'i hareket ettirin, sonra bırakın")
        print("📊 Motor pozisyonunu tutmalı")
        
        last_position = None
        holding_start_time = None
        
        while True:
            current_position = joystick.get_stepper_angle()
            
            # Check if position is stable (holding)
            if last_position is not None and abs(current_position - last_position) < 1:
                if holding_start_time is None:
                    holding_start_time = time.time()
                    print(f"🔒 Pozisyon tutma başladı: {current_position}°")
                else:
                    holding_duration = time.time() - holding_start_time
                    if holding_duration > 5:  # 5 seconds of stable holding
                        print(f"✅ Pozisyon başarıyla tutuluyor: {current_position}° ({holding_duration:.1f}s)")
            else:
                if holding_start_time is not None:
                    print("🔄 Pozisyon değişiyor - tutma durdu")
                holding_start_time = None
            
            last_position = current_position
            joystick.manual_mode_control()
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n⏹️ Pozisyon tutma testi durduruldu")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        if 'joystick' in locals():
            joystick.close()
        if 'serial_comm' in locals():
            serial_comm.close()

def test_acceleration_curve():
    """Test acceleration curve behavior"""
    
    print("=== Acceleration Curve Test ===")
    print("Joystick'i yavaşça hareket ettirin ve hızlanma eğrisini gözlemleyin")
    print("⏹️ Çıkmak için Ctrl+C")
    print()
    
    try:
        serial_comm = SerialComm(port="COM4", protocol="binary")
        joystick = JoystickController(serial_comm=serial_comm)
        
        if not joystick.joystick:
            print("❌ Joystick bulunamadı!")
            return False
        
        print("✅ Hızlanma eğrisi testi başlatıldı")
        print("🎮 Joystick'i yavaşça hareket ettirin")
        print("📊 Hızlanma eğrisini gözlemleyin")
        
        last_velocity = 0
        last_time = time.time()
        
        while True:
            current_velocity = joystick.current_stepper_velocity
            current_time = time.time()
            
            # Report significant velocity changes
            if abs(current_velocity - last_velocity) > 5:  # 5°/s change
                dt = current_time - last_time
                acceleration = (current_velocity - last_velocity) / dt if dt > 0 else 0
                print(f"📈 Hız: {current_velocity:.1f}°/s, İvme: {acceleration:.1f}°/s²")
                last_velocity = current_velocity
                last_time = current_time
            
            joystick.manual_mode_control()
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n⏹️ Hızlanma eğrisi testi durduruldu")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        if 'joystick' in locals():
            joystick.close()
        if 'serial_comm' in locals():
            serial_comm.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "acceleration":
            test_acceleration_control()
        elif test_type == "holding":
            test_position_holding()
        elif test_type == "curve":
            test_acceleration_curve()
        else:
            print("Kullanım:")
            print("  python test_improved_stepper_control.py [acceleration|holding|curve]")
    else:
        print("Test türü seçin:")
        print("  acceleration - Hızlanma tabanlı kontrol testi")
        print("  holding - Pozisyon tutma testi")
        print("  curve - Hızlanma eğrisi testi")
        print()
        test_acceleration_control() 