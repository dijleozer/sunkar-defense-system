# Autonomous Mode Guide

## Overview

The autonomous mode provides fully automated target detection, tracking, and engagement capabilities for the Sunkar Defense System. It integrates **spiral scanning patterns** with computer vision to automatically detect and track enemy targets (red balloons).

## Components

### 1. SimpleAutonomousMode
- **Purpose**: High-level autonomous control interface
- **Features**:
  - ✅ **Spiral scanning pattern** - covers both horizontal and vertical axes
  - ✅ **Slower, controlled motor movements** - precise positioning
  - ✅ Auto-fire capabilities
  - ✅ Target classification (enemy vs friendly)
  - ✅ Emergency stop functionality
  - ✅ GUI integration methods

### 2. Spiral Scanning System (NEW)
- **Purpose**: Comprehensive area coverage with controlled movements
- **Features**:
  - **Spiral Pattern**: Starts from center, expands outward in spiral motion
  - **Dual-Axis Coverage**: Covers both horizontal (stepper) and vertical (servo) axes
  - **Controlled Speed**: Slower movements (1.0° per step) for precision
  - **Auto-Reset**: Automatically resets to center when spiral completes
  - **Configurable Parameters**: Adjustable radius, angle, and speed settings

## Spiral Scanning Parameters

### Core Parameters
```python
spiral_center_servo = 30      # Center servo position
spiral_center_stepper = 150   # Center stepper position
spiral_radius = 0             # Current spiral radius
spiral_angle = 0              # Current spiral angle (radians)
spiral_radius_step = 0.5      # Radius increase per step
spiral_angle_step = 0.1       # Angle increase per step
max_spiral_radius = 20        # Maximum spiral radius
spiral_reset_threshold = 25   # Reset threshold
```

### Movement Control
```python
movement_speed = 1.0          # Degrees per movement (reduced from 2.0)
movement_interval = 0.05      # Seconds between movements (increased from 0.03)
movement_tolerance = 0.5      # Position tolerance (reduced from 1.0)
```

## How Spiral Scanning Works

### 1. Spiral Pattern Generation
```python
# Calculate spiral position
servo_offset = radius * cos(angle)
stepper_offset = radius * sin(angle)

# Calculate target positions
target_servo = center_servo + servo_offset
target_stepper = center_stepper + stepper_offset
```

### 2. Movement Control
- **Smooth Movement**: Gradual movement to target positions
- **Speed Limiting**: Maximum 1.0° per movement for precision
- **Position Tolerance**: Only move if change > 0.5° to avoid jitter
- **Boundary Limits**: Respect servo (5-55°) and stepper (10-290°) limits

### 3. Auto-Reset Mechanism
- When spiral radius reaches threshold (25), automatically reset to center
- Ensures continuous scanning without getting stuck at boundaries
- Provides complete area coverage over time

## Advantages of Spiral Scanning

### vs. Simple Horizontal Sweep
1. **Better Coverage**: Covers both axes instead of just horizontal
2. **More Efficient**: Spiral pattern provides better area coverage
3. **Controlled Movement**: Slower, more precise motor control
4. **Auto-Reset**: Never gets stuck at boundaries
5. **Predictable Pattern**: Systematic coverage of entire area

### Performance Benefits
- **Reduced Motor Stress**: Slower movements reduce wear and tear
- **Better Target Acquisition**: More thorough area coverage
- **Smoother Operation**: Controlled movements prevent jerky motion
- **Energy Efficient**: Optimized movement patterns

## Usage

### Starting Autonomous Mode
```python
# Initialize autonomous mode
autonomous = SimpleAutonomousMode(serial_comm, laser_control, camera_manager, motor_control)

# Activate (starts spiral scanning)
autonomous.activate()

# Check status
status = autonomous.get_status()
print(f"Active: {status['is_active']}")
print(f"Current target: {status['current_target']}")
print(f"Servo angle: {status['servo_angle']}")
print(f"Stepper angle: {status['stepper_angle']}")
```

### GUI Integration
The autonomous mode now fully integrates with the GUI:
- **`activate()`**: Starts autonomous mode and spiral scanning
- **`deactivate()`**: Stops autonomous mode
- **`process_frame(frame, tracks)`**: Processes camera frame and returns target info

### Status Messages
- **"SCANNING - spiral X% complete"**: When no targets detected
- **"TRACKING enemy X - distance: Ypx"**: When tracking enemy target
- **"FIRING at enemy X"**: When auto-firing at target
- **"TRACKING [type] X"**: When tracking non-enemy target

## Testing

### Test Spiral Scanning
```bash
cd sunkar-defense-system
python test_spiral_scanning.py
```

This will test:
- Spiral parameter initialization
- Position calculation
- Movement control
- Auto-reset functionality
- Coverage area analysis

### Test Full System
```bash
cd sunkar-defense-system
python src/main.py
```

Then:
1. Switch to "Auto" mode in GUI
2. Watch spiral scanning in action
3. Observe controlled motor movements
4. Test target detection and tracking

## Configuration

### Adjusting Spiral Parameters
```python
# For faster scanning (less precise)
autonomous.spiral_radius_step = 1.0
autonomous.spiral_angle_step = 0.2
autonomous.movement_speed = 2.0

# For slower scanning (more precise)
autonomous.spiral_radius_step = 0.3
autonomous.spiral_angle_step = 0.05
autonomous.movement_speed = 0.5
```

### Adjusting Coverage Area
```python
# For larger coverage area
autonomous.max_spiral_radius = 30
autonomous.spiral_reset_threshold = 35

# For smaller coverage area
autonomous.max_spiral_radius = 15
autonomous.spiral_reset_threshold = 20
```

## Troubleshooting

### Common Issues

1. **Spiral Not Moving**
   - Check motor connections
   - Verify serial communication
   - Check movement tolerance settings

2. **Jerky Movement**
   - Reduce `movement_speed`
   - Increase `movement_interval`
   - Check motor limits

3. **Incomplete Coverage**
   - Increase `max_spiral_radius`
   - Adjust `spiral_radius_step`
   - Check boundary limits

4. **GUI Not Responding**
   - Ensure `activate()` and `deactivate()` methods are called
   - Check `process_frame()` integration
   - Verify camera manager connection

## Safety Features

- **Emergency Stop**: Immediately stops all movement
- **Boundary Limits**: Respects motor position limits
- **Auto-Reset**: Prevents getting stuck at boundaries
- **Movement Tolerance**: Prevents unnecessary motor commands
- **Target Classification**: Only fires at enemy targets

## Performance Monitoring

The system provides real-time performance metrics:
- **FPS**: Control loop frequency
- **Target Count**: Number of detected targets
- **Current Target**: Active target being tracked
- **Spiral Progress**: Percentage of spiral completion
- **Motor Positions**: Current servo and stepper angles 