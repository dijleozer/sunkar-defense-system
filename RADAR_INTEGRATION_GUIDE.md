# Simple Radar Tracker Integration Guide

## Overview

The `SimpleRadarTracker` is a lightweight, effective system for radar-like scanning and target tracking. It's designed to work with your existing setup:

- **Stepper Motor**: Horizontal movement (0-300°)
- **Servo Motor**: Vertical movement (0-60°) with laser mounted
- **Camera**: Mounted on platform above laser
- **YOLO Detection**: Red balloons = enemies, Blue balloons = allies

## Key Features

### 🎯 **Simple & Effective**
- No complex PID controllers
- Gentle movement to prevent overshooting
- Easy to understand and modify

### 📡 **Radar Scanning**
- Horizontal sweep when no target detected
- Configurable scan speed (0.5-3.0°/s)
- Smooth back-and-forth movement

### 🎯 **Target Tracking**
- Automatically selects best red balloon target
- Prioritizes larger, more centered targets
- Smooth motor movement to keep target centered
- Configurable movement speed (0.5-3.0°/update)

## How It Works

### 1. **Scanning Mode** (No Target)
```
📡 Horizontal sweep: 0° → 300° → 0° → 300°...
   - Slow, smooth movement
   - Servo stays at middle position (30°)
   - Detects red balloons
```

### 2. **Tracking Mode** (Target Found)
```
🎯 When red balloon detected:
   - Calculate target center in image
   - Convert to motor angles
   - Move motors smoothly to center target
   - Keep tracking until target lost
```

### 3. **Target Selection**
```
🏆 Best target = (Size × 0.7) + (Center Proximity × 0.3)
   - Larger balloons get higher priority
   - More centered balloons get higher priority
   - Prevents switching between multiple targets
```

## Integration Steps

### Step 1: Import the Module
```python
from simple_radar_tracker import SimpleRadarTracker
```

### Step 2: Initialize Components
```python
# Your existing components
serial_comm = SerialComm(port="COM14", protocol="text")
camera_manager = CameraManager(serial_comm=serial_comm)

# New radar tracker
radar_tracker = SimpleRadarTracker(serial_comm, camera_manager)
```

### Step 3: Start the System
```python
# Start camera manager (your existing code)
camera_manager.start()

# Start radar tracker
radar_tracker.start()
```

### Step 4: Control Loop
```python
try:
    while True:
        # Your existing GUI/display code here
        # Radar tracker runs in background thread
        
        # Get status for display
        status = radar_tracker.get_status()
        print(f"Mode: {status['scan_mode']}, Target: {status['current_target']}")
        
        time.sleep(0.1)
        
except KeyboardInterrupt:
    radar_tracker.stop()
    camera_manager.stop()
```

## Configuration Options

### Scan Speed
```python
radar_tracker.set_scan_speed(1.0)  # degrees per second
# Range: 0.5 - 3.0
# Lower = slower, smoother scanning
# Higher = faster, more responsive
```

### Movement Speed
```python
radar_tracker.set_movement_speed(1.5)  # degrees per update
# Range: 0.5 - 3.0
# Lower = gentler, less overshooting
# Higher = faster, more responsive
```

### Target Loss Timeout
```python
radar_tracker.target_lost_timeout = 3.0  # seconds
# How long to wait before giving up on lost target
```

## Safety Features

### Emergency Stop
```python
radar_tracker.emergency_stop()  # Centers motors immediately
```

### Reset Position
```python
radar_tracker.reset_position()  # Returns to safe starting position
```

### Movement Limits
- **Servo**: 0° - 60° (hardware limits)
- **Stepper**: 0° - 300° (hardware limits)
- **Movement Speed**: Limited to prevent overshooting
- **Scan Speed**: Limited for smooth operation

## Troubleshooting

### Problem: Motors move too fast
**Solution**: Reduce movement speed
```python
radar_tracker.set_movement_speed(1.0)  # Try lower value
```

### Problem: Target tracking is jerky
**Solution**: Reduce scan speed and movement speed
```python
radar_tracker.set_scan_speed(0.5)
radar_tracker.set_movement_speed(0.8)
```

### Problem: System loses targets quickly
**Solution**: Increase target loss timeout
```python
radar_tracker.target_lost_timeout = 5.0  # More seconds
```

### Problem: Not detecting targets
**Solution**: Check camera and YOLO detection
```python
# Verify camera is working
frame, tracks = camera_manager.get_frame()
print(f"Detected {len(tracks)} objects")
```

## Performance Tips

### 1. **Start with Conservative Settings**
```python
radar_tracker.set_scan_speed(0.8)    # Slow scanning
radar_tracker.set_movement_speed(1.0) # Gentle movement
```

### 2. **Monitor Performance**
```python
status = radar_tracker.get_status()
print(f"Current mode: {status['scan_mode']}")
print(f"Motor positions: Servo={status['servo_angle']:.1f}°, Stepper={status['stepper_angle']:.1f}°")
```

### 3. **Fine-tune Based on Environment**
- **Indoor**: Use slower speeds
- **Outdoor**: Can use faster speeds
- **Moving targets**: Increase movement speed
- **Static targets**: Decrease movement speed

## Integration with Your GUI

The radar tracker works independently of your GUI. You can:

1. **Display Status**: Show current mode and target info
2. **Manual Override**: Allow manual control when needed
3. **Settings Panel**: Let users adjust speeds
4. **Emergency Controls**: Add emergency stop button

## Example Integration

```python
# In your main.py or GUI
from simple_radar_tracker import SimpleRadarTracker

class YourGUI:
    def __init__(self):
        # Your existing initialization
        self.radar_tracker = SimpleRadarTracker(serial_comm, camera_manager)
        
    def start_autonomous_mode(self):
        self.radar_tracker.start()
        
    def stop_autonomous_mode(self):
        self.radar_tracker.stop()
        
    def update_display(self):
        status = self.radar_tracker.get_status()
        # Update your GUI with status info
        self.display_mode(status['scan_mode'])
        self.display_target(status['current_target'])
        self.display_motor_positions(status['servo_angle'], status['stepper_angle'])
```

## Testing

Use the test script to verify everything works:

```bash
cd sunkar-defense-system/src
python test_simple_radar.py
```

This will start the radar tracker and let you test all features interactively.

## Summary

The `SimpleRadarTracker` provides:
- ✅ Simple, reliable radar scanning
- ✅ Smooth target tracking
- ✅ Prevents overshooting
- ✅ Easy to integrate
- ✅ Configurable parameters
- ✅ Safety features

It's designed to work with your existing system without requiring complex changes or PID tuning. 