# MG995 Servo Wiring Diagram

## Overview

This document provides detailed wiring diagrams and connection information for integrating the MG995 servo motor into the Sunkar Defense System.

## MG995 Pin Configuration

### Servo Connector
```
┌─────────┐
│ 1  2  3 │
│ ─  ─  ─ │
└─────────┘
```

### Pin Functions
- **Pin 1**: Signal (PWM) - Yellow/White wire
- **Pin 2**: Power (VCC) - Red wire  
- **Pin 3**: Ground (GND) - Brown/Black wire

## Arduino Connection

### Basic Connection
```
Arduino Uno    MG995 Servo
───────────    ───────────
Pin 9 ──────── Signal (Pin 1)
5V ─────────── Power (Pin 2)
GND ────────── Ground (Pin 3)
```

### Detailed Wiring
```
Arduino Uno R3
┌─────────────────┐
│                 │
│  ┌─────────────┐│
│  │   Digital   ││
│  │   Pin 9     ││ ──── Signal (Yellow)
│  └─────────────┘│
│                 │
│  ┌─────────────┐│
│  │     5V      ││ ──── Power (Red)
│  └─────────────┘│
│                 │
│  ┌─────────────┐│
│  │    GND      ││ ──── Ground (Brown)
│  └─────────────┘│
│                 │
└─────────────────┘
```

## Power Supply Connection

### External Power Supply
```
Power Supply     MG995 Servo
─────────────    ───────────
+5V ──────────── Power (Pin 2)
GND ──────────── Ground (Pin 3)
```

### Shared Ground Configuration
```
Arduino Uno    Power Supply    MG995 Servo
───────────    ────────────    ───────────
Pin 9 ──────── ──────────── ── Signal (Pin 1)
GND ────────── GND ─────────── Ground (Pin 3)
5V ─────────── +5V ─────────── Power (Pin 2)
```

## Multiple Servo Configuration

### Two Servo Setup
```
Arduino Uno    MG995 Servo 1    MG995 Servo 2
───────────    ─────────────    ─────────────
Pin 9 ──────── Signal (Pin 1)   ────────────
Pin 10 ─────── ─────────────    Signal (Pin 1)
5V ─────────── Power (Pin 2)    Power (Pin 2)
GND ────────── Ground (Pin 3)   Ground (Pin 3)
```

### Power Distribution
```
Power Supply    ┌─ MG995 Servo 1
+5V ───────────┤
                └─ MG995 Servo 2
GND ────────────┬─ Arduino GND
                ├─ Servo 1 GND
                └─ Servo 2 GND
```

## Sunkar System Integration

### Complete System Wiring
```
Arduino Uno    Power Supply    MG995 Servo    Stepper Motor
───────────    ────────────    ───────────    ─────────────
Pin 9 ──────── ──────────── ── Signal ─────── ────────────
Pin 8 ──────── ──────────── ── ───────────── ── Step
Pin 7 ──────── ──────────── ── ───────────── ── Dir
5V ─────────── +5V ─────────── Power ─────── ── ────────────
GND ────────── GND ─────────── Ground ─────── ── GND
```

### Power Requirements
- **MG995 Servo**: 5V, 500mA-1.5A
- **Stepper Motor**: 12V, 1A-2A
- **Arduino**: 5V, 200mA
- **Total System**: 12V, 3A-4A

## Safety Considerations

### Fuse Protection
```
Power Supply    Fuse (2A)    MG995 Servo
+5V ──────────── ● ─────────── Power
```

### Diode Protection
```
Arduino Pin 9    Diode (1N4007)    MG995 Signal
───────────── ──── ● ───────────── ────────────
```

### Capacitor Filtering
```
Power Supply    Capacitor (100μF)    MG995 Servo
+5V ──────────── || ───────────────── Power
GND ──────────── || ───────────────── Ground
```

## Cable Management

### Cable Routing
```
┌─────────────────────────────────────┐
│ Arduino Mounting Plate              │
│ ┌─────────┐    ┌─────────┐        │
│ │Arduino  │    │MG995    │        │
│ │Uno      │    │Servo    │        │
│ └─────────┘    └─────────┘        │
│     │              │              │
│     └──────────────┘              │
│         Cable Bundle               │
└─────────────────────────────────────┘
```

### Cable Specifications
- **Signal Wire**: 22 AWG, shielded
- **Power Wire**: 18 AWG, stranded
- **Ground Wire**: 18 AWG, stranded
- **Cable Length**: 30cm maximum

## Testing Connections

### Continuity Test
```python
def test_connections():
    """Test servo connections"""
    # Test signal connection
    signal_ok = test_signal_connection()
    print(f"Signal connection: {'OK' if signal_ok else 'FAIL'}")
    
    # Test power connection
    power_ok = test_power_connection()
    print(f"Power connection: {'OK' if power_ok else 'FAIL'}")
    
    # Test ground connection
    ground_ok = test_ground_connection()
    print(f"Ground connection: {'OK' if ground_ok else 'FAIL'}")
```

### Voltage Test
```python
def test_voltages():
    """Test voltage levels"""
    # Test power supply voltage
    vcc = measure_voltage('VCC')
    print(f"VCC voltage: {vcc}V")
    
    # Test signal voltage
    signal = measure_voltage('SIGNAL')
    print(f"Signal voltage: {signal}V")
    
    # Test ground voltage
    gnd = measure_voltage('GND')
    print(f"Ground voltage: {gnd}V")
```

## Troubleshooting

### Common Wiring Issues

#### No Movement
- **Check Power**: Verify 5V power connection
- **Check Ground**: Verify ground connection
- **Check Signal**: Verify PWM signal connection
- **Check Polarity**: Verify wire polarity

#### Erratic Movement
- **Loose Connections**: Check for loose wires
- **Power Supply**: Check power supply stability
- **Signal Noise**: Shield signal wires
- **Ground Loop**: Check for ground loops

#### Overheating
- **Overload**: Check for mechanical overload
- **Power Supply**: Check power supply capacity
- **Duty Cycle**: Reduce continuous operation
- **Cooling**: Improve ventilation

### Diagnostic Commands
```python
def diagnose_wiring():
    """Diagnose wiring issues"""
    # Test continuity
    continuity = test_continuity()
    print(f"Continuity: {continuity}")
    
    # Test resistance
    resistance = test_resistance()
    print(f"Resistance: {resistance}Ω")
    
    # Test insulation
    insulation = test_insulation()
    print(f"Insulation: {insulation}")
```

## Maintenance

### Regular Checks
1. **Visual Inspection**: Check for loose connections
2. **Continuity Test**: Test wire continuity
3. **Voltage Test**: Test voltage levels
4. **Performance Test**: Test servo performance

### Preventive Maintenance
1. **Cable Inspection**: Check for cable wear
2. **Connection Cleaning**: Clean connections
3. **Tightening**: Tighten loose connections
4. **Replacement**: Replace damaged cables

## Documentation

### Wiring Diagram Legend
- **Solid Line**: Power connection
- **Dashed Line**: Signal connection
- **Dotted Line**: Ground connection
- **Arrow**: Direction of current flow

### Color Coding
- **Red**: Power (VCC)
- **Black/Brown**: Ground (GND)
- **Yellow/White**: Signal (PWM)
- **Blue**: Optional control signals

### Labeling
- **Arduino Pins**: Label with pin numbers
- **Servo Pins**: Label with pin functions
- **Power Supply**: Label with voltage/current
- **Cable Ends**: Label with connection points 