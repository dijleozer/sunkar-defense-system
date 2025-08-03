#!/usr/bin/env python3
"""
Target prediction module for Sunkar Defense System
"""

import numpy as np
import cv2
import time
from typing import List, Tuple, Optional

class TargetPredictor:
    """
    Predicts target movement based on historical data
    """
    
    def __init__(self):
        self.history = []
        self.max_history = 10
        self.prediction_horizon = 5
        
    def add_observation(self, target_id: int, position: Tuple[int, int], timestamp: float):
        """Add new target observation"""
        observation = {
            'target_id': target_id,
            'position': position,
            'timestamp': timestamp
        }
        
        self.history.append(observation)
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
    def predict_position(self, target_id: int, time_ahead: float) -> Optional[Tuple[int, int]]:
        """Predict target position at future time"""
        # Get target history
        target_history = [obs for obs in self.history if obs['target_id'] == target_id]
        
        if len(target_history) < 3:
            return None
            
        # Calculate velocity
        velocities = []
        for i in range(1, len(target_history)):
            dt = target_history[i]['timestamp'] - target_history[i-1]['timestamp']
            if dt > 0:
                dx = target_history[i]['position'][0] - target_history[i-1]['position'][0]
                dy = target_history[i]['position'][1] - target_history[i-1]['position'][1]
                vx = dx / dt
                vy = dy / dt
                velocities.append((vx, vy))
                
        if not velocities:
            return None
            
        # Average velocity
        avg_vx = np.mean([v[0] for v in velocities])
        avg_vy = np.mean([v[1] for v in velocities])
        
        # Predict position
        last_pos = target_history[-1]['position']
        predicted_x = int(last_pos[0] + avg_vx * time_ahead)
        predicted_y = int(last_pos[1] + avg_vy * time_ahead)
        
        return (predicted_x, predicted_y)
        
    def get_target_velocity(self, target_id: int) -> Optional[Tuple[float, float]]:
        """Get current target velocity"""
        target_history = [obs for obs in self.history if obs['target_id'] == target_id]
        
        if len(target_history) < 2:
            return None
            
        # Calculate current velocity
        dt = target_history[-1]['timestamp'] - target_history[-2]['timestamp']
        if dt > 0:
            dx = target_history[-1]['position'][0] - target_history[-2]['position'][0]
            dy = target_history[-1]['position'][1] - target_history[-2]['position'][1]
            vx = dx / dt
            vy = dy / dt
            return (vx, vy)
            
        return None
        
    def clear_history(self):
        """Clear prediction history"""
        self.history.clear()
        
    def get_prediction_confidence(self, target_id: int) -> float:
        """Get confidence in prediction"""
        target_history = [obs for obs in self.history if obs['target_id'] == target_id]
        
        if len(target_history) < 3:
            return 0.0
            
        # Calculate prediction confidence based on velocity consistency
        velocities = []
        for i in range(1, len(target_history)):
            dt = target_history[i]['timestamp'] - target_history[i-1]['timestamp']
            if dt > 0:
                dx = target_history[i]['position'][0] - target_history[i-1]['position'][0]
                dy = target_history[i]['position'][1] - target_history[i-1]['position'][1]
                vx = dx / dt
                vy = dy / dt
                velocities.append((vx, vy))
                
        if len(velocities) < 2:
            return 0.5
            
        # Calculate velocity consistency
        vx_values = [v[0] for v in velocities]
        vy_values = [v[1] for v in velocities]
        
        vx_std = np.std(vx_values)
        vy_std = np.std(vy_values)
        
        # Higher consistency = higher confidence
        confidence = 1.0 / (1.0 + vx_std + vy_std)
        return min(1.0, max(0.0, confidence))

def test_target_predictor():
    """Test target predictor functionality"""
    print("=== Testing Target Predictor ===")
    
    predictor = TargetPredictor()
    
    # Simulate target movement
    current_time = time.time()
    positions = [
        (100, 100),
        (105, 102),
        (110, 104),
        (115, 106),
        (120, 108)
    ]
    
    # Add observations
    for i, pos in enumerate(positions):
        predictor.add_observation(1, pos, current_time + i * 0.1)
        
    # Test prediction
    predicted_pos = predictor.predict_position(1, 0.5)
    print(f"Predicted position: {predicted_pos}")
    
    # Test velocity
    velocity = predictor.get_target_velocity(1)
    print(f"Target velocity: {velocity}")
    
    # Test confidence
    confidence = predictor.get_prediction_confidence(1)
    print(f"Prediction confidence: {confidence:.2f}")
    
    print("✅ Target predictor test completed!")

if __name__ == "__main__":
    test_target_predictor() 