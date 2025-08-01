#include <Arduino.h>
#include <Servo.h>

// Stepper motor pins
#define STEP_PIN    2
#define DIR_PIN     3
#define ENABLE_PIN  4

// Servo motor pin
#define SERVO_PIN   9

// Stepper motor parameters
const int stepsPerRev = 200; // Full-step mode (1.8° per step)
const float degreesPerStep = 360.0 / stepsPerRev;
const int maxStepperAngle = 270;

// Servo parameters
const int minServoAngle = 0;
const int maxServoAngle = 180;

Servo myServo;
int currentStepperStep = 0; // Track current stepper position (in steps)

void setup() {
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW); // Enable stepper driver

  myServo.attach(SERVO_PIN);
  myServo.write(90); // Initialize servo to center

  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.startsWith("STEP:")) {
      int targetAngle = input.substring(5).toInt();
      targetAngle = constrain(targetAngle, 0, maxStepperAngle);
      int targetStep = round(targetAngle / degreesPerStep);
      moveStepperTo(targetStep);
    } else if (input.startsWith("SERVO:")) {
      int servoAngle = input.substring(6).toInt();
      servoAngle = constrain(servoAngle, minServoAngle, maxServoAngle);
      myServo.write(servoAngle);
    }
  }
}

void moveStepperTo(int targetStep) {
  int stepsToMove = targetStep - currentStepperStep;
  if (stepsToMove == 0) return;
  int dir = (stepsToMove > 0) ? HIGH : LOW;
  digitalWrite(DIR_PIN, dir);
  for (int i = 0; i < abs(stepsToMove); i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(2000);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(2000);
  }
  currentStepperStep = targetStep;
} 