# Servo Motor Upgrade: FT5335M-FB → MG995

## Overview
The vertical movement (pitch axis) has been upgraded from FT5335M-FB to MG995 servo motor.

## Changes Made

### Arduino Code (`motor_control.ino`)

#### Updated Parameters:
- **Pin Assignment**: Updated comment from "FT5335M-FB signal" to "MG995 signal"
- **Pulse Width Range**: 
  - Old: `servoMinPulse = 900µs`, `servoMaxPulse = 2100µs`
  - New: `servoMinPulse = 500µs`, `servoMaxPulse = 2500µs`
- **Angle Range**: Maintained at 0-60° for pitch control

#### Technical Specifications:
- **MG995 Pulse Range**: 500-2500µs (standard for MG995)
- **FT5335M-FB Pulse Range**: 900-2100µs (previous model)
- **Movement Range**: 0-60° pitch (unchanged)

### Python Code Updates

#### `camera_manager.py`:
- **Angle Mapping**: Fixed to map joystick Y-axis (-1 to 1) to 0-60° range
- **Reset Position**: Updated to use 0° instead of 90° for MG995
- **Comments**: Updated to reflect MG995 specifications

#### `manuel_mode_control.py`:
- **Already Correct**: This file was already configured for 0-60° range
- **No Changes Required**: Mapping was already appropriate for MG995

## MG995 Servo Specifications

### Key Features:
- **Operating Voltage**: 4.8V-7.2V
- **Pulse Width**: 500-2500µs
- **Rotation Range**: 180° (limited to 0-60° for this application)
- **Torque**: 10kg-cm at 6V
- **Speed**: 0.17sec/60° at 6V

### Advantages over FT5335M-FB:
- **Higher Torque**: Better holding power
- **Wider Pulse Range**: More precise control
- **Better Performance**: Faster response time
- **Standard Compatibility**: More widely supported

## Testing Recommendations

1. **Calibration Test**: Verify servo moves to correct angles (0°, 30°, 60°)
2. **Smoothness Test**: Check for jerky movements or binding
3. **Torque Test**: Ensure servo can hold position under load
4. **Safety Test**: Verify emergency stop functionality
5. **Integration Test**: Test with full system (camera + tracking)

## Notes
- The MG995 has a wider pulse range (500-2500µs vs 900-2100µs)
- This provides more precise control and better compatibility
- The 0-60° range is maintained for safety and application requirements
- All Python code has been updated to reflect the new specifications

## Compatibility
- **Hardware**: Direct replacement - same pin connections
- **Software**: Updated for new pulse width parameters
- **Safety**: All safety features maintained (no-fire zone, emergency stop) 