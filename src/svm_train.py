#!/usr/bin/env python3
"""
SVM training module for color classification
"""

import numpy as np
import cv2
import pickle
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import pandas as pd

def train_color_classifier(data_file: str, model_file: str, encoder_file: str):
    """Train SVM classifier for color classification"""
    
    # Load training data
    print("Loading training data...")
    data = pd.read_csv(data_file)
    
    # Extract features and labels
    X = data[['R', 'G', 'B', 'H', 'S', 'V']].values
    y = data['Color'].values
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42
    )
    
    # Train SVM classifier
    print("Training SVM classifier...")
    svm_classifier = SVC(kernel='rbf', C=1.0, gamma='scale', random_state=42)
    svm_classifier.fit(X_train, y_train)
    
    # Evaluate model
    train_score = svm_classifier.score(X_train, y_train)
    test_score = svm_classifier.score(X_test, y_test)
    
    print(f"Training accuracy: {train_score:.3f}")
    print(f"Test accuracy: {test_score:.3f}")
    
    # Save model and encoder
    with open(model_file, 'wb') as f:
        pickle.dump(svm_classifier, f)
        
    with open(encoder_file, 'wb') as f:
        pickle.dump(label_encoder, f)
        
    print(f"Model saved to {model_file}")
    print(f"Encoder saved to {encoder_file}")
    
    return svm_classifier, label_encoder

def test_color_classifier(model_file: str, encoder_file: str):
    """Test trained color classifier"""
    
    # Load model and encoder
    with open(model_file, 'rb') as f:
        classifier = pickle.load(f)
        
    with open(encoder_file, 'rb') as f:
        encoder = pickle.load(f)
        
    # Test colors
    test_colors = [
        [255, 0, 0, 0, 255, 255],    # Red
        [0, 0, 255, 240, 255, 255],  # Blue
        [0, 255, 0, 120, 255, 255],  # Green
        [255, 255, 0, 60, 255, 255], # Yellow
    ]
    
    print("Testing color classifier...")
    for color in test_colors:
        prediction = classifier.predict([color])
        color_name = encoder.inverse_transform(prediction)[0]
        print(f"RGB({color[0]},{color[1]},{color[2]}) -> {color_name}")

if __name__ == "__main__":
    # Train classifier
    train_color_classifier(
        'labeled_colorss.csv',
        'svm_model.pkl',
        'label_encoder.pkl'
    )
    
    # Test classifier
    test_color_classifier('svm_model.pkl', 'label_encoder.pkl') 