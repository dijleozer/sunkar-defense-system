#include <Arduino.h>
#include <Servo.h>

// Stepper motor pins (A4988)
#define STEP_PIN 2
#define DIR_PIN 3
#define ENABLE_PIN 4

// Servo pin
#define SERVO_PIN 9

// Communication protocol
#define START_BYTE 0xAA
#define END_BYTE 0x55
#define SERVO_CMD 0x01
#define STEPPER_CMD 0x02

// Motor parameters
const int stepsPerRevolution = 200; // 1.8° per step
const int stepperMinAngle = 0;
const int stepperMaxAngle = 270;
const int servoMinAngle = 0;
const int servoMaxAngle = 60;

// Stepper state
float currentStepperAngle = stepperMinAngle;
float targetStepperAngle = stepperMinAngle;

// Servo state
int currentServoAngle = servoMinAngle;
int targetServoAngle = servoMinAngle;

// Stepper movement parameters
const int stepDelay = 800;        // Microseconds between steps
const int maxStepIncrement = 2;   // Maximum degrees per loop

Servo myServo;

void setup() {
  Serial.begin(9600);

  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);

  myServo.attach(SERVO_PIN);
  myServo.write(currentServoAngle);

  Serial.println("Arduino ready - Joystick Control System");
  Serial.println("Protocol: 0xAA + CMD + DATA + 0x55");
}

void moveStepperToAngle(float targetAngle) {
  targetAngle = constrain(targetAngle, stepperMinAngle, stepperMaxAngle);
  float angleDiff = targetAngle - currentStepperAngle;
  if (abs(angleDiff) < 0.5) return; // Already at target

  bool direction = (angleDiff > 0) ? HIGH : LOW;
  digitalWrite(DIR_PIN, direction);

  int stepsToMove = min(abs(angleDiff), maxStepIncrement) * stepsPerRevolution / 360.0;
  if (stepsToMove == 0) stepsToMove = 1; // Always move at least one step if not at target

  for (int i = 0; i < stepsToMove; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(stepDelay);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(stepDelay);
  }

  // Update current angle
  if (angleDiff > 0) {
    currentStepperAngle += (stepsToMove * 360.0 / stepsPerRevolution);
    if (currentStepperAngle > targetAngle) currentStepperAngle = targetAngle;
  } else {
    currentStepperAngle -= (stepsToMove * 360.0 / stepsPerRevolution);
    if (currentStepperAngle < targetAngle) currentStepperAngle = targetAngle;
  }
  currentStepperAngle = constrain(currentStepperAngle, stepperMinAngle, stepperMaxAngle);
}

void moveServoToAngle(int targetAngle) {
  targetAngle = constrain(targetAngle, servoMinAngle, servoMaxAngle);
  if (targetAngle != currentServoAngle) {
    myServo.write(targetAngle);
    currentServoAngle = targetAngle;
    delay(15);
  }
}

void processSerialCommand() {
  if (Serial.available() >= 4) {
    if (Serial.read() == START_BYTE) {
      byte cmd = Serial.read();
      byte data = Serial.read();
      if (Serial.read() == END_BYTE) {
        switch (cmd) {
          case SERVO_CMD:
            targetServoAngle = data;
            Serial.print("Servo target: ");
            Serial.println(targetServoAngle);
            break;
          case STEPPER_CMD:
            targetStepperAngle = data;
            Serial.print("Stepper target: ");
            Serial.println(targetStepperAngle);
            break;
          default:
            Serial.print("Unknown command: ");
            Serial.println(cmd);
            break;
        }
      }
    }
  }
}

void loop() {
  processSerialCommand();
  moveStepperToAngle(targetStepperAngle);
  moveServoToAngle(targetServoAngle);
  delay(10);
}
