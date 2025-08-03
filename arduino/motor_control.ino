#include <Arduino.h>
#include <Servo.h>

// === Servo Ayarları ===
Servo servo;
const int servoPin = 9;
const int servoMinAngle = 0;
const int servoMaxAngle = 60;
int currentServoAngle = servoMinAngle;
int targetServoAngle = servoMinAngle;

// === Step Motor (A4988) Ayarları ===
#define STEP_PIN 2
#define DIR_PIN 3
#define ENABLE_PIN 4
const int stepsPerRevolution = 200;
const int stepperMinAngle = 0;
const int stepperMaxAngle = 300;
const int stepDelay = 1000;            // Slower but more stable
const int maxStepIncrement = 12;        // Larger steps for smoother movement
float currentStepperAngle = stepperMinAngle;
float targetStepperAngle = stepperMinAngle;

// === Anti-Jitter Filtreleme ===
const float angleTolerance = 3.0;      // Smaller tolerance for more precise control
const unsigned long minCommandInterval = 100;  // Faster response
unsigned long lastStepperCommand = 0;
int lastTargetStepperAngle = -1;

// === Lazer Ayarı ===
const int lazerPin = 6;

// === Protokol Tanımları ===
#define START_BYTE 0xAA
#define END_BYTE 0x55
#define SERVO_CMD 0x01
#define STEPPER_CMD 0x02
#define LASER_CMD 0x03

void setup() {
  servo.attach(servoPin);
  servo.write(currentServoAngle);

  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);  // Enable stepper motor permanently

  pinMode(lazerPin, OUTPUT);
  digitalWrite(lazerPin, LOW);

  Serial.begin(9600);
  Serial.println("Integrated Servo + Step + Lazer kontrol sistemi hazır.");
}

void loop() {
  if (Serial.available() > 0) {
    if (Serial.peek() == 'S' || Serial.peek() == 'M' || Serial.peek() == 'a' || Serial.peek() == 'p') {
      processTextCommand();
    }
    else if (Serial.peek() == START_BYTE) {
      processBinaryCommand();
    }
  }

  moveStepperToAngle(targetStepperAngle);
  moveServoToAngle(targetServoAngle);
  
  delay(10);  // Faster loop for better responsiveness
}

void processTextCommand() {
  String input = Serial.readStringUntil('\n');
  input.trim();

  if (input.startsWith("S")) {
    int angle = input.substring(1).toInt();
    targetServoAngle = constrain(angle, servoMinAngle, servoMaxAngle);
  } else if (input.startsWith("M")) {
    int angle = input.substring(1).toInt();
    // Improved anti-jitter filtering for stepper
    if (abs(angle - lastTargetStepperAngle) > angleTolerance || 
        (millis() - lastStepperCommand) > minCommandInterval) {
      targetStepperAngle = constrain(angle, stepperMinAngle, stepperMaxAngle);
      lastTargetStepperAngle = angle;
      lastStepperCommand = millis();
    }
  } else if (input == "a") {
    digitalWrite(lazerPin, HIGH);
  } else if (input == "p") {
    digitalWrite(lazerPin, LOW);
  }
}

void processBinaryCommand() {
  if (Serial.available() >= 4) {
    if (Serial.read() == START_BYTE) {
      byte cmd = Serial.read();
      byte data = Serial.read();
      if (Serial.read() == END_BYTE) {
        switch (cmd) {
          case SERVO_CMD:
            targetServoAngle = constrain(data, servoMinAngle, servoMaxAngle);
            break;
          case STEPPER_CMD:
            // Improved anti-jitter filtering for stepper
            if (abs(data - lastTargetStepperAngle) > angleTolerance || 
                (millis() - lastStepperCommand) > minCommandInterval) {
              targetStepperAngle = constrain(data, stepperMinAngle, stepperMaxAngle);
              lastTargetStepperAngle = data;
              lastStepperCommand = millis();
            }
            break;
          case LASER_CMD:
            digitalWrite(lazerPin, (data > 0) ? HIGH : LOW);
            break;
        }
      }
    }
  }
}

void moveServoToAngle(int targetAngle) {
  targetAngle = constrain(targetAngle, servoMinAngle, servoMaxAngle);
  if (currentServoAngle != targetAngle) {
    currentServoAngle += (currentServoAngle < targetAngle) ? 1 : -1;
    servo.write(currentServoAngle);
    delay(20);
  }
}

void moveStepperToAngle(float targetAngle) {
  targetAngle = constrain(targetAngle, stepperMinAngle, stepperMaxAngle);
  float angleDiff = targetAngle - currentStepperAngle;
  
  // Smaller tolerance for more precise control
  if (abs(angleDiff) < angleTolerance) return;

  bool direction = (angleDiff > 0) ? HIGH : LOW;
  digitalWrite(DIR_PIN, direction);

  // Calculate steps with larger increments for smoother movement
  int stepsToMove = min(abs(angleDiff), maxStepIncrement) * stepsPerRevolution / 360.0;
  if (stepsToMove == 0) stepsToMove = 1;

  // Smooth stepping with proper timing
  for (int i = 0; i < stepsToMove; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(stepDelay);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(stepDelay);
  }

  float stepMovedAngle = (stepsToMove * 360.0 / stepsPerRevolution);
  currentStepperAngle += direction == HIGH ? stepMovedAngle : -stepMovedAngle;
  currentStepperAngle = constrain(currentStepperAngle, stepperMinAngle, stepperMaxAngle);
}
