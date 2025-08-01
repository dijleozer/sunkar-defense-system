import serial
import time

class SerialComm:
    def __init__(self, port="/dev/serial0", baudrate=9600, timeout=1, protocol="binary"):
        self.protocol = protocol  # "binary" or "text"
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)
            print(f"[SerialComm] Port {port} açıldı, baudrate: {baudrate}, protocol: {protocol}")
        except serial.SerialException as e:
            print(f"[SerialComm] Seri port açılamadı: {e}")
            self.ser = None

    def send_command(self, cmd, data):
        """Send command using current protocol"""
        if self.protocol == "binary":
            self._send_binary_command(cmd, data)
        else:
            self._send_text_command(cmd, data)

    def _send_binary_command(self, cmd, data):
        """Send binary protocol command (0xAA + CMD + DATA + 0x55)"""
        data = max(0, min(255, data))
        if self.ser and self.ser.is_open:
            packet = bytearray([0xAA, cmd, data, 0x55])
            self.ser.write(packet)
            print(f"[SerialComm] Binary gönderildi: CMD={cmd}, DATA={data}")
        else:
            print("[SerialComm] Port açık değil, gönderim yapılamadı.")

    def _send_text_command(self, cmd, data):
        """Send text protocol command (S30, M135, a, p)"""
        if self.ser and self.ser.is_open:
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
        else:
            print("[SerialComm] Port açık değil, gönderim yapılamadı.")

    def read_response(self):
        if self.ser and self.ser.in_waiting:
            response = self.ser.readline().decode(errors='ignore').strip()
            print(f"[SerialComm] Gelen cevap: {response}")
            return response
        return None

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SerialComm] Port kapatıldı.")

    def set_protocol(self, protocol):
        """Change protocol between binary and text"""
        self.protocol = protocol
        print(f"[SerialComm] Protocol changed to: {protocol}")