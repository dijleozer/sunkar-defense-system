#!/usr/bin/env python3
"""
COM port availability checker
"""
import serial.tools.list_ports
import serial
import time

def check_available_ports():
    """Check all available COM ports"""
    print("🔍 Mevcut COM portları kontrol ediliyor...")
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print("❌ Hiç COM port bulunamadı!")
        return []
    
    print(f"✅ {len(ports)} COM port bulundu:")
    
    available_ports = []
    for port in ports:
        print(f"  📡 {port.device}: {port.description}")
        print(f"     Hardware ID: {port.hwid}")
        print(f"     Manufacturer: {port.manufacturer}")
        print(f"     Product: {port.product}")
        print()
        available_ports.append(port.device)
    
    return available_ports

def test_port_connection(port_name):
    """Test if a specific port can be opened"""
    print(f"🧪 {port_name} portu test ediliyor...")
    
    try:
        # Try to open the port
        ser = serial.Serial(port_name, 9600, timeout=1)
        time.sleep(1)
        
        if ser.is_open:
            print(f"✅ {port_name} başarıyla açıldı")
            ser.close()
            return True
        else:
            print(f"❌ {port_name} açılamadı")
            return False
            
    except serial.SerialException as e:
        print(f"❌ {port_name} hatası: {e}")
        return False
    except PermissionError as e:
        print(f"❌ {port_name} izin hatası: {e}")
        print("   💡 Çözüm: Programı yönetici olarak çalıştırın")
        return False

def main():
    print("=" * 50)
    print("🔧 COM PORT DURUM KONTROLÜ")
    print("=" * 50)
    
    # Check available ports
    available_ports = check_available_ports()
    
    if not available_ports:
        print("❌ Hiç COM port bulunamadı!")
        print("💡 Arduino'nun bağlı olduğundan emin olun")
        return
    
    # Test COM14 specifically
    print("🎯 COM14 özel test:")
    if "COM14" in available_ports:
        test_port_connection("COM14")
    else:
        print("❌ COM14 bulunamadı!")
        print("💡 Arduino'nun COM14'e bağlı olduğundan emin olun")
    
    # Test other available ports
    print("\n🔍 Diğer portlar test ediliyor:")
    for port in available_ports[:3]:  # Test first 3 ports
        if port != "COM14":
            test_port_connection(port)
    
    print("\n" + "=" * 50)
    print("📋 ÖNERİLER:")
    print("1. Arduino'nun USB ile bağlı olduğundan emin olun")
    print("2. Arduino IDE'de port seçimini kontrol edin")
    print("3. Programı yönetici olarak çalıştırın")
    print("4. Başka programların portu kullanmadığından emin olun")
    print("5. Arduino sürücülerini yeniden yükleyin")
    print("=" * 50)

if __name__ == "__main__":
    main() 