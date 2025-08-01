# MG995 Servo Motor Integration Analysis

## MG995 Datasheet Specifications

### Electrical Specifications:
- **Operating Voltage**: 4.8V - 7.2V (6V recommended)
- **Current Draw**: 500-900mA under load, 10mA idle
- **Pulse Width**: 500-2500µs (1-2ms standard)
- **Pulse Frequency**: 50Hz (20ms period)
- **Rotation Range**: 180° (±90° from center)

### Mechanical Specifications:
- **Torque**: 10kg-cm at 6V, 8.5kg-cm at 4.8V
- **Speed**: 0.17sec/60° at 6V, 0.20sec/60° at 4.8V
- **Weight**: 55g
- **Dimensions**: 40.7 x 20.2 x 38.1mm

## Required System Changes

### 1. POWER SUPPLY REQUIREMENTS

#### Current Issues:
- **Voltage Range**: MG995 requires 4.8V-7.2V (6V optimal)
- **Current Capacity**: Needs 500-900mA under load
- **Power Stability**: Requires stable voltage supply

#### Required Changes:

##### **A. Power Supply Upgrade**
```arduino
// Add power monitoring in Arduino code
const int voltagePin = A0;  // Voltage divider for power monitoring
const float minVoltage = 4.8;  // MG995 minimum voltage
const float optimalVoltage = 6.0;  // MG995 optimal voltage
const float maxVoltage = 7.2;  // MG995 maximum voltage

void checkPowerSupply() {
  float voltage = analogRead(voltagePin) * (5.0 / 1023.0) * 2; // Voltage divider
  if (voltage < minVoltage) {
    Serial.println("WARNING: Low voltage detected!");
    stopAll();
  }
}
```

##### **B. Power Supply Recommendations**
- **Use 6V power supply** (not 5V Arduino power)
- **Separate power rails** for servo and logic
- **Add capacitors** (1000µF) for current spikes
- **Current rating**: Minimum 1A, recommended 2A

### 2. WIRING CHANGES

#### Current Wiring Issues:
- **Signal wire**: Pin 9 (unchanged)
- **Power wire**: Needs separate 6V supply
- **Ground wire**: Common ground required

#### Required Wiring Changes:

##### **A. Power Distribution**
```
6V Power Supply
├── Arduino (5V regulator)
├── MG995 Servo (6V direct)
└── Stepper Motor (if 6V compatible)
```

##### **B. Add Power Monitoring Circuit**
```
Voltage Divider:
6V → [10kΩ] → [10kΩ] → GND
              ↓
           Arduino A0
```

### 3. CODE MODIFICATIONS

#### **A. Arduino Code Updates**

##### **1. Add Power Monitoring**
```arduino
// Add to motor_control.ino
const int voltagePin = A0;
const float voltageDividerRatio = 2.0;

void checkVoltage() {
  int rawValue = analogRead(voltagePin);
  float voltage = (rawValue * 5.0 / 1023.0) * voltageDividerRatio;
  
  if (voltage < 4.8) {
    Serial.println("ERR:LOW_VOLTAGE");
    stopAll();
  }
}
```

##### **2. Update Servo Parameters**
```arduino
// Current settings are correct for MG995
const int servoMinPulse = 500;   // ✓ Correct for MG995
const int servoMaxPulse = 2500;  // ✓ Correct for MG995
```

##### **3. Add Servo Speed Control**
```arduino
// Add gradual movement for MG995
void movePitchGradual(int targetPitch) {
  int current = currentPitch;
  int step = (targetPitch > current) ? 1 : -1;
  
  while (current != targetPitch) {
    current += step;
    movePitch(current);
    delay(20); // 50Hz update rate
  }
}
```

#### **B. Python Code Updates**

##### **1. Add Power Monitoring in GUI**
```python
# Add to gui.py
def check_servo_voltage(self):
    # Read voltage from Arduino
    voltage = self.serial.read_voltage()
    if voltage < 4.8:
        self.status_box.configure(text="⚠️ Low Voltage!")
        return False
    return True
```

