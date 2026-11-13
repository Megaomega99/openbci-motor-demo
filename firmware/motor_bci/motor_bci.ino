// Motor paso a paso controlado por el PC (demo_bci.py) por puerto serie, 115200 baudios.
// Comandos (terminados en \n):  R1 = girar, R0 = parar, D = invertir sentido, S<us> = microsegundos entre pasos
// Funciona en Arduino UNO/Nano y ESP32. Elige tu driver aquí abajo:

#define DRIVER_ULN2003      // 28BYJ-48 con placa ULN2003 (IN1..IN4)
// #define DRIVER_STEPDIR   // A4988 / DRV8825 / TMC2208 con NEMA17 (STEP/DIR/EN)

#ifndef LED_BUILTIN
#define LED_BUILTIN 2
#endif

#if defined(ESP32)
const int P1 = 26, P2 = 25, P3 = 33, P4 = 32;   // ULN2003 IN1..IN4  o  STEP=P1, DIR=P2, EN=P3
#else
const int P1 = 8, P2 = 9, P3 = 10, P4 = 11;     // ULN2003 IN1..IN4  o  STEP=P1, DIR=P2, EN=P3
#endif

#ifdef DRIVER_ULN2003
unsigned long stepUs = 1500;    // 28BYJ-48 en medio paso: no bajar de ~1000
const uint8_t SEQ[8][4] = {{1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
                           {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}};
int phase = 0;
#else
unsigned long stepUs = 1000;    // paso completo; con microstepping 1/16 usa ~100
#endif

bool running = false;
int dir = 1;
unsigned long lastStep = 0;
String buf;

void coilsOff() {
#ifdef DRIVER_ULN2003
  digitalWrite(P1, LOW); digitalWrite(P2, LOW); digitalWrite(P3, LOW); digitalWrite(P4, LOW);
#else
  digitalWrite(P3, HIGH);  // EN activo en bajo -> desactiva driver
#endif
}

void doStep() {
#ifdef DRIVER_ULN2003
  phase = (phase + dir + 8) % 8;
  digitalWrite(P1, SEQ[phase][0]); digitalWrite(P2, SEQ[phase][1]);
  digitalWrite(P3, SEQ[phase][2]); digitalWrite(P4, SEQ[phase][3]);
#else
  digitalWrite(P3, LOW);
  digitalWrite(P2, dir > 0 ? HIGH : LOW);
  digitalWrite(P1, HIGH); delayMicroseconds(5); digitalWrite(P1, LOW);
#endif
}

void handle(const String &c) {
  if (c == "R1")      { running = true; }
  else if (c == "R0") { running = false; coilsOff(); }
  else if (c == "D")  { dir = -dir; }
  else if (c.startsWith("S")) { long v = c.substring(1).toInt(); if (v > 50) stepUs = v; }
  digitalWrite(LED_BUILTIN, running ? HIGH : LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(P1, OUTPUT); pinMode(P2, OUTPUT); pinMode(P3, OUTPUT); pinMode(P4, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  coilsOff();
  // Prueba al arrancar: media vuelta corta para comprobar el cableado
  running = true;
  unsigned long t0 = millis();
  while (millis() - t0 < 600) { if (micros() - lastStep >= stepUs) { lastStep = micros(); doStep(); } }
  running = false; coilsOff();
}

void loop() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') { buf.trim(); handle(buf); buf = ""; }
    else if (ch != '\r') buf += ch;
  }
  if (running && micros() - lastStep >= stepUs) {
    lastStep = micros();
    doStep();
  }
}
