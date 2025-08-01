# Sunkar Defense System - Integration Changes

## Overview
This document summarizes the changes made to integrate the updated Arduino code and joystick controller into the main Sunkar Defense System project.

## Key Changes Made

### 1. Arduino Code (`arduino/motor_control.ino`)

**Major Changes:**
- **Simplified Command Protocol**: Replaced complex packet-based protocol with simple string commands
  - `S{angle}` for servo control (e.g., "S30")
  - `M{angle}` for stepper control (e.g., "M135") 
  - `a` for laser ON
  - `p` for laser OFF

**Improvements:**
- **Better Servo Control**: Smoother movement with improved timing (20ms delays)
- **Enhanced Stepper Control**: Improved angle calculation and movement with configurable step increments
- **Simplified Pin Configuration**: Cleaner pin definitions and setup
- **Removed Complex Features**: Removed voltage monitoring, thermal protection, and emergency stop for simplicity

**Pin Configuration:**
- Servo: Pin 9
- Stepper STEP: Pin 2
- Stepper DIR: Pin 3  
- Stepper ENABLE: Pin 4
- Laser: Pin 6

### 2. Serial Communication (`src/serial_comm.py`)

**Changes:**
- **New Protocol Support**: Added methods for the simplified string-based protocol
- **Direct Command Methods**: 
  - `send_servo_angle(angle)`
  - `send_stepper_angle(angle)`
  - `send_laser_command(enable)`
- **Backward Compatibility**: Maintained original `send_command()` method for existing code

**New Methods:**
```python
serial_comm.send_servo_angle(30)      # Send servo to 30 degrees
serial_comm.send_stepper_angle(135)   # Send stepper to 135 degrees  
serial_comm.send_laser_command(True)  # Turn laser ON
serial_comm.send_laser_command(False) # Turn laser OFF
```

### 3. Joystick Controller (`src/joystick_controller.py`)

**Major Updates:**
- **New Button Mappings**:
  - Button B (2): Laser ON
  - Button Y (3): Laser OFF
  - Button LB (4): Toggle servo control
  - Button RB (5): Toggle stepper control

- **Toggle Functionality**: LB/RB buttons can enable/disable servo and stepper control independently
- **Improved Angle Calculations**:
  - Servo: Left analog stick vertical (Axis 1) mapped to 0-60°
  - Stepper: Right analog stick horizontal (Axis 2) mapped to 0-270°
- **Rate Limiting**: 0.1 second intervals between commands to prevent spam
- **Better Deadzone Handling**: Improved joystick deadzone processing

**New Features:**
- **Independent Motor Control**: Can disable servo or stepper independently
- **Rate-Limited Updates**: Prevents excessive serial communication
- **Improved Feedback**: Better console output for debugging

### 4. Laser Control (`src/laser_control.py`)

**Changes:**
- **Simplified Control**: Removed PWM power control, now uses simple ON/OFF
- **New Protocol**: Uses `send_laser_command()` instead of power-based control
- **Cleaner Interface**: Simplified methods for laser control

**Updated Methods:**
```python
laser_control.turn_on()   # Turn laser ON
laser_control.turn_off()  # Turn laser OFF
laser_control.fire_laser(duration=0.5)  # Fire for specified duration
```

## Integration Summary

### What Works Now:
1. **Simplified Communication**: String-based commands are more reliable and easier to debug
2. **Better Motor Control**: Smoother servo and stepper movements
3. **Independent Controls**: Can disable individual motors for testing
4. **Improved Joystick Response**: Better deadzone handling and angle mapping
5. **Rate Limiting**: Prevents serial communication overload

### Testing:
- Use `test_integration.py` to verify the integration works correctly
- The test script will check serial communication, joystick control, and direct commands

### Compatibility:
- **Backward Compatible**: Existing code using `send_command()` still works
- **GUI Integration**: No changes needed to the main GUI or autonomous mode
- **Serial Protocol**: Simplified but maintains functionality

## Usage Instructions

### Manual Control:
1. **Servo Control**: Use left analog stick (vertical) to control servo (0-60°)
2. **Stepper Control**: Use right analog stick (horizontal) to control stepper (0-270°)
3. **Laser Control**: 
   - Press B button to turn laser ON
   - Press Y button to turn laser OFF
4. **Motor Toggle**:
   - Press LB to toggle servo control on/off
   - Press RB to toggle stepper control on/off

### Testing:
```bash
cd sunkar-defense-system
python test_integration.py
```

## Troubleshooting

### Common Issues:
1. **Serial Port Not Found**: Check if Arduino is connected to COM14
2. **Joystick Not Detected**: Ensure joystick is connected and drivers installed
3. **Motors Not Responding**: Check if motors are enabled (LB/RB toggles)
4. **Laser Not Working**: Verify laser pin connection and power supply

### Debug Commands:
- Check serial communication: Look for "[SerialComm]" messages
- Check joystick status: Look for "[JoystickController]" messages
- Monitor Arduino output: Check Serial Monitor in Arduino IDE

## Next Steps

1. **Upload Arduino Code**: Upload the updated `motor_control.ino` to your Arduino
2. **Test Integration**: Run `test_integration.py` to verify everything works
3. **Test Main Application**: Run `python src/main.py` to test the full system
4. **Calibrate if Needed**: Use joystick calibration if needed

The integration maintains all existing functionality while providing improved reliability and easier debugging capabilities. 