##### **2. Update Serial Communication**
```python
# Add voltage monitoring to serial_comm.py
def read_voltage(self):
    if self.ser and self.ser.is_open:
        self.ser.write(b"VOLTAGE\n")
        response = self.ser.readline().decode().strip()
        return float(response.split(':')[1])
    return 0.0
```

### 4. MECHANICAL CONSIDERATIONS

#### **A. Mounting Changes**
- **MG995 Dimensions**: 40.7 x 20.2 x 38.1mm
- **Check mounting compatibility** with existing bracket
- **Ensure proper ventilation** (MG995 can get warm)

#### **B. Torque Requirements**
- **MG995 Torque**: 10kg-cm at 6V
- **Verify load capacity** for your application
- **Consider gear reduction** if needed

### 5. SAFETY IMPROVEMENTS

#### **A. Add Thermal Protection**
```arduino
// Add to motor_control.ino
unsigned long lastMoveTime = 0;
const unsigned long maxContinuousTime = 30000; // 30 seconds

void checkThermalProtection() {
  if (millis() - lastMoveTime > maxContinuousTime) {
    // Allow servo to cool
    pitchServo.detach();
    delay(5000); // 5 second cooldown
    pitchServo.attach(servoPin, servoMinPulse, servoMaxPulse);
  }
}
```

#### **B. Add Current Monitoring**
```arduino
// Add current sensor if available
const int currentPin = A1;
const float currentThreshold = 1.0; // 1A max

void checkCurrent() {
  float current = analogRead(currentPin) * (5.0 / 1023.0) / 0.185; // ACS712
  if (current > currentThreshold) {
    Serial.println("ERR:OVER_CURRENT");
    stopAll();
  }
}
```

### 6. PERFORMANCE OPTIMIZATIONS

#### **A. Update Movement Speed**
```arduino
// MG995 speed: 0.17sec/60° at 6V
const int servoDelay = 17; // ms per degree

void movePitch(int targetPitch) {
  int pulse = map(targetPitch, pitchMin, pitchMax, servoMinPulse, servoMaxPulse);
  pitchServo.writeMicroseconds(pulse);
  currentPitch = targetPitch;
  
  // Add delay for smooth movement
  int angleDiff = abs(targetPitch - currentPitch);
  delay(angleDiff * servoDelay);
}
```

#### **B. Add Position Feedback**
```arduino
// Optional: Add potentiometer for position feedback
const int feedbackPin = A2;

int getActualPosition() {
  int rawValue = analogRead(feedbackPin);
  return map(rawValue, 0, 1023, pitchMin, pitchMax);
}
```

## IMPLEMENTATION PRIORITY

### **High Priority (Required)**
1. **Power Supply Upgrade** to 6V
2. **Separate Power Rails** for servo
3. **Add Voltage Monitoring**
4. **Update Wiring** for 6V supply

### **Medium Priority (Recommended)**
1. **Add Thermal Protection**
2. **Implement Gradual Movement**
3. **Add Current Monitoring**
4. **Update GUI** for voltage display

### **Low Priority (Optional)**
1. **Add Position Feedback**
2. **Implement Speed Control**
3. **Add Advanced Diagnostics**

## TESTING CHECKLIST

### **Electrical Testing**
- [ ] Measure voltage at servo terminals (should be 6V)
- [ ] Check current draw under load (should be <1A)
- [ ] Verify voltage stability during movement
- [ ] Test emergency stop functionality

### **Mechanical Testing**
- [ ] Verify smooth movement 0-60°
- [ ] Check for binding or jerky motion
- [ ] Test torque under load
- [ ] Verify mounting stability

### **Software Testing**
- [ ] Test power monitoring alerts
- [ ] Verify gradual movement function
- [ ] Check thermal protection
- [ ] Test integration with full system

## COST ESTIMATE

### **Required Components**
- **6V Power Supply**: $15-25
- **Voltage Divider Resistors**: $2-5
- **Power Capacitors**: $3-8
- **Wiring/Connectors**: $5-10

### **Optional Components**
- **Current Sensor (ACS712)**: $8-15
- **Position Potentiometer**: $3-8
- **Thermal Sensor**: $2-5

**Total Estimated Cost**: $25-50 (required) + $13-28 (optional) 