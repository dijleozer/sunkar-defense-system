# MG995 Servo Motor Wiring Diagram

## Power Supply Requirements

### **6V Power Supply Setup**
```
6V Power Supply (2A recommended)
├── Arduino 5V (via voltage regulator)
├── MG995 Servo (6V direct)
└── Stepper Motor (if 6V compatible)
```

## Detailed Wiring Diagram

### **1. Power Distribution**

```
6V Power Supply
│
├── [Voltage Regulator] → Arduino 5V
│   (LM7805 or similar)
│
├── [1000µF Capacitor] → MG995 Power
│   (for current spikes)
│
└── [1000µF Capacitor] → Stepper Power
    (if needed)
```

### **2. MG995 Servo Connections**

```
MG995 Servo Motor
├── Red Wire   → 6V Power Supply (+)
├── Brown Wire → Common Ground (-)
└── Orange Wire → Arduino Pin 9 (Signal)
```

### **3. Voltage Monitoring Circuit**

```
Voltage Divider (for 6V monitoring)
6V → [10kΩ Resistor] → [10kΩ Resistor] → GND
                        ↓
                     Arduino A0
```

**Calculation:**
- Input: 6V
- Output: 3V (safe for Arduino 5V input)
- Ratio: 2:1 (voltageDividerRatio = 2.0)

### **4. Complete Wiring Layout**

```
┌─────────────────────────────────────────┐
│              6V Power Supply            │
│              (2A, 6V)                   │
└─────────────────┬───────────────────────┘
                  │
                  ├── [LM7805] ──→ Arduino 5V
                  │
                  ├── [1000µF] ──→ MG995 Red
                  │
                  ├── [10kΩ] ────→ [10kΩ] ──→ GND
                  │               ↓
                  │            Arduino A0
                  │
                  └── Common Ground ──→ All GND
```

## Component List

### **Required Components:**
1. **6V Power Supply** (2A minimum, 3A recommended)
2. **LM7805 Voltage Regulator** (for Arduino 5V)
3. **1000µF Electrolytic Capacitors** (2x for power filtering)
4. **10kΩ Resistors** (2x for voltage divider)
5. **Breadboard/PCB** for connections
6. **Heat Sink** for LM7805 (if needed)

### **Optional Components:**
1. **ACS712 Current Sensor** (for current monitoring)
2. **Thermal Sensor** (for temperature monitoring)
3. **Position Potentiometer** (for feedback)

## Safety Considerations

### **1. Power Isolation**
- **Separate power rails** for servo and logic
- **Common ground** connection required
- **Voltage monitoring** to prevent damage

### **2. Current Protection**
- **Fuse protection** (1A fast-blow recommended)
- **Current monitoring** (optional but recommended)
- **Overcurrent shutdown** in software

### **3. Thermal Protection**
- **Servo cooling** periods (implemented in code)
- **Heat sink** for voltage regulator
- **Ventilation** for MG995

## Testing Procedure

### **1. Power Supply Test**
```bash
# Measure voltages at test points:
1. Power Supply Output: 6.0V ±0.2V
2. Arduino 5V: 5.0V ±0.1V
3. MG995 Power: 6.0V ±0.2V
4. Voltage Divider Output: 3.0V ±0.1V
```

### **2. Servo Movement Test**
```arduino
// Test servo movement through full range
movePitch(0);   // Should move to 0°
delay(1000);
movePitch(30);  // Should move to 30°
delay(1000);
movePitch(60);  // Should move to 60°
delay(1000);
movePitch(0);   // Return to start
```

### **3. Voltage Monitoring Test**
```arduino
// Check voltage readings
Serial.print("Voltage: ");
Serial.println(getVoltage()); // Should read ~6.0V
```

## Troubleshooting Guide

### **Common Issues:**

#### **1. Servo Not Moving**
- **Check power supply** (should be 6V)
- **Verify signal wire** (Pin 9)
- **Check ground connection** (common ground required)

#### **2. Jerky Movement**
- **Add capacitors** for power filtering
- **Check voltage stability** during movement
- **Verify pulse width** settings (500-2500µs)

#### **3. Low Voltage Warning**
- **Check power supply** capacity
- **Verify voltage divider** resistors
- **Test voltage at servo** terminals

#### **4. Overheating**
- **Reduce continuous operation** time
- **Add cooling periods** (implemented in code)
- **Check load** on servo

## Performance Specifications

### **MG995 Expected Performance:**
- **Speed**: 0.17sec/60° at 6V
- **Torque**: 10kg-cm at 6V
- **Current**: 500-900mA under load
- **Temperature**: Monitor for overheating

### **System Performance:**
- **Response Time**: <100ms for position changes
- **Accuracy**: ±1° positioning
- **Reliability**: Continuous operation with thermal protection

## Maintenance

### **Regular Checks:**
1. **Voltage monitoring** (daily)
2. **Servo temperature** (during operation)
3. **Connections** (weekly)
4. **Power supply** stability (monthly)

### **Preventive Maintenance:**
1. **Clean connections** regularly
2. **Check for loose wires**
3. **Monitor servo wear**
4. **Update firmware** as needed 