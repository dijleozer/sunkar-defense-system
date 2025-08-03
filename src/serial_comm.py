import serial
import time
import threading

class SerialComm:
    def __init__(self, port="/dev/serial0", baudrate=9600, timeout=1, protocol="binary", simulation_mode=False):
        self.protocol = protocol  # "binary" or "text"
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connection_retries = 3
        self.retry_delay = 2
        self.simulation_mode = simulation_mode
        
        # Thread safety
        self._lock = threading.Lock()
        
        if not self.simulation_mode:
            self._connect_with_retry()
        else:
            print("[SerialComm] 🎮 Simülasyon modu aktif - Gerçek donanım kullanılmayacak")
            self.ser = None

    def _connect_with_retry(self):
        """Connect to serial port with retry logic"""
        for attempt in range(self.connection_retries):
            try:
                print(f"[SerialComm] 🔌 Port {self.port} açılmaya çalışılıyor (deneme {attempt + 1}/{self.connection_retries})...")
                
                # Check if port exists first
                import serial.tools.list_ports
                available_ports = [p.device for p in serial.tools.list_ports.comports()]
                
                if self.port not in available_ports:
                    print(f"[SerialComm] ❌ Port {self.port} mevcut değil!")
                    print(f"[SerialComm] 📋 Mevcut portlar: {available_ports}")
                    if attempt == self.connection_retries - 1:
                        print("[SerialComm] ⚠️ Port bulunamadı, simülasyon modunda çalışacak")
                        self.ser = None
                        return
                    time.sleep(self.retry_delay)
                    continue
                
                # Try to open the port
                self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
                time.sleep(2)  # Wait for connection to stabilize
                
                if self.ser.is_open:
                    print(f"[SerialComm] ✅ Port {self.port} başarıyla açıldı")
                    print(f"[SerialComm] 📡 Baudrate: {self.baudrate}, Protocol: {self.protocol}")
                    return
                else:
                    print(f"[SerialComm] ❌ Port {self.port} açılamadı")
                    
            except serial.SerialException as e:
                print(f"[SerialComm] ❌ Seri port hatası (deneme {attempt + 1}): {e}")
                if "Access is denied" in str(e) or "PermissionError" in str(e):
                    print("[SerialComm] 💡 İzin hatası - Programı yönetici olarak çalıştırın")
                elif "Port is in use" in str(e):
                    print("[SerialComm] 💡 Port kullanımda - Diğer programları kapatın")
                
            except PermissionError as e:
                print(f"[SerialComm] ❌ İzin hatası (deneme {attempt + 1}): {e}")
                print("[SerialComm] 💡 Çözüm: Programı yönetici olarak çalıştırın")
                
            except Exception as e:
                print(f"[SerialComm] ❌ Beklenmeyen hata (deneme {attempt + 1}): {e}")
            
            if attempt < self.connection_retries - 1:
                print(f"[SerialComm] ⏳ {self.retry_delay} saniye sonra tekrar deneniyor...")
                time.sleep(self.retry_delay)
        
        # If all retries failed
        print(f"[SerialComm] ⚠️ Port {self.port} açılamadı, simülasyon modunda çalışacak")
        self.ser = None

    def send_command(self, cmd, data):
        """Send command using current protocol with error handling"""
        with self._lock:
            if self.simulation_mode:
                self._simulate_command(cmd, data)
            elif self.protocol == "binary":
                self._send_binary_command(cmd, data)
            else:
                self._send_text_command(cmd, data)

    def _simulate_command(self, cmd, data):
        """Simulate command sending for testing without hardware"""
        if cmd == 0x01:  # Servo
            command = f"S{data}"
            print(f"[SerialComm] 🎮 Simülasyon - Servo: {command}")
        elif cmd == 0x02:  # Stepper
            command = f"M{data}"
            print(f"[SerialComm] 🎮 Simülasyon - Stepper: {command}")
        elif cmd == 0x03:  # Laser
            command = "Laser AÇ" if data > 0 else "Laser KAPAT"
            print(f"[SerialComm] 🎮 Simülasyon - {command}")
        else:
            print(f"[SerialComm] 🎮 Simülasyon - Unknown command: {cmd}, data: {data}")

    def _send_binary_command(self, cmd, data):
        """Send binary protocol command (0xAA + CMD + DATA + 0x55)"""
        data = max(0, min(255, data))
        if self.ser and self.ser.is_open:
            try:
                packet = bytearray([0xAA, cmd, data, 0x55])
                self.ser.write(packet)
                print(f"[SerialComm] Binary gönderildi: CMD={cmd}, DATA={data}")
            except (serial.SerialException, PermissionError) as e:
                print(f"[SerialComm] ❌ Binary gönderim hatası: {e}")
        else:
            print("[SerialComm] ⚠️ Port açık değil, simülasyon modunda")

    def _send_text_command(self, cmd, data):
        """Send text protocol command (S30, M135, a, p)"""
        if self.ser and self.ser.is_open:
            try:
                if cmd == 0x01:  # Servo
                    command = f"S{data}\n"
                elif cmd == 0x02:  # Stepper
                    command = f"M{data}\n"
                elif cmd == 0x03:  # Laser
                    command = "a\n" if data > 0 else "p\n"
                else:
                    print(f"[SerialComm] Unknown command: {cmd}")
                    return
                    
                self.ser.write(command.encode())
                print(f"[SerialComm] Text gönderildi: {command.strip()}")
            except (serial.SerialException, PermissionError) as e:
                print(f"[SerialComm] ❌ Text gönderim hatası: {e}")
        else:
            print("[SerialComm] ⚠️ Port açık değil, simülasyon modunda")

    def read_response(self):
        if self.simulation_mode:
            return "[SIMULATION] Mock response"
        
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting:
                    response = self.ser.readline().decode(errors='ignore').strip()
                    print(f"[SerialComm] Gelen cevap: {response}")
                    return response
            except (serial.SerialException, PermissionError) as e:
                print(f"[SerialComm] ❌ Okuma hatası: {e}")
        return None

    def close(self):
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
                print("[SerialComm] ✅ Port kapatıldı.")
            except Exception as e:
                print(f"[SerialComm] ❌ Port kapatma hatası: {e}")
        elif self.simulation_mode:
            print("[SerialComm] 🎮 Simülasyon modu kapatıldı")

    def set_protocol(self, protocol):
        """Change protocol between binary and text"""
        self.protocol = protocol
        print(f"[SerialComm] Protocol changed to: {protocol}")
    
    def is_connected(self):
        """Check if serial connection is active"""
        if self.simulation_mode:
            return True
        return self.ser is not None and self.ser.is_open
    
    def reconnect(self):
        """Attempt to reconnect to the serial port"""
        if self.simulation_mode:
            print("[SerialComm] 🎮 Simülasyon modu - yeniden bağlanma gerekmez")
            return
            
        print("[SerialComm] 🔄 Yeniden bağlanmaya çalışılıyor...")
        if self.ser:
            try:
                self.ser.close()
            except:
                pass
        self._connect_with_retry()