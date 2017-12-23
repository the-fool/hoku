// #include <unistd.h>
#include "MicroBit.h"
#include "MicroBitUARTService.h"
#include "ubit-neopixel/uBit_neopixel.h"

MicroBit uBit;
_neopixel_strip_t pixels;
MicroBitI2C i2c = MicroBitI2C(I2C_SDA0, I2C_SCL0);
MicroBitAccelerometer acc = MicroBitAccelerometer(i2c);
MicroBitUARTService *uart;
MicroBitPin P0(MICROBIT_ID_IO_P0, MICROBIT_PIN_P0, PIN_CAPABILITY_ALL);
MicroBitSerial serial(USBTX, USBRX);

int i, r, g, b;
char buffer[64];

int pitch, roll, roll_quad, pitch_quad;

int* color;

int RED[] = {209,0,0};
int ORANGE[] = {255,102,34};
int YELLOW[] = {255,218,33};
int GREEN[] = {51,221,0};
int BLUE[] = {17,51,204};
int VIOLET[] = {51,0,68};

int COLORS[][] = { RED, ORANGE, YELLOW, GREEN, BLUE, VIOLET };

int contacted;
int LED_LEN = 1;
int prev_face = -1;
int face;

void setColor(int face) {
  /*
  if (face == 0) {
    color = RED;
    r = 250;
    b = 0;
    g = 0;
  }
  if (face == 1) {
    r = 0;
    b = 250;
    g = 0;
  }
  if (face == 2) {
    r = 0;
    b = 0;
    g = 250;
  }
  if (face == 3) {
    r = 120;
    b = 120;
    g = 0;
  }
  if (face == 4) {
    r = 120;
    b = 0;
    g = 120;
  }
  if (face == 5) {
    r = 250;
    b = 250;
    g = 120;
  }*/


  color = COLORS[face];

  for (i = 0; i < LED_LEN; i++)
    neopixel_set_color_and_show(&pixels, i, color[0], color[1], color[2]);
}
void onConnected(MicroBitEvent)
{
  uBit.display.print("C");
  connected = 1;
}

void onDisconnected(MicroBitEvent)
{
  uBit.display.print("D");
  connected = 0;
}

int getQuad(int deg) {
  if (deg > -45 && deg <= 45) {
    return 0;
  }

  if (deg >  45 && deg <= 90 + 45) {
    return 1;
  }

  if (deg > 90 + 45 || deg < -180 + 45) {
    return 2;
  }

  return 3;
}

int calcFace(int pitch_quad, int roll_quad) {
  // 0 - 5
  if (pitch_quad == 0) {
    // front or back
    return roll_quad;
  }

  if (pitch_quad == 1) {
    return 4;
  }

  if (pitch_quad == 3) {
    return 5;
  }

  return 5;
}

int getFace()
{
  pitch = acc.getPitch();
  roll = acc.getRoll();

  roll_quad = getQuad(roll);
  pitch_quad = getQuad(pitch);

  face = calcFace(pitch_quad, roll_quad);
}

void onContact(MicroBitEvent)
{
  contacted = P0.getDigitalValue();

  getFace();

  if (face != prev_face) {
    prev_face = face;
    if (contacted) {
      setColor(face);
    }
    sprintf(buffer, "%d%d", contacted, face);
    uart->send(buffer);
    uBit.sleep(500);
  }
}

void onButtonA(MicroBitEvent)
{
  getFace();

  setColor(face);

  sprintf(buffer, "1%d", face);

  uart->send(buffer);

  uBit.sleep(500);
}


int main() {
  uBit.init();
  uBit.display.scroll("GO");

  uBit.serial.baud(115200);
  acc.setRange(1);
  acc.setPeriod(20);

  uBit.messageBus.listen(MICROBIT_ID_BLE, MICROBIT_BLE_EVT_CONNECTED, onConnected);
  uBit.messageBus.listen(MICROBIT_ID_BLE, MICROBIT_BLE_EVT_DISCONNECTED, onDisconnected);

  uBit.messageBus.listen(MICROBIT_ID_IO_P0, MICROBIT_BUTTON_EVT_UP, onContact);
  uBit.messageBus.listen(MICROBIT_ID_IO_P0, MICROBIT_BUTTON_EVT_DOWN, onContact);
  uBit.io.P0.isTouched();

  // new MicroBitAccelerometerService(*uBit.ble, uBit.accelerometer);

  uart = new MicroBitUARTService(*uBit.ble, 32, 32);
  neopixel_init(&pixels, MICROBIT_PIN_P2, LED_LEN);

  uBit.messageBus.listen(MICROBIT_ID_BUTTON_A, MICROBIT_BUTTON_EVT_CLICK, onButtonA);


  while(1)
    uBit.sleep(50);

  release_fiber();
}
