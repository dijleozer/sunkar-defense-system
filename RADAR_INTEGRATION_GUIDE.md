# Radar Integration Guide

## Overview

This guide explains how to integrate radar-like scanning functionality into the Sunkar Defense System. The radar system provides autonomous scanning patterns for target detection and tracking.

## Components

### RadarTrackingSystem
- **Purpose**: Low-level radar-like scanning and target tracking
- **Features**:
  - Multiple scanning patterns (radar sweep, spiral, sector scan, tracking)
  - Real-time target detection and prioritization
  - Motor control for servo and stepper motors
  - Continuous scanning when no targets are detected
  - Automatic target tracking when targets are found

### ScanMode Enum
- **RADAR_SWEEP**: Horizontal sweeping pattern
- **SPIRAL**: Spiral scanning pattern
- **SECTOR**: Sector-based scanning
- **TRACKING**: Direct target tracking

## Integration Steps

### 1. Initialize Radar System
```python
from radar_tracking_system import RadarTrackingSystem, ScanMode

# Initialize radar system
radar_system = RadarTrackingSystem(
    motor_control=motor_control,
    camera_manager=camera_manager,
    serial_comm=serial_comm
)
```

### 2. Configure Scanning Parameters
```python
# Set scan mode
radar_system.set_scan_mode(ScanMode.SPIRAL)

# Set scan speed
radar_system.set_scan_speed(2.0)  # degrees per second

# Set movement speed
radar_system.set_movement_speed(3.0)  # degrees per update
```

### 3. Start Scanning
```python
# Start radar system
radar_system.start()

# Update targets from camera
radar_system.update_targets()

# Get current scan position
position = radar_system.get_current_position()
```

### 4. Target Tracking
```python
# Get current target
target = radar_system.get_current_target()

if target:
    # Track target
    radar_system.track_target(target)
else:
    # Continue scanning
    radar_system.execute_scanning()
```

## Scanning Patterns

### Radar Sweep
- Horizontal back-and-forth movement
- Covers full horizontal range
- Configurable speed and direction

### Spiral Scan
- Spiral pattern from center outward
- Covers both horizontal and vertical axes
- Auto-reset when reaching boundaries

### Sector Scan
- Scans specific angular sectors
- Useful for focused area coverage
- Configurable sector boundaries

### Tracking Mode
- Direct target tracking
- Smooth motor movements
- Automatic target prioritization

## Motor Control Integration

### Servo Motor (Vertical)
- Range: 0-60 degrees
- Center position: 30 degrees
- Smooth movement with acceleration

### Stepper Motor (Horizontal)
- Range: 0-300 degrees
- Center position: 150 degrees
- Precise positioning control

## Target Detection

### Target Types
- **ENEMY**: Red balloons (priority targets)
- **FRIENDLY**: Blue balloons (avoid)
- **UNKNOWN**: Unclassified targets

### Target Prioritization
1. **Enemy targets** (highest priority)
2. **Closest to crosshair**
3. **Highest confidence**
4. **Largest size**

## Configuration

### Scan Parameters
```python
# Radar sweep parameters
sweep_speed = 2.0  # degrees per second
sweep_direction = 1  # 1 for clockwise, -1 for counter-clockwise

# Spiral parameters
spiral_radius_step = 0.5
spiral_angle_step = 0.1
max_spiral_radius = 20

# Movement parameters
movement_speed = 3.0
movement_interval = 0.03
movement_tolerance = 1.0
```

### Motor Limits
```python
# Servo motor limits
servo_min = 0
servo_max = 60

# Stepper motor limits
stepper_min = 0
stepper_max = 300
```

## Safety Features

### Emergency Stop
- Immediately stops all movement
- Resets to safe position
- Disables all scanning

### Position Limits
- Respects motor boundaries
- Prevents over-rotation
- Safe movement ranges

### Target Validation
- Validates target before tracking
- Checks target confidence
- Ensures target is within range

## Performance Optimization

### For Better Coverage
- Use spiral scan for comprehensive coverage
- Increase scan speed for faster detection
- Adjust sector boundaries for focused areas

### For Better Accuracy
- Reduce movement speed for precision
- Increase movement tolerance
- Use tracking mode for high-confidence targets

### For Better Responsiveness
- Decrease movement interval
- Optimize target update frequency
- Use predictive tracking

## Troubleshooting

### Common Issues

1. **Motors not moving**
   - Check serial communication
   - Verify motor connections
   - Check motor limits

2. **Scanning not working**
   - Verify scan mode is set
   - Check scan parameters
   - Ensure radar system is started

3. **Target tracking issues**
   - Check camera feed
   - Verify target detection
   - Check tracking parameters

4. **Performance issues**
   - Reduce scan speed
   - Increase movement interval
   - Check system resources

### Debug Information

The system provides detailed logging:
- `[RadarTracking]`: Radar system messages
- `[MotorControl]`: Motor control messages
- `[TargetDetection]`: Target detection messages

## Integration with GUI

### GUI Integration Methods
```python
# Activate radar system
radar_system.activate()

# Deactivate radar system
radar_system.deactivate()

# Process frame from GUI
target_info = radar_system.process_frame(frame, tracks)

# Get status for GUI display
status = radar_system.get_status()
```

### Status Reporting
- Current scan mode
- Scan progress percentage
- Target information
- Motor positions
- System status

## Future Enhancements

### Planned Features
- Machine learning-based target prediction
- Advanced scanning algorithms
- Multi-target tracking
- Adaptive scanning patterns
- Integration with external sensors

### Performance Improvements
- Optimized motor control algorithms
- Enhanced target detection accuracy
- Improved scanning efficiency
- Better resource utilization 