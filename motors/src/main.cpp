#include <Arduino.h>
#include <Servo.h>

// Stepper motor pins (A4988)
#define STEP_PIN 2
#define DIR_PIN 3
#define ENABLE_PIN 8 // Optional, connect to A4988 ENABLE

// Servo pin
#define SERVO_PIN 9

const int stepsPerRevolution = 200; // 1.8° per step
const int maxStepperAngle = 270;
const int stepsForMax = (stepsPerRevolution * maxStepperAngle) / 360;

Servo myServo;

void setup() {
  // Stepper setup
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW); // Enable A4988 (LOW = enabled)

  // Servo setup
  myServo.attach(SERVO_PIN);
  myServo.write(0); // Start at 0°
}

void rotateStepperToAngle(int angle, bool dir, int stepDelay = 800) {
  int steps = (stepsPerRevolution * angle) / 360;
  digitalWrite(DIR_PIN, dir ? HIGH : LOW);
  for (int i = 0; i < steps; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(stepDelay);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(stepDelay);
  }
}

void loop() {
  // Example: Sweep stepper from 0° to 270° and back, servo from 0° to 60° and back

  // Stepper: 0° to 270°
  rotateStepperToAngle(270, true);
  delay(1000);

  // Stepper: 270° to 0°
  rotateStepperToAngle(270, false);
  delay(1000);

  // Servo: 0° to 60°
  myServo.write(60);
  delay(1000);

  // Servo: 60° to 0°
  myServo.write(0);
  delay(1000);
